# Catamount Wednesdays

An explorable archive of the [Catamount Outdoor Family Center](https://catamountoutdoor.org/)
Wednesday night race series — every result, every season, in one page you can click
through instead of opening forty separate Webscorer tabs.

Two facts about this series shape everything here.

**A Wednesday is not one race.** The series runs Half, 1, 2, 3 and 4 lap options, and
each goes off on its own gun, minutes apart, on a stagger that has been reshuffled over
the years. A 4-lap rider and a 1-lap rider are not competing and did not even start
together, so placings, percentiles, rivals and head-to-head are all computed *within* a
lap count. Ranking them against each other would invent results that never happened.

**A course name is not a fixed course.** Red on Black in 2019 and Red on Black in
2025 cover roughly the same terrain, but the loop gets re-cut between seasons. So
times on the "same" course compare confidently *within* a season, where it's
genuinely the same lap repeated, and only loosely across years. Where a number has
to span seasons, the page uses finish percentile instead.

## What you can look up

**Racers** — a profile per person: starts, wins, podiums, best finish, which
distances they ride, and a scatter of where they land in the field over their whole
history, coloured by course.

**Rivals** — for any racer, everyone they've ever lined up against, ranked by how
often, with the head-to-head record and average margin. This is the "who beat who"
table.

**Head to head** — pick two people and get every night they both finished *at the
same distance*: who was ahead, by how much, and whether the gap is closing or
widening over the years.

**Courses** — a page per course showing every running of it across seasons, the
all-time fastest times per distance, and how the winning time has moved. A step
between years usually means the loop was re-cut rather than the field changing.

**Seasons** — standings for any year, sortable by starts, wins, podiums or median
finish.

**Weather** — conditions at the 6pm gun for every race: temperature, what it felt
like, sky, wind and gusts, humidity, and rain in the three hours beforehand (which
is what actually decides whether the dirt is slick). Each racer's profile breaks
their finishes down by temperature band, wet vs dry, and sun vs cloud.

## Running it

The page is a single static HTML file that reads a generated data bundle. Nothing
to build, no dependencies at runtime.

```sh
pip install -r requirements.txt

python scrape.py discover   # find every Catamount race        -> data/races.json
python scrape.py fetch      # pull each race's results         -> data/results.json
python scrape.py weather    # conditions at each race's 6pm    -> data/weather.json
python scrape.py build      # bundle for the page              -> data/catamount.{json,js}

python scrape.py all        # or just do all four
```

Then open `index.html`. It works straight off disk — the data is loaded as
`data/catamount.js` precisely so you don't need a local web server.

## Deploying

Set up to publish to Cloudflare Pages the same way `burghertime-landing` and
`emoji-rpg` do: `.github/workflows/deploy.yml` stages the static files into
`dist/` and runs `wrangler pages deploy` on every push to `main`.

Three one-time steps, all outside this repo:

1. **Create the Pages project.** In the Cloudflare dashboard, Workers & Pages →
   Create → Pages → *direct upload*, named `catamount-results`. No Git connection
   — the workflow pushes to it. (Recent wrangler will create the project on first
   deploy, but making it by hand avoids surprises about the production branch.)
2. **Add the credentials to this repo.** Settings → Secrets and variables →
   Actions:
   - secret `CLOUDFLARE_API_TOKEN` — the same account-wide Pages:Edit token the
     other two repos use.
   - variable `CLOUDFLARE_ACCOUNT_ID` — same account.
3. **Add the custom domain** `catamount.burghertime.com` through the Pages
   project's custom-domain flow, matching how `rpg.burghertime.com` is set up.
   burghertime.com's MX records are untouched by this.

`burghertime.com`'s landing page already links here, so once the domain resolves
the link goes live with it.

GitHub Pages works as a fallback with no setup beyond Settings → Pages → deploy
from `main`, root — the site is plain static files either way.

### Comparing anything to anything

Raw times mean something only within one course, one season, and one lap count.
That's a narrow window, so where a number has to reach past it the page uses one of
two normalisations:

- **Finish percentile** — where you placed in your lap group, 100% being the win.
  Immune to course length and lap count, sensitive to who showed up.
- **vs winner** — your time divided by the winning time at your distance that night.
  1.00 is a win, 1.20 means you took 20% longer. Immune to who showed up, sensitive
  to whether the winner had an off night.

Both are shown because neither is right on its own. Neither is shown as a single
headline "score", because there isn't one.

## Weather

Conditions come from the [Open-Meteo historical archive](https://open-meteo.com/),
sampled at the venue (44.4419, -73.1093) at 18:00 local for each race date.

Open-Meteo needs **no API key**, which is deliberate: this repository is public and
there is no credential for it to leak. Nothing here reads an environment variable or
expects a secret, and nothing should ever be added that does — if a future data
source needs a key, put it in GitHub Actions secrets and read it there, never in a
committed file.

```sh
python scrape.py weather    # -> data/weather.json, merged into the bundle by `build`
```

## What is and isn't published

Per racer, the data carries only what a results board already shows: name,
category, team, placing, time and lap count. Hometown is **deliberately dropped**
even though Webscorer displays it — nothing in the interface uses it, and
publishing where a named amateur lives is exposure this project has no reason to
create.

## How the scraping works

`scrape.py` runs in three phases so you can redo one without redoing the others.
Every page it fetches is cached as raw HTML under `cache/` (gitignored), so re-runs
cost nothing and you can iterate the parser offline against real pages.

Race metadata comes out of the Webscorer race title, which the series formats
consistently: `Catamount 6-21-23 MTB Race (Yellow on Green)` yields the date, the
discipline and the course. Lap count is dug out of whichever column carries it —
a Laps column when there is one, otherwise parsed from the distance, category or
event text (`Men A - 4 lap`), since it decides who is actually racing whom.

The results grid is found by scoring every `<table>` on
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
cache/                        raw HTML and weather JSON, gitignored
```
