// Headless UI tests: loads index.html and the real data bundle into a stubbed DOM
// and renders every route. No browser, no network, no dependencies.
//
//     node tools/test/ui.test.js
//
// Two kinds of check. Data checks read data/catamount.json directly and guard what
// is published (see "Hard rules" in CLAUDE.md). UI checks render every page and
// assert on the HTML. Test subjects are picked from the data, never named here.
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { ROOT, readBundle, fixtures, prefixQuery } = require("./fixtures.js");

let failures = 0, total = 0;
function check(name, ok, detail) {
  total++;
  if (!ok) failures++;
  if (!ok || process.env.VERBOSE) console.log((ok ? "PASS " : "FAIL ") + name + (detail !== undefined ? "  -> " + detail : ""));
}

// ---------------------------------------------------------------------------
// data checks (untouched bundle, before the UI adds its derived fields)
// ---------------------------------------------------------------------------
const bundle = readBundle();
const fx = fixtures(bundle);
const races = bundle.races;
const strip = (h) => h.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");

// Published rows are a name, a placing, a time and the race group, and nothing else
// that identifies a person. This is the allowlist; adding a field means changing it
// here on purpose.
const ALLOWED_RESULT = new Set(["raceid", "place", "name", "racer", "distance", "laps", "time", "seconds"]);
const ALLOWED_RACE = new Set(["raceid", "title", "url", "date", "year", "discipline", "course", "courseSource", "finishers", "sport", "weather"]);
const extraResult = new Set();
bundle.results.forEach((r) => Object.keys(r).forEach((k) => { if (!ALLOWED_RESULT.has(k)) extraResult.add(k); }));
check("data: results carry only allowlisted fields", extraResult.size === 0, [...extraResult].join(","));
const extraRace = new Set();
races.forEach((r) => Object.keys(r).forEach((k) => { if (!ALLOWED_RACE.has(k)) extraRace.add(k); }));
check("data: races carry only allowlisted fields", extraRace.size === 0, [...extraRace].join(","));
check("data: bundle is not the invented sample set", bundle.sample === undefined);
check("data: there are races and results", races.length > 0 && bundle.results.length > 0);

const PLACEHOLDER = /e-?mail|unknown|\btbd\b|\(missing\)|need name|no bib|^cofc\b|^skirack\b|please|pleasse|plz/i;
const badNames = [...new Set(bundle.results.map((r) => r.name).filter((n) => PLACEHOLDER.test(n) || /\(\s*bib/i.test(n)))];
check("data: no timing-day placeholder names", badNames.length === 0, badNames.slice(0, 3).join(" | "));

const TIME = /^\s*\+?\s*(?:\d+:)?\d{1,2}:\d{2}(?:\.\d+)?\s*$/;
const junkTimes = bundle.results.filter((r) => r.time && !(TIME.test(r.time) || ["DNF", "DNS", "DQ", "-"].includes(r.time) || /^-\d+ laps?$/.test(r.time)));
check("data: every finish time is a time, DNF or laps-down", junkTimes.length === 0, junkTimes.length + " rows, e.g. " + (junkTimes[0] && junkTimes[0].time));

check("data: every race has a date, year and discipline", races.every((r) => r.date && r.year && ["MTB", "TR", "CX"].includes(r.discipline)));
check("data: every race has weather", races.every((r) => r.weather && r.weather.temp != null), races.filter((r) => !r.weather).length + " without");
check("data: every result belongs to a race and has a group label", bundle.results.every((r) => fx.raceById[r.raceid] && typeof r.distance === "string"));
check("data: 'N Lap' groups carry that many laps", bundle.results.every((r) => { const m = /^(\d+) Lap$/.exec(r.distance); return !m || r.laps === +m[1]; }));
check("data: every racer has a display name", fx.racers.every((k) => bundle.racers[k]));

const aliases = JSON.parse(fs.readFileSync(path.join(ROOT, "aliases.json"), "utf8")).aliases;
const resolved = Object.keys(aliases).filter((s) => bundle.racers[s]);
check("aliases: no merged-away spelling is still a racer", resolved.length === 0, resolved.slice(0, 3).join(","));
check("aliases: every target is a racer with results", Object.values(aliases).every((t) => bundle.racers[t]));

// Courses the race titles never named are filled in from course_labels.json and marked.
const labelFile = JSON.parse(fs.readFileSync(path.join(ROOT, "course_labels.json"), "utf8")).labels;
const inferred = races.filter((r) => r.courseSource);
const namedInTitle = (t) => /\([^)]+\)/.test(t) || /\b(red|black|white|yellow|green|blue|orange|purple)\s+(on|in)\s+(red|black|white|yellow|green|blue|orange|purple)\b/i.test(t);
// Titles only use three courses, but 2021 also ran "Black on Orange" (named on Catamount's own weekly sheets).
const knownCourses = new Set(races.filter((r) => !r.courseSource && r.course).map((r) => r.course).concat(["Black on Orange"]));
check("labels: every labelled race is in the bundle with that course and source", Object.entries(labelFile).every(([id, l]) => { const r = fx.raceById[id]; return r && r.course === l.course && r.courseSource === l.source; }));
check("labels: only races whose title names no course carry a label", inferred.every((r) => !namedInTitle(r.title)) && inferred.length === Object.keys(labelFile).length, inferred.length + " inferred");
check("labels: sources are gps, center or sibling, and courses are ones the titles use", inferred.every((r) => ["gps", "center", "sibling"].includes(r.courseSource) && knownCourses.has(r.course)));

// ---------------------------------------------------------------------------
// the UI, in a stubbed DOM
// ---------------------------------------------------------------------------
const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
if (scripts.length !== 1) throw new Error("expected one inline script, found " + scripts.length);

const els = {};
const el = (id) => els[id] || (els[id] = { id, innerHTML: "", textContent: "", value: "", focus() {}, dataset: {}, style: {} });
const listeners = {};
const win = {
  location: { hash: "" }, scrollTo() {},
  addEventListener(t, f) { (listeners[t] = listeners[t] || []).push(f); },
};
const ctx = {
  window: win, location: win.location, console, Set, Date, Math, Object, Array, JSON, String, Number, RegExp,
  isFinite, parseInt, parseFloat, setTimeout, clearTimeout,
  document: {
    getElementById: el, querySelectorAll: () => [],
    addEventListener(t, f) { (listeners["doc:" + t] = listeners["doc:" + t] || []).push(f); },
  },
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(ROOT, "data", "catamount.js"), "utf8"), ctx);
vm.runInContext(scripts[0], ctx, { filename: "index.html" });
const D = ctx.window.CATAMOUNT_DATA;   // the UI adds div, grp, dplace, pct ... to these rows

function route(hash) {
  win.location.hash = hash;
  (listeners.hashchange || []).forEach((f) => f());
  return el("view").innerHTML;
}
function clickFilter(id) {
  (listeners["doc:click"] || []).forEach((f) => f({
    target: { closest: (sel) => (/data-filter/.test(sel) ? { dataset: { filter: id } } : null) },
  }));
}

// ---- every route renders --------------------------------------------------------------
const years = [...new Set(races.map((r) => r.year))].sort();
const courses = [...new Set(races.map((r) => r.course).filter(Boolean))];
const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const routes = ["#/racer", "#/racer/" + fx.top, "#/h2h", "#/h2h/" + fx.top + "/" + fx.partner, "#/h2h/" + fx.top + "/-", "#/h2h/-/-",
  "#/course", "#/series", "#/races"]
  .concat(fx.allRounders.slice(0, 2).map((k) => "#/racer/" + k))
  .concat(courses.map((c) => "#/course/" + slug(c)))
  .concat(years.map((y) => "#/series/" + y))
  .concat(races.map((r) => "#/race/" + r.raceid));
const rendered = {};
let renderFailures = 0, sample = "";
routes.forEach((r) => {
  try {
    rendered[r] = route(r);
    const t = strip(rendered[r]);
    if (rendered[r].length < 150 || /undefined|NaN/.test(t)) { renderFailures++; sample = sample || r + " -> " + (t.match(/.{0,30}(undefined|NaN).{0,30}/) || [t.slice(0, 60)])[0]; }
  } catch (e) { renderFailures++; sample = sample || r + " threw " + e.message; }
});
check("ui: every route renders with no undefined/NaN (" + routes.length + " routes)", renderFailures === 0, renderFailures + " bad, first: " + sample);

// ---- the unit of competition is the start-line group -----------------------------------
const rowsByRace = {};
D.results.forEach((r) => { (rowsByRace[r.raceid] = rowsByRace[r.raceid] || []).push(r); });
let badDivs = 0, badDisc = 0, missingGrp = 0;
Object.keys(rowsByRace).forEach((id) => {
  const rows = rowsByRace[id];
  if (new Set(rows.map((r) => r.div)).size !== new Set(rows.map((r) => r.distance)).size) badDivs++;
  rows.forEach((r) => {
    if (!r.grp) missingGrp++;
    else if (r.grp.split("|")[0] !== fx.raceById[id].discipline) badDisc++;
  });
});
check("groups: each race has exactly one division per start-line group (never per lap count)", badDivs === 0, badDivs + " races");
check("groups: every result has a group key of its own sport", missingGrp === 0 && badDisc === 0);

const groupCount = (id) => new Set((rowsByRace[id] || []).map((r) => r.distance)).size;
let badTables = 0, badFinishers = 0;
races.forEach((r) => {
  const h = rendered["#/race/" + r.raceid], n = (rowsByRace[r.raceid] || []).length;
  if (!n) return;
  if ((h.match(/<table>/g) || []).length !== groupCount(r.raceid)) badTables++;
  if (!new RegExp("\\b" + n + " finishers\\b").test(strip(h))) badFinishers++;
});
check("race pages: one results table per start-line group", badTables === 0, badTables + " races");
check("race pages: the finisher count matches the data", badFinishers === 0, badFinishers + " races");

const med = (a) => { const s = a.slice().sort((x, y) => x - y); return s.length ? (s.length % 2 ? s[s.length >> 1] : (s[(s.length >> 1) - 1] + s[s.length >> 1]) / 2) : -1; };
let badOrder = 0, multi = 0;
races.forEach((r) => {
  const groups = {};
  (rowsByRace[r.raceid] || []).forEach((x) => { (groups[x.distance] = groups[x.distance] || []).push(x.seconds); });
  const names = Object.keys(groups);
  if (names.length < 3) return;
  multi++;
  const expected = names.sort((a, b) => med(groups[b].filter((v) => v != null)) - med(groups[a].filter((v) => v != null)));
  const h = rendered["#/race/" + r.raceid];
  const pos = expected.map((g) => h.indexOf("<h2>" + (g || "Results") + "</h2>"));
  if (pos.some((p) => p < 0) || pos.some((p, i) => i && p < pos[i - 1])) badOrder++;
});
check("race pages: groups run longest-first (" + multi + " multi-group races)", badOrder === 0, badOrder + " races out of order");

const mass = races.filter((r) => r.discipline === "CX" && groupCount(r.raceid) === 1 && (rowsByRace[r.raceid] || []).length);
check("cyclocross: a mass start is one table with a laps column", mass.length > 0 && mass.every((r) => { const h = rendered["#/race/" + r.raceid]; return (h.match(/<table>/g) || []).length === 1 && />Laps</.test(h); }), mass.length + " races");

// ---- event-type filter ---------------------------------------------------------------------
const byDisc = (d) => races.filter((r) => r.discipline === d);
for (const d of ["MTB", "CX", "TR"]) {
  clickFilter(d);
  const v = route("#/races");
  const links = (v.match(/href="#\/race\/\d+"/g) || []).length;
  const shown = Math.min(byDisc(d).length, 200);
  check("filter " + d + ": races page lists " + byDisc(d).length + " races", new RegExp('<p class="hint">' + byDisc(d).length + " races \\(").test(v) && links === shown, links + " rows");
  check("filter " + d + ": the button is marked pressed", new RegExp('data-filter="' + d + '" class="on"').test(v));
}
clickFilter("CX");
check("filter: home heading follows the filter, do-it-all card stays", /Most starts, Cyclocross/.test(route("#/racer")) && (fx.allRounders.length === 0 || route("#/racer").includes("Do-it-all racers")));
const noCx = fx.missing("CX");
if (noCx) check("filter: a racer with no starts in the sport gets a message and the bar", /No Cyclocross results for this racer/.test(route("#/racer/" + noCx)) && route("#/racer/" + noCx).includes('data-filter="all"'));
clickFilter("all");
check("filter: All restores every race", new RegExp('<p class="hint">' + races.length + " races on record").test(route("#/races")));
check("filter: all races has an Event column", route("#/races").includes(">Event<"));

// ---- inferred courses are marked ------------------------------------------------------------------
if (inferred.length) {
  check("inferred: an inferred course is starred on its race page", /class="inferred"/.test(rendered["#/race/" + inferred[0].raceid]));
  const named = races.find((r) => r.course && !r.courseSource);
  check("inferred: a course named in the title is not starred", !/class="inferred"/.test(rendered["#/race/" + named.raceid]));
  check("inferred: the footer explains the asterisk", /does not name a course/.test(el("footer").innerHTML));
}

// ---- type-to-search --------------------------------------------------------------------------
const src = html.match(/\/\/ ---- racer search \(begin\) ----([\s\S]*?)\/\/ ---- racer search \(end\) ----/)[1];
const byRacer = {};
bundle.results.forEach((r) => { (byRacer[r.racer] = byRacer[r.racer] || []).push(r); });
const searchRacers = vm.runInNewContext(src + "; searchRacers", { RACER_KEYS: Object.keys(bundle.racers), nameOf: (k) => bundle.racers[k], resultsByRacer: byRacer });
const topName = bundle.racers[fx.top];
const names = (q, n) => searchRacers(q, n || 8).map((e) => e.name);
check("search: empty and blank queries return nothing", searchRacers("", 8).length === 0 && searchRacers("   ", 8).length === 0);
check("search: gibberish returns nothing", searchRacers("zzzzqqxx", 8).length === 0);
check("search: the full name finds that racer first", names(topName)[0] === topName, names(topName)[0]);
check("search: first letters of each word are enough", names(prefixQuery(topName)).includes(topName), prefixQuery(topName));
check("search: case and spacing do not matter", names("  " + topName.toUpperCase().replace(/ /g, "   ") + " ")[0] === topName);
check("search: every typed word must match", names(prefixQuery(topName) + " zzzzqq").length === 0);
check("search: the limit is respected", searchRacers("a", 5).length === 5);
{
  const q = topName.split(/\s+/).pop().slice(0, 3).toLowerCase();   // e.g. the first three letters of a last name
  const res = searchRacers(q, 60);
  const word = (e) => e.name.toLowerCase().split(/[^a-z0-9']+/).filter(Boolean).some((w) => w.startsWith(q));
  const firstInside = res.findIndex((e) => !word(e)), lastWord = res.map(word).lastIndexOf(true);
  check("search: words that start with the query rank above ones that only contain it", firstInside === -1 || lastWord < firstInside, "first inside " + firstInside + ", last word-start " + lastWord);
  let tie = true;
  for (let i = 1; i < res.length; i++) if (word(res[i - 1]) === word(res[i]) && res[i - 1].starts < res[i].starts) tie = false;
  check("search: equal matches order by number of starts", tie);
}

// ---- head to head picker ------------------------------------------------------------------------------
const h2h = rendered["#/h2h/" + fx.top + "/" + fx.partner];
check("h2h: type-to-search boxes, no drop-down of everyone", (h2h.match(/class="picker-input"/g) || []).length === 2 && !/<select/.test(h2h));
check("h2h: chosen racers are prefilled", h2h.includes('value="' + topName + '"') && h2h.includes('value="' + bundle.racers[fx.partner] + '"'));
check("h2h: the boxes are accessible comboboxes", /role="combobox"[^>]*aria-expanded="false"/.test(h2h) && /role="listbox"/.test(h2h));
check("h2h: a half-filled URL leaves the second box empty", /id="h2h-b"[^>]*value=""/.test(rendered["#/h2h/" + fx.top + "/-"]));
check("h2h: an empty URL leaves both boxes empty", (rendered["#/h2h/-/-"].match(/value=""/g) || []).length >= 2);

// ---- charts -------------------------------------------------------------------------------------------------------
const yearTicks = (h) => new Set([...h.matchAll(/<text[^>]*text-anchor="middle"[^>]*>(\d{4})<\/text>/g)].map((m) => +m[1]));
const topPage = rendered["#/racer/" + fx.top];
check("charts: the time axis names every season on record", years.every((y) => yearTicks(topPage).has(y)), [...yearTicks(topPage)].join(","));
const firstChart = (topPage.split('class="chart"')[1] || "").split("</svg>")[0];
const withPct = D.results.filter((r) => r.racer === fx.top && r.pct != null).length;
check("charts: 'Where they finish' plots every start that has a percentile", (firstChart.match(/<circle class="pt"/g) || []).length === withPct, withPct + " expected");
check("charts: courseless races are plotted as 'Course not listed'", !D.results.some((r) => r.racer === fx.top && r.pct != null && !fx.raceById[r.raceid].course) || topPage.includes("Course not listed"));
check("charts: every chart is followed by a tap readout", (topPage.match(/class="chart-readout"/g) || []).length === (topPage.match(/<svg class="chart"/g) || []).length);
check("charts: dots carry their text for a tap and there are no leftover rings", /<circle class="pt"[^>]* data-t="[^"]+"/.test(topPage) && !/class="hit"/.test(topPage));
{
  const W = 720, PL = 46, PR = 14;
  const x0 = Date.parse(years[0] + "-01-01"), x1 = Date.parse((years[years.length - 1] + 1) + "-01-01");
  const yearAt = (x) => new Date(x0 + ((x - PL) / (W - PL - PR)) * (x1 - x0)).getUTCFullYear();
  let segments = 0, crossing = 0;
  fx.racers.slice(0, 3).map((k) => "#/racer/" + k).concat(courses.slice(0, 1).map((c) => "#/course/" + slug(c))).forEach((r) => {
    for (const m of route(r).matchAll(/<path[^>]* d="([^"]+)"/g)) {
      let prev = null;
      m[1].trim().split(/\s*(?=[ML])/).map((t) => t.trim()).filter(Boolean).forEach((t) => {
        const x = parseFloat(t.slice(1));
        if (t[0] === "L" && prev !== null) { segments++; if (yearAt(prev) !== yearAt(x)) crossing++; }
        prev = x;
      });
    }
  });
  check("charts: no line segment joins two different seasons", segments > 0 && crossing === 0, crossing + " of " + segments + " segments cross");
}

// ---- long tables ---------------------------------------------------------------------------------------------------------
const bigYear = years.find((y) => new Set(D.results.filter((r) => fx.raceById[r.raceid].year === y).map((r) => r.racer)).size > 200);
if (bigYear) {
  const page = route("#/series/" + bigYear);
  const table = (page.match(/<table>[\s\S]*?<\/table>/g) || []).find((t) => /Podiums/.test(t));
  check("tables: a very long table is cut to 200 rows with a Show-all button", /data-more>Show all \d+ rows</.test(page) && !!table && (table.match(/<tr>/g) || []).length - 1 === 200);
}
check("tables: a short table gets no Show-all button", !/data-more/.test(route("#/race/" + races[0].raceid)));

console.log(failures ? "\n" + failures + " of " + total + " checks FAILED" : "\nAll " + total + " checks passed");
process.exit(failures ? 1 : 0);
