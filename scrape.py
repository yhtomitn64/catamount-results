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
from bs4 import BeautifulSoup

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

# "Catamount 6-21-23 MTB Race (Yellow on Green)"
TITLE_RE = re.compile(
    r"(?P<m>\d{1,2})[-/](?P<d>\d{1,2})[-/](?P<y>\d{2,4})"
    r"(?:\s+(?P<disc>MTB|TR|XC|SS))?",
    re.I,
)
COURSE_RE = re.compile(r"\(([^)]+)\)")

DISCIPLINE_NAMES = {"MTB": "Mountain bike", "TR": "Trail run", "XC": "Cross country", "SS": "Single speed"}


def parse_title(title: str) -> dict:
    """Pull date, discipline and course out of a Webscorer race title."""
    out = {"date": None, "year": None, "discipline": None, "course": None}

    m = TITLE_RE.search(title)
    if m:
        month, day, year = int(m["m"]), int(m["d"]), int(m["y"])
        if year < 100:
            year += 2000
        if 1 <= month <= 12 and 1 <= day <= 31 and 1990 <= year <= 2100:
            out["date"] = f"{year:04d}-{month:02d}-{day:02d}"
            out["year"] = year
        if m["disc"]:
            out["discipline"] = m["disc"].upper()

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

    pages = [(ORGANIZER, "organizer")]
    # Organizer listings paginate; walk until a page adds nothing new.
    for n in range(2, 30):
        pages.append((f"{ORGANIZER}?pg={n}", f"organizer-p{n}"))

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
    "time": "time", "finish": "time", "chip time": "time", "elapsed": "time",
    "diff": "diff", "difference": "diff", "gap": "diff", "behind": "diff",
    "pace": "pace", "speed": "pace",
    "laps": "laps", "lap": "laps",
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


def norm_header(text: str) -> str | None:
    t = re.sub(r"\s+", " ", text or "").strip().lower().rstrip(".")
    t = re.sub(r"\(.*?\)", "", t).strip()
    return HEADER_MAP.get(t)


def score_table(table) -> int:
    """How likely is this <table> the results grid? More rows + a name column wins."""
    headers = [norm_header(th.get_text(" ", strip=True)) for th in table.find_all("th")]
    if "name" not in headers:
        return 0
    return len(table.find_all("tr"))


def parse_results(html: str, raceid: int) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    tables = sorted(soup.find_all("table"), key=score_table, reverse=True)
    if not tables or score_table(tables[0]) == 0:
        return []
    table = tables[0]

    header_cells = table.find_all("th")
    cols = [norm_header(th.get_text(" ", strip=True)) for th in header_cells]

    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue
        row: dict = {}
        for idx, td in enumerate(cells):
            key = cols[idx] if idx < len(cols) else None
            if not key:
                continue
            value = " ".join(td.get_text(" ", strip=True).split())
            if key in row and row[key]:
                continue
            row[key] = value
        name = row.get("name", "").strip()
        if not name:
            continue

        place_raw = re.sub(r"[^\d]", "", row.get("place", ""))
        rows.append(
            {
                "raceid": raceid,
                "place": int(place_raw) if place_raw else None,
                "name": name,
                "racer": racer_key(name),
                "category": row.get("category") or None,
                "gender": row.get("gender") or None,
                "team": row.get("team") or None,
                "city": row.get("city") or None,
                "laps": row.get("laps") or None,
                "time": row.get("time") or None,
                "seconds": parse_time(row.get("time", "")),
            }
        )
    return rows


def fetch_results(races: list[dict], refresh: bool = False) -> list[dict]:
    all_rows: list[dict] = []
    empty: list[int] = []
    for i, race in enumerate(races, 1):
        rid = race["raceid"]
        try:
            html = fetch(f"{BASE}/race?raceid={rid}", f"race-{rid}", refresh=refresh)
        except requests.HTTPError as exc:
            print(f"  [{i}/{len(races)}] {rid}: {exc}", file=sys.stderr)
            continue
        rows = parse_results(html, rid)
        if not rows:
            empty.append(rid)
        race["finishers"] = len(rows)
        all_rows.extend(rows)
        print(f"  [{i}/{len(races)}] {rid} {race.get('date') or '?'} {race.get('course') or ''}: {len(rows)} finishers")

    if empty:
        print(
            f"\n{len(empty)} race page(s) yielded no rows: {empty[:10]}"
            "\nInspect cache/race-<id>.html and adjust parse_results().",
            file=sys.stderr,
        )
    return all_rows


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def build(races: list[dict], results: list[dict]) -> dict:
    """Bundle races + results, dropping races we never got rows for."""
    by_race: dict[int, int] = {}
    for r in results:
        by_race[r["raceid"]] = by_race.get(r["raceid"], 0) + 1

    keep = [r for r in races if by_race.get(r["raceid"])]
    for r in keep:
        r["finishers"] = by_race[r["raceid"]]
    keep.sort(key=lambda r: (r.get("date") or "", r["raceid"]))

    names: dict[str, str] = {}
    for r in results:
        # Prefer the longest spelling seen; handles "Tim" vs "Timothy" less
        # aggressively than merging, but keeps display stable.
        if len(r["name"]) > len(names.get(r["racer"], "")):
            names[r["racer"]] = r["name"]

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
    ap.add_argument("phase", choices=["discover", "fetch", "build", "all"])
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

    if args.phase in ("build", "all"):
        write_bundle(build(load("races.json"), load("results.json")))


if __name__ == "__main__":
    main()
