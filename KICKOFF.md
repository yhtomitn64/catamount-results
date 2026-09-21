# Handoff

Where the project stands, and what is left. Delete this file when the last item
below is done.

## Where things stand

- **Live at https://catamount.burghertime.com** (Cloudflare Pages project
  `catamount-results`, direct upload; `deploy.yml` redeploys on every push to
  `main`). The deploy token is the repo secret `CLOUDFLARE_API_TOKEN` (Pages:Edit,
  this account only) and the account id is the variable `CLOUDFLARE_ACCOUNT_ID`.
- **Real data:** 277 races (Wednesday MTB, Tuesday trail run, cyclocross), 23,373
  results, 4,103 racers, 2009-2026 with gaps (see below), with 6pm weather for every in-person
  race date. Three sources: Webscorer (2021-), Catamount's own 2021 weekly sheets
  (`tools/virtual_2021.py`, 14 self-timed "virtual" weeks) and Catamount's old website via the
  Wayback Machine (`tools/oldsite.py`: 68 nights across 2009, 2010, 2012, 2013, 2017, 2018, 2019). Every
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

1. **Name merges beyond the safe set (optional).** `aliases.json` holds 284
   merges: 140 reviewed by Tim, plus one-letter typos of a well-attested spelling (a rider with
   3+ starts and a variant with 1-2, never on the same night) added when the old pages arrived.
   Pairs left for a human call are listed at the bottom. Only add ones you are sure of.
2. **Scheduled refresh.** `refresh.yml` is manual-only. Before enabling the
   schedule, add `actions/cache` for `cache/` or every run re-downloads all ~196
   pages.

Done and live: the site, the domain, the landing-page card, the event filter,
and the GitHub "block pushes that expose my email" setting.

## Older results (mostly done)

`tools/oldsite.py` reads every usable page of `catamountoutdoor.com/results/` from the Wayback
Machine cache (`cache/wayback/`, fetched by `tools/wayback.py`: 136 pages, 68 usable nights).
Gaps: the Archive holds nothing for 2014-2016 and only scattered nights for 2009-2013, 2018.
Half of the 2017-2018 captures are the site's home page instead of the results (a redirect), so
those nights are simply missing. Not read: special events, attendance reports, one Excel export.

Still worth a look (Archive permitting): a 2020 check (the site's pages from 2020, the
season was mostly cancelled or virtual), Catamount's dated "Current Race Course" banner for the
4 unlabelled 2022 courses, and the Velocity Results / BikeReg pages for special events.

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

### Typo candidates not merged yet

One-letter or transposition variants where neither spelling is clearly the main one, or the pair
could be two people (Brian/Bryan, Sara/Sarah). Nothing here shares a night. Merge by adding to
`aliases.json`.

- Adam Jezek / Adam Juzek (held back on purpose)
- Lea Davidson / Lea Davison (held back on purpose)
- Kevin Bouchard-Hill / Kevin Bouchard-Hall (held back on purpose)
- Kip Robers / Kip Roberts (held back on purpose)
- John Schwartz / John Schwarz (held back on purpose)
- Lucas Bauton / Lucas Barton (held back on purpose)
- Madelene Larson / Madeleine Larson (held back on purpose)
- Madeline Larson / Madeleine Larson (held back on purpose)
- Bryan Picotte / Brian Picotte (held back on purpose)
- Bryan Mitchell / Brian Mitchell (held back on purpose)
- Sarah Powell / Sara Powell (held back on purpose)
- Bob Parkes / Bob Parker (held back on purpose)
- Brian Salatino / Bryan Salatino (held back on purpose)
- Brady Rexroad / Brody Rexroad (held back on purpose)
- Janel Kilburn / Janet Kilburn (held back on purpose)
- Dileep Netrabile / Duleep Netrabile (held back on purpose)
- Gunner Curtis / Gunnar Curtis (held back on purpose)
- Chris Zeigler / Chris Zigler (held back on purpose)
- Aaron Lackowski (1) / Aaron Lazkowski (1)
- Addie Voelegi (1) / Addie Voegeli (1)
- Alec Mogielnicki (1) / Alec Moglielnicki (1)
- Amanda Borok (1) / Amanda Borak (1)
- Andrew Geesin (1) / Andrew Geeslin (1)
- Andrew Wellmen (1) / Andrew Wellman (2)
- Annie Kernoff (1) / Annie Kemoff (1)
- Ansel Emman (1) / Ansel Enman (1)
- Arthur Harmon (1) / Arthur Harmen (1)
- Austin Nickolson (1) / Austin Nicholson (1)
- Billy Malone (2) / Billy Melone (2)
- Bradley Patnadue (1) / Bradley Patnaude (1)
- Brian Forrest (1) / Bryan Forrest (1)
- Brian MacDonald (1) / Brian Mcdonall (1)
- Brian McDonnell (3) / Brian Mcdonall (1)
- Brian Salafino (1) / Brian Salatino (1)
- Camille Bolduc (1) / Camille Buldoc (1)
- Cherly McNeil (2) / Cheryl McNeil (1)
- Chris Bernier (2) / Chris Berger (1)
- Chris Matthews (2) / Chris Mathews (1)
- Chris Trudel (1) / Chris Trudell (1)
- Colleen Dando (2) / Collen Dando (1)
- Daneille Petter (2) / Danielle Petter (2)
- Daniel Kernoff (1) / Daniel Kemoff (1)
- Daniel Schmidt (12) / Daniel Schiedt (1)
- Dave Rochelean (2) / Dave Rocheleau (1)
- Drew Gelinas (2) / Drew Gelinag (1)
- Dunbar Oehmog (3) / Dunbar Ohmig (2)
- Eli Quickel (2) / Eli Quickle (1)
- Eliza Otter (1) / Elisa Otter (1)
- Elizabeth Bernier (1) / Elizabeth Berger (2)
- Elizabeth Gares (3) / Elizabeth Garvey (1)
- Elizabeth Garvey (1) / Elisabeth Garvey (1)
- Ellisa Doiron (2) / Ellisa Dorion (1)
- Emma Ramirez-richer (1) / Emma Ramirez-Ritcher (2)
- Emmett Poirier (1) / Emmett Poirer (1)
- Eric Hickley (1) / Eric Hinkley (1)
- Evan Riggs (1) / Even Riggs (1)
- Evan Taures (1) / Evan Tavares (3)
- Finn Robinson (1) / Finn Robinskn (1)
- Giney Haggerty (1) / Ginny Haggerty (1)
- Grace Gillman (1) / Grace Gilman (2)
- Greta Kilburn (55) / Greta Kulbern (1)
- Harriet Veltcamp (1) / Harriet Veltkamp (1)
- Henry Stern (1) / Henry Sterner (5)
- JAred Thartchor (1) / Jared Thatcher (1)
- James Doiron (1) / James Dorion (1)
- Jennie Lowell (2) / Jennie Lawell (1)
- Jenny Crowford (1) / Jenny Crawford (1)
- Jerry Macner (16) / Jerry Moener (1)
- Joanne Grogan (47) / Joanne Giorgan (1)
- John Carney (1) / John Cooney (6)
- John Ricardi (1) / John Ricardo (1)
- John Ricardi (1) / John Richardi (1)
- John Richardi (1) / John Ricardo (1)
- John Schaefer (2) / John Scheer (2)
- John Streker (2) / John Sterker (1)
- John Thartchor (1) / John Thatcher (1)
- Julia Humphrey (1) / Julia Humphries (1)
- Kate Christman (1) / Kate Christian (1)
- Kathryn Kernoff (1) / Kathryn Kemoff (1)
- Katie Christman (1) / Kate Christman (1)
- Kelly Melasky (2) / Kelly Melashy (1)
- Kelly Melasky (2) / Kelly Melesy (1)
- Kelly Melesy (1) / Kelly Melashy (1)
- Kendra Kenny (2) / Kendra Kenney (1)
- Kevin Thorley (5) / Kevin Thorpe (1)
- Kevin Thorpe (1) / Kevin Thorp (1)
- Lili Martin (2) / Lily Martin (1)
- Lilly Doiron (1) / Lilly Dorion (1)
- Liz Gleeson (1) / Liz Gleason (1)
- Luke Helmer (3) / Luke Holmes (1)
- MEgan BEliste (1) / Megan Belisle (1)
- Madelene Larson (1) / Madeline Larson (1)
- Mark Hanarhan (1) / Mark Hannahan (2)
- Matt Wineberger (1) / Matt Weinberger (1)
- Matthew Frazer (1) / Matthew Fraser (1)
- Michael Miklas (1) / Michael Miklus (1)
- Mike Dacey (4) / Mike Dorcey (1)
- Mike Dorsey (1) / Mike Dorcey (1)
- Miranda Voelegi (1) / Miranda Voegeli (1)
- Molly Coseno (1) / Molly Coffeno (1)
- Nicholas Bouffard (2) / Nicholas Bonffard (1)
- Nick Bouffard (1) / Nick Buffard (1)
- Nick Oritz (1) / Nick Ortiz (1)
- Noah Tautfest (50) / Noah Tautfece (1)
- Noelle Lefeevre (1) / Noelle Lefebvre (1)
- Oliver Fanning (2) / Oliver Fannine (1)
- Paige Poirier (2) / Paige Poirer (2)
- Paul Bolychevtsev (1) / Paul Bolychevstsev (1)
- Reuben Campbell (2) / Reuben Cambell (1)
- Robert Leubbers (2) / Robert Luebbers (1)
- Robert Peterson (59) / Robert Patterson (1)
- Ross MacGilliunay (1) / Ross MacGillivray (1)
- Roth Bernstein (5) / Roth Bemstein (1)
- Ryan Jennigs (1) / Ryan Jennings (2)
- Ryan Thartchor (1) / Ryan Thatcher (5)
- Sabastian Bronk (1) / Sebastian Bronk (1)
- Sadie Dyhman (1) / Sadie Dyhrman (2)
- Sali Cornwall (1) / Soli Cornwall (2)
- Sam Bowers (7) / Sam Bowen (1)
- Sam Damphousse (1) / Sam Damphouse (2)
- Sam Weber (1) / Sam Werbel (2)
- Sammy Hedlund (9) / Sammy Headland (1)
- Sara Benoure (1) / Sarah Benoure (1)
- Scarlet Stimsom (1) / Scarlet Stimpson (1)
- Shala Erlich (1) / Shala Elrich (1)
- Slane Greene (1) / Shane Greene (2)
- Soli Cornwall (2) / Sofi Cornwall (1)
- Stephanie Aydiayan (1) / Stephanie Aydinyan (1)
- Steve Messier (17) / Steve Meymier (1)
- Steve Meunier (6) / Steve Meymier (1)
- Tanner Mogan (1) / Tanner Magnan (53)
- Todd Wamock (1) / Todd Warnock (1)
- Wayne Wamken (1) / Wayne Warnken (34)
- Yannick Charbonneau (2) / Yannick Charbonneu (1)
- You-ran Handy (1) / Youran Handy (1)
