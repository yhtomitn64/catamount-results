# Handoff

Where the project stands, and what is left. Delete this file when the last item
below is done.

## Where things stand

- **Live at https://catamount.burghertime.com** (Cloudflare Pages project
  `catamount-results`, direct upload; `deploy.yml` redeploys on every push to
  `main`). The deploy token is the repo secret `CLOUDFLARE_API_TOKEN` (Pages:Edit,
  this account only) and the account id is the variable `CLOUDFLARE_ACCOUNT_ID`.
- **Real data:** 427 races (Wednesday MTB, Tuesday trail run, cyclocross), 45,617
  results, 7,423 racers, 2001-2026 with gaps (see below), with 6pm weather for every in-person
  race date. Three sources: Webscorer (2021-), Catamount's own 2021 weekly sheets
  (`tools/virtual_2021.py`, 14 self-timed "virtual" weeks) and Catamount's old website via the
  Wayback Machine (`tools/oldsite.py`: 222 nights, 2001-2019). Every
  parsed race matches the page's own "Racers: N" except those short by exactly
  the number of finishers with no registered name or a placeholder name
  ("COFC 3", "Please email for results"), which are skipped on purpose.
- **Published fields** are a name, a placing, a time and the start-line group
  (plus laps). Age category, team, hometown, bib and gender are dropped. See
  CLAUDE.md.
- **The UI is keyed on distance group** (`discipline|distance`), not lap count.
  Verified headlessly against the real bundle.
- **Identity merges** live in `aliases.json` (explicit, hand-kept). Only
  Tim / Timothy Burgher is merged so far.
- **Global email guard** is installed (`~/.githooks`) and verified: a fake secret
  staged in `family-mail-digest` and in `someday` is blocked by each repo's own
  `detect-secrets` hook, chained through the global one.
- **`burghertime-landing` history is rewritten**; any other clone of it diverges
  (re-clone, or `git reset --hard origin/master`).

## Not done yet

1. **Name merges (mostly done).** `aliases.json` holds 704 merges: the ones Tim reviewed, one-letter typos of
   a well-attested spelling, and (at his say-so) every remaining typo candidate from the old-results import.
   The only pair refused was Steve Messier / Steve Meunier (four shared nights: two people). What is left is
   in "Name pairs to review" below. Only add ones you are sure of.
2. **Scheduled refresh.** `refresh.yml` is manual-only. Before enabling the
   schedule, add `actions/cache` for `cache/` or every run re-downloads all ~196
   pages.

Done and live: the site, the domain, the landing-page card, the event filter,
and the GitHub "block pushes that expose my email" setting.

## Older results (mostly done)

`tools/oldsite.py` reads every usable page of the old site from the Wayback Machine cache
(`cache/wayback/`, fetched by `tools/wayback.py`): 222 nights. Two places hold them: `/results/YYYY/`
(2009-2019) and the site root, `/MMDDYY.HTM` (2001-2009) plus `/cxMMDDYY.htm` (cyclocross 2006-2008); a
full-domain CDX listing (`matchType=domain`) is what found the root pages, so if more turn up, list the
domain again. After the 2019 redesign the site answers a missing page with its home page, and the CDX
index's "one capture per URL" often picked such a capture; `wayback.candidates()` skips home-page-sized
captures (post-2019 only) and tries the next.

Gaps that remain: nothing archived for 2014-2016, and for 2011 only the index tables (below). The WordPress
series pages (2009-2013) list a results page for every night, e.g. `/results/2011/052411.HTM`,
`/results/2012/*.HTM`, `/results/2010/CX090810.htm`, `/results/2011/cx090711.htm`,
`/results/2012/cx091912.htm`, `/results/2013/CX_090413.htm`, but the Archive never captured them (a
prefix query on `/results/2011/`, `/2014/`, `/2015/`, `/2016/` finds none; the whole-domain listing has
1,577 URLs and 76 from 2009-2016). Web searches turn up no other host. So 2011, 2014-2016 and most of
2012-2013 are gaps unless someone at Catamount has the files. Also scattered: 2003, 2004, 2007-2013, 2018.
Deliberately not read: special events (Flower Power, Bramble Scramble, Eastern Cup, Stampy Stomp, the
duathlons, the 2006 Catamount Cyclocross Weekend), attendance and team reports, `2018/052218.htm` (an Excel
export whose times are not minutes and seconds), `080702.HTM` (2002-08-07: times like "39.9"), and the
plain-text `*.TXT` pages. The 2020 check found only re-captures of old pages.

Not yet looked at: `newresults.html` (2003), Catamount's dated "Current Race Course" banner for the 4
unlabelled 2022 courses, and Velocity Results / BikeReg for special events.

## Known data quirks

- Webscorer's organizer listing starts in July 2021. Earlier nights come from the old
  website (2019 so far) and are read by `tools/oldsite.py` from `cache/wayback/`.
  The old pages give each rider a placing inside a gender/age table; the site
  recomputes the placing inside the distance group from the times.
- 2019 pages `2019/060519.htm` (MTB) and `2019/061819.htm` (run) have a blank
  course line, so those two nights show no course. Their courses are not the same as
  the neighbouring night's (6/11 run Yellow on Green, 6/12 MTB Red on Black), so no
  sibling guess is made.
- Tim has one 2026 row, a DNF on 5-27-26 (4 lap). That is correct: he quit
  part-way through and did not race again that year. Not a scraper bug.

## Name pairs to review

Counts are (starts, years) as spelled on Webscorer. These pairs are NOT merged: an
earlier list of likely-same-person pairs was reviewed by Tim and merged, and what
is left here is what he declined (Matt/Max Tabasko, Sara/Sam Phillips) plus
pairs that are probably different people. Add a line to `aliases.json` only for
ones you are sure of. Two names that raced the same night are almost certainly
different people (family members with similar names are common here).

### Looks like the same person but held back by a safety check (0)



### Similar first names, not accepted as the same name (2)

- Matt Tabasko (53, 2021-2026) / Max Tabasko (10, 2024-2026) — raced the same night x9, likely different people
- Sara Phillips (11, 2021-2022) / Sam Phillips (1, 2024)

### One or two letters apart, found by edit distance (17)

- Bill Everett (3, 2022-2024) / Jill Everett (1, 2026) — 1 letter apart
- Bart Flagler (1, 2026) / Sara Flagler (1, 2026) — 2 letters apart; raced the same night x1, likely different people
- Bill Everett (3, 2022-2024) / Willy Everett (7, 2022) — 2 letters apart
- Kate Kogut (6, 2021-2022) / Dave Kogut (13, 2021-2026) — 2 letters apart; raced the same night x2, likely different people
- Leta Griffith (2, 2021-2022) / Leila Griffith (3, 2021-2023) — 2 letters apart
- Mary Rogers (4, 2024-2025) / Matt Rogers (17, 2025-2026) — 2 letters apart; raced the same night x2, likely different people
- Mira Carmolli (2, 2024-2026) / Nina Carmolli (3, 2026) — 2 letters apart
- Nora Donahue (1, 2022) / Rory Donahue (1, 2024) — 2 letters apart
- Nora Donahue (1, 2022) / Sara Donahue (1, 2022) — 2 letters apart; raced the same night x1, likely different people
- Olivia Smith (1, 2022) / Oliver Smith (1, 2023) — 2 letters apart
- Rose Donahue (1, 2023) / Rory Donahue (1, 2024) — 2 letters apart
- Ruth Knox (15, 2023-2026) / Beth Knox (1, 2026) — 2 letters apart; raced the same night x1, likely different people
- Sage Putnam (14, 2022-2026) / Kate Putnam (1, 2025) — 2 letters apart; raced the same night x1, likely different people
- Sarah Guidice (1, 2022) / Norah Guidice (1, 2022) — 2 letters apart; raced the same night x1, likely different people
- Willy Everett (7, 2022) / Jill Everett (1, 2026) — 2 letters apart
