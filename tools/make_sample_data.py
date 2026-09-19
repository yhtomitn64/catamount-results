#!/usr/bin/env python3
"""Generate a plausible stand-in dataset so the interface can be built and
checked before the real Webscorer scrape runs.

This is invented data. Running scrape.py overwrites everything it produces.

    python tools/make_sample_data.py
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scrape  # noqa: E402

random.seed(20260919)

COURSES = ["Red on Black", "Black on White", "Yellow on Green", "Green on Yellow", "Blue on Orange"]
COURSE_BASE = {"Red on Black": 2280, "Black on White": 2040, "Yellow on Green": 2520,
               "Green on Yellow": 2460, "Blue on Orange": 1920}
YEARS = list(range(2017, 2027))

FIRST = ["Timothy", "Sarah", "Mike", "Dave", "Emily", "Chris", "Katie", "Ben", "Laura", "Pete",
         "Anna", "Josh", "Megan", "Ryan", "Nicole", "Adam", "Rachel", "Eric", "Jess", "Nate",
         "Hannah", "Luke", "Claire", "Sam", "Olivia", "Matt", "Erin", "Greg", "Molly", "Tyler",
         "Sophie", "Dan", "Abby", "Kevin", "Lily", "Brian", "Grace", "Andrew", "Nora", "Scott"]
LAST = ["Burgher", "Whitcomb", "Lang", "Pelletier", "Marsh", "Hoyt", "Deforge", "Bouchard",
        "Steele", "Nadeau", "Ainsworth", "Corriveau", "Braun", "Rivers", "Gagnon", "Thorne",
        "Mercier", "Knapp", "Vance", "Ledoux"]
CATEGORIES = ["Men A", "Men B", "Men C", "Women A", "Women B", "Junior"]


def make_racers(n: int = 58) -> list[dict]:
    seen, racers = set(), []
    while len(racers) < n:
        name = f"{random.choice(FIRST)} {random.choice(LAST)}"
        if name in seen:
            continue
        seen.add(name)
        racers.append({
            "name": name,
            "ability": random.gauss(1.18, 0.16),        # time multiplier vs. course base
            "category": random.choice(CATEGORIES),
            "loyalty": random.betavariate(2, 3),         # share of races entered
            "first_year": random.choice(YEARS[:6]),
            "trend": random.gauss(-0.006, 0.010),        # per-year improvement
        })
    # Pin one known racer so the demo has something to search for.
    racers[0].update(name="Timothy Burgher", ability=1.12, category="Men B",
                     loyalty=0.62, first_year=2018, trend=-0.014)
    for r in racers:
        r["ability"] = max(1.0, r["ability"])
        r["racer"] = scrape.racer_key(r["name"])
    return racers


def wednesdays(year: int) -> list[dt.date]:
    d = dt.date(year, 5, 1)
    d += dt.timedelta(days=(2 - d.weekday()) % 7)
    out = []
    while d < dt.date(year, 8, 31):
        out.append(d)
        d += dt.timedelta(days=7)
    return out


def main() -> None:
    racers = make_racers()
    races, results = [], []
    raceid = 180000

    for year in YEARS:
        # Each season uses a rotating subset of courses, repeated through the summer.
        pool = random.sample(COURSES, 3)
        for i, date in enumerate(wednesdays(year)):
            raceid += random.randint(7, 40)
            course = pool[i % len(pool)]
            title = f"Catamount {date.month}-{date.day}-{str(date.year)[2:]} MTB Race ({course})"
            races.append({
                "raceid": raceid, "title": title, "url": f"https://www.webscorer.com/race?raceid={raceid}",
                "date": date.isoformat(), "year": year, "discipline": "MTB", "course": course,
            })

            base = COURSE_BASE[course]
            field = []
            for r in racers:
                if year < r["first_year"] or random.random() > r["loyalty"]:
                    continue
                if r["name"] == "Timothy Burgher" and year == 2026:
                    continue  # he sat this season out
                years_in = year - r["first_year"]
                mult = r["ability"] * (1 + r["trend"] * years_in) * random.gauss(1.0, 0.035)
                field.append((base * mult, r))

            field.sort(key=lambda t: t[0])
            for place, (secs, r) in enumerate(field, 1):
                mins, rest = divmod(secs, 60)
                results.append({
                    "raceid": raceid, "place": place, "name": r["name"], "racer": r["racer"],
                    "category": r["category"], "gender": None, "team": None, "city": None,
                    "laps": "3", "time": f"{int(mins)}:{rest:04.1f}", "seconds": round(secs, 1),
                })

    out = pathlib.Path(__file__).resolve().parent.parent / "data"
    out.mkdir(exist_ok=True)
    (out / "races.json").write_text(json.dumps(races, indent=2))
    (out / "results.json").write_text(json.dumps(results, indent=2))
    bundle = scrape.build(races, results)
    bundle["sample"] = True
    scrape.write_bundle(bundle)


if __name__ == "__main__":
    main()
