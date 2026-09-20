// Picks test subjects from the data bundle itself, so no test names a real person
// and the tests keep working after every re-scrape.
"use strict";
const fs = require("fs");
const path = require("path");

// CATAMOUNT_ROOT points the suite at another copy of the site (used to prove the
// guards fail when the data is tampered with).
const ROOT = process.env.CATAMOUNT_ROOT || path.join(__dirname, "..", "..");

function readBundle() {
  return JSON.parse(fs.readFileSync(path.join(ROOT, "data", "catamount.json"), "utf8"));
}

function fixtures(bundle) {
  const starts = {};
  bundle.results.forEach((r) => { starts[r.racer] = (starts[r.racer] || 0) + 1; });
  const racers = Object.keys(starts).sort((a, b) => starts[b] - starts[a] || (a < b ? -1 : 1));
  const raceById = {};
  bundle.races.forEach((r) => { raceById[r.raceid] = r; });

  const top = racers[0];
  // the racer who shared the most start-line groups with the top racer
  const topDivs = new Set(bundle.results.filter((r) => r.racer === top).map((r) => r.raceid + "|" + r.distance));
  const shared = {};
  bundle.results.forEach((r) => {
    if (r.racer !== top && topDivs.has(r.raceid + "|" + r.distance)) shared[r.racer] = (shared[r.racer] || 0) + 1;
  });
  const partner = Object.keys(shared).sort((a, b) => shared[b] - shared[a] || (a < b ? -1 : 1))[0];

  const disciplinesOf = {};
  bundle.results.forEach((r) => {
    const set = (disciplinesOf[r.racer] = disciplinesOf[r.racer] || new Set());
    if (!raceById[r.raceid].virtual) set.add(raceById[r.raceid].discipline);   // self-timed weeks are not a sport
  });
  const allRounders = racers.filter((k) => disciplinesOf[k].size >= 3);
  // someone who never raced one of the disciplines (to exercise the empty state)
  const missing = (d) => racers.find((k) => !disciplinesOf[k].has(d));

  return { starts, racers, raceById, top, partner, disciplinesOf, allRounders, missing };
}

// the first letters of each name word: "Jane Doe" -> "jan do"
function prefixQuery(name, n = 3) {
  return name.toLowerCase().split(/\s+/).filter(Boolean).map((w) => w.slice(0, n)).join(" ");
}

module.exports = { ROOT, readBundle, fixtures, prefixQuery };
