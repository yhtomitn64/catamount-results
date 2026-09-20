#!/usr/bin/env python3
"""Read Catamount's pre-Webscorer results pages (Wayback Machine copies) into data/extra/oldsite.json.

Before Webscorer, Catamount posted each night as a plain HTML page at
catamountoutdoor.com/results/YYYY/MMDDYY.htm. The 2019 pages (the only ones read so far)
are the age-group reports of the timing software: a title, a line naming the course, then a
section per distance ("5k", "2.5k", "10k" for the Tuesday run; "1 LAP", "2 LAPS", "Cadets" ...
for the Wednesday bike race) that holds one preformatted table per gender and age group.

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
TOKEN_RE = re.compile(r"<h2[^>]*>(.*?)</h2>|<pre[^>]*>(.*?)</pre>", re.S | re.I)


def clean_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def discipline_of(title: str) -> str | None:
    t = title.lower()
    if "cross" in t:
        return "CX"
    if "bike" in t or "bicycle" in t or "mtb" in t or "mountain" in t:
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
    if t in ("cadet", "cadets"):
        return "Cadet", None
    if m := re.fullmatch(r"(\d+(?:\.\d+)?) ?k", t):
        return f"{m[1]}K", None
    return None


def to_seconds(text: str) -> float | None:
    m = TIME_RE.match(text)
    if not m:
        return None
    h, mi, s, frac = m[1], m[2], m[3], m[4]
    return int(h or 0) * 3600 + int(mi) * 60 + int(s) + (float("0." + frac) if frac else 0.0)


def parse_page(html: str, url: str) -> dict | None:
    """One results page -> {date, discipline, course, rows}, or None if it is not a results page."""
    title_m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    title = clean_html(title_m.group(1)) if title_m else ""
    disc = discipline_of(title)
    date = course = None
    section = None
    rows: list[dict] = []
    skipped: list[str] = []

    for m in TOKEN_RE.finditer(html):
        if m.group(1) is not None:                       # a heading
            text = clean_html(m.group(1))
            try:
                date = datetime.datetime.strptime(text, "%B %d, %Y").date()
                continue
            except ValueError:
                pass
            section = section_label(text)
            if section is None:
                skipped.append(text)
            continue
        if section is None:
            continue
        for line in m.group(2).splitlines():
            line = re.sub(r"<[^>]+>", "", line).rstrip()
            chunks = [c for c in re.split(r"\s{2,}", line.strip()) if c]
            if len(chunks) < 3 or not chunks[0].isdigit():
                continue                                   # column headings, blank lines, "Top" anchors
            secs = to_seconds(chunks[-1])
            name = scrape.clean_name(chunks[1])
            if secs is None or not name or re.search(r"\d", name) or name.lower().startswith("participant"):
                continue                                   # DNF rows, "Participant 559", other placeholders
            rows.append({"name": name, "racer": scrape.racer_key(name), "distance": section[0], "laps": section[1],
                         "time": chunks[-1], "seconds": secs})

    course_m = re.search(r"<b><i>(.*?)</i></b>", html, re.S | re.I)
    if course_m:
        line = clean_html(course_m.group(1))
        cm = re.match(r"(.+?)\s*(?:course\s*)?-\s*\d+\s+\w+\s*$", line, re.I) or re.match(r"(.+?)\s*(?:course)?\s*$", line, re.I)
        course = scrape.normalize_course(re.sub(r"\s*course\s*$", "", cm.group(1), flags=re.I)) if cm else None
        if course and not re.fullmatch(r"(Red|Black|Yellow|White|Green|Orange|Blue|Purple) (on|in) (Red|Black|Yellow|White|Green|Orange|Blue|Purple)", course):
            course = None                                  # not a course name after all
    if not (date and disc and rows):
        return None
    return {"date": date, "discipline": disc, "course": course, "title": title, "rows": rank(rows), "skipped": skipped}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="show how each cached page parses; write nothing")
    args = ap.parse_args()

    seen: dict[str, tuple[str, str]] = {}
    for ts, url in wayback.cdx("catamountoutdoor.com/results/", match="prefix", limit=5000):
        norm = re.sub(r":80(?=/)", "", url.replace("https://", "http://").replace("://www.", "://"))
        seen.setdefault(norm, (ts, url))

    races, results, pages = [], [], 0
    for norm, (ts, url) in sorted(seen.items()):
        if not re.search(r"/results/\d{4}/\d{6}\.htm$", norm):
            continue
        html = wayback.cached(ts, url)
        if html is None:
            continue
        pages += 1
        page = parse_page(html, url)
        label = norm.split("/results/")[-1]
        if page is None:
            print(f"  {label:18} not a results page")
            continue
        name_date = re.search(r"/(\d\d)(\d\d)(\d\d)\.htm$", norm)
        mm, dd, yy = (int(x) for x in name_date.groups())
        if (page["date"].month, page["date"].day, page["date"].year % 100) != (mm, dd, yy):
            print(f"  {label:18} DATE MISMATCH: page says {page['date']}", file=sys.stderr)
            continue
        raceid = -(int(page["date"].strftime("%Y%m%d")) * 10 + CODE[page["discipline"]])
        groups = sorted({r["distance"] for r in page["rows"]})
        print(f"  {label:18} {page['date']} {page['discipline']:3} {(page['course'] or '?'):16} {len(page['rows']):4} rows  {groups}"
              + (f"  ignored headings: {page['skipped']}" if page["skipped"] else ""))
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
