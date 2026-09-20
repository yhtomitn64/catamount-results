# Handoff

Where the project stands, and what is left. Delete this file when the last item
below is done.

## Where things stand

- **Live at https://catamount.burghertime.com** (Cloudflare Pages project
  `catamount-results`, direct upload; `deploy.yml` redeploys on every push to
  `main`). The deploy token is the repo secret `CLOUDFLARE_API_TOKEN` (Pages:Edit,
  this account only) and the account id is the variable `CLOUDFLARE_ACCOUNT_ID`.
- **Real data:** 195 races (Wednesday MTB, Tuesday trail run, cyclocross), 13,879
  results, 2,024 racers, 2021-2026, with 6pm weather for every race date. Every
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

1. **Name merges beyond the safe set (optional).** `aliases.json` holds 102
   hand-kept merges (nicknames, spelling slips, middle names) that never share a race
   night. The pairs left for a human call are listed in "Name pairs to review" below.
   Only add ones you are sure of.
2. **Scheduled refresh.** `refresh.yml` is manual-only. Before enabling the
   schedule, add `actions/cache` for `cache/` or every run re-downloads all ~196
   pages.

Done and live: the site, the domain, the landing-page card, the event filter,
and the GitHub "block pushes that expose my email" setting.

## Known data quirks

- The organizer listing starts in July 2021; there is no earlier data.
- Tim has one 2026 row, a DNF on 5-27-26 (4 lap). That is correct: he quit
  part-way through and did not race again that year. Not a scraper bug.

## Name pairs to review

Counts are (starts, years) as spelled on Webscorer. A pair that shows up in these
lists is NOT merged; add a line to `aliases.json` only for ones you are sure of. If
two names raced the same night they are almost certainly different people (family
members with similar names are common here). Some names below are already merged
into a third spelling (for example Sam Moniz and Torsren Dworshak), so they are
effectively one person already.

### Looks like the same person but held back by a safety check (11)

- Aidan May (8, 2022) / Aiden May (1, 2025) — 3-year gap
- Benjamin Rogers (1, 2021) / Ben Rogers (14, 2025-2026) — 4-year gap
- Billy D Dysart (4, 2021) / Bill Dysart (22, 2023-2025) — 2-year gap
- Cricket Mccusker (1, 2023) / Kricket McCusker (6, 2025-2026) — 2-year gap
- Gilman M Lang (5, 2021) / Gillman Lang (13, 2025) — 4-year gap
- James Langan (4, 2021-2022) / Jim Langan (9, 2022-2025) — raced the same night x1
- Katie Areson (7, 2024) / Katherine Areson (9, 2026) — 2-year gap
- Kim Coleman (59, 2021-2026) / Kim Coleman 2 (1, 2024) — digit in name
- Nate Schafsteck (5, 2021-2023) / Nathan Schafsteck (1, 2021) — raced the same night x1
- Rosanne Van Dorn (2, 2023) / Roseanne Van Dorn (1, 2025) — 2-year gap
- Torsren Dworshak (1, 2021) / Tor Dworshak (4, 2023) — 2-year gap

### Similar first names, not accepted as the same name (21)

- Alden Samler (6, 2025-2026) / Aleen Samler (1, 2025)
- Braden Harden (1, 2022) / Brad Harden (2, 2024)
- Charles B Mccleary (1, 2022) / C.Brennan McCleary (8, 2023-2026)
- Devon Randall (6, 2024-2026) / Devin Randall (1, 2024)
- Don Bahrenburg (1, 2022) / Dan Bahrenburg (1, 2023)
- Eli Borofsky (1, 2025) / Elias Borofsky (1, 2025)
- Joe Near (1, 2025) / Jojo Near (6, 2026)
- John RODD (1, 2021) / Johnathan Rodd (10, 2025)
- Jon Rodd (8, 2021) / John RODD (1, 2021)
- Karen Bove (39, 2021-2026) / Karin Bove (1, 2023)
- Louise Larson (1, 2021) / Louisa Larson (54, 2022-2026)
- Marc Cass (12, 2023-2025) / Mark Cass (3, 2024-2025)
- Matt Tabasko (53, 2021-2026) / Max Tabasko (10, 2024-2026) — raced the same night x9, likely different people
- Mazza Merritt (1, 2022) / Mazzy Merritt (4, 2022-2023)
- Sam Fox (4, 2021-2023) / Samantha Fox (5, 2022-2023)
- Sam Moniz (1, 2022) / Samantha Moniz (2, 2024)
- Sara Phillips (11, 2021-2022) / Sam Phillips (1, 2024)
- Whitney Hanson (10, 2022-2025) / Whit Hanson (13, 2023-2026)
- Willa Loomis (2, 2022-2023) / Willow Loomis (1, 2023)
- Willy Picotte (1, 2024) / Wiley Picotte (1, 2024)
- Zech Brewton (3, 2021) / Zach Brewton (6, 2021-2024)

### One or two letters apart, found by edit distance (33)

- Bill Everett (3, 2022-2024) / Jill Everett (1, 2026) — 1 letter apart
- Caitlin Tyburski (1, 2023) / Kaitlin Tyburski (1, 2024) — 1 letter apart
- Caitlyn Tyburski (2, 2024) / Kaitlyn Tyburski (1, 2024) — 1 letter apart
- Jonathan Rodd (74, 2022-2026) / Johnathan Rodd (10, 2025) — 1 letter apart
- Bart Flagler (1, 2026) / Sara Flagler (1, 2026) — 2 letters apart; raced the same night x1, likely different people
- Bill Everett (3, 2022-2024) / Willy Everett (7, 2022) — 2 letters apart
- Caitlin Tyburski (1, 2023) / Kaitlyn Tyburski (1, 2024) — 2 letters apart
- Caitlyn Tyburski (2, 2024) / Kaitlin Tyburski (1, 2024) — 2 letters apart
- Doyle Strack (19, 2023-2026) / Dolye Strack (1, 2025) — 2 letters apart
- Ezra Buehler (57, 2021-2026) / Erza Buehler (7, 2025) — 2 letters apart
- Gaylene Randall (8, 2024-2026) / Galen Randall (1, 2024) — 2 letters apart
- Jamie Spencer (24, 2023-2025) / Jaime Spencer (1, 2023) — 2 letters apart
- Johannes Hollenbach (8, 2024-2025) / Johnes Hollenbach (1, 2026) — 2 letters apart
- Jonathan Harty (17, 2024-2026) / Johathon Harty (1, 2024) — 2 letters apart
- Kate Kogut (6, 2021-2022) / Dave Kogut (13, 2021-2026) — 2 letters apart; raced the same night x2, likely different people
- Leta Griffith (2, 2021-2022) / Leila Griffith (3, 2021-2023) — 2 letters apart
- Mary Rogers (4, 2024-2025) / Matt Rogers (17, 2025-2026) — 2 letters apart; raced the same night x2, likely different people
- Michael Gaughan (16, 2023-2026) / Micheal Gaughan (1, 2025) — 2 letters apart
- Michele Sandler (4, 2024) / Michael Sandler (19, 2025-2026) — 2 letters apart
- Mira Carmolli (2, 2024-2026) / Nina Carmolli (3, 2026) — 2 letters apart
- Nora Donahue (1, 2022) / Rory Donahue (1, 2024) — 2 letters apart
- Nora Donahue (1, 2022) / Sara Donahue (1, 2022) — 2 letters apart; raced the same night x1, likely different people
- Olivia Smith (1, 2022) / Oliver Smith (1, 2023) — 2 letters apart
- Reuben Campbell (1, 2025) / Rubin Campbell (1, 2025) — 2 letters apart
- Rosalie Niggel (3, 2023-2026) / Rosie Niggel (1, 2026) — 2 letters apart
- Rose Donahue (1, 2023) / Rory Donahue (1, 2024) — 2 letters apart
- Ruth Knox (15, 2023-2026) / Beth Knox (1, 2026) — 2 letters apart; raced the same night x1, likely different people
- Sage Putnam (14, 2022-2026) / Kate Putnam (1, 2025) — 2 letters apart; raced the same night x1, likely different people
- Sarah Guidice (1, 2022) / Norah Guidice (1, 2022) — 2 letters apart; raced the same night x1, likely different people
- Sean Hurley (3, 2023) / Shawn Hurley (1, 2023) — 2 letters apart
- Turman Durant (1, 2022) / Truman Durant (16, 2022-2026) — 2 letters apart
- Willy Everett (7, 2022) / Jill Everett (1, 2026) — 2 letters apart
- Zech Brewton (3, 2021) / Zack Brewton (1, 2022) — 2 letters apart
