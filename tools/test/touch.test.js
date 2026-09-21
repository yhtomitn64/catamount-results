// Touch tests: drives real headless Chrome as a phone (390x844, coarse pointer, real
// touch events) and taps, types and swipes through the site.
//
//     node tools/test/touch.test.js                         # the local index.html
//     node tools/test/touch.test.js https://example.org/    # a deployed copy
//     node tools/test/touch.test.js --shots /tmp/shots      # also save screenshots
//
// Needs Node 22+ and a local Chrome or Edge (set CHROME_PATH to pick one).
// Test subjects come from the data, so no test names a real person.
"use strict";
const path = require("path");
const { pathToFileURL } = require("url");
const { launch } = require("./cdp.js");
const { ROOT, readBundle, fixtures, prefixQuery } = require("./fixtures.js");

const args = process.argv.slice(2);
const shotIdx = args.indexOf("--shots");
const shotDir = shotIdx >= 0 ? args.splice(shotIdx, 2)[1] : null;
const target = args[0] || pathToFileURL(path.join(ROOT, "index.html")).href;
const base = target.replace(/#.*$/, "");

const bundle = readBundle();
const fx = fixtures(bundle);
const topName = bundle.racers[fx.top], partnerName = bundle.racers[fx.partner];
const races = bundle.races;
const cxCount = races.filter((r) => r.discipline === "CX").length;
const yearRacers = {};
bundle.results.forEach((r) => { (yearRacers[fx.raceById[r.raceid].year] = yearRacers[fx.raceById[r.raceid].year] || new Set()).add(r.racer); });
const bigYear = Object.keys(yearRacers).find((y) => yearRacers[y].size > 200);

let failures = 0, total = 0;
const check = (name, ok, detail) => {
  total++;
  if (!ok) failures++;
  console.log((ok ? "PASS " : "FAIL ") + name + (detail !== undefined ? "  -> " + detail : ""));
};

(async () => {
  const b = await launch({ shotDir });
  try {
    await b.phone(390, 844);

    // ---- nothing grabs focus on load ------------------------------------------------------
    await b.go(base + "#/racer");
    check("emulation is a real touch phone", await b.eval("matchMedia('(pointer: coarse)').matches && 'ontouchstart' in window"));
    check("home: no field is focused on load (the keyboard stays down)", (await b.eval("document.activeElement.tagName")) === "BODY");
    await b.hash("#/h2h");
    check("head to head: no box is focused on load", (await b.eval("document.activeElement.tagName")) === "BODY");

    // ---- layout facts ---------------------------------------------------------------------------
    const f = await b.eval(`(() => { const nav = document.getElementById("nav"); const btn = document.querySelector(".filter button");
      const input = document.getElementById("h2h-a");
      return { navOverflow: nav.scrollWidth - nav.clientWidth, filterH: Math.round(btn.getBoundingClientRect().height),
               inputFont: getComputedStyle(input).fontSize, overflowX: document.documentElement.scrollWidth - innerWidth }; })()`);
    // The tab row is wider than a phone, so it scrolls sideways; what must hold is that the page does not,
    // and that the current tab is in view. Counted off the row itself, so adding a tab does not fail here.
    await b.hash("#/power");
    const nv = await b.eval(`(() => { const nav = document.getElementById("nav"), on = nav.querySelector("a.on"), r = on.getBoundingClientRect(), n = nav.getBoundingClientRect();
      return { tabs: [...nav.querySelectorAll("a")].map((a) => a.getAttribute("href")), inView: r.left >= n.left - 1 && r.right <= n.right + 1, page: document.documentElement.scrollWidth - innerWidth }; })()`);
    check("the nav tabs are distinct routes, the current one is scrolled into view and the page does not scroll sideways",
      nv.tabs.length >= 6 && new Set(nv.tabs).size === nv.tabs.length && nv.tabs.includes("#/power") && nv.tabs.includes("#/best") &&
      nv.inView && nv.page <= 0, JSON.stringify(nv));
    await b.hash("#/h2h");
    check("filter buttons are at least 44px tall", f.filterH >= 44, f.filterH + "px");
    check("inputs are 16px, so iOS does not zoom in on focus", f.inputFont === "16px", f.inputFont);
    check("no sideways page scroll", f.overflowX <= 0, f.overflowX);

    // ---- type-to-search with real taps -------------------------------------------------------------
    await b.tap("#h2h-a");
    check("tapping a box focuses it", (await b.eval("document.activeElement.id")) === "h2h-a");
    await b.type(prefixQuery(topName));
    await b.sleep(500);
    const opts = await b.eval("[...document.querySelectorAll('#h2h-a-list li')].map(li => li.textContent)");
    check("typing shows matches, the right person first", opts.length > 0 && opts[0].startsWith(topName), opts.length + " matches");
    const liH = await b.eval("Math.round(document.querySelector('#h2h-a-list li').getBoundingClientRect().height)");
    check("suggestions are at least 44px tall", liH >= 44, liH + "px");
    await b.shot("picker-open");
    await b.tap(`#h2h-a-list li[data-key="${fx.top}"]`);
    await b.sleep(400);
    check("tapping a suggestion selects it", (await b.eval("document.getElementById('h2h-a').value")) === topName && (await b.eval("location.hash")).includes(fx.top), await b.eval("location.hash"));
    await b.tap("#h2h-b");
    await b.type(prefixQuery(partnerName));
    await b.sleep(500);
    await b.tap(`#h2h-b-list li[data-key="${fx.partner}"]`);
    await b.sleep(600);
    check("the second pick loads the comparison", (await b.eval("document.getElementById('view').innerText")).includes(topName + " vs " + partnerName), await b.eval("location.hash"));
    await b.shot("h2h-result");

    // ---- filter ------------------------------------------------------------------------------------------
    await b.hash("#/races");
    await b.tap(".filter button[data-filter='CX']");
    check("tapping Cyclocross filters the races list", new RegExp(cxCount + " races \\(Cyclocross\\)").test(await b.eval("document.getElementById('view').innerText")));
    await b.tap(".filter button[data-filter='all']");

    // ---- charts ---------------------------------------------------------------------------------------------
    await b.hash("#/racer/" + fx.top);
    const label = await b.eval(`(() => { const t = document.querySelector("svg.chart text"), svg = t.ownerSVGElement;
      const scale = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
      return { scale: +scale.toFixed(2), fontPx: +(parseFloat(getComputedStyle(t).fontSize) * scale).toFixed(1), viewBoxW: svg.viewBox.baseVal.width }; })()`);
    check("the chart is drawn at its shown width, so labels are not shrunk", label.scale >= 0.95 && label.scale <= 1.05, JSON.stringify(label));

    // ---- Seasons page: the participation charts fit a phone ------------------------------------------------------
    await b.hash("#/series");
    check("the Seasons page has no sideways scroll on a phone", (await b.eval("document.documentElement.scrollWidth - innerWidth")) <= 0);
    await b.eval("document.querySelector('svg.chart').scrollIntoView()");
    await b.shot("participation");
    await b.hash("#/power");
    check("the Rankings page has no sideways scroll on a phone", (await b.eval("document.documentElement.scrollWidth - innerWidth")) <= 0);
    // The method note is a real fold-out, so open it as a finger would and check it fits.
    const sum = await b.eval(`(() => { const s = document.querySelector("details.method > summary");
      return { h: Math.round(s.getBoundingClientRect().height), open: !!s.parentNode.open }; })()`);
    check("the method note offers a finger-sized way in, shut to start with", sum.h >= 44 && !sum.open, JSON.stringify(sum));
    await b.tap("details.method > summary");
    const opened = await b.eval(`(() => { const d = document.querySelector("details.method");
      return { open: !!d.open, headings: d.querySelectorAll("h4").length, odds: d.querySelectorAll(".odds li").length,
               overflowX: document.documentElement.scrollWidth - innerWidth,
               wide: Math.max(0, ...[...d.querySelectorAll("*")].map((e) => Math.round(e.getBoundingClientRect().right - innerWidth))) }; })()`);
    check("tapping it opens the whole explanation without pushing the page sideways",
      opened.open && opened.headings >= 8 && opened.odds >= 4 && opened.overflowX <= 0 && opened.wide <= 0, JSON.stringify(opened));
    await b.shot("rankings-method");
    await b.shot("rankings");

    // ---- Best of: the seasons are fitted on a timer, so the page has to paint first and fill in ----------------------
    // Only a real browser runs that loop; a stubbed DOM would just see the finished table.
    await b.hash("#/best");
    const painted = await b.eval(`(() => ({ rows: document.querySelectorAll("tbody tr").length,
      fitting: /Fitting \\d+ of \\d+ seasons/.test(document.body.textContent) }))()`);
    check("the Best of page paints its seasons before they are fitted", painted.rows > 0 && painted.fitting, JSON.stringify(painted));
    let filled = null;
    for (let i = 0; i < 40; i++) {                 // a few seconds of arithmetic, a season per tick
      await b.sleep(250);
      filled = await b.eval(`(() => ({ fitting: /Fitting \\d+ of \\d+ seasons/.test(document.body.textContent),
        podiums: [...document.querySelectorAll("tbody tr")].filter((r) => /#\\/racer\\//.test(r.innerHTML)).length,
        overflowX: document.documentElement.scrollWidth - innerWidth }))()`);
      if (!filled.fitting) break;
    }
    check("it fills itself in and stops saying it is working", filled && !filled.fitting && filled.podiums > 0, JSON.stringify(filled));
    check("the Best of page has no sideways scroll on a phone", filled && filled.overflowX <= 0, JSON.stringify(filled));
    await b.shot("best-of");
    await b.hash("#/racer/" + fx.top);

    // ---- season zoom: a phone-sized tap target, zooms to one season, and All years brings it back ----------------
    const yr = await b.eval(`(() => { const bs = [...document.querySelectorAll(".seasons button[data-year]:not([data-year='all'])")];
      const last = bs[bs.length - 1];
      return { n: bs.length, year: last && last.dataset.year, h: last ? Math.round(last.getBoundingClientRect().height) : 0,
               overflowX: document.documentElement.scrollWidth - innerWidth }; })()`);
    check("the season buttons are at least 40px tall and do not push the page sideways", yr.n > 1 && yr.h >= 40 && yr.overflowX <= 0, JSON.stringify(yr));
    await b.tap(".seasons button[data-year='" + yr.year + "']");
    const z = await b.eval(`(() => ({ pressed: document.querySelector(".seasons button.on").dataset.year,
      labels: [...document.querySelector("svg.chart").querySelectorAll("text[text-anchor=middle]")].map((t) => t.textContent) }))()`);
    check("tapping a season zooms the chart to its months", z.pressed === yr.year && z.labels.length > 1 && z.labels.every((t) => /^[A-Z][a-z]{2}$/.test(t)), JSON.stringify(z));
    await b.shot("season-zoom");
    await b.tap(".seasons button[data-year='all']");
    check("tapping All years restores the whole axis", (await b.eval("document.querySelector('.seasons button.on').dataset.year")) === "all" && /^\d{4}$/.test(await b.eval("document.querySelector('svg.chart text[text-anchor=middle]').textContent")));
    check("chart axis labels are at least 9px on screen", label.fontPx >= 9, label.fontPx + "px");
    const dot = await b.rect("svg.chart circle.pt");
    check("a chart dot is tiny on a phone, which is why a tap takes the nearest dot", dot && dot.w < 12, dot && dot.w.toFixed(1) + "px wide");
    await b.tapAt(dot.x + 9, dot.y + 7);   // a fingertip away from the dot's centre, not on it
    const readout = await b.eval("document.querySelector('.chart-readout').textContent");
    check("tapping near a dot shows its race in the readout", !!readout && !/^Tap a point/.test(readout), readout);
    const empty = await b.eval(`(() => { const svg = document.querySelector("svg.chart"), r = svg.getBoundingClientRect();
      const dots = [...svg.querySelectorAll("circle.pt")].map((c) => { const q = c.getBoundingClientRect(); return [q.x + q.width / 2, q.y + q.height / 2]; });
      for (let y = r.top + 8; y < r.bottom - 8; y += 6) for (let x = r.left + 60; x < r.right - 8; x += 6) {
        if (y < 0 || y > innerHeight) continue;
        if (dots.every((d) => Math.hypot(d[0] - x, d[1] - y) > 40)) return { x, y }; }
      return null; })()`);
    if (empty) {
      await b.eval("document.querySelector('.chart-readout').textContent = 'UNCHANGED'");
      await b.tapAt(empty.x, empty.y);
      check("tapping empty chart space leaves the readout alone", (await b.eval("document.querySelector('.chart-readout').textContent")) === "UNCHANGED");
    }
    await b.shot("chart-tap");
    const wPortrait = await b.eval("document.querySelector('svg.chart').viewBox.baseVal.width");
    await b.phone(844, 390);
    await b.sleep(900);
    const wLandscape = await b.eval("document.querySelector('svg.chart').viewBox.baseVal.width");
    check("rotating to landscape redraws the chart wider", wLandscape > wPortrait, wPortrait + " -> " + wLandscape);
    await b.phone(390, 844);
    await b.sleep(900);

    // ---- long tables, scrolling ------------------------------------------------------------------------------------
    if (bigYear) {
      await b.hash("#/series/" + bigYear);
      const shown = await b.eval("[...document.querySelectorAll('#view table')].map(t => t.querySelectorAll('tbody tr').length).sort((a, b) => b - a)[0]");
      check("a very long table starts at 60 rows on a phone", shown === 60, shown + " rows");
      check("it offers Show all", await b.eval("!!document.querySelector('button[data-more]')"));
      await b.tap("button[data-more]");
      const all = await b.eval("[...document.querySelectorAll('#view table')].map(t => t.querySelectorAll('tbody tr').length).sort((a, b) => b - a)[0]");
      check("tapping Show all reveals every row", all > shown, shown + " -> " + all);
      await b.hash("#/series/" + bigYear);
      await b.eval("window.scrollTo(0, 0)");
      await b.sleep(200);
      const y0 = await b.eval("scrollY");
      await b.swipe(200, 700, 250);
      const y1 = await b.eval("scrollY");
      check("swiping over a table scrolls the page", y1 > y0, y0 + " -> " + y1);
      check("no table is a vertical scroll box on a phone", (await b.eval("[...document.querySelectorAll('.scroll')].filter(e => e.scrollHeight > e.clientHeight + 4).length")) === 0);
    }

    check("no console errors or exceptions", b.consoleLog.filter((l) => /^(error|EXCEPTION)/.test(l)).length === 0, b.consoleLog.slice(0, 3).join(" | "));
  } finally {
    await b.close();
  }
  console.log(failures ? "\n" + failures + " of " + total + " checks FAILED" : "\nAll " + total + " checks passed");
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error("FAILED: " + e.message); process.exit(1); });
