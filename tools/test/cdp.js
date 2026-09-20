// A tiny Chrome DevTools Protocol driver for the touch tests: headless Chrome,
// phone emulation, real touch events, typing, screenshots. No dependencies.
//
// Needs Node 22+ (global WebSocket) and a local Chrome or Edge. Set CHROME_PATH
// to use a specific binary. It talks only to Chrome on 127.0.0.1 and opens only
// the URL it is given; the profile is a throwaway temp directory.
"use strict";
const { spawn, execSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function findChrome() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const env = process.env;
  const candidates = process.platform === "win32"
    ? [
        [env.PROGRAMFILES, "Google/Chrome/Application/chrome.exe"],
        [env["PROGRAMFILES(X86)"], "Google/Chrome/Application/chrome.exe"],
        [env.LOCALAPPDATA, "Google/Chrome/Application/chrome.exe"],
        [env["PROGRAMFILES(X86)"], "Microsoft/Edge/Application/msedge.exe"],
        [env.PROGRAMFILES, "Microsoft/Edge/Application/msedge.exe"],
      ].filter((c) => c[0]).map((c) => path.join(c[0], c[1]))
    : process.platform === "darwin"
      ? ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
         "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
      : ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"].map((n) => {
          try { return execSync(`command -v ${n}`, { stdio: ["ignore", "pipe", "ignore"] }).toString().trim(); } catch (e) { return null; }
        }).filter(Boolean);
  const found = candidates.find((p) => p && fs.existsSync(p));
  if (!found) throw new Error("No Chrome/Edge found. Install one or set CHROME_PATH.");
  return found;
}

async function launch(options = {}) {
  if (typeof WebSocket === "undefined") throw new Error("Node 22+ is required (global WebSocket).");
  const port = 9300 + Math.floor(Math.random() * 600);
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "catamount-chrome-"));
  const proc = spawn(findChrome(), [
    "--headless=new", `--remote-debugging-port=${port}`, "--remote-debugging-address=127.0.0.1",
    `--user-data-dir=${profile}`, "--no-first-run", "--no-default-browser-check", "--disable-gpu",
    "--hide-scrollbars", "about:blank",
  ], { stdio: "ignore" });

  let targets = [];
  for (let i = 0; i < 80; i++) {
    try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); if (targets.some((t) => t.type === "page")) break; } catch (e) { /* not up yet */ }
    await sleep(250);
  }
  const page = targets.find((t) => t.type === "page");
  if (!page) { proc.kill(); throw new Error("Chrome did not start."); }

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener("open", r));
  let nextId = 0;
  const pending = new Map();
  const consoleLog = [];
  ws.addEventListener("message", (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
    else if (m.method === "Runtime.consoleAPICalled") consoleLog.push(m.params.type + ": " + m.params.args.map((a) => (a.value !== undefined ? a.value : a.description)).join(" "));
    else if (m.method === "Runtime.exceptionThrown") consoleLog.push("EXCEPTION: " + ((m.params.exceptionDetails.exception && m.params.exceptionDetails.exception.description) || m.params.exceptionDetails.text));
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++nextId;
    pending.set(id, (m) => (m.error ? reject(new Error(method + ": " + m.error.message)) : resolve(m.result)));
    ws.send(JSON.stringify({ id, method, params }));
  });
  await send("Page.enable");
  await send("Runtime.enable");

  const b = {
    consoleLog, sleep, send,

    async phone(w = 390, h = 844) {
      await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 2, mobile: true });
      await send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 5 });
      await send("Emulation.setEmulatedMedia", { features: [{ name: "pointer", value: "coarse" }, { name: "hover", value: "none" }] }).catch(() => {});
    },
    async desktop(w = 1280, h = 900) {
      await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: false });
      await send("Emulation.setTouchEmulationEnabled", { enabled: false });
    },
    async go(url, settle = 1200) {
      await send("Page.navigate", { url });
      for (let i = 0; i < 60; i++) {
        await sleep(250);
        const ready = await b.eval("document.readyState === 'complete' && !!window.CATAMOUNT_DATA").catch(() => false);
        if (ready) break;
      }
      await sleep(settle);
    },
    async eval(expr) {
      const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
      if (r.exceptionDetails) throw new Error("eval: " + ((r.exceptionDetails.exception && r.exceptionDetails.exception.description) || r.exceptionDetails.text));
      return r.result.value;
    },
    async hash(h, wait = 700) { await b.eval(`location.hash = ${JSON.stringify(h)}`); await sleep(wait); },

    // Screenshots are only written when a directory is given (options.shotDir).
    async shot(name) {
      if (!options.shotDir) return null;
      fs.mkdirSync(options.shotDir, { recursive: true });
      const r = await send("Page.captureScreenshot", { format: "png" });
      const file = path.join(options.shotDir, name + ".png");
      fs.writeFileSync(file, Buffer.from(r.data, "base64"));
      return file;
    },

    rect(sel) {
      return b.eval(`(() => { const e = document.querySelector(${JSON.stringify(sel)}); if (!e) return null;
        e.scrollIntoView({ block: "center" }); const r = e.getBoundingClientRect();
        return { x: r.x + r.width / 2, y: r.y + r.height / 2, w: r.width, h: r.height }; })()`);
    },
    async tapAt(x, y) {
      await send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x, y }] });
      await sleep(60);
      await send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
      await sleep(350);
    },
    async tap(sel) {
      if (!(await b.rect(sel))) throw new Error("no element " + sel);
      await sleep(150);
      const r = await b.rect(sel);   // measured again after the scroll settles
      await b.tapAt(r.x, r.y);
      return r;
    },
    async swipe(x, y1, y2) {
      await send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x, y: y1 }] });
      for (let i = 1; i <= 8; i++) {
        await send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ x, y: y1 + ((y2 - y1) * i) / 8 }] });
        await sleep(16);
      }
      await send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
      await sleep(300);
    },
    type(text) { return send("Input.insertText", { text }); },

    async close() {
      try { ws.close(); } catch (e) { /* ignore */ }
      try {
        if (process.platform === "win32") execSync(`taskkill /pid ${proc.pid} /T /F`, { stdio: "ignore" });
        else proc.kill("SIGKILL");
      } catch (e) { /* ignore */ }
      await sleep(400);
      try { fs.rmSync(profile, { recursive: true, force: true }); } catch (e) { /* a locked temp dir is harmless */ }
    },
  };
  return b;
}

module.exports = { launch, sleep };
