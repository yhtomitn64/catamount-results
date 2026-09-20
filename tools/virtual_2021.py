#!/usr/bin/env python3
"""Read Catamount's public 2021 weekly results sheets into data/extra/virtual_2021.json.

In 2021 the series began virtually: riders timed themselves on the week's course, and
Catamount published one results PDF per week (public Google Drive folders, linked from its
series page). In-person racing, the part that is on Webscorer, only began July 13 / 14.
These sheets are a separate kind of result, so every race written here is marked
`"virtual": true` and the site keeps them out of head-to-head and rivals.

    python tools/virtual_2021.py            # list, download (once each, slowly), parse, write
    python tools/virtual_2021.py --offline  # parse what is already cached

Each sheet's header reads "Week: 9  Course: Red on Black/Black on Orange". Week n is the
calendar week of Wednesday June 2 + 7(n-1) for MTB and Tuesday June 1 + 7(n-1) for trail
running; that lines up with both ends of the season (in-person MTB began Wed 7/14 = week 7,
trail running ended Tue 9/14 = week 16). A parsed row count that differs from the sheet's own
"Attendees" number is printed, never hidden.

Needs pdfplumber (see requirements.txt). Downloads are cached under cache/drive/ (gitignored).
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import pathlib
import random
import re
import sys
import time

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scrape  # noqa: E402  (shared name cleaning and racer keys)

FOLDERS = {"MTB": "1LhMoaG0a9CIVF-7YIRqPQx872t543SCf", "TR": "1mIPHsYwF4GBaYn3hP5FVw0nuZ7xWwzpp"}
FIRST_NIGHT = {"MTB": datetime.date(2021, 6, 2), "TR": datetime.date(2021, 6, 1)}
CODE = {"MTB": 1, "TR": 2}
CACHE = scrape.ROOT / "cache" / "drive"
OUT = scrape.DATA / "extra" / "virtual_2021.json"
UA = "catamount-results/1.0 (personal race-results archive; contact via github.com/yhtomitn64/catamount-results)"

_session = requests.Session()
_session.headers["User-Agent"] = UA


def _polite_get(url: str, **kw) -> requests.Response:
    time.sleep(3.5 + random.random() * 1.5)
    resp = _session.get(url, timeout=60, **kw)
    resp.raise_for_status()
    return resp


def list_folder(folder_id: str, offline: bool) -> dict[str, str]:
    """{file name: drive file id} from the folder's plain "embedded view" (no login needed)."""
    path = CACHE / f"folder_{folder_id}.html"
    if not path.exists():
        if offline:
            return {}
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_text(_polite_get("https://drive.google.com/embeddedfolderview", params={"id": folder_id}).text, encoding="utf-8")
    text = path.read_text(encoding="utf-8", errors="replace")
    found = re.findall(r'href="https://drive\.google\.com/file/d/([^/"]+)/[^"]*".*?flip-entry-title">(.*?)</div>', text, re.S)
    return {html.unescape(name): fid for fid, name in found}


def download(name: str, file_id: str, offline: bool) -> pathlib.Path | None:
    path = CACHE / re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    if not path.exists():
        if offline:
            return None
        resp = _polite_get("https://drive.google.com/uc", params={"export": "download", "id": file_id})
        if not resp.content.startswith(b"%PDF"):
            print(f"  not a PDF, skipped: {name}", file=sys.stderr)
            return None
        path.write_bytes(resp.content)
    return path


GROUP = r"(?P<group>\d Laps?|Cadet Cutoff \(Half Lap\)|2\.5k Cadet Cutoff \(Half Lap\)|10k \(Two Laps\)|5k \(One Lap\))"
AGE = r"(?P<age>\d\d and Under|\d\d to \d\d|\d\d and Over)"
LINE = re.compile(
    rf"^(?:{GROUP}\s+)?(?:{AGE}\s+)?(?:(?P<rank>\d+)\s+)?(?P<name>[A-Za-z][^\d]*?)\s+"
    r"(?P<time>\d:\d\d:\d\d)(?:\s+(?P<overall>\d+|Total))?(?:\s+(?P<team>.*))?$"
)


def group_label(raw: str) -> tuple[str, int | None]:
    """A sheet's distance heading -> (the label the site uses, laps)."""
    t = raw.lower()
    if t.startswith("2.5k"):
        return "2.5K", None
    if "cadet" in t:
        return "Cadet", None
    if t.startswith("10k"):
        return "10K", None
    if t.startswith("5k"):
        return "5K", None
    n = int(t[0])
    return f"{n} Lap", n


def to_seconds(t: str) -> tuple[float, str]:
    h, m, s = (int(x) for x in t.split(":"))
    secs = h * 3600 + m * 60 + s
    return float(secs), (f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}")


def parse_pdf(path: pathlib.Path, disc: str) -> dict:
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        lines = [l.strip() for p in pdf.pages for l in (p.extract_text() or "").splitlines() if l.strip()]
    head = lines[0]
    course = re.search(r"Course:\s*(.+)$", head)
    attendees = next((int(m.group(1)) for l in lines[:4] if (m := re.search(r"Attendees:\s*(\d+)", l))), None)

    rows, group, laps = [], None, None
    for line in lines:
        if "Series Week" in line or line.startswith("Attendees") or "Full Name" in line or "Race Timed" in line:
            continue
        m = LINE.match(line)
        if not m:
            print(f"  unparsed line in {path.name}: {line[:70]!r}", file=sys.stderr)
            continue
        if m["group"]:
            group, laps = group_label(m["group"])
        if group is None:
            continue
        name = scrape.clean_name(m["name"])
        if not name:
            continue
        secs, shown = to_seconds(m["time"])
        rows.append({"name": name, "racer": scrape.racer_key(name), "distance": group, "laps": laps,
                     "time": shown, "seconds": secs})
    return {"course": course.group(1).strip() if course else None, "attendees": attendees, "rows": rank(rows)}


def rank(rows: list[dict]) -> list[dict]:
    """Place within each distance group by time. The sheet's own rank runs across every group.

    A time the sheet typed as "45:00:00" (a spreadsheet reading 45:00 as hours) fails the
    h:mm:ss pattern and is reported as unparsed rather than guessed at.

    The sheet also lists a rider once per age group they are entered in (a shared family ride
    can appear twice), so one row per (racer, distance): the fastest.
    """
    best: dict[tuple, dict] = {}
    for r in rows:
        k = (r["racer"], r["distance"])
        if k not in best or r["seconds"] < best[k]["seconds"]:
            best[k] = r
    out, by_group = [], {}
    for r in best.values():
        by_group.setdefault(r["distance"], []).append(r)
    for group_rows in by_group.values():
        group_rows.sort(key=lambda r: r["seconds"])
        for i, r in enumerate(group_rows):
            tied = i and r["seconds"] == group_rows[i - 1]["seconds"]
            r["place"] = group_rows[i - 1]["place"] if tied else i + 1
            out.append(r)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--offline", action="store_true", help="parse only what is already cached")
    args = ap.parse_args()

    in_person = {(r["date"], r["discipline"]) for r in json.loads((scrape.DATA / "races.json").read_text(encoding="utf-8"))}
    races, results = [], []
    for disc, folder in FOLDERS.items():
        for name, fid in sorted(list_folder(folder, args.offline).items()):
            m = re.match(r"Week (\d+)", name)
            if not m:
                print(f"  skipped (not a numbered week): {name}")   # the in-person 7/13 sheet is on Webscorer already
                continue
            week = int(m.group(1))
            path = download(name, fid, args.offline)
            if path is None:
                continue
            date = FIRST_NIGHT[disc] + datetime.timedelta(days=7 * (week - 1))
            if (date.isoformat(), disc) in in_person:
                print(f"  {disc} week {week:2} {date}  already on Webscorer, skipped")
                continue
            sheet = parse_pdf(path, disc)
            raceid = -(int(date.strftime("%Y%m%d")) * 10 + CODE[disc])
            course = sheet["course"] or ""
            race = {
                "raceid": raceid,
                "title": f"2021 Week {week} {'MTB' if disc == 'MTB' else 'trail run'} (virtual)",
                "url": f"https://drive.google.com/file/d/{fid}/view",
                "date": date.isoformat(), "year": 2021, "discipline": disc, "virtual": True,
                "course": scrape.normalize_course(course) if course else None,
                "courseSource": "center",   # the race title names no course; the sheet does
            }
            races.append(race)
            for r in sheet["rows"]:
                results.append({"raceid": raceid, **r})
            flag = "" if sheet["attendees"] == len(sheet["rows"]) else f"   <-- sheet says {sheet['attendees']} attendees"
            print(f"  {disc} week {week:2} {date}  {course:32} {len(sheet['rows']):3} rows{flag}")

    if not races:
        sys.exit("nothing parsed (offline with an empty cache?)")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": "Catamount Outdoor Family Center weekly results sheets (2021)",
                               "races": races, "results": results}, indent=1), encoding="utf-8")
    print(f"\nWrote {OUT.relative_to(scrape.ROOT)}: {len(races)} virtual weeks, {len(results)} results.")


if __name__ == "__main__":
    main()
