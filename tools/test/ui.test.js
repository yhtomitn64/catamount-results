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
const ALLOWED_RACE = new Set(["raceid", "title", "url", "date", "year", "discipline", "course", "courseSource", "finishers", "sport", "weather", "virtual"]);
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
check("data: names are plain text (no leftover HTML entities or tags)", !bundle.results.some((r) => /[<>&; ]/.test(r.name)), bundle.results.filter((r) => /[<>&; ]/.test(r.name)).slice(0, 2).map((r) => r.name).join(" | "));
check("data: no timing-day placeholder names", badNames.length === 0, badNames.slice(0, 3).join(" | "));

const TIME = /^\s*\+?\s*(?:\d+:)?\d{1,2}:\d{2}(?:\.\d+)?\s*$/;
const junkTimes = bundle.results.filter((r) => r.time && !(TIME.test(r.time) || ["DNF", "DNS", "DQ", "-"].includes(r.time) || /^-\d+ laps?$/.test(r.time)));
check("data: every finish time is a time, DNF or laps-down", junkTimes.length === 0, junkTimes.length + " rows, e.g. " + (junkTimes[0] && junkTimes[0].time));

check("data: every race has a date, year and discipline", races.every((r) => r.date && r.year && ["MTB", "TR", "CX"].includes(r.discipline)));
// Virtual weeks were self-timed wherever riders were, so a 6pm reading at the venue would be wrong for them.
const virtual = races.filter((r) => r.virtual);
check("data: every in-person race has weather, no virtual week does", races.filter((r) => !r.virtual).every((r) => r.weather && r.weather.temp != null) && virtual.every((r) => !r.weather),
  races.filter((r) => !r.virtual && !r.weather).length + " without");
check("data: virtual weeks are extras (negative id, on a results sheet) and their placings are within the distance", virtual.every((r) => {
  if (!(r.raceid < 0 && /^https:\/\/drive\.google\.com\//.test(r.url))) return false;
  const byDist = {};
  bundle.results.filter((x) => x.raceid === r.raceid).forEach((x) => { (byDist[x.distance] = byDist[x.distance] || []).push(x); });
  return Object.values(byDist).every((g) => new Set(g.map((x) => x.racer)).size === g.length &&
    g.every((x) => x.place === 1 + g.filter((y) => y.seconds < x.seconds).length));
}), virtual.length + " virtual weeks");
// Nights read from the old website: the page's own heading date is sometimes stale, so the title's date is
// used and must land on the sport's weekday; and a time nobody could have run is left out.
const oldRaces = races.filter((r) => /archive\.org/.test(r.url));
const weekday = (d) => new Date(d + "T12:00:00Z").getUTCDay();
check("old site: every night falls on its sport's weekday (Tue run, Wed bike and cross)", oldRaces.length > 0 && oldRaces.every((r) => weekday(r.date) === (r.discipline === "TR" ? 2 : 3)),
  oldRaces.filter((r) => weekday(r.date) !== (r.discipline === "TR" ? 2 : 3)).map((r) => r.date).join(","));
const oldIds = new Set(oldRaces.map((r) => r.raceid));
const tooFast = bundle.results.filter((r) => oldIds.has(r.raceid) && r.seconds && ((r.distance === "5K" && r.seconds < 720) || (/^\d Lap$/.test(r.distance) && r.seconds < 450 * r.laps)));
check("old site: no time faster than anyone could run", tooFast.length === 0, tooFast.length + " rows");
check("old site: every race id is unique and negative", oldRaces.every((r) => r.raceid < 0) && new Set(races.map((r) => r.raceid)).size === races.length);
check("data: every result belongs to a race and has a group label", bundle.results.every((r) => fx.raceById[r.raceid] && typeof r.distance === "string"));
check("data: 'N Lap' groups carry that many laps", bundle.results.every((r) => { const m = /^(\d+) Lap$/.exec(r.distance); return !m || r.laps === +m[1]; }));
check("data: every racer has a display name", fx.racers.every((k) => bundle.racers[k]));

const aliases = JSON.parse(fs.readFileSync(path.join(ROOT, "aliases.json"), "utf8")).aliases;
const resolved = Object.keys(aliases).filter((s) => bundle.racers[s]);
check("aliases: no merged-away spelling is still a racer", resolved.length === 0, resolved.slice(0, 3).join(","));
check("aliases: every target is a racer with results", Object.values(aliases).every((t) => bundle.racers[t]));

// Courses the race titles never named are filled in from course_labels.json and marked.
const labelFile = JSON.parse(fs.readFileSync(path.join(ROOT, "course_labels.json"), "utf8")).labels;
// Virtual weeks name their course on the sheet, not in the title, so they carry a source but no label-file entry.
const inferred = races.filter((r) => r.courseSource && !r.virtual);
const namedInTitle = (t) => /\([^)]+\)/.test(t) || /\b(red|black|white|yellow|green|blue|orange|purple)\s+(on|in)\s+(red|black|white|yellow|green|blue|orange|purple)\b/i.test(t);
// Titles only use three courses, but 2021 also ran "Black on Orange" (named on Catamount's own weekly sheets).
const knownCourses = new Set(races.filter((r) => !r.courseSource && r.course).map((r) => r.course).concat(["Black on Orange"]));
check("virtual: every week names a course from the sheet and is marked as inferred", races.filter((r) => r.virtual).every((r) => r.courseSource === "center" && knownCourses.has(r.course)));
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
    else if (r.grp.split("|")[0] !== (fx.raceById[id].virtual ? "v" : "") + fx.raceById[id].discipline) badDisc++;
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
const byDisc = (d) => races.filter((r) => d === "V" ? r.virtual : !r.virtual && r.discipline === d);
for (const d of ["MTB", "CX", "TR", "V"]) {
  clickFilter(d);
  const v = route("#/races");
  const links = (v.match(/href="#\/race\/-?\d+"/g) || []).length;
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

// ---- virtual weeks are their own event type -------------------------------------------------
if (virtual.length) {
  const isVirt = (r) => fx.raceById[r.raceid].virtual;
  const virtualWinner = D.results.find((r) => isVirt(r) && r.dplace === 1);
  const winsOn = (k) => D.results.filter((r) => r.racer === k && !isVirt(r) && r.dplace === 1).length;
  check("virtual: a virtual win is not counted as a win on the racer page", (() => {
    const v = route("#/racer/" + virtualWinner.racer);
    return new RegExp('<div class="n">' + winsOn(virtualWinner.racer) + '</div><div class="l">Wins</div>').test(v);
  })());
  const vr = virtual[0];
  const vpage = route("#/race/" + vr.raceid);
  check("virtual: the race page says it was self-timed and links the results sheet", /A virtual week/.test(vpage) && /Results sheet/.test(vpage) && !/Webscorer/.test(vpage) && /Virtual (MTB|run)/.test(vpage));
  check("virtual: an in-person race page has neither the note nor the sheet link", (() => {
    const p = route("#/race/" + races.find((r) => /webscorer\.com/.test(r.url)).raceid);
    return !/A virtual week/.test(p) && /Webscorer/.test(p) && !/Results sheet/.test(p);
  })());
  const old = races.find((r) => /archive\.org/.test(r.url));
  if (old) check("old site: the footer names the old website and the 2021 sheets as sources", /Wayback/.test(el("footer").innerHTML) && /2021 weekly sheets/.test(el("footer").innerHTML));
  if (old) check("old site: a page from the old website links its archived copy, not Webscorer", (() => {
    const p = route("#/race/" + old.raceid);
    return /Old results page/.test(p) && !/Webscorer/.test(p) && !/A virtual week/.test(p);
  })());
  // Two riders who only ever shared a virtual week have no head to head or rivalry.
  const inPersonRacers = new Set(D.results.filter((r) => !isVirt(r)).map((r) => r.racer));
  const sameDiv = {};
  D.results.filter((r) => isVirt(r) && !inPersonRacers.has(r.racer)).forEach((r) => { (sameDiv[r.div] = sameDiv[r.div] || []).push(r.racer); });
  const pair = Object.values(sameDiv).find((g) => g.length >= 2);
  check("virtual: two riders who only ever shared a virtual group have no head to head or rivalry", !!pair && /have never finished the same race/.test(strip(route("#/h2h/" + pair[0] + "/" + pair[1]))) &&
    !new RegExp("#/h2h/" + pair[0] + "/" + pair[1]).test(route("#/racer/" + pair[0])), pair ? "" : "no pair found");
  clickFilter("V");
  check("virtual filter: the racer list counts only virtual starts", route("#/racer").includes("Most starts, Virtual 2021"));
  clickFilter("all");
}
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
// With 20 seasons on a 720px chart the labels thin to every second year (never closer than 34px); every label
// must still be a season on record, and the newest is always named.
const axisYears = [...yearTicks(topPage)];
check("charts: the time axis labels only seasons on record, newest included, at least a third of them", axisYears.every((y) => years.includes(y)) && axisYears.includes(Math.max(...years)) && axisYears.length * 3 >= years.length, axisYears.join(","));
// On a phone the axis is 300px wide: labels thin out (newest year always kept) instead of overprinting.
win.innerWidth = 360;
const narrow = route("#/racer/" + fx.top);
win.innerWidth = 0;
const labelXs = [...narrow.split('class="chart"')[1].split("</svg>")[0].matchAll(/<text x="([\d.]+)"[^>]*text-anchor="middle"[^>]*>(\d{4})<\/text>/g)].map((m) => [+m[1], +m[2]]);
check("charts: on a narrow screen the year labels never crowd and keep the newest year",
  labelXs.length > 1 && labelXs.every((l, i) => !i || l[0] - labelXs[i - 1][0] >= 30) && labelXs[labelXs.length - 1][1] === Math.max(...years), labelXs.map((l) => l[1]).join(","));
const firstChart = (topPage.split('class="chart"')[1] || "").split("</svg>")[0];
const withPct = D.results.filter((r) => r.racer === fx.top && r.pct != null).length;
check("charts: 'Where they finish' plots every start that has a percentile", (firstChart.match(/<circle class="pt"/g) || []).length === withPct, withPct + " expected");
check("charts: courseless races are plotted as 'Course not listed'", !D.results.some((r) => r.racer === fx.top && r.pct != null && !fx.raceById[r.raceid].course) || topPage.includes("Course not listed"));
check("charts: every chart is followed by a tap readout", (topPage.match(/class="chart-readout"/g) || []).length === (topPage.match(/<svg class="chart"/g) || []).length);
check("charts: dots carry their text for a tap and there are no leftover rings", /<circle class="pt"[^>]* data-t="[^"]+"/.test(topPage) && !/class="hit"/.test(topPage));
// ---- season zoom: all years = dots only; one season = zoomed, with the line -------------------------------------------------
function clickYear(y) {
  (listeners["doc:click"] || []).forEach((f) => f({
    target: { closest: (sel) => (/data-year/.test(sel) ? { dataset: { year: String(y) } } : null) },
  }));
}
{
  const topRows = D.results.filter((r) => r.racer === fx.top && !fx.raceById[r.raceid].virtual);
  const seasons = [...new Set(topRows.map((r) => fx.raceById[r.raceid].year))].sort();
  const charts = (h) => h.split('<svg class="chart"').slice(1).map((c) => c.split("</svg>")[0]);
  const paths = (h) => charts(h).reduce((n, c) => n + (c.match(/<path /g) || []).length, 0);
  const home = route("#/racer/" + fx.top);
  check("seasons: all years shows dots only (a line inside a sliver of a 20-year axis is a smear)", charts(home).length > 0 && paths(home) === 0);
  check("seasons: the time charts offer All years plus each season", seasons.length > 1 && home.includes('data-year="all"') && seasons.every((y) => home.includes('data-year="' + y + '"')) && /data-year="all" class="on"/.test(home));

  const y = seasons.filter((s) => topRows.filter((r) => fx.raceById[r.raceid].year === s).length >= 3).pop();
  clickYear(y);
  const zoomed = route("#/racer/" + fx.top);   // route() changes the hash, which must reset to All years
  check("seasons: a new page starts on All years again", /data-year="all" class="on"/.test(zoomed));
  route("#/racer/" + fx.top); clickYear(y);
  const one = el("view").innerHTML;
  const inYear = D.results.filter((r) => r.racer === fx.top && r.pct != null && !fx.raceById[r.raceid].virtual && fx.raceById[r.raceid].year === y).length;
  check("seasons: picking a season keeps only that season's dots and marks it pressed", (charts(one)[0].match(/<circle class="pt"/g) || []).length === inYear && new RegExp('data-year="' + y + '" class="on"').test(one), inYear + " expected");
  check("seasons: a season view draws the line and labels months", paths(one) > 0 && /text-anchor="middle"[^>]*>(May|Jun|Jul|Aug|Sep)</.test(charts(one)[0]) && !new RegExp(">" + seasons[0] + "</text>").test(charts(one)[0]));
  let cross = 0, segs = 0;
  const W = 720, PL = 46, PR = 14;
  for (const m of one.matchAll(/<path[^>]* d="([^"]+)"/g)) {
    const xs = m[1].trim().split(/\s*(?=[ML])/).filter(Boolean).map((t) => parseFloat(t.trim().slice(1)));
    segs += xs.length; xs.forEach((x) => { if (x < PL - 1 || x > W - PR + 1) cross++; });
  }
  check("seasons: every point of a season line sits inside the chart", segs > 0 && cross === 0);
  clickYear("all");
  check("seasons: All years restores the full chart", paths(el("view").innerHTML) === 0 && el("view").innerHTML.includes('data-year="all" class="on"'));
  route("#/racer/" + fx.top);
}

// ---- participation over time --------------------------------------------------------------------------------------------------
{
  clickFilter("all");
  const page = route("#/series");
  const both = page.split('<svg class="chart"').slice(1).map((c) => c.split("</svg>")[0]);
  const live = races.filter((r) => !r.virtual);
  const perYear = new Set(live.map((r) => r.discipline + "|" + r.year));
  check("participation: a trend chart and a night-by-night chart on the Seasons page", both.length === 2 && page.includes("How many people race"));
  check("participation: the trend has one point per sport and season on record, virtual weeks left out", (both[0].match(/<circle class="pt"/g) || []).length === perYear.size, perYear.size + " expected");
  check("participation: the trend keeps its line across seasons and has no season zoom above it", /<path /.test(both[0]) && page.indexOf('class="seasons"') > page.indexOf(both[0].slice(0, 40)) + both[0].length);
  check("participation: the night-by-night chart has a dot per in-person night and a season zoom", (both[1].match(/<circle class="pt"/g) || []).length === live.length && (page.match(/class="seasons"/g) || []).length === 1);
  const oneYear = live.find((r) => live.filter((x) => x.discipline === r.discipline && x.year === r.year).length >= 3);
  const nightsThatYear = live.filter((r) => r.discipline === oneYear.discipline && r.year === oneYear.year);
  const avg = Math.round(nightsThatYear.reduce((n, r) => n + D.results.filter((x) => x.raceid === r.raceid).length, 0) / nightsThatYear.length);
  check("participation: a point's tooltip gives the average and the number of nights it rests on", page.includes(oneYear.year + " · " + ({ MTB: "MTB", TR: "Trail run", CX: "Cyclocross" })[oneYear.discipline] + " · " + avg + " racers a night on average · " + nightsThatYear.length + " nights"));
  check("participation: the seasons table has a per-night column", />Per night</.test(page));
  clickYear(oneYear.year);
  const zoom = el("view").innerHTML.split('<svg class="chart"').slice(1).map((c) => c.split("</svg>")[0]);
  check("participation: zooming a season leaves the trend alone and joins that season's night dots", (zoom[0].match(/<circle class="pt"/g) || []).length === (both[0].match(/<circle class="pt"/g) || []).length && /<path /.test(zoom[1]));
  clickYear("all");
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
