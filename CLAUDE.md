# catamount-results

An explorable archive of the Catamount Outdoor Family Center Wednesday night
race series (Williston, VT). One static page (`index.html`) reads a generated
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
  are skipped. Do not add anything that links racers to personal accounts
  (Strava, social) or infers identity — that idea was considered and dropped.
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
tools/protect-email.sh     optional: install the guard for every repo (read its caveat)
.githooks/pre-commit       email + credential guard
.github/workflows/         deploy.yml (Cloudflare Pages), guard.yml, refresh.yml
```

## Working notes

- `index.html` stores literal UTF-8 (—, ·, °), not JS escapes. Match that when
  patching with find/replace or the anchors won't match.
- `/racealldetails` lists every racer twice: in a "<group> - Overall" table and again
  in each category table. The parser reads only the Overall table per group. A
  finisher with a bib but no registered name is skipped, so parsed rows can be one
  or two short of the page's own "Racers: N".
- Age and hometown are on the Webscorer page and are deliberately dropped.
- Sample data is built to exercise the UI; a green run on it proves the UI logic,
  not the scraper. The results-table parser had never seen a real page as of the
  last commit.
