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
  board already shows (name, category, team, placing, time, lap count). Hometown is
  deliberately dropped. Do not add anything that links racers to personal accounts
  (Strava, social) or infers identity — that idea was considered and dropped.
- **Do not deploy sample data.** `data/` currently holds invented stand-in data
  (banner on the page says so). Replace it with a real scrape before this goes live.

## The two facts the whole design rests on

1. **A Wednesday is not one race.** The series runs 1, 2, 3 and 4 lap options off
   the same start. The unit of competition is (race night, lap count). Placings,
   percentiles, rivals and head-to-head are computed inside that unit — never
   across lap counts. If real data ever loses its lap counts, everything silently
   collapses into one group and reintroduces the bug, so check `lapCount` is
   populated after any scrape. (Tim usually rides 4 laps, sometimes 3.)
2. **A course name is not a fixed course.** Red on Black in 2019 and 2025 cover
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

Webscorer's robots.txt allows `/cofc` and `/race?raceid=…` and disallows
`/members/`, `/secure/`, `/racemap/`, `/errors/`, `/controls`, `/v1/features/`.
Stay inside that. The scraper sends a descriptive User-Agent (Webscorer's CDN
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
- Sample data is built to exercise the UI; a green run on it proves the UI logic,
  not the scraper. The results-table parser had never seen a real page as of the
  last commit.
