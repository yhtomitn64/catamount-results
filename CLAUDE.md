# catamount-results

An explorable archive of the weekly summer and fall race series (Tuesday trail
running, Wednesday mountain biking, cyclocross) at Catamount Outdoor Family Center in
Williston, VT: a family outdoor center that was privately owned and is now owned by the
Town of Williston. It is not a club. One static page (`index.html`) reads a generated
data bundle (`data/catamount.js`); `scrape.py` builds that bundle from Webscorer.

**This is a PUBLIC repository.** Everything committed is world-readable forever.

## Hard rules

- **Never commit a personal email address or any credential.** Commits must be
  authored with the GitHub noreply address (`ID+USERNAME@users.noreply.github.com`).
  `.githooks/pre-commit` enforces this by allowlist (it never names the address it
  protects, because that would put it in the repo), and `.github/workflows/guard.yml`
  re-checks in CI. In a fresh clone run `git config core.hooksPath .githooks`.
  Do not use `--no-verify`.
- **No secrets, no env-var reads.** Open-Meteo needs no API key on purpose. If a
  future source needs a key, it goes in GitHub Actions secrets, never in a file.
- **Real names of amateur athletes are published here.** Publish only what a results
  board already shows, and only what the UI needs: name, placing, time, distance
  group, laps. Nothing that identifies a person beyond the race they did: hometown,
  age, age category, team, bib and gender are all dropped (bib and gender are read
  only to de-duplicate). Placeholder names ("COFC 3", "Please email for results")
  are skipped. Do not link racers to personal accounts (Strava, social) or infer
  identity from them. One narrow use of Strava is allowed: the owner's OWN activities,
  read locally and once, to work out which course a race night used. That yields one
  course label per race in `course_labels.json` and nothing per person; no token, key or
  raw track is ever committed. Other riders' Strava, Garmin or Trailforks data is off
  limits (Strava's API terms bar collecting it).
  Merging one person's spelled variants ("Tim" / "Timothy") is done only through the
  hand-kept `aliases.json`, never by guessing.
- **Do not deploy sample data.** `data/` holds a real scrape. `python
  tools/make_sample_data.py` overwrites it with invented data (the page shows a
  banner) — restore with `git checkout -- data` and never commit that.

## The two facts the whole design rests on

1. **A race night is not one race.** Wednesday MTB runs Half, 1, 2, 3 and 4 lap
   groups off the same start; Tuesday trail run runs Half and 5K; cyclocross is a
   single mass start where laps completed decide the order. The unit of
   competition is (race night, distance group). Placings, percentiles, rivals and
   head-to-head are computed inside that unit — never across groups. Each result
   row carries `distance` (the group label: "3 Lap", "5K", "Half", or "" for an
   undivided field) and `laps` (numeric when lap-based, and for cross the laps
   actually completed). If real data ever loses these, everything silently
   collapses into one group and reintroduces the bug, so check they are populated
   after any scrape. (Tim usually rides 4 laps, sometimes 3.)
2. **A course name is not a fixed course.** Red on Black in an early season and a recent one cover
   roughly the same terrain but the loop is re-cut. Times compare confidently
   within a season and only loosely across years; use finish percentile across
   years.

## Commands

```
pip install -r requirements.txt
python scrape.py discover     # -> data/races.json   (find every race id)
python scrape.py fetch        # -> data/results.json
python scrape.py weather      # -> data/weather.json (Open-Meteo, 6pm at the venue)
python scrape.py build        # -> data/catamount.{json,js}
python scrape.py all
python tools/make_sample_data.py   # invented data; overwrites the above
```

Open `index.html` directly — the data loads as a `<script>` so no server is needed.

## Tests

```
node tools/test/ui.test.js       # headless, no browser, no dependencies; CI runs it on every push
node tools/test/touch.test.js    # real touch events in headless Chrome as a phone (Node 22+, Chrome/Edge)
node tools/test/touch.test.js https://catamount.burghertime.com/    # a deployed copy
```

`ui.test.js` checks the data bundle against the publishing rules (only the allowlisted
fields, no placeholder names, no junk finish times, aliases resolve) and renders every
route against the real data. It is what proves the two design facts below still hold, so
run it after any change to `index.html` or `scrape.py`. `touch.test.js` covers what a
stubbed DOM cannot: tap targets, the keyboard staying down, the picker, chart taps,
rotation and scrolling. Both pick their test subjects from the data, so no test names a
real person; `CHROME_PATH` selects a browser and `--shots DIR` saves screenshots.

## Scraping etiquette

Webscorer's robots.txt allows `/cofc`, `/race?raceid=…` and
`/racealldetails?raceid=…` and disallows `/members/`, `/secure/`, `/racemap/`,
`/errors/`, `/controls`, `/v1/features/` and the register/pass confirm pages.
Stay inside that. Full results live at `/racealldetails`, not `/race` (which is
only a winners summary); the scraper reads it. `/cofc?pg=N` is not pagination. The scraper sends a descriptive User-Agent (Webscorer's CDN
403s the default curl one) and waits 1s between requests. Every page is cached
under `cache/` (gitignored) so parser work can be iterated offline.

## Files

```
index.html                 the whole interface (vanilla JS, inline SVG charts)
scrape.py                  discover / fetch / weather / build
tools/make_sample_data.py  invented stand-in data
tools/wayback.py           polite Wayback Machine client (slow, cached under cache/wayback/, backs off)
tools/virtual_2021.py      Catamount's 2021 weekly results PDFs (public Drive) -> data/extra/virtual_2021.json
tools/oldsite.py            Catamount's old results pages (Wayback copies in cache/wayback/) -> data/extra/oldsite.json
data/extra/                results that are not on Webscorer; scrape.py build merges them (negative race ids)
course_labels.json         courses the race titles never named, found another way (see Working notes)
tools/test/                ui.test.js (headless), touch.test.js + cdp.js (touch), fixtures.js
aliases.json               hand-kept merges of one person's spelled names
_headers                   Cloudflare Pages response headers
tools/protect-email.sh     optional: install the guard for every repo (read its caveat)
.githooks/pre-commit       email + credential guard
.github/workflows/         deploy.yml (Cloudflare Pages), guard.yml, test.yml, refresh.yml
```

## Working notes

- **Old website (2001-2019, with gaps).** `tools/oldsite.py` reads the results pages Catamount
  posted before Webscorer (Wayback copies; see its docstring for the four page formats). Same
  rules as everywhere: name, placing, time, distance group, laps; team, city, bib, age and gender
  are dropped. Race links say "Old results page" and point at the Wayback copy. A course is shown
  only where the page names one (2019; no star). Placings are recomputed inside each distance
  group, and a time no one could have run (a 5K in 1:40) is left out. `python tools/wayback.py`
  fetches (slow: 10 s apart, cached, backs off on 429/offline; it skips captures that are the site's
  home page, which the Archive stores for pages the redesigned site no longer has);
  oldsite.py never touches the network.
- **Power rankings** (`views.power`, tab "Rankings"). A Bradley-Terry fit per season over every pair of
  finishers inside each (night, distance) group, in-person nights only: beating a strong rider counts
  for more than beating a weak one, so a 3rd behind two fast riders can outrank a 2nd in a soft field.
  A prior (one win and one loss against an average rider) lets groups that never met be rated. Seasons
  only: a chain of opponents from 2008 to 2024 is not a comparison. A racer listed twice in one group
  counts once. `window.CatamountRank` exposes `ratings`, `step`, `dropFrom` and `budget` for the tests.
  Three things there are easy to "fix" and must not be, because each was chosen against held-out nights
  (refit a season with one night hidden, then predict it; 324,011 pairs over 2021-2026):
  - **Your worst night is set aside** (`DROP_FROM` = 4 nights before you can spare one, chosen on finish
    percentile so nobody picks their own). One bad night in a field of forty arrives as 39 losses and
    buries someone who beats those same forty every other week. 87.4% -> 87.7% of held-out pairs called
    right. The pair goes for *both* riders, so a night can lose pairs wholesale when it is many people's
    worst (a rare sport like the 10K, where the median group still keeps 84% of its pairs, the worst 23%).
    `#/power/<year>/<min>/counted` switches the rule off so a reader can see what it does.
  - **The spread is tempered** (`TEMPER` = 1.5). The fit treats 39 losses as 39 independent facts; they
    are not. Held-out nights put the raw spread about half again too wide. Rating =
    1500 + (`STEP`/`TEMPER`)*log10(strength), and with the temper a `STEP` (200) point gap really is
    ten-to-one odds (promised 87.5%, happened 88.9% on the busiest season).
  - **`BUDGET` = 400 passes is early stopping, not a tolerance.** Left to run the fit does not settle:
    a racer who won the only night they rode has no finite best strength and climbs for tens of thousands
    of passes until they top the season. Stopping short is what holds thin records near the middle, and
    it beat every principled alternative tried (a prior scaled to each racer's evidence, a bigger flat
    prior, counting a night as one result rather than forty: 87.7% against 84.9-87.5%). Raising it
    changes every rating on the page; a test pins the behaviour.

- **The method note** (`methodNote`, a folded `<details class="method">` on Rankings and Best of).
  Long-form "How the rating is worked out": the start-line group as the unit, pairs as results, the
  Bradley-Terry fit, the drop, early stopping, the temper, what a points gap means, and what the rating
  does *not* say. Its numbers come from the code, not from prose: the odds table is computed from `STEP`,
  the drop threshold from `DROP_FROM`, and on Rankings it quotes `agreement(pr)` for the season on screen
  (every pair that season, set-aside nights included, labelled as the flattering in-sample number next to
  the honest held-out one). Tests recompute all three and fail if the prose drifts from the fit.

- **Best of** (`views.best`, tab "Best of"). Each season's podium and the strongest seasons on record,
  for the current sport filter. There is no all-time rating and there must not be one: the all-time table
  ranks *seasons*, since 2100 in 2005 and 2100 in 2026 both mean "this far clear of the people who showed
  up". Fitting all 21 seasons costs about 5s, far too long for one repaint, so it is done a season per
  timer tick (`bestPump`) and each finished season re-renders: the table paints at once and fills in.
  `seasonRatings` caches by season + sport + drop, so the bill is paid once and Rankings is instant after.
  `window.CatamountBest.fill()` drives it straight through for the tests. Deeper fields leave more room
  at the top, so the all-time table leans slightly towards the 200-rider Wednesdays; ranking by each
  season's spread instead barely reorders it (9 of the top 10 are the same), so the raw rating stands.
- **Season zoom.** Time charts show dots only across all years (a line inside a sliver of a 20-year
  axis is a smear); a button per season zooms in and draws the line. `opts.trend` (the participation
  chart) opts out: one point per season, joined, gaps of more than a year break the line.
- **Virtual 2021.** The 2021 series opened with self-timed weeks (June 1 - July 21, minus the
  nights Webscorer already has). `data/extra/virtual_2021.json` holds them (`virtual: true`,
  14 weeks, 673 rows). The page treats them as their own event type: `evOf(race)` makes the
  group key `vMTB|4 Lap` / `vTR|5K`, they have a "Virtual 2021" filter, get no weather, and are
  left out of wins, podiums, rivals and head to head (nobody shared a start line). Placings are
  recomputed inside each distance because the sheet ranks across all of them; a rider listed
  under two age groups is kept once. Age group and team on the sheets are dropped like
  everywhere else. `python tools/virtual_2021.py --offline` re-parses `cache/drive/`.

- `index.html` stores literal UTF-8 (—, ·, °), not JS escapes. Match that when
  patching with find/replace or the anchors won't match.
- `/racealldetails` lists every racer twice: in a "<group> - Overall" table and again
  in each category table. The parser reads only the Overall table per group. A
  finisher with a bib but no registered name is skipped, so parsed rows can be one
  or two short of the page's own "Racers: N".
- Age and hometown are on the Webscorer page and are deliberately dropped.
- Race titles name a course only from 2023 (plus a few in 2024 written as plain words),
  and cross never has one. `course_labels.json` fills the unnamed 2021-22 MTB / trail-run
  races and marks them `courseSource`: `center` (2021: every in-person night, from the "Course:"
  line on Catamount's own weekly results PDFs in its public Google Drive folders, lined up to
  calendar weeks, plus the dated "Current Race Course" banner from the Wayback Machine),
  `gps` (2022: the owner's ride matched against the three 2022 courses' lap shapes: 11/11 on
  held-out known nights, 3 of 3 independent checks agreed) or `sibling` (the Tuesday run uses
  the same week's Wednesday course: true in 48 of 49 known weeks). 2021 ran a fourth course,
  "Black on Orange", which a three-course GPS match cannot tell from its neighbours (it
  mislabelled two such nights until Catamount's sheets corrected it), so GPS is only used for
  2022, when Catamount listed three courses. The page stars every filled-in course.
- Sample data is built to exercise the UI; a green run on it proves the UI logic,
  not the scraper. The results-table parser had never seen a real page as of the
  last commit.
