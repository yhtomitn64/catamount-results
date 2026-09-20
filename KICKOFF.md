# Handoff

Where the project stands, and what is left. Delete this file when the last item
below is done.

## Where things stand

- **Live at https://catamount.burghertime.com** (Cloudflare Pages project
  `catamount-results`, direct upload; `deploy.yml` redeploys on every push to
  `main`). The deploy token is the repo secret `CLOUDFLARE_API_TOKEN` (Pages:Edit,
  this account only) and the account id is the variable `CLOUDFLARE_ACCOUNT_ID`.
- **Real data:** 224 races (Wednesday MTB, Tuesday trail run, cyclocross), 16,789
  results, 2,346 racers, 2019 and 2021-2026 (2020 was skipped), with 6pm weather for
  every in-person race date. Three sources: Webscorer (2021-), Catamount's own 2021
  weekly sheets (`tools/virtual_2021.py`, 14 self-timed "virtual" weeks) and Catamount's
  old website via the Wayback Machine (`tools/oldsite.py`, so far 15 nights of 2019). Every
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

1. **Name merges beyond the safe set (optional).** `aliases.json` holds 213
   merges: 140 reviewed by Tim, plus 73 one-letter typos of a well-attested spelling
   (a rider with 3+ starts and a variant with 1-2, never on the same night) that were
   added when the 2019 pages arrived. The pairs left for a human call are listed in
   "Name pairs to review" below. Only add ones you are sure of.
2. **Scheduled refresh.** `refresh.yml` is manual-only. Before enabling the
   schedule, add `actions/cache` for `cache/` or every run re-downloads all ~196
   pages.

Done and live: the site, the domain, the landing-page card, the event filter,
and the GitHub "block pushes that expose my email" setting.

## Older results: the Wayback plan (paused, the Archive was down)

Catamount's own pre-Webscorer results pages are archived at `catamountoutdoor.com/results/`:
2009-2013 (scattered weekly pages and special events), **2017 (38 pages, about a full
season), 2018 (13 pages), 2019 (39 pages)**, and nothing for 2014-2016. The list of 137
archived URLs is cached in `cache/wayback/` (rebuild with `tools/wayback.py cdx`). When the
Archive is back: fetch them with `tools/wayback.py` (4+ s apart, cached), look at each
era's HTML format, write one parser per format, and decide how to show pre-2021 seasons
(no distance groups on old pages?). Same publishing rules as everything else.

Other places that might hold results, not yet checked: Catamount's dated "Current Race
Course" banner on `catamountoutdoor.org/race-series-weekly/` (Wayback captures from 2021-22
name the week's course); Google Drive folders of 2021 *virtual* results linked from that page
(DONE: `tools/virtual_2021.py`, 14 self-timed weeks in `data/extra/`);
VMBA and BikeReg event pages (entries, not times); Velocity Results (special events such as
the Catamount Classic XCT). `cofc.org` is NOT Catamount (Webscorer's "cofc" is only an
account name); its archive is an unrelated organisation.

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
- Gaylene Randall (8, 2024-2026) / Galen Randall (1, 2024) — 2 letters apart
- Kate Kogut (6, 2021-2022) / Dave Kogut (13, 2021-2026) — 2 letters apart; raced the same night x2, likely different people
- Leta Griffith (2, 2021-2022) / Leila Griffith (3, 2021-2023) — 2 letters apart
- Mary Rogers (4, 2024-2025) / Matt Rogers (17, 2025-2026) — 2 letters apart; raced the same night x2, likely different people
- Michele Sandler (4, 2024) / Michael Sandler (19, 2025-2026) — 2 letters apart
- Mira Carmolli (2, 2024-2026) / Nina Carmolli (3, 2026) — 2 letters apart
- Nora Donahue (1, 2022) / Rory Donahue (1, 2024) — 2 letters apart
- Nora Donahue (1, 2022) / Sara Donahue (1, 2022) — 2 letters apart; raced the same night x1, likely different people
- Olivia Smith (1, 2022) / Oliver Smith (1, 2023) — 2 letters apart
- Rose Donahue (1, 2023) / Rory Donahue (1, 2024) — 2 letters apart
- Ruth Knox (15, 2023-2026) / Beth Knox (1, 2026) — 2 letters apart; raced the same night x1, likely different people
- Sage Putnam (14, 2022-2026) / Kate Putnam (1, 2025) — 2 letters apart; raced the same night x1, likely different people
- Sarah Guidice (1, 2022) / Norah Guidice (1, 2022) — 2 letters apart; raced the same night x1, likely different people
- Willy Everett (7, 2022) / Jill Everett (1, 2026) — 2 letters apart

### 2019 typo candidates not merged yet (69)

One-letter or transposition variants where neither spelling is clearly the main one, or a
nickname pair. Nothing here shares a night. Merge by adding to `aliases.json`.

- Aaron Lackowski (1) / Aaron Lazkowski (1)
- Addie Voelegi (1) / Addie Voegeli (1)
- Amanda Borok (1) / Amanda Borak (1)
- Andrew Geesin (1) / Andrew Geeslin (1)
- Andy Mckinny (2) / Andy McKinney (1)
- Annie Kernoff (1) / Annie Kemoff (1)
- Ansel Emman (1) / Ansel Enman (1)
- Arthur Harmon (1) / Arthur Harmen (1)
- Austin Nickolson (1) / Austin Nicholson (1)
- Billy Malone (2) / Billy Melone (1)
- Bradley Patnadue (1) / Bradley Patnaude (1)
- Brian McDonnell (3) / Brian Mcdonall (1)
- Chris Fitzhugh (2) / Chris Fitshugh (2)
- Chris Matthews (2) / Chris Mathews (1)
- Chris Trudel (1) / Chris Trudell (1)
- Colleen Dando (2) / Collen Dando (1)
- Daniel Kernoff (1) / Daniel Kemoff (1)
- Daniel Scheidt (3) / Daniel Shmidt (1)
- Eli Quickel (2) / Eli Quickle (1)
- Ellisa Doiron (1) / Ellisa Dorion (1)
- Emma Ramirez-richer (1) / Emma Ramirez-Ritcher (2)
- Emmett Poirier (1) / Emmett Poirer (1)
- Eric Hickley (1) / Eric Hinkley (1)
- Finn Robinson (1) / Finn Robinskn (1)
- Galen Randall (1) / Galene Randall (1)
- Giney Haggerty (1) / Ginny Haggerty (1)
- Grace Gillman (1) / Grace Gilman (2)
- Greta Kilburn (36) / Greta Kulbern (1)
- Henry Stern (1) / Henry Sterner (4)
- James Doiron (1) / James Dorion (1)
- Jennie Lawell (1) / Jennie Lowell (1)
- Jenny Crowford (1) / Jenny Crawford (1)
- Jerry Macner (14) / Jerry Moener (1)
- Kathryn Kernoff (1) / Kathryn Kemoff (1)
- Kelly Melasky (2) / Kelly Melashy (1)
- Kelly Melasky (2) / Kelly Melesy (1)
- Kelly Melesy (1) / Kelly Melashy (1)
- Kendra Kenny (2) / Kendra Kenney (1)
- Kirsten Workman (1) / Kiersten Workman (1)
- Kristen Workman (1) / Kirsten Workman (1)
- Lili Martin (2) / Lily Martin (1)
- Lilly Doiron (1) / Lilly Dorion (1)
- Luke Helmer (2) / Luke Holmes (1)
- Maddy Dorion (1) / Maddy Doiron (1)
- Matthew Frazer (1) / Matthew Fraser (1)
- Matthew Mckinney (2) / Mathew Mckinney (1)
- Mazzy Merrit (1) / Mazzy Meritt (1)
- Michael Gawghan (1) / Michael Gauhan (1)
- Mike Dacey (4) / Mike Dorcey (1)
- Mike Dorsey (1) / Mike Dorcey (1)
- Miranda Voelegi (1) / Miranda Voegeli (1)
- Molly Coseno (1) / Molly Coffeno (1)
- Nick Bouffard (1) / Nick Buffard (1)
- Noelle Lefeevre (1) / Noelle Lefebvre (1)
- Oliver Fanning (1) / Oliver Fannine (1)
- Paige Poirier (2) / Paige Poirer (2)
- Phil Parish (1) / Phil Parrish (2)
- Roth Bernstein (5) / Roth Bemstein (1)
- Ryan Jennigs (1) / Ryan Jennings (2)
- Sam Weber (1) / Sam Werbel (1)
- Sammy Hedlund (6) / Sammy Headland (1)
- Sarah Primbram (1) / Sarah Pribram (1)
- Scarlet Stimsom (1) / Scarlet Stimpson (1)
- Scarlet Stimsom (1) / Scarlett Stimsom (1)
- Sydney Carney-knisely (1) / Sydney Carney-kinsely (1)
- Tanner Mogan (1) / Tanner Magan (1)
- Tanner Mogan (1) / Tanner Magnan (52)
- Wayne Wamken (1) / Wayne Warnken (32)
- You-ran Handy (1) / Youran Handy (1)
