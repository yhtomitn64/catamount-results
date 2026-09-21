#!/usr/bin/env python3
"""Read Catamount's pre-Webscorer results pages (Wayback Machine copies) into data/extra/oldsite.json.

Before Webscorer, Catamount posted each night as a plain HTML page, at first in the site root
(catamountoutdoor.com/MMDDYY.HTM, 2001-2009), later under /results/YYYY/. Formats read:

  2001-2003  a "Click on the class you want" index, then one small table per class
      (Rank, Bib, Name, Result). Trail run classes carry no distance ("Full course" plus a "Cadet"
      partial lap); bike classes say "1 lap", "2 laps", "1KF" (kids), "Cadet Partial Lap". The page
      names the course ("The Hill Course", "The Blue Course").
  2004-2013, 2017-2019  the age-group reports of the timing software: a title, a section per
      distance ("5k", "2.5k", "10k" for the Tuesday run; "1 LAP", "2 LAPS", "Cadets" ... for the
      Wednesday bike race) holding one preformatted table per gender and age group. 2004-2005
      put the distance inside each age heading and add a Pace column; 2006-2013 head each distance
      with a centred <h1>; 2019 names the course under the date.
  2007-2008  courses (Pink / Blue / Purple) come from the series index pages results07.html and
      results08.html, whose drop-downs read "May 29 Pink Course".
  2017-2019 cyclocross  CrossMgr saves (one JSON payload with every rider's lap times).
  2006-2008, 2012 cyclocross  nights typed up in Word ("1. First Last 34:20", a lap down as "-1 lap"), at
      catamountoutdoor.com/cxMMDDYY.htm (the night is taken from the file name; the heading is sometimes stale).

The night's date is the first of {title date, file-name date, heading date} that falls on the sport's
weekday (Tuesday run, Wednesday bike and cross); pages copied forward often keep last week's heading.

Not read: special events (Flower Power, Bramble Scramble, the Eastern Cup, Stampy Stomp), the
attendance/team reports, and 2018/052218.htm, an Excel export whose times are not reliably
minutes and seconds. Years with no page in the archive (2011, 2014-2016, most of 2012/2018) are
simply absent.

    python tools/oldsite.py            # parse every archived page already in cache/wayback/
    python tools/oldsite.py --list     # what is cached and how each page parses

This never touches the network: `tools/wayback.py` (slow, polite, cached) fetches the pages.

Only what a results board shows and the site publishes is kept: name, placing, time, distance
group and laps. Team, bib, age and gender are read to find the columns and then dropped. The
page's own placing is within a gender/age table, so the placing here is recomputed inside each
distance group from the times, the same unit the rest of the site uses.
"""
from __future__ import annotations

import argparse
import datetime
import html as htmllib
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scrape  # noqa: E402
import wayback  # noqa: E402
from virtual_2021 import rank  # noqa: E402  (one row per rider per group, placing within the group)

OUT = scrape.DATA / "extra" / "oldsite.json"
CODE = {"MTB": 1, "TR": 2, "CX": 3}
TIME_RE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{2})(?:\.(\d+))?$")
# 2017-2019 pages head each distance with an <h2>; the 2009-2013 pages head it with a centred <h1>
# and use <h2> for the age/gender tables inside it.
TOKEN_RE = re.compile(r"<h1[^>]*align=.?center.?[^>]*>(.*?)</h1>|<h2[^>]*>(.*?)</h2>|<pre[^>]*>(.*?)</pre>", re.S | re.I)


def clean_html(text: str) -> str:
    """Tags out, entities (&nbsp; &amp;) decoded, whitespace collapsed."""
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", text)).replace(" ", " ")).strip()


def discipline_of(title: str) -> str | None:
    t = title.lower()
    if "cross" in t:
        return "CX"
    if re.search(r"bik|bicycle|mtb|mtn|mountain", t):
        return "MTB"
    if "run" in t:
        return "TR"
    return None


def section_label(h2: str) -> tuple[str, int | None] | None:
    """A section heading -> (the label the site uses, laps). None for anything unrecognised."""
    t = clean_html(h2).lower()
    if m := re.fullmatch(r"(\d) laps? kids", t):
        return f"{m[1]} Lap Kids", int(m[1])
    if m := re.fullmatch(r"(\d) laps?", t):
        return f"{m[1]} Lap", int(m[1])
    if m := re.fullmatch(r"(\d) laps? \d+ (?:&|and)? ?under(?: [\d:]+ start)?", t):      # "2 lap 12 under": the children's group of that distance
        return f"{m[1]} Lap Kids", int(m[1])
    if t in ("cadet", "cadets", "1/2 lap", "1/2 lap cadets", "cadets 1/2 lap"):
        return "Cadet", None
    if m := re.fullmatch(r"(?:cadets? ~)?(\d+(?:\.\d+)?) ?k(?:ilometers?|m)?", t):     # "5k", "5 Kilometer", "Cadets ~2.5 Kilometer"
        return f"{m[1]}K", None
    return None


# The boards carry the odd timing-day glitch (a 5K in 1:40, four laps in 27 minutes). Anything faster
# than this per group cannot have been run, so the row is left out rather than published as a result.
FASTEST = {"5K": 720, "2.5K": 360, "10K": 1440, "Cadet": 240}
SECONDS_PER_LAP = 450


def impossible(distance: str, laps: int | None, seconds: float) -> bool:
    floor = FASTEST.get(distance) or (SECONDS_PER_LAP * laps if laps else 0)
    return seconds < floor


def category_distance(heading: str) -> tuple[str, int | None] | None:
    """The distance inside an age/gender heading ("Teen (13-17) 5k Female"), on pages with no distance heading."""
    t = clean_html(heading).lower()
    if m := re.search(r"(?<![\d.])(\d+(?:\.\d+)?) ?k(?:m|ilometers?)?\b", t):
        return f"{m[1]}K", None
    return None


def to_seconds(text: str) -> float | None:
    m = TIME_RE.match(text)
    if not m:
        return None
    h, mi, s, frac = m[1], m[2], m[3], m[4]
    return int(h or 0) * 3600 + int(mi) * 60 + int(s) + (float("0." + frac) if frac else 0.0)


def fmt_time(sec: float) -> str:
    """Seconds -> the "m:ss.t" / "h:mm:ss.t" the page and Webscorer show."""
    tenths = int(round(sec * 10))
    h, rem = divmod(tenths, 36000)
    m, rem = divmod(rem, 600)
    return f"{h}:{m:02d}:{rem // 10:02d}.{rem % 10}" if h else f"{m}:{rem // 10:02d}.{rem % 10}"


def parse_crossmgr(html: str) -> dict | None:
    """A cyclocross night saved by CrossMgr: one JSON payload in the page, a lap-time list per bib.

    Same shape as Webscorer's cross results: one undivided field, laps completed decide the order,
    and a rider a lap or more down shows "-N laps" instead of a time.
    """
    start = html.find("var payload = ")
    if start < 0:
        return None
    try:
        payload, _ = json.JSONDecoder().raw_decode(html[start + len("var payload = "):])
        date = datetime.date.fromisoformat(payload["raceDate"])
    except (ValueError, KeyError):
        return None
    riders = []
    for entry in payload.get("data", {}).values():
        first, last = (entry.get("FirstName") or "").strip(), (entry.get("LastName") or "").strip()
        times = entry.get("raceTimes") or []
        if not last or entry.get("status") != "Finisher" or len(times) < 2:
            continue                                        # no name on the sheet, or never completed a lap
        name = scrape.clean_name(" ".join(w.title() if w.isupper() else w for w in f"{first} {last}".split()))
        if name:
            riders.append((name, len(times) - 1, float(entry["lastTime"])))
    if not riders:
        return None
    lead = max(laps for _, laps, _ in riders)
    riders.sort(key=lambda r: (-r[1], r[2]))
    rows = []
    for name, laps, secs in riders:
        down = lead - laps
        rows.append({"name": name, "racer": scrape.racer_key(name), "distance": "", "laps": laps,
                     "time": fmt_time(secs) if not down else f"-{down} lap{'s' if down > 1 else ''}",
                     "seconds": secs if not down else None})
    seen, out = set(), []
    for i, r in enumerate(rows):                            # one row per rider; sorted, so the first is the best
        if r["racer"] in seen:
            continue
        seen.add(r["racer"])
        out.append({**r, "place": len(out) + 1})
    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    return {"date": date, "discipline": "CX", "course": None, "rows": out, "skipped": [],
            "title": clean_html(title_m.group(1)) if title_m else "Cyclocross"}


def parse_text_cx(html: str, url: str) -> dict | None:
    """A cyclocross night typed up in Word (2006-2008, 2012): "1. First Last 34:20", a lap down as "-1 lap".

    The night is named in the file (cxMMDDYY.htm); the heading inside is sometimes last week's. Men and
    women are listed separately but raced together, so they are one undivided field: rows with a time
    first, by time, then riders a lap or more down in the order printed. The lead lap count is not on
    the page, so `laps` is left empty.
    """
    fm = re.search(r"/cx(\d\d)(\d\d)(\d\d)\.html?$", url, re.I)
    if not fm:
        return None
    try:
        date = datetime.date(2000 + int(fm[3]), int(fm[1]), int(fm[2]))
    except ValueError:
        return None
    if date.weekday() != 2:
        return None
    paras = [clean_html(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", html, re.S | re.I)]
    rows = []
    for order, p in enumerate(paras):
        m = re.match(r"(\d+) ?\.? (.+?) (\d{1,2}:\d{2}(?::\d{2})?|-\d+(?: laps?)?)(?: F?\d+)?$", p)
        name = scrape.clean_name(re.sub(r"\([^)]*\)", " ", m[2])) if m else None
        if not name:
            continue
        down = int(m[3][1:].split()[0]) if m[3].startswith("-") else 0
        rows.append({"name": name, "racer": scrape.racer_key(name), "distance": "", "laps": None, "order": order,
                     "time": m[3] if not down else f"-{down} lap{'s' if down > 1 else ''}",
                     "seconds": None if down else to_seconds(m[3]), "down": down})
    if len(rows) < 8:
        return None
    rows.sort(key=lambda r: (r["down"], r["seconds"] or 0, r["order"]))
    seen, out = set(), []
    for r in rows:
        if r["racer"] in seen:
            continue
        seen.add(r["racer"])
        out.append({k: v for k, v in r.items() if k not in ("order", "down")} | {"place": len(out) + 1})
    return {"date": date, "discipline": "CX", "course": None, "rows": out, "skipped": [], "title": "Catamount Cyclocross Series"}


def class_label(cls: str, disc: str) -> tuple[str, int | None] | None:
    """A class title from the 2001-2003 tables -> (group label, laps). Tandem teams are skipped."""
    t = re.sub(r"\s+", " ", cls).strip().lower()
    if "tandem" in t:
        return None
    if "cadet" in t:
        return "Cadet", None
    if disc == "TR":
        return "Full course", None                       # the run's length is not stated on these pages
    if m := re.fullmatch(r"(\d)([a-z])([fm])", t):        # "1KF": laps, class (K = kids), gender
        n = int(m[1])
        return (f"{n} Lap Kids" if m[2] == "k" and n == 1 else f"{n} Lap"), n
    m = re.search(r"\b(\d) ?laps?\b", t)
    if "full lap" in t or (m and re.search(r"\bkids?\b", t)):
        return "1 Lap Kids", 1
    if m:
        return f"{m[1]} Lap", int(m[1])
    return None


def parse_class_tables(html: str, url: str) -> dict | None:
    """2001-2003 pages: a "Click on the class you want" index, then one small table per class."""
    title_m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    title = clean_html(title_m.group(1)) if title_m else ""
    disc = discipline_of(title)
    root_m = re.search(r"/(\d\d)(\d\d)(\d\d)\.html?$", url, re.I)
    if not (disc and root_m):
        return None                                       # a duathlon or other one-off is not part of the series
    try:
        date = datetime.date(2000 + int(root_m[3]), int(root_m[1]), int(root_m[2]))
    except ValueError:
        return None
    if date.weekday() != {"TR": 1, "MTB": 2}.get(disc, -1):
        return None
    cm = re.search(r'The\s+["\u201c]?([A-Z][a-z]+)\s+Course', html[:4000])
    rows: list[dict] = []
    dropped: list[str] = []
    for tm in re.finditer(r"<TABLE BORDER>(.*?)</TABLE>", html, re.S | re.I):
        block = tm.group(1)
        th = re.search(r"<TH[^>]*COLSPAN[^>]*>(.*?)</TH>", block, re.S | re.I)
        label = class_label(clean_html(th.group(1)), disc) if th else None
        if label is None:
            continue
        for tr in re.findall(r"<TR[^>]*>(.*?)</TR>", block, re.S | re.I):
            tds = [clean_html(x) for x in re.findall(r"<TD[^>]*>(.*?)</TD>", tr, re.S | re.I)]
            if len(tds) < 4 or not tds[0].isdigit():
                continue
            secs = to_seconds(tds[3])
            name = scrape.clean_name(tds[2])
            if secs is None or not name or re.search(r"\d", name):
                continue
            if impossible(label[0], label[1], secs):
                dropped.append(f"{name} {tds[3]} ({label[0]})")
                continue
            rows.append({"name": name, "racer": scrape.racer_key(name), "distance": label[0], "laps": label[1],
                         "time": tds[3], "seconds": secs})
    if not rows:
        return None
    return {"date": date, "discipline": disc, "course": f"{cm[1]} Course" if cm else None, "title": title,
            "rows": rank(rows), "skipped": [], "dropped": dropped}


def parse_page(html: str, url: str) -> dict | None:
    """One results page -> {date, discipline, course, rows}, or None if it is not a results page."""
    if "Click on the class you want" in html:
        return parse_class_tables(html, url)
    if "Microsoft Word" in html[:3000]:
        return parse_text_cx(html, url)
    if "generator" in html[:3000] and "CrossMgr" in html[:3000]:
        return parse_crossmgr(html)
    title_m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    title = clean_html(title_m.group(1)) if title_m else ""
    disc = discipline_of(title)
    date = course = None
    section = None
    rows: list[dict] = []
    skipped: list[str] = []
    dropped: list[str] = []

    h1_sections = False
    for m in TOKEN_RE.finditer(html):
        if m.group(1) is not None:                       # a centred <h1>: the distance, on the older pages
            h1_sections = True
            section = section_label(m.group(1))
            if section is None:
                skipped.append(clean_html(m.group(1)))
            continue
        if m.group(2) is not None:                       # an <h2>
            text = clean_html(m.group(2))
            try:
                date = datetime.datetime.strptime(text, "%B %d, %Y").date()
                continue
            except ValueError:
                pass
            if h1_sections:
                continue                                 # an age/gender table inside the current distance
            section = section_label(text) or category_distance(text)
            if section is None:
                skipped.append(text)
            continue
        if section is None:
            continue
        for line in m.group(3).splitlines():
            line = htmllib.unescape(re.sub(r"<[^>]+>", "", line)).replace(" ", " ").rstrip()
            chunks = [c for c in re.split(r"\s{2,}", line.strip()) if c]
            if len(chunks) < 3 or not chunks[0].isdigit():
                continue                                   # column headings, blank lines, "Top" anchors
            time_text = next((c for c in reversed(chunks[2:]) if to_seconds(c) is not None), chunks[-1])
            secs = to_seconds(time_text)
            name = scrape.clean_name(chunks[1])
            if secs is None or not name or re.search(r"\d", name) or name.lower().startswith("participant"):
                continue                                   # DNF rows, "Participant 559", other placeholders
            if impossible(section[0], section[1], secs):
                dropped.append(f"{name} {time_text} ({section[0]})")
                continue
            rows.append({"name": name, "racer": scrape.racer_key(name), "distance": section[0], "laps": section[1],
                         "time": time_text, "seconds": secs})

    course_m = re.search(r"<b><i>(.*?)</i></b>", html, re.S | re.I)
    if course_m:
        line = clean_html(course_m.group(1))
        cm = re.match(r"(.+?)\s*(?:course\s*)?-\s*\d+\s+\w+\s*$", line, re.I) or re.match(r"(.+?)\s*(?:course)?\s*$", line, re.I)
        course = scrape.normalize_course(re.sub(r"\s*course\s*$", "", cm.group(1), flags=re.I)) if cm else None
        if course and not re.fullmatch(r"(Red|Black|Yellow|White|Green|Orange|Blue|Purple) (on|in) (Red|Black|Yellow|White|Green|Orange|Blue|Purple)", course):
            course = None                                  # not a course name after all
    # The heading's date is sometimes left over from the night before and the title has typos too, so the
    # candidates are the title's date, the date in the file name and the heading's, and the first one that
    # falls on the sport's weekday wins (Tuesday run, Wednesday bike and cross).
    year_m = re.search(r"/results/(\d{4})/", url)
    root_m = re.search(r"/(\d\d)(\d\d)(\d\d)\.html?$", url, re.I)         # pages are named MMDDYY
    year = int(year_m[1]) if year_m else (2000 + int(root_m[3]) if root_m else None)
    tm = re.search(r"(\d{1,2})/(\d{1,2})", title)
    candidates = []
    for month, day in ([(int(tm[1]), int(tm[2]))] if tm else []) + ([(int(root_m[1]), int(root_m[2]))] if root_m else []):
        try:
            candidates.append(datetime.date(year, month, day))
        except (ValueError, TypeError):
            pass
    if date:
        candidates.append(date)
    weekday = {"TR": 1, "MTB": 2, "CX": 2}.get(disc)
    date = next((d for d in candidates if d.weekday() == weekday), None)
    if not (date and disc and rows):
        return None
    return {"date": date, "discipline": disc, "course": course, "title": title, "rows": rank(rows), "skipped": skipped, "dropped": dropped}


MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def index_courses() -> dict[datetime.date, str]:
    """Course per night from the 2007 and 2008 series index pages.

    Those pages are a drop-down per series whose entries read "May 29 Pink Course" and point at the
    night's results page, so the course is Catamount's own label for that night. An "Invite" night
    (no course named), a cancelled night and a nickname without the word Course are left alone.
    """
    out: dict[datetime.date, str] = {}
    for ts, url in wayback.cdx("catamountoutdoor.com/results/", match="prefix", limit=5000):
        m = re.search(r"/results(\d\d)\.html$", wayback.norm_url(url))
        html = wayback.cached(ts, url) if m else None
        if not html:
            continue
        year = 2000 + int(m[1])
        for label in re.findall(r'<option value="[^"]*">([^<]+)</option>', html):
            lm = re.match(r"([A-Za-z]+)\s*(\d{1,2})\s+(?:New\s+)?(Pink|Blue|Purple|Green|Red|Yellow|Hill|Black|White|Orange)\s+Course", label.strip())
            if lm and lm[1][:3].lower() in MONTHS:
                try:
                    out[datetime.date(year, MONTHS[lm[1][:3].lower()], int(lm[2]))] = f"{lm[3]} Course"
                except ValueError:
                    pass
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="show how each cached page parses; write nothing")
    args = ap.parse_args()

    from_index = index_courses()
    races, results, pages = [], [], 0
    found = {**wayback.candidates("catamountoutdoor.com/results/"), **wayback.candidates("catamountoutdoor.com/cx"),
             **wayback.candidates("catamountoutdoor.com/0")}
    for norm, captures in sorted(found.items()):
        if not re.search(r"/(?:results/\d{4}/(?:cx)?|cx)?\d{6}\.html?$", norm, re.I):
            continue
        # The earliest capture that is on disk and parses; captures that were never fetched are skipped.
        page = ts = url = None
        for ts, url in captures:
            html = wayback.cached(ts, url)
            if html is not None and (page := parse_page(html, url)):
                break
        label = norm.split("catamountoutdoor.com/")[-1].replace("results/", "")
        pages += 1
        if page is None:
            print(f"  {label:18} not a results page")
            continue
        if not page["course"] and page["date"] in from_index:
            page["course"] = from_index[page["date"]]
        raceid = -(int(page["date"].strftime("%Y%m%d")) * 10 + CODE[page["discipline"]])
        if any(r["raceid"] == raceid for r in races):
            print(f"  {label:18} DUPLICATE night {page['date']}, skipped", file=sys.stderr)
            continue
        groups = sorted({r["distance"] for r in page["rows"]})
        print(f"  {label:18} {page['date']} {page['discipline']:3} {(page['course'] or '?'):16} {len(page['rows']):4} rows  {groups}"
              + (f"  ignored headings: {page['skipped']}" if page["skipped"] else "")
              + (f"  left out as impossible times: {len(page['dropped'])}" if page.get("dropped") else ""))
        races.append({"raceid": raceid, "title": page["title"], "url": f"https://web.archive.org/web/{ts}/{url}",
                      "date": page["date"].isoformat(), "year": page["date"].year, "discipline": page["discipline"],
                      "course": page["course"]})
        results += [{"raceid": raceid, **r} for r in page["rows"]]

    print(f"\n{pages} cached pages, {len(races)} parsed races, {len(results)} results.")
    if args.list or not races:
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": "catamountoutdoor.com results pages, via the Wayback Machine",
                               "races": races, "results": results}, indent=1), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(scrape.ROOT)}")


if __name__ == "__main__":
    main()
