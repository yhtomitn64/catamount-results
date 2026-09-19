#!/usr/bin/env python3
"""Scrape Catamount Outdoor Family Center race results from Webscorer.

Two phases, run independently so you can re-run one without the other:

    python scrape.py discover    # find every Catamount race -> data/races.json
    python scrape.py fetch       # pull each race's results -> data/results.json
    python scrape.py build       # emit data/catamount.{json,js} for index.html
    python scrape.py all         # all three

Every page fetched is cached under cache/ as raw HTML. Re-runs are free and the
cache is what you iterate the parser against when a page turns out to be shaped
differently than expected.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time
import unicodedata

import requests
from bs4 import BeautifulSoup, NavigableString

ROOT = pathlib.Path(__file__).resolve().parent
CACHE = ROOT / "cache"
DATA = ROOT / "data"

BASE = "https://www.webscorer.com"
ORGANIZER = f"{BASE}/cofc"
UA = "catamount-results/1.0 (personal race-results archive; contact via github.com/yhtomitn64/catamount-results)"
DELAY = 1.0  # seconds between live requests


# --------------------------------------------------------------------------
# fetching
# --------------------------------------------------------------------------

_session = requests.Session()
_session.headers["User-Agent"] = UA
_last_request = 0.0


def fetch(url: str, cache_key: str, refresh: bool = False) -> str:
    """GET url, caching the body under cache/<cache_key>.html."""
    global _last_request
    path = CACHE / f"{cache_key}.html"
    if path.exists() and not refresh:
        return path.read_text(encoding="utf-8", errors="replace")

    wait = DELAY - (time.time() - _last_request)
    if wait > 0:
        time.sleep(wait)
    resp = _session.get(url, timeout=30)
    _last_request = time.time()
    resp.raise_for_status()

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(resp.text, encoding="utf-8")
    return resp.text


# --------------------------------------------------------------------------
# title parsing
# --------------------------------------------------------------------------

# Titles come in three date shapes:
#   "Catamount 6-21-23 MTB Race (Yellow on Green)"     m-d-yy
#   "2021-07-13 Catamount trail running race"           ISO
#   "Catamount Cyclocross Race 15-Sep-2021"             d-Mon-yyyy
TITLE_RE = re.compile(r"(?P<m>\d{1,2})[-/](?P<d>\d{1,2})[-/](?P<y>\d{2,4})")
ISO_RE = re.compile(r"(?P<y>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})")
DMY_RE = re.compile(r"(?P<d>\d{1,2})-(?P<mon>[A-Za-z]{3})[a-z]*-(?P<y>\d{4})")
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
COURSE_RE = re.compile(r"\(([^)]+)\)")

DISCIPLINE_NAMES = {"MTB": "Mountain bike", "TR": "Trail run", "CX": "Cyclocross", "XC": "Cross country", "SS": "Single speed"}


def discipline_from_title(title: str) -> str | None:
    t = title.lower()
    if "cyclocross" in t or re.search(r"\bcx\b", t):
        return "CX"
    if "mtb" in t:
        return "MTB"
    if "trail" in t or re.search(r"\btr\b", t):
        return "TR"
    return None


def parse_title(title: str) -> dict:
    """Pull date, discipline and course out of a Webscorer race title."""
    out = {"date": None, "year": None, "discipline": discipline_from_title(title), "course": None}

    y = mo = d = None
    if m := ISO_RE.search(title):
        y, mo, d = int(m["y"]), int(m["m"]), int(m["d"])
    elif m := DMY_RE.search(title):
        y, mo, d = int(m["y"]), MONTHS.get(m["mon"].lower()), int(m["d"])
    elif m := TITLE_RE.search(title):
        mo, d, y = int(m["m"]), int(m["d"]), int(m["y"])
        if y < 100:
            y += 2000
    if y and mo and d and 1 <= mo <= 12 and 1 <= d <= 31 and 1990 <= y <= 2100:
        out["date"] = f"{y:04d}-{mo:02d}-{d:02d}"
        out["year"] = y

    c = COURSE_RE.search(title)
    if c:
        out["course"] = normalize_course(c.group(1))
    return out


def normalize_course(raw: str) -> str:
    """'YELLOW ON  green' and 'Yellow on Green' are the same course."""
    words = re.sub(r"\s+", " ", raw).strip().split(" ")
    out = []
    for w in words:
        out.append(w.lower() if w.lower() in {"on", "the", "and", "of"} else w.capitalize())
    if out:
        out[0] = out[0].capitalize()
    return " ".join(out)


def racer_key(name: str) -> str:
    """Stable id for a person. Webscorer names vary in case and spacing."""
    n = unicodedata.normalize("NFKD", name)
    n = "".join(ch for ch in n if not unicodedata.combining(ch))
    n = re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")
    return n


# --------------------------------------------------------------------------
# discover
# --------------------------------------------------------------------------

RACEID_RE = re.compile(r"raceid=(\d+)", re.I)


def discover(refresh: bool = False, extra_ids: list[int] | None = None) -> list[dict]:
    """Find every Catamount race id Webscorer will show us."""
    found: dict[int, str] = {}

    # One page lists every race. (?pg=N is not pagination; it returns the same page.)
    pages = [(ORGANIZER, "organizer")]

    for url, key in pages:
        try:
            html = fetch(url, key, refresh=refresh)
        except requests.HTTPError as exc:
            print(f"  {url}: {exc}", file=sys.stderr)
            break
        before = len(found)
        for a in BeautifulSoup(html, "lxml").find_all("a", href=True):
            m = RACEID_RE.search(a["href"])
            if not m:
                continue
            text = " ".join(a.get_text(" ", strip=True).split())
            rid = int(m.group(1))
            if text and (rid not in found or len(text) > len(found[rid])):
                found[rid] = text
        added = len(found) - before
        print(f"  {key}: {added} new (total {len(found)})")
        if added == 0 and key != "organizer":
            break

    for rid in extra_ids or []:
        found.setdefault(int(rid), "")

    races = []
    for rid, title in sorted(found.items()):
        meta = parse_title(title)
        races.append(
            {
                "raceid": rid,
                "title": title,
                "url": f"{BASE}/race?raceid={rid}",
                **meta,
            }
        )

    if not races:
        print(
            "\nNo races found. Either the organizer page moved or it renders its\n"
            "listing with JavaScript. Check cache/organizer.html, then re-run with\n"
            "  python scrape.py discover --ids 319077 315755 389829 445071\n"
            "to seed known race ids by hand.",
            file=sys.stderr,
        )
    return races


# --------------------------------------------------------------------------
# results parsing
# --------------------------------------------------------------------------

HEADER_MAP = {
    "place": "place", "pl": "place", "#": "place", "pos": "place", "rank": "place",
    "name": "name", "racer": "name", "athlete": "name",
    "bib": "bib", "no": "bib",
    "cat": "category", "category": "category", "class": "category", "division": "category",
    "gender": "gender", "sex": "gender",
    "age": "age",
    "team": "team", "club": "team",
    "time": "time", "finish": "time", "finish time": "time", "chip time": "time", "elapsed": "time",
    "diff": "diff", "difference": "diff", "gap": "diff", "behind": "diff",
    "pace": "pace", "speed": "pace",
    "laps": "laps", "lap": "laps", "distance": "distance", "dist": "distance",
    "course": "coursecol", "event": "event", "race": "event",
    "city": "city", "hometown": "city",
    "state": "state",
}

TIME_RE = re.compile(r"^\s*\+?\s*(?:(\d+):)?(\d{1,2}):(\d{2})(?:\.(\d+))?\s*$")


def parse_time(text: str) -> float | None:
    """'1:02:33.4' -> 3753.4 seconds. Returns None for DNF/DNS/blank."""
    if not text:
        return None
    m = TIME_RE.match(text.replace(",", ""))
    if not m:
        return None
    hours = int(m.group(1) or 0)
    minutes, seconds = int(m.group(2)), int(m.group(3))
    frac = float(f"0.{m.group(4)}") if m.group(4) else 0.0
    return hours * 3600 + minutes * 60 + seconds + frac


LAP_RE = re.compile(r"(\d+)\s*(?:x|\u00d7)?\s*laps?\b|\blaps?\s*[:=]?\s*(\d+)", re.I)


def lap_count(row: dict) -> int | None:
    """How many laps this rider actually did.

    The series runs 1-4 lap options off the same start, and which column
    carries that varies: sometimes a Laps column, sometimes it is buried in the
    category or distance text ("Men A - 4 lap"). Placings are meaningless
    across lap counts, so this is worth digging for.
    """
    raw = row.get("laps")
    if raw:
        m = re.search(r"\d+", str(raw))
        if m:
            return int(m.group())

    for key in ("distance", "category", "event", "coursecol"):
        text = row.get(key)
        if not text:
            continue
        m = LAP_RE.search(str(text))
        if m:
            return int(m.group(1) or m.group(2))
    return None


def norm_header(text: str) -> str | None:
    t = re.sub(r"\s+", " ", text or "").strip().lower().rstrip(".")
    t = re.sub(r"\(.*?\)", "", t).strip()
    if t in HEADER_MAP:
        return HEADER_MAP[t]
    # Webscorer's headers carry menu text: "Difference % back % winning time ...",
    # "Lap times Show all Hide all".
    if t.startswith("name"):
        return "name"  # older pages: "Name Affiliation"
    if t.startswith("difference"):
        return "diff"
    if t.startswith("lap times"):
        return "laptimes"
    if t.startswith("finish time"):
        return "time"
    return None


def score_table(table) -> int:
    """How likely is this <table> the results grid? More rows + a name column wins."""
    headers = [norm_header(th.get_text(" ", strip=True)) for th in table.find_all("th")]
    if "name" not in headers:
        return 0
    return len(table.find_all("tr"))


GROUP_SUFFIX = " - Overall"

# Timing-day stand-ins entered in the name field ("COFC 3", "Please email for
# results", "Unknown racer", the sponsor "SkiRack 1") are not people.
PLACEHOLDER_RE = re.compile(
    r"e-?mail|unknown|\btbd\b|\(missing\)|need name|no bib|^cofc\b|^skirack\b|please|pleasse|plz", re.I)
# A real name with a bib note stuck on it: "Oliver (bib 243) Tremble".
BIB_NOTE_RE = re.compile(r"\(\s*bib\s*\d+\s*\)", re.I)


def distance_label(raw: str) -> str:
    """'3 Lap' -> '3 Lap', '5k' -> '5K', 'Half' -> 'Half'. '' means one undivided field."""
    t = re.sub(r"\s+", " ", raw or "").strip()
    m = re.fullmatch(r"(\d+)\s*laps?", t, re.I)
    if m:
        return f"{int(m.group(1))} Lap"
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(k|km|m|mi)", t, re.I)
    if m:
        unit = "mi" if m.group(2).lower() == "mi" else m.group(2).upper()
        return f"{m.group(1)}{unit}"
    return t


GENDER_WORDS = {"male": "M", "female": "F", "no gender": None}


def split_group(raw: str) -> tuple[str, int | None, str | None]:
    """A Webscorer group heading -> (distance, laps, gender).

    Groups are named per distance, but some nights also split by sex or name a
    kids' group oddly, so the label is cleaned into its parts:
        "3 Lap Male" -> ("3 Lap", 3, "M")     "Cadet Lap" -> ("Cadet", None, None)
        "Female"     -> ("", None, "F")       "6"         -> ("", 6, None)   (cross)
    """
    t = re.sub(r"\s+", " ", raw or "").strip()
    gender = None
    if t.lower() in GENDER_WORDS:
        return "", None, GENDER_WORDS[t.lower()]
    m = re.search(r"\s+(male|female|no gender)$", t, re.I)
    if m:
        gender = GENDER_WORDS[m.group(1).lower()]
        t = t[: m.start()].strip()
    if re.fullmatch(r"cadet(?: lap)?", t, re.I):
        return "Cadet", None, gender
    if t.isdigit():
        return "", int(t), gender
    label = distance_label(t)
    return label, laps_from_distance(label), gender


def laps_from_distance(label: str) -> int | None:
    m = re.fullmatch(r"(\d+) Lap", label)
    return int(m.group(1)) if m else None


def cell_laps(td) -> int | None:
    """Cyclocross: laps done = rows in the racer's lap-time list that have a time.

    A lapped rider still gets a numbered row for the lap they did not finish,
    with "- -" where the time would be, so counting numbered rows overcounts.
    """
    n = 0
    for ul in td.select("ul.dataRow"):
        num = ul.select_one("li.lap")
        secs = ul.select_one("li.lap-time-rank")
        if num and num.get_text(strip=True).isdigit() and secs and parse_time(secs.get_text(" ", strip=True).split(" ")[0]) is not None:
            n += 1
    return n or None


def parse_meta(html: str) -> dict:
    """The race-info box: how many racers Webscorer says there were."""
    text = " ".join(BeautifulSoup(html, "lxml").get_text(" ", strip=True).split())
    m = re.search(r"Racers:\s*(\d+)", text)
    s = re.search(r"Sport:\s*(.+?)\s+Location:", text)
    updated = None
    u = re.search(r"Updated:\s*\w+,\s*(\w+)\s+(\d{1,2}),\s*(\d{4})", text)
    if u and u.group(1)[:3].lower() in MONTHS:
        updated = f"{int(u.group(3)):04d}-{MONTHS[u.group(1)[:3].lower()]:02d}-{int(u.group(2)):02d}"
    return {"racers": int(m.group(1)) if m else None, "sport": s.group(1) if s else None, "updated": updated}


def panel_heading(panel, table) -> str:
    parts = []
    for el in panel.descendants:
        if el is table:
            break
        if isinstance(el, NavigableString) and el.strip():
            parts.append(el.strip())
    head = " ".join(" ".join(parts).split())
    # Each panel's heading ends in a screen-reader caption, "Results Table".
    return re.sub(r"\s*Results Table$", "", head)


def read_table(table, raceid: int, distance: str, group_laps: int | None = None, group_gender: str | None = None) -> list[dict]:
    cols = [norm_header(th.get_text(" ", strip=True)) for th in table.find_all("th", recursive=True)]
    # Nested lap tables have their own <th>; only the outer header row counts.
    outer = table.find("tr")
    if outer is not None:
        cols = [norm_header(th.get_text(" ", strip=True)) for th in outer.find_all("th", recursive=False)] or cols
    rows = []
    for tr in table.find_all("tr"):
        if tr.find_parent("table") is not table:
            continue  # a row of a nested lap table
        cells = tr.find_all("td", recursive=False)
        if not cells or len(cells) < len([c for c in cols if c]):
            continue
        row: dict = {}
        laps_cell = None
        for idx, td in enumerate(cells):
            key = cols[idx] if idx < len(cols) else None
            if not key:
                continue
            if key == "laptimes":
                laps_cell = td
                continue
            if key == "name":
                # Older pages put the affiliation in a span inside the name cell.
                span = td.select_one("span.team-name")
                if span is not None:
                    affil = " ".join(span.get_text(" ", strip=True).split())
                    span.extract()
                    if affil and not row.get("team"):
                        row["team"] = affil
            value = " ".join(td.get_text(" ", strip=True).split())
            if key in row and row[key]:
                continue
            row[key] = value
        name = " ".join(BIB_NOTE_RE.sub(" ", row.get("name", "")).split())
        if not name or PLACEHOLDER_RE.search(name):
            continue

        place_raw = re.sub(r"[^\d]", "", row.get("place", ""))
        laps = group_laps if group_laps is not None else laps_from_distance(distance)
        if laps is None and laps_cell is not None:
            laps = cell_laps(laps_cell)
        rows.append(
            {
                "raceid": raceid,
                "place": int(place_raw) if place_raw else None,
                "bib": row.get("bib") or None,
                "name": name,
                "racer": racer_key(name),
                "category": row.get("category") or None,
                "gender": {"M": "M", "F": "F"}.get((row.get("gender") or "").strip().upper()) or group_gender,
                "team": row.get("team") or None,
                # Which start-line group they raced in ("3 Lap", "5K", "Half"),
                # or "" when the whole field ran one event. This is the real
                # unit of competition; laps is just the numeric form when the
                # group is lap-based (or, for cross, the laps actually done).
                "distance": distance,
                "laps": laps,
                # Hometown and age are deliberately NOT carried through.
                # Webscorer shows them, but nothing here uses them, and
                # publishing where a named amateur lives is exposure this
                # project has no need for. Bib and gender are read for
                # de-duplication only and stripped in parse_results.
                "time": row.get("time") or None,
                "seconds": parse_time(row.get("time", "")),
            }
        )
    return rows


def parse_results(html: str, raceid: int) -> list[dict]:
    """Rows from a /racealldetails page.

    The page repeats every racer: once in an "<group> - Overall" table and again
    in each category table. Only the Overall table per group is read, so each
    racer appears once, tagged with the group (distance) they raced in.
    """
    soup = BeautifulSoup(html, "lxml")
    panels = []
    for panel in soup.select('div[id*="repRaceDetails_pnlRaceDetail"]'):
        table = panel.find("table", id="RaceTable") or panel.find("table")
        if table is not None:
            panels.append((panel_heading(panel, table), table))

    groups = {h[: -len(GROUP_SUFFIX)] for h, _ in panels if h.endswith(GROUP_SUFFIX)}
    rows: list[dict] = []
    seen: set = set()
    if groups:
        # Some nights list a combined "5k - Overall" and also "5k Female - Overall"
        # and "5k Male - Overall". Read the combined table first, then drop
        # anyone already seen in the same distance.
        overall = []
        for h, table in panels:
            if h.endswith(GROUP_SUFFIX):
                distance, glaps, ggender = split_group(h[: -len(GROUP_SUFFIX)])
                overall.append((ggender is not None, distance, glaps, ggender, table))
        for _, distance, glaps, ggender, table in sorted(overall, key=lambda o: o[0]):
            for r in read_table(table, raceid, distance, glaps, ggender):
                key = (r["distance"], r["laps"], r["bib"], r["name"])
                if key not in seen:
                    seen.add(key)
                    rows.append(r)
    else:
        # One undivided field: take "Overall", or if a page has no such table,
        # every table with duplicates dropped.
        overall = [t for h, t in panels if h.lower() == "overall"]
        for table in overall or [t for _, t in panels]:
            for r in read_table(table, raceid, ""):
                key = (r["bib"], r["name"])
                if key not in seen:
                    seen.add(key)
                    rows.append(r)
    # Published rows carry a name, a placing, a time and the race group, and
    # nothing else that identifies a person. Bib and gender exist only to
    # de-duplicate; category (an age band, "14 and Under") and team are
    # dropped as well: nothing here uses them.
    for r in rows:
        for field in ("bib", "gender", "category", "team"):
            r.pop(field, None)
    return rows


def fetch_results(races: list[dict], refresh: bool = False) -> list[dict]:
    all_rows: list[dict] = []
    empty: list[int] = []
    mismatch: list[str] = []
    for i, race in enumerate(races, 1):
        rid = race["raceid"]
        if not race.get("discipline"):
            # The organizer also hosts one-off events (e.g. a charity ride) that
            # are not part of the MTB / trail run / cyclocross series.
            print(f"  [{i}/{len(races)}] {rid}: skipped, not a series race: {race['title']!r}")
            continue
        try:
            html = fetch(f"{BASE}/racealldetails?raceid={rid}", f"raceall-{rid}", refresh=refresh)
        except requests.HTTPError as exc:
            print(f"  [{i}/{len(races)}] {rid}: {exc}", file=sys.stderr)
            continue
        rows = parse_results(html, rid)
        meta = parse_meta(html)
        if not rows:
            empty.append(rid)
        race["finishers"] = len(rows)
        race["sport"] = meta["sport"]
        if not race.get("date") and meta["updated"]:
            # A title with no year ("Catamount 9-6 Final MTB Race"): the results
            # page is stamped the evening of the race.
            race["date"], race["year"] = meta["updated"], int(meta["updated"][:4])
        if meta["racers"] is not None and meta["racers"] != len(rows):
            mismatch.append(f"{rid}: page says {meta['racers']}, parsed {len(rows)}")
        all_rows.extend(rows)
        print(f"  [{i}/{len(races)}] {rid} {race.get('date') or '?'} {race.get('course') or ''}: {len(rows)} finishers")

    if empty:
        print(
            f"\n{len(empty)} race page(s) yielded no rows: {empty[:10]}"
            "\nInspect cache/raceall-<id>.html and adjust parse_results().",
            file=sys.stderr,
        )
    if mismatch:
        print(f"\n{len(mismatch)} race(s) where parsed rows != the page's own racer count:", file=sys.stderr)
        for m in mismatch[:15]:
            print("  " + m, file=sys.stderr)
    return all_rows


# --------------------------------------------------------------------------
# weather
# --------------------------------------------------------------------------

# Catamount Outdoor Family Center, Williston VT. Races roll off at 6pm.
VENUE_LAT, VENUE_LON = 44.4419, -73.1093
VENUE_TZ = "America/New_York"
RACE_HOUR = 18

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
HOURLY = ["temperature_2m", "apparent_temperature", "relative_humidity_2m",
          "precipitation", "cloud_cover", "wind_speed_10m", "wind_gusts_10m", "weather_code"]

# WMO 4677 weather codes, collapsed to what a racer would actually say.
WMO = {
    0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Freezing fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    56: "Freezing drizzle", 57: "Freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    66: "Freezing rain", 67: "Freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Light showers", 81: "Showers", 82: "Heavy showers",
    85: "Snow showers", 86: "Snow showers",
    95: "Thunderstorm", 96: "Thunderstorm, hail", 99: "Thunderstorm, hail",
}


def sky_from_cloud(pct):
    """Cloud cover percentage -> the word someone would use standing there."""
    if pct is None:
        return None
    if pct < 15:
        return "Sunny"
    if pct < 40:
        return "Mostly sunny"
    if pct < 70:
        return "Partly cloudy"
    if pct < 90:
        return "Mostly cloudy"
    return "Overcast"


def fetch_json(url: str, params: dict, cache_key: str, refresh: bool = False):
    global _last_request
    path = CACHE / f"{cache_key}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text())

    wait = DELAY - (time.time() - _last_request)
    if wait > 0:
        time.sleep(wait)
    resp = _session.get(url, params=params, timeout=60)
    _last_request = time.time()
    resp.raise_for_status()

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(resp.text, encoding="utf-8")
    return resp.json()


def fetch_weather(races: list[dict], refresh: bool = False) -> dict:
    """Conditions at the start line for every race date.

    Open-Meteo's archive is free and needs no API key, so nothing secret ever
    has to live in this repo. One request per season covers that season.
    """
    dates = sorted({r["date"] for r in races if r.get("date")})
    if not dates:
        return {}

    by_year: dict[int, list[str]] = {}
    for d in dates:
        by_year.setdefault(int(d[:4]), []).append(d)

    out: dict[str, dict] = {}
    for year in sorted(by_year):
        days = by_year[year]
        params = {
            "latitude": VENUE_LAT, "longitude": VENUE_LON,
            "start_date": days[0], "end_date": days[-1],
            "hourly": ",".join(HOURLY), "timezone": VENUE_TZ,
            "temperature_unit": "fahrenheit", "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
        }
        try:
            blob = fetch_json(ARCHIVE, params, f"weather-{year}", refresh=refresh)
        except requests.RequestException as exc:
            print(f"  {year}: {exc}", file=sys.stderr)
            continue

        hourly = blob.get("hourly") or {}
        stamps = hourly.get("time") or []
        index = {t: i for i, t in enumerate(stamps)}

        hit = 0
        for day in days:
            i = index.get(f"{day}T{RACE_HOUR:02d}:00")
            if i is None:
                continue

            def at(key):
                col = hourly.get(key) or []
                return col[i] if i < len(col) else None

            # Rain in the three hours before the gun is what makes the dirt slick.
            recent = 0.0
            for back in range(0, 4):
                j = i - back
                col = hourly.get("precipitation") or []
                if 0 <= j < len(col) and col[j] is not None:
                    recent += col[j]

            code = at("weather_code")
            cloud = at("cloud_cover")
            out[day] = {
                "temp": at("temperature_2m"),
                "feels": at("apparent_temperature"),
                "humidity": at("relative_humidity_2m"),
                "precip": at("precipitation"),
                "precip_3h": round(recent, 3),
                "cloud": cloud,
                "wind": at("wind_speed_10m"),
                "gust": at("wind_gusts_10m"),
                "code": code,
                "sky": sky_from_cloud(cloud),
                "summary": WMO.get(int(code), None) if code is not None else None,
            }
            hit += 1
        print(f"  {year}: {hit}/{len(days)} race dates matched")

    missing = [d for d in dates if d not in out]
    if missing:
        print(f"\n{len(missing)} date(s) without weather: {missing[:8]}", file=sys.stderr)
    return out


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def load_aliases() -> dict:
    """Hand-kept merges of one person's spelled names: {"tim-burgher": "timothy-burgher"}.

    Identity here is the spelled name, so a nickname or a typo makes a second
    racer. Merging is deliberately explicit (aliases.json), never inferred.
    """
    path = ROOT / "aliases.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("aliases", {})


def build(races: list[dict], results: list[dict], weather: dict | None = None) -> dict:
    """Bundle races + results, dropping races we never got rows for."""
    aliases = load_aliases()
    for r in results:
        r["racer"] = aliases.get(r["racer"], r["racer"])

    by_race: dict[int, int] = {}
    for r in results:
        by_race[r["raceid"]] = by_race.get(r["raceid"], 0) + 1

    keep = [r for r in races if by_race.get(r["raceid"])]
    for r in keep:
        r["finishers"] = by_race[r["raceid"]]
        if weather and r.get("date") in weather:
            r["weather"] = weather[r["date"]]
    keep.sort(key=lambda r: (r.get("date") or "", r["raceid"]))

    names: dict[str, str] = {}
    for r in results:
        # Prefer the longest spelling seen; handles "Tim" vs "Timothy" less
        # aggressively than merging, but keeps display stable.
        if len(r["name"]) > len(names.get(r["racer"], "")):
            names[r["racer"]] = r["name"]
    for r in results:
        r["name"] = names[r["racer"]]

    return {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": ORGANIZER,
        "races": keep,
        "results": results,
        "racers": names,
    }


def write_bundle(bundle: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "catamount.json").write_text(json.dumps(bundle, indent=None, separators=(",", ":")))
    # A JS copy so index.html also works when opened straight off disk, where
    # fetch() of a local file is blocked by the browser.
    (DATA / "catamount.js").write_text("window.CATAMOUNT_DATA = " + json.dumps(bundle, separators=(",", ":")) + ";")
    print(
        f"\nWrote data/catamount.json and data/catamount.js: "
        f"{len(bundle['races'])} races, {len(bundle['results'])} results, "
        f"{len(bundle['racers'])} racers."
    )


def load(name: str):
    path = DATA / name
    if not path.exists():
        sys.exit(f"{path} missing - run an earlier phase first.")
    return json.loads(path.read_text())


def save(name: str, obj) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / name).write_text(json.dumps(obj, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phase", choices=["discover", "fetch", "weather", "build", "all"])
    ap.add_argument("--refresh", action="store_true", help="ignore the cache and re-download")
    ap.add_argument("--ids", nargs="*", type=int, default=[], help="extra race ids to include")
    args = ap.parse_args()

    if args.phase in ("discover", "all"):
        print("Discovering races...")
        races = discover(refresh=args.refresh, extra_ids=args.ids)
        save("races.json", races)
        print(f"Wrote data/races.json: {len(races)} races.\n")

    if args.phase in ("fetch", "all"):
        races = load("races.json")
        print("Fetching results...")
        results = fetch_results(races, refresh=args.refresh)
        save("races.json", races)
        save("results.json", results)
        print(f"Wrote data/results.json: {len(results)} rows.\n")

    if args.phase in ("weather", "all"):
        races = load("races.json")
        print("Fetching weather...")
        save("weather.json", fetch_weather(races, refresh=args.refresh))
        print("Wrote data/weather.json.\n")

    if args.phase in ("build", "all"):
        weather = {}
        if (DATA / "weather.json").exists():
            weather = json.loads((DATA / "weather.json").read_text())
        write_bundle(build(load("races.json"), load("results.json"), weather))


if __name__ == "__main__":
    main()
