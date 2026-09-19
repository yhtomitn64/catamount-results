# Catamount Wednesdays

An explorable archive of the [Catamount Outdoor Family Center](https://catamountoutdoor.org/)
Wednesday night race series — every result, every season, in one page you can click
through instead of opening forty separate Webscorer tabs.

The series rotates its courses between seasons (Red on Black, Black on White,
Yellow on Green…) but repeats the same course several times within a season. That
shape is the whole point of this project: it means times *are* comparable, but only
along the right axis. Every view here is built around that constraint.

## What you can look up

**Racers** — a profile per person: starts, wins, podiums, best finish, and a scatter
of where they land in the field over their whole history, coloured by course.

**Rivals** — for any racer, everyone they've ever lined up against, ranked by how
often, with the head-to-head record and average margin. This is the "who beat who"
table.

**Head to head** — pick two people and get every race they both finished: who was
ahead, by how much, and whether the gap is closing or widening over the years.

**Courses** — a page per course showing every running of it across seasons, the
all-time fastest times, and how the winning and median times have moved. A step
change in that chart usually means the loop was re-cut, not that the field changed.

**Seasons** — standings for any year, sortable by starts, wins, podiums or median
finish.

## Running it

The page is a single static HTML file that reads a generated data bundle. Nothing
to build, no dependencies at runtime.

```sh
pip install -r requirements.txt

python scrape.py discover   # find every Catamount race        -> data/races.json
python scrape.py fetch      # pull each race's results         -> data/results.json
python scrape.py build      # bundle for the page              -> data/catamount.{json,js}

python scrape.py all        # or just do all three
```

Then open `index.html`. It works straight off disk — the data is loaded as
`data/catamount.js` precisely so you don't need a local web server.

To publish it, turn on GitHub Pages for this repo (Settings → Pages → deploy from
`main`, root). The whole thing is static.

### Comparing across courses

Raw times only mean something within a single course. Where a number has to span
courses, the page uses one of two normalisations instead:

- **Finish percentile** — where you placed in the field, 100% being the win. Immune
  to course length, sensitive to who showed up.
- **vs winner** — your time divided by the winning time that night. 1.00 is a win,
  1.20 means you took 20% longer. Immune to who showed up, sensitive to whether the
  winner had an off night.

Both are shown because neither is right on its own.

## How the scraping works

`scrape.py` runs in three phases so you can redo one without redoing the others.
Every page it fetches is cached as raw HTML under `cache/` (gitignored), so re-runs
cost nothing and you can iterate the parser offline against real pages.

Race metadata comes out of the Webscorer race title, which the series formats
consistently: `Catamount 6-21-23 MTB Race (Yellow on Green)` yields the date, the
discipline and the course. The results grid is found by scoring every `<table>` on
the page and taking the one that has a name column and the most rows, then mapping
column headers through a synonym table — that survives markup changes better than
pinned CSS selectors do.

If a race page comes back with no rows, the script says so and names the ids. Look
at `cache/race-<id>.html` and adjust `parse_results()`.

Requests are rate-limited to one per second and identify themselves.

## Sample data

`tools/make_sample_data.py` generates a plausible invented dataset so the interface
can be developed and checked without hitting the live site. When it's loaded, the
page says so in a banner. Running `scrape.py` overwrites everything it produced.

## Layout

```
index.html                    the interface — one self-contained file
scrape.py                     discover / fetch / build
tools/make_sample_data.py     invented stand-in data
data/                         generated; committed so the page works on Pages
cache/                        raw HTML, gitignored
```
