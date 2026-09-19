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
# Seconds per lap. Riders pick a lap count; the series runs 1 through 4.
COURSE_BASE = {"Red on Black": 760, "Black on White": 680, "Yellow on Green": 840,
               "Green on Yellow": 820, "Blue on Orange": 640}
LAP_CATEGORY = {4: "Men A", 3: "Men B", 2: "Men C", 1: "Junior"}
YEARS = list(range(2017, 2027))

FIRST = ["Timothy", "Sarah", "Mike", "Dave", "Emily", "Chris", "Katie", "Ben", "Laura", "Pete",
         "Anna", "Josh", "Megan", "Ryan", "Nicole", "Adam", "Rachel", "Eric", "Jess", "Nate",
         "Hannah", "Luke", "Claire", "Sam", "Olivia", "Matt", "Erin", "Greg", "Molly", "Tyler",
         "Sophie", "Dan", "Abby", "Kevin", "Lily", "Brian", "Grace", "Andrew", "Nora", "Scott"]
LAST = ["Burgher", "Whitcomb", "Lang", "Pelletier", "Marsh", "Hoyt", "Deforge", "Bouchard",
        "Steele", "Nadeau", "Ainsworth", "Corriveau", "Braun", "Rivers", "Gagnon", "Thorne",
        "Mercier", "Knapp", "Vance", "Ledoux"]
LAP_WEIGHTS = [(4, 0.22), (3, 0.30), (2, 0.33), (1, 0.15)]


def make_racers(n: int = 58) -> list[dict]:
    seen, racers = set(), []
    while len(racers) < n:
        name = f"{random.choice(FIRST)} {random.choice(LAST)}"
        if name in seen:
            continue
        seen.add(name)
        roll = random.random()
        acc, laps = 0.0, 4
        for lap_n, weight in LAP_WEIGHTS:
            acc += weight
            if roll <= acc:
                laps = lap_n
                break
        racers.append({
            "name": name,
            "ability": random.gauss(1.18, 0.16),        # time multiplier vs. course base
            "laps": laps,                                # the distance they usually pick
            "category": LAP_CATEGORY[laps],
            "loyalty": random.betavariate(2, 3),         # share of races entered
            "first_year": random.choice(YEARS[:6]),
            "trend": random.gauss(-0.006, 0.010),        # per-year improvement
        })
    # Pin one known racer so the demo has something to search for.
    # Tim rides the 4-lap almost always, and drops to 3 now and then.
    racers[0].update(name="Timothy Burgher", ability=1.12, laps=4, category="Men A",
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
                # Most nights they ride their usual distance; sometimes one less.
                laps = r["laps"] - 1 if (r["laps"] > 1 and random.random() < 0.15) else r["laps"]
                field.append((base * laps * mult, laps, r))

            # Placings are per lap-distance - that is the actual race being run.
            by_laps: dict[int, list] = {}
            for secs, laps, r in field:
                by_laps.setdefault(laps, []).append((secs, r))
            for laps, group in by_laps.items():
                group.sort(key=lambda t: t[0])
                for place, (secs, r) in enumerate(group, 1):
                    mins, rest = divmod(secs, 60)
                    results.append({
                        "raceid": raceid, "place": place, "name": r["name"], "racer": r["racer"],
                        "category": r["category"], "team": None,
                        # Same shape the real scraper emits: `distance` is the
                        # start-line group the UI keys on, `laps` its numeric form.
                        "distance": f"{laps} Lap", "laps": laps,
                        "time": f"{int(mins)}:{rest:04.1f}", "seconds": round(secs, 1),
                    })

    # Plausible Vermont summer evenings, so the weather views have something
    # to render before the real Open-Meteo pull runs.
    weather = {}
    for race in races:
        month = int(race["date"][5:7])
        base = {5: 64, 6: 72, 7: 78, 8: 76}.get(month, 70)
        temp = round(random.gauss(base, 7), 1)
        cloud = round(min(100, max(0, random.gauss(45, 30))))
        wet = random.random() < 0.18
        precip = round(abs(random.gauss(0.05, 0.05)), 3) if wet else 0.0
        code = 61 if wet and precip > 0.04 else (95 if wet else None)
        if code is None:
            code = 0 if cloud < 15 else 1 if cloud < 40 else 2 if cloud < 70 else 3
        weather[race["date"]] = {
            "temp": temp,
            "feels": round(temp + random.gauss(0, 3), 1),
            "humidity": round(min(100, max(25, random.gauss(62, 15)))),
            "precip": precip,
            "precip_3h": round(precip * random.uniform(1, 3), 3),
            "cloud": cloud,
            "wind": round(abs(random.gauss(6, 3)), 1),
            "gust": round(abs(random.gauss(13, 5)), 1),
            "code": code,
            "sky": scrape.sky_from_cloud(cloud),
            "summary": scrape.WMO.get(code),
        }

    out = pathlib.Path(__file__).resolve().parent.parent / "data"
    out.mkdir(exist_ok=True)
    (out / "races.json").write_text(json.dumps(races, indent=2))
    (out / "results.json").write_text(json.dumps(results, indent=2))
    (out / "weather.json").write_text(json.dumps(weather, indent=2))
    bundle = scrape.build(races, results, weather)
    bundle["sample"] = True
    scrape.write_bundle(bundle)


if __name__ == "__main__":
    main()
