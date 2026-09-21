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

1. **Name merges beyond the safe set (optional).** `aliases.json` holds 410
   merges: 140 reviewed by Tim, plus one-letter typos of a well-attested spelling (a rider with
   3+ starts and a variant with 1-2, never on the same night) added when the old pages arrived.
   Pairs left for a human call are listed at the bottom. Only add ones you are sure of.
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
could be two people (Brian/Bryan, Sara/Sarah, Steve/Steven, Kelly/Kelley). Nothing here shares a night. Merge
by adding to `aliases.json`.

- Adam Jezek / Adam Juzek (held back on purpose)
- Lea Davidson / Lea Davison (held back on purpose)
- Kevin Bouchard-Hill / Kevin Bouchard-Hall (held back on purpose)
- Marc Landry / Mark Landry (held back on purpose)
- Andrew Garner / Andrew Gardner (held back on purpose)
- John Schwartz / John Schwarz (held back on purpose)
- Tim Cater / Tim Carter (held back on purpose)
- Lucas Bauton / Lucas Barton (held back on purpose)
- Madelene Larson / Madeleine Larson (held back on purpose)
- Madeline Larson / Madeleine Larson (held back on purpose)
- Karen Ward / Karin Ward (held back on purpose)
- Brian Lister / Brian Lyster (held back on purpose)
- Bryan Picotte / Brian Picotte (held back on purpose)
- Brian Latourneau / Brian Letourneau (held back on purpose)
- Brian Spargue / Brian Sprague (held back on purpose)
- Ansel Spargue / Ansel Sprague (held back on purpose)
- Gunnar Steastes / Gunnar Steates (held back on purpose)
- Steven White / Steve White (held back on purpose)
- Dileep Netrahile / Dileep Netrabile (held back on purpose)
- Bob Parkes / Bob Parker (held back on purpose)
- Kamren Williams / Karen Williams (held back on purpose)
- John Maroney / John Mahoney (held back on purpose)
- Kristi Rochelea / Kristi Rocheleau (held back on purpose)
- Kristie Rocheleau / Kristi Rocheleau (held back on purpose)
- Brendan O'Connell / Brendan O'Donnell (held back on purpose)
- Steven Arnold / Steve Arnold (held back on purpose)
- Adam Juczek / Adam Juzek (held back on purpose)
- Steven Gioacchini / Steve Gioacchini (held back on purpose)
- Brian Ekenroth / Brian Eckenroth (held back on purpose)
- Steven Colangeli / Steve Colangeli (held back on purpose)
- Mary Smith / Mark Smith (held back on purpose)
- Pam Shwartz / Pam Swartz (held back on purpose)
- Pam Swarts / Pam Swartz (held back on purpose)
- Bryan Mitchell / Brian Mitchell (held back on purpose)
- Steve Munier / Steve Meunier (held back on purpose)
- Christina Fuller / Christine Fuller (held back on purpose)
- Brian Salatino / Bryan Salatino (held back on purpose)
- Joan Shaw / Joann Shaw (held back on purpose)
- Dick Anderson / Dirk Anderson (held back on purpose)
- Alyson Churchill / Alison Churchill (held back on purpose)
- Mark Barnett / Mark Burnett (held back on purpose)
- Pete Teasdale / Peter Teasdale (held back on purpose)
- Kristen Betz / Kristin Betz (held back on purpose)
- Ricky Witham / Rick Witham (held back on purpose)
- Tim Kelly / Tim Kelley (held back on purpose)
- Sarah Benoure / Sara Benoure (held back on purpose)
- Sarah Powell / Sara Powell (held back on purpose)
- Brady Rexroad / Brody Rexroad (held back on purpose)
- Janel Kilburn / Janet Kilburn (held back on purpose)
- Gunner Curtis / Gunnar Curtis (held back on purpose)
- Marna Stevenson / Marina Stevenson (held back on purpose)
- Renee Wolny / Renae Wolny (held back on purpose)
- Aaron Lackowski (1) / Aaron Lazkowski (1)
- Aaron Sommers (1) / Aaron Simmers (2)
- Adam Jezek (1) / Adam Juczek (1)
- Addie Voelegi (1) / Addie Voegeli (1)
- Alec Mogielnicki (2) / Alec Moglielnicki (1)
- Ali Weekes (1) / Ali Weeks (2)
- Allan Serrano (2) / Allen Serrano (1)
- Amanda Borok (1) / Amanda Borak (1)
- Amanda Halland (1) / Amanda Holland (1)
- Amelia Rodgers (1) / Amelia Rogers (1)
- Amilia Rodgers (1) / Amelia Rodgers (1)
- Amy Mayer (1) / Amy Miner (1)
- Andrea Wilson (2) / Andrea Willson (1)
- Andrew Geesin (1) / Andrew Geeslin (1)
- Andrew Jullow (1) / Andrew Julow (1)
- Andrew Wellman (6) / Andrew Wellam (1)
- Annie Kernoff (2) / Annie Kemoff (1)
- Ansel Emman (1) / Ansel Enman (1)
- Anthony Locicero (1) / Anthony Locieero (1)
- Arthur Harmon (1) / Arthur Harmen (1)
- Austin Nickolson (1) / Austin Nicholson (1)
- Autum Francis (1) / Autumn Francis (1)
- Bennett Shapird (1) / Bennett Shapiro (2)
- Bill Porter (10) / Bill Parker (1)
- Billy Malone (2) / Billy Melone (2)
- Bradley Patnadue (1) / Bradley Patnaude (1)
- Brian Forrest (1) / Bryan Forrest (1)
- Brian MacDonald (3) / Brian Mcdonall (1)
- Brian McDonnell (3) / Brian Mcdonall (1)
- Brian Salafino (1) / Brian Salatino (1)
- Bryan Bissell (1) / Brian Bissell (1)
- Caleb Kernan (2) / Caleb Kenan (1)
- Camille Bolduc (6) / Camille Buldoc (1)
- Carl Layfayette (1) / Carl Lafayette (1)
- Charie Erdman (1) / Charlie Erdman (1)
- Cheri Audet (1) / Cheri Audete (1)
- Chris Baron (5) / Chris Bardy (1)
- Chris Chaznon (1) / Chris Chagonon (1)
- Chris Lamonthe (1) / Chris Lomothe (1)
- Chris Lassy (11) / Chris Lacey (1)
- Chris Matthews (2) / Chris Mathews (1)
- Chris Trudel (1) / Chris Trudell (1)
- Christopher Settino (2) / Chirstopher Settino (1)
- Colleen Dando (2) / Collen Dando (1)
- Cory Marceau (1) / Corey Marceau (1)
- Curt Taylor (12) / Curt Tyler (1)
- Daniel Kernoff (2) / Daniel Kemoff (1)
- Dave Rochelean (2) / Dave Rocheleau (1)
- Dave Rucheleau (1) / Dave Rochelean (2)
- Dave Rucheleau (1) / Dave Rocheleau (1)
- Derek Bibb (1) / Derik Bibb (2)
- Devin MulacK (1) / Devin Mulac (2)
- Drew Gelinas (2) / Drew Gelinag (1)
- Eamon Welter (1) / Eamon Walker (1)
- Eleanor Devereux (10) / Eleanor Dervereaux (1)
- Elena Bilodeou (1) / Elena Bilodeau (1)
- Eli Quickel (2) / Eli Quickle (1)
- Eliza Otter (1) / Elisa Otter (1)
- Elizabeth Bernier (1) / Elizabeth Berger (4)
- Elizabeth Gares (3) / Elizabeth Garvey (1)
- Elizabeth Garvey (1) / Elisabeth Garvey (1)
- Elizabeth Havens (2) / Elizibeth Havens (1)
- Ellisa Doiron (2) / Ellisa Dorion (1)
- Emily Parenteau (2) / Emily Perecteau (1)
- Emma Ramirez-richer (1) / Emma Ramirez-Ritcher (2)
- Emmett Poirier (1) / Emmett Poirer (1)
- Eric Hickley (1) / Eric Hinkley (1)
- Eric Housler (1) / Eric Hausler (1)
- Erica Hartnick (1) / Erica Hartwick (1)
- Erica Mc Connell (1) / Erica Mac Connell (1)
- Ernie Buford (1) / Ernie Bouford (1)
- Evan Riggs (1) / Even Riggs (1)
- Evan Taures (1) / Evan Tavares (3)
- Finn Robinson (1) / Finn Robinskn (1)
- Francis Delisle (7) / Francis Decisie (1)
- Frank Grenon (4) / Frank Grennan (1)
- Garrich Applebee (2) / Garrick Applebee (1)
- Gerry McMahan (2) / Gerry Memahan (2)
- Giney Haggerty (1) / Ginny Haggerty (1)
- Grace Gillman (1) / Grace Gilman (2)
- Grace Rogers (2) / Grace Rodgers (1)
- Greg Connoly (2) / Greg Conelly (1)
- Greta Kilburn (64) / Greta Kulbern (1)
- Gretta Garvey (1) / Greta Garvey (1)
- Hannah Nichols (4) / Hannah Nichads (1)
- Harriet Veltcamp (1) / Harriet Veltkamp (1)
- Hatie Johnson (1) / Hattie Johnson (1)
- Henry Stern (1) / Henry Sterner (5)
- Hilary Delabrume (1) / Hilary Delabruere (3)
- Hillary Powulak (1) / Hillary Pawulack (1)
- JAred Thartchor (1) / Jared Thatcher (1)
- Jack Bates (1) / Jack Barnes (1)
- James Doiron (1) / James Dorion (1)
- James Iatridis (2) / James Intridis (1)
- James McLansland (1) / James McCausland (1)
- Jeff Hildebrand (2) / Jeff Hidlebrand (1)
- Jeff Labossiere (1) / Jeff Labassiere (2)
- Jeff Sprenger (5) / Jeff Spencer (2)
- Jeff Warner (23) / Jeff Warren (1)
- Jen Tumilowcz (1) / Jen Tumilowicz (1)
- Jennie Lowell (2) / Jennie Lawell (1)
- Jennifer Karpinski (1) / Jennifer Karpisnki (2)
- Jenny Crowford (1) / Jenny Crawford (1)
- Jerry Macner (21) / Jerry Moener (1)
- Jessie Homes (3) / Jessie Hines (1)
- Jessie Homes (3) / Jessie Holme (1)
- Jim Howley (2) / Jim Hawley (2)
- Joanne Grogan (57) / Joanne Giorgan (1)
- John Carney (1) / John Cooney (9)
- John Kelley (1) / John Kelly (2)
- John Luman (17) / John Lucas (1)
- John Ricardi (1) / John Ricardo (1)
- John Ricardi (1) / John Richardi (1)
- John Richardi (1) / John Ricardo (1)
- John Streker (2) / John Sterker (1)
- John Thartchor (1) / John Thatcher (5)
- Jon Greeley (1) / Jon Greene (1)
- Jonathan Marcin (1) / Jonathan Martin (1)
- Joseph Calano (1) / Joseph Castano (2)
- Josh Kemoff (1) / Josh Kernoff (1)
- Julia Humphrey (1) / Julia Humphries (1)
- Julie Davis (2) / Julie Davie (1)
- Julie Lowel (1) / Julie Lowell (1)
- Julie MacDougall (27) / Julie Macdougelll (1)
- Julie Mullowney (1) / Julie Meillowney (1)
- Justin Kelsey (16) / Justin Kenney (1)
- Justin Kenny (2) / Justin Kenney (1)
- Kate Christman (1) / Kate Christian (1)
- Kate Kogut (17) / Kate Kogge (2)
- Kathryn Kernoff (3) / Kathryn Kemoff (1)
- Katie Christman (1) / Kate Christman (1)
- Katie Humphrey (1) / Katie Humphry (1)
- Katie Lahiri (1) / Katie Lahir (1)
- Kelly Melasky (2) / Kelly Melashy (1)
- Kelly Melasky (2) / Kelly Melesy (1)
- Kelly Melesy (1) / Kelly Melashy (1)
- Kendra Kenny (2) / Kendra Kenney (1)
- Kevin Thorley (5) / Kevin Thorpe (1)
- Kevin Thorpe (1) / Kevin Thorp (1)
- Kiern Donnelly (1) / Kieran Donnelly (1)
- Kimberly Evans (1) / Kimberley Evans (2)
- Leah Haire (1) / Leah Harie (1)
- Liam Donnelly (1) / Liam Donnolly (1)
- Lili Martin (2) / Lily Martin (1)
- Lilly Doiron (2) / Lilly Dorion (1)
- Lisa Beter (1) / Lisa Beier (1)
- Lisa Kingsbury (1) / Lisa Kingsburg (1)
- Liz Gleeson (1) / Liz Gleason (1)
- Luke Helmer (3) / Luke Holmes (1)
- Luke Kirsch (2) / Luke Krisch (1)
- MEgan BEliste (1) / Megan Belisle (1)
- Madelene Larson (1) / Madeline Larson (1)
- Marc Vigeant (1) / Mark Vigeant (1)
- Maria Dziembrowska (1) / Maria Dziembowska (1)
- Marina Fisher (1) / Marina Fischer (1)
- Mark Bates (4) / Mark Baker (1)
- Mark Thomsen (1) / Mark Thamsen (1)
- Mark Weidmer (1) / Mark Weigner (1)
- Matt Davis (2) / Matt Davide (1)
- Matt Gordon (1) / Matt Germon (1)
- Matt Wineberger (1) / Matt Weinberger (1)
- Matthew Fraser (2) / Matthew Frazer (1)
- Matthew Williams (2) / Matthew Wiliams (1)
- Melissa Baker (1) / Melissa Barber (1)
- Michael Miklas (1) / Michael Miklus (1)
- Michael Russell (2) / Michael Russen (1)
- Michela Reagan (1) / Michaela Reagan (1)
- Mike Bergeron (2) / Mike Bereron (1)
- Mike Dacey (4) / Mike Dorcey (1)
- Mike Dorsey (1) / Mike Dorcey (1)
- Mike Maggz (1) / Mike Maggs (2)
- Miranda Voelegi (1) / Miranda Voegeli (1)
- Molly Coseno (7) / Molly Coffeno (1)
- Niall Keheler (1) / Niall Keleher (1)
- Nick Bouffard (1) / Nick Buffard (1)
- Nick Ortiz (2) / Nick Oritz (1)
- Nick Porier (3) / Nick Parker (1)
- Noah Tautfest (57) / Noah Tautfece (1)
- Noelle Lefeevre (1) / Noelle Lefebvre (1)
- Oliver Fanning (2) / Oliver Fannine (1)
- Olivia Osekoski (1) / Olivia Osekoshi (1)
- Paige Poirier (2) / Paige Poirer (2)
- Pam Shwartz (1) / Pam Swarts (1)
- Pat Omeara (1) / Pat O'Mera (1)
- Patrick O'brien (2) / Patrick Obrien (1)
- Paul Bolychevtsev (1) / Paul Bolychevstsev (1)
- Paula Miner (1) / Paula Miller (5)
- Peter Davey (12) / Peter Davis (1)
- Peter Nasveschuk (1) / Peter Nesveschuk (1)
- Peter Stewart (2) / Peter Stewert (1)
- Peter Stewart (2) / Peter Stuart (1)
- Rachel Hannah (1) / Rachel Hanna (1)
- Rachel Peters (11) / Rachel Powers (2)
- Randi Brevik (13) / Randi Brenk (1)
- Randy Novak (1) / Randy Nowak (2)
- Reuben Campbell (2) / Reuben Cambell (1)
- Riley Morigeau (1) / Ryley Morigeau (1)
- Robert Peterson (79) / Robert Patterson (1)
- Robin Percy (3) / Robin Perez (1)
- Rodney Putman (1) / Rodney Putnam (1)
- Ross MacGilliunay (1) / Ross MacGillivray (1)
- Roth Bemstein (1) / Roth Berstin (1)
- Roth Bernstein (6) / Roth Bemstein (1)
- Roth Bernstein (6) / Roth Berstin (1)
- Ryan Fitsimons (2) / Ryan Fitzimons (2)
- Ryan Fitsimons (2) / Ryan Fitzsimons (2)
- Ryan Fitzimons (2) / Ryan Fitzsimons (2)
- Ryan Jennigs (1) / Ryan Jennings (2)
- Ryan Marvin (2) / Ryan Marvyn (1)
- Ryan Mitighy (1) / Ryan Mitiguy (2)
- Ryan Thartchor (1) / Ryan Thatcher (5)
- Sadie Dyhman (1) / Sadie Dyhrman (2)
- Sali Cornwall (1) / Soli Cornwall (2)
- Sam Blakeley (2) / Sam Blakely (1)
- Sam Bowers (7) / Sam Bowen (1)
- Sam Damphousse (1) / Sam Damphouse (2)
- Sam Weber (1) / Sam Weaver (2)
- Sam Weber (1) / Sam Werbel (2)
- Sammy Hedlund (9) / Sammy Headland (1)
- Sandra Alton (4) / Sandra Allen (1)
- Sarah Palmer (1) / Sarah Parker (5)
- Scarlet Stimsom (1) / Scarlet Stimpson (1)
- Scott Rounds (2) / Scott Rands (1)
- Sean Melinn (23) / Sean Mellin (1)
- Shala Erlich (1) / Shala Elrich (1)
- Shaun O'Rourk (1) / Shaun O'Rourke (1)
- Sierra Fisher (2) / Sierra Fischer (1)
- Slane Greene (1) / Shane Greene (2)
- Soli Cornwall (2) / Sofi Cornwall (1)
- Solveig Hofving (1) / Solveig Hofuind (1)
- Stella O'Brien (2) / Stella Obrien (1)
- Stephanie Aydiayan (1) / Stephanie Aydinyan (1)
- Steve Finkle (2) / Steve Fiske (1)
- Steve Messier (18) / Steve Meymier (1)
- Steve Meunier (63) / Steve Meymier (1)
- Tanner Mogan (1) / Tanner Magnan (53)
- Ted McKnight (2) / Ted McNight (1)
- Teri Furlani (2) / Teri Furleni (1)
- Tess Swett (2) / Tess Sweet (1)
- Tessa Auwarter (2) / Tessa Anwarter (1)
- Tiger Bronsen (1) / Tiger Bronson (2)
- Tim Maher (1) / Tim Meyer (5)
- Tim Stowe (2) / Tim Stokes (11)
- Toby Richmaki (1) / Toby Richman (2)
- Todd Wamock (1) / Todd Warnock (1)
- Tom Rhodes (2) / Tom Rhoads (4)
- Tonje Hofvind (2) / Tonje Hofuind (1)
- Tonje Hofvind (2) / Tonje Hofving (2)
- Tonje Hofving (2) / Tonje Hofuind (1)
- Treavor Barr (1) / Trevor Barr (1)
- Turner Ramsay (1) / Turner Ramsey (1)
- Wayne Wamken (1) / Wayne Warnken (34)
- Weston Wheeler (1) / Westin Wheeler (1)
- Will Lacrois (1) / Will Lacross (1)
- Will Lacroix (21) / Will Lacross (1)
- Yannick Charbonneau (2) / Yannick Charbonneu (1)
- You-ran Handy (1) / Youran Handy (1)
