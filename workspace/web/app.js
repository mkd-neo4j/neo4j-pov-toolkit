/**
 * Time-Slice demo — pure-JS NVL + neo4j-driver, no framework, no build step.
 *
 * Loads the scan CSVs, wires the day buttons to call ingest_template.cypher,
 * and drives the NVL canvas from snapshot.cypher on every slider input.
 */

const LOG = (...args) => console.log("[timeslice]", ...args);

LOG("module start — importing neo4j-driver, NVL, interaction-handlers");

// neo4j-driver: use the pre-bundled browser ESM (no Node deps).
import neo4j from "https://unpkg.com/neo4j-driver@5/lib/browser/neo4j-web.esm.js";
import NVL from "https://esm.sh/@neo4j-nvl/base@0.3";
import {
  ZoomInteraction,
  PanInteraction,
  DragNodeInteraction,
  HoverInteraction,
} from "https://esm.sh/@neo4j-nvl/interaction-handlers@0.3";

LOG("imports resolved", {
  neo4jVersion: neo4j.driver ? "driver export present" : "DRIVER EXPORT MISSING",
  NVL: typeof NVL,
  NVLname: NVL?.name,
});

// ─── Config ──────────────────────────────────────────────────────────────────

const CONFIG = {
  uri: "neo4j://localhost:7687",
  user: "neo4j",
  database: "timeslice",
  windowStart: Date.UTC(2026, 3, 20, 9, 0, 0),  // Mon 2026-04-20 09:00 UTC
  windowEnd:   Date.UTC(2026, 3, 24, 9, 0, 0),  // Fri 2026-04-24 09:00 UTC
};

// Tracks the most recent run_time that has been ingested. The slider's
// reachable range is clamped to this — you can't time-travel into a future
// for which no scan has happened yet.
const state = {
  latestIngestedMs: null,   // number | null
};

// ─── DOM helpers ─────────────────────────────────────────────────────────────

const $ = (sel) => document.querySelector(sel);

const connStatus = $("#connection-status");
const connUri = $("#connection-uri");
const sliderEl = $("#time-slider");
const sliderReadout = $("#slider-readout");
const statsEl = $("#snapshot-stats");
const canvas = $("#nvl-canvas");
const toastEl = $("#toast");
const queryCypherEl = $("#query-cypher-snapshot");
const queryCurrentCallEl = $("#query-current-call");

connUri.textContent = `${CONFIG.uri} · ${CONFIG.database}`;

function showToast(msg, level = "info", ms = 3000) {
  toastEl.textContent = msg;
  toastEl.dataset.level = level;
  toastEl.hidden = false;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => { toastEl.hidden = true; }, ms);
}

function setConnState(state, detail) {
  connStatus.textContent = detail;
  connStatus.dataset.state = state;
}

// ─── Credentials ─────────────────────────────────────────────────────────────

function getPassword() {
  let pw = sessionStorage.getItem("timeslice.password");
  if (pw === null) {
    pw = prompt(`Neo4j password for user "${CONFIG.user}" on ${CONFIG.uri}:`);
    if (pw === null) throw new Error("Password required to connect.");
    sessionStorage.setItem("timeslice.password", pw);
  }
  return pw;
}

// ─── Driver ──────────────────────────────────────────────────────────────────

let driver;

async function connect() {
  setConnState("connecting", "connecting…");
  console.log("[timeslice] creating driver for", CONFIG.uri);
  const pw = getPassword();
  try {
    driver = neo4j.driver(CONFIG.uri, neo4j.auth.basic(CONFIG.user, pw));
  } catch (err) {
    setConnState("error", `driver init failed: ${err.message}`);
    throw err;
  }
  try {
    await driver.verifyConnectivity({ database: CONFIG.database });
    setConnState("ok", "connected");
    console.log("[timeslice] connected to", CONFIG.database);
  } catch (err) {
    sessionStorage.removeItem("timeslice.password");
    setConnState("error", `connection failed: ${err.message}`);
    throw err;
  }
}

async function runRead(cypher, params = {}) {
  const session = driver.session({ database: CONFIG.database, defaultAccessMode: neo4j.session.READ });
  try {
    return await session.run(cypher, params);
  } finally {
    await session.close();
  }
}

async function runWrite(cypher, params = {}) {
  const session = driver.session({ database: CONFIG.database, defaultAccessMode: neo4j.session.WRITE });
  try {
    return await session.run(cypher, params);
  } finally {
    await session.close();
  }
}

async function runMultiWrite(cypherText) {
  // Split on ; outside of strings/comments (same spec as harness.py).
  const stmts = splitStatements(cypherText);
  for (const s of stmts) {
    await runWrite(s);
  }
}

// ─── Cypher + CSV loading ────────────────────────────────────────────────────

const ASSETS = {};

async function loadAssets() {
  const [setupC, templateC, snapshotC, serversCsv, relsCsv] = await Promise.all([
    fetch("../cypher/setup.cypher").then((r) => r.text()),
    fetch("../cypher/ingest_template.cypher").then((r) => r.text()),
    fetch("../cypher/snapshot.cypher").then((r) => r.text()),
    fetch("../data/scans_servers.csv").then((r) => r.text()),
    fetch("../data/scans_relationships.csv").then((r) => r.text()),
  ]);
  ASSETS.setup = setupC;
  ASSETS.ingestTemplate = templateC;
  ASSETS.snapshot = snapshotC;
  ASSETS.observationsByRun = parseObservations(serversCsv, relsCsv);
}

function parseCsv(text) {
  const [header, ...lines] = text.trim().split(/\r?\n/);
  const cols = header.split(",");
  return lines.filter(Boolean).map((line) => {
    const values = line.split(",");
    const row = {};
    cols.forEach((c, i) => { row[c.trim()] = values[i]?.trim() ?? ""; });
    return row;
  });
}

function parseObservations(serversCsv, relsCsv) {
  const byRun = new Map();
  for (const row of parseCsv(serversCsv)) {
    const rt = row.run_time;
    if (!byRun.has(rt)) byRun.set(rt, { servers: [], relationships: [] });
    byRun.get(rt).servers.push({ id: row.id, name: row.name });
  }
  for (const row of parseCsv(relsCsv)) {
    const rt = row.run_time;
    if (!byRun.has(rt)) byRun.set(rt, { servers: [], relationships: [] });
    byRun.get(rt).relationships.push({ from_id: row.from_id, to_id: row.to_id });
  }
  return byRun;
}

// ─── Statement splitter (mirrors harness.py) ─────────────────────────────────

function splitStatements(cypher) {
  const out = [];
  let buf = "";
  let i = 0;
  let inStr = null, inLineC = false, inBlockC = false;
  while (i < cypher.length) {
    const ch = cypher[i];
    const nx = cypher[i + 1] ?? "";
    if (inLineC) {
      buf += ch;
      if (ch === "\n") inLineC = false;
      i++; continue;
    }
    if (inBlockC) {
      buf += ch;
      if (ch === "*" && nx === "/") { buf += nx; i += 2; inBlockC = false; continue; }
      i++; continue;
    }
    if (inStr) {
      buf += ch;
      if (ch === inStr) inStr = null;
      i++; continue;
    }
    if (ch === "/" && nx === "/") { inLineC = true; buf += ch + nx; i += 2; continue; }
    if (ch === "/" && nx === "*") { inBlockC = true; buf += ch + nx; i += 2; continue; }
    if (ch === "'" || ch === '"') { inStr = ch; buf += ch; i++; continue; }
    if (ch === ";") {
      const s = buf.trim();
      if (hasCypher(s)) out.push(s);
      buf = ""; i++; continue;
    }
    buf += ch; i++;
  }
  const tail = buf.trim();
  if (hasCypher(tail)) out.push(tail);
  return out;
}
function hasCypher(s) {
  let i = 0, inLineC = false, inBlockC = false;
  while (i < s.length) {
    const ch = s[i]; const nx = s[i + 1] ?? "";
    if (inLineC) { if (ch === "\n") inLineC = false; i++; continue; }
    if (inBlockC) { if (ch === "*" && nx === "/") { i += 2; inBlockC = false; continue; } i++; continue; }
    if (ch === "/" && nx === "/") { inLineC = true; i += 2; continue; }
    if (ch === "/" && nx === "*") { inBlockC = true; i += 2; continue; }
    if (!/\s/.test(ch)) return true;
    i++;
  }
  return false;
}

// ─── DB ops ──────────────────────────────────────────────────────────────────

async function setupSchema() {
  // setup.cypher uses IF NOT EXISTS throughout so this is idempotent.
  await runMultiWrite(ASSETS.setup);
}

async function restoreStateFromDb() {
  // Every scan touches at least one ServerState field — either valid_from
  // (opened), last_seen_alive (extended), or valid_to (closed). Unioning all
  // three captures every run that ever fired, including "absent-only" runs
  // like our Thursday (which only closes B's state).
  const res = await runRead(`
    MATCH (st:ServerState)
    UNWIND [st.valid_from, st.last_seen_alive, st.valid_to] AS t
    WITH DISTINCT t WHERE t IS NOT NULL
    RETURN collect(t) AS run_times
  `);
  const runTimes = (res.records[0]?.get("run_times") ?? [])
    .map((dt) => {
      const d = typeof dt.toStandardDate === "function" ? dt.toStandardDate() : new Date(dt);
      return d.getTime();
    });
  if (!runTimes.length) return;

  const observedSet = new Set(runTimes);
  for (const btn of document.querySelectorAll(".day-btn")) {
    const ms = new Date(btn.dataset.at).getTime();
    if (observedSet.has(ms)) {
      btn.dataset.state = "ingested";
    }
  }
  state.latestIngestedMs = Math.max(...runTimes);
  LOG("restoreStateFromDb: runs observed =", runTimes.map((ms) => new Date(ms).toISOString()));
  LOG("restoreStateFromDb: latest ingested =", new Date(state.latestIngestedMs).toISOString());
}

async function wipeDb() {
  await runWrite("MATCH (n) DETACH DELETE n");
}

async function ingestDay(runTimeIso) {
  const obs = ASSETS.observationsByRun.get(runTimeIso) ?? { servers: [], relationships: [] };
  const runTime = neo4j.types.DateTime.fromStandardDate(new Date(runTimeIso));
  return runWrite(ASSETS.ingestTemplate, {
    run_time: runTime,
    servers: obs.servers,
    relationships: obs.relationships,
    offline_threshold: "PT0S",
  });
}

async function snapshotAt(atDate) {
  const at = neo4j.types.DateTime.fromStandardDate(atDate);
  const res = await runRead(ASSETS.snapshot, { at });
  const rec = res.records[0];
  const nodes = (rec?.get("nodes") ?? []).map((n) => ({
    id: n.id,
    name: n.name,
  }));
  const rels = (rec?.get("rels") ?? []).map((r) => ({
    from_id: r.from_id,
    to_id: r.to_id,
  }));
  return { nodes, rels };
}

// ─── NVL rendering ───────────────────────────────────────────────────────────

let nvl;
let nvlReady = false;
let nvlReadyPromise;

const GRAPH_NODE_COLOR = "#56c7e4";    // --neo4j-graph-4 (Baltic-adjacent cyan)
const REL_COLOR        = "#0a6190";    // --neo4j-primary-bg-strong (Baltic-50)
const NODE_BORDER      = "#ffffff";

function describeContainer(el) {
  const r = el.getBoundingClientRect();
  return {
    width: r.width,
    height: r.height,
    childCount: el.childElementCount,
    children: [...el.children].map((c) => `${c.tagName.toLowerCase()}${c.id ? "#" + c.id : ""}${c.className ? "." + String(c.className).split(/\s+/).join(".") : ""}`),
    clientSize: `${el.clientWidth}x${el.clientHeight}`,
  };
}

function initNvl() {
  LOG("initNvl — container pre-construct:", describeContainer(canvas));

  nvlReadyPromise = new Promise((resolve) => {
    let resolved = false;
    const resolveOnce = (src) => {
      if (resolved) return;
      resolved = true;
      nvlReady = true;
      LOG(`NVL ready (via ${src})`, describeContainer(canvas));
      resolve();
    };

    try {
      nvl = new NVL(
        canvas,
        [],
        [],
        {
          initialZoom: 0.9,
          renderer: "canvas",
          disableWebWorkers: true,    // CDN-hosted workers fail CORS; sync layout is fine for small graphs.
          disableTelemetry: true,
          layout: "forceDirected",
          layoutOptions: { enableCytoscape: false, enableVerlet: true },
          styling: {
            defaultNodeColor: GRAPH_NODE_COLOR,
            defaultRelationshipColor: REL_COLOR,
            nodeDefaultBorderColor: NODE_BORDER,
          },
          callbacks: {
            onInitialization: () => resolveOnce("onInitialization"),
            onLayoutComputing: (isComputing) => LOG("NVL onLayoutComputing:", isComputing),
            onLayoutDone: () => LOG("NVL onLayoutDone — nodes=", nvl?.getNodes().length, "rels=", nvl?.getRelationships().length),
            onError: (err) => {
              console.error("[timeslice] NVL onError:", err);
              showToast(`NVL error: ${err?.message || err}`, "error");
            },
            onWebGLContextLost: (e) => LOG("NVL webgl context lost:", e),
          },
        }
      );
      LOG("NVL constructed. post-construct container:", describeContainer(canvas));
    } catch (err) {
      console.error("[timeslice] NVL constructor threw:", err);
      showToast(`NVL constructor failed: ${err.message}`, "error", 10000);
      resolveOnce("constructor-threw");
      return;
    }

    // Fallback resolver in case onInitialization doesn't fire in this version.
    setTimeout(() => resolveOnce("timeout-fallback"), 300);
  });

  try { new ZoomInteraction(nvl); LOG("ZoomInteraction attached"); } catch (e) { console.error("ZoomInteraction failed", e); }
  try { new PanInteraction(nvl);  LOG("PanInteraction attached"); }  catch (e) { console.error("PanInteraction failed", e); }
  try { new DragNodeInteraction(nvl); LOG("DragNodeInteraction attached"); } catch (e) { console.error("DragNodeInteraction failed", e); }
  try { new HoverInteraction(nvl); LOG("HoverInteraction attached"); } catch (e) { console.error("HoverInteraction failed", e); }
}

async function renderSnapshot({ nodes, rels }) {
  LOG("renderSnapshot called:", nodes.length, "nodes /", rels.length, "rels", { nodes, rels });
  LOG("renderSnapshot — waiting for NVL ready…");
  await nvlReadyPromise;
  LOG("renderSnapshot — NVL ready. current container:", describeContainer(canvas));

  const nodePayload = nodes.map((n) => ({
    id: `srv:${n.id}`,
    caption: n.id,
    captionAlign: "center",
    size: 50,
    color: GRAPH_NODE_COLOR,
  }));
  const relPayload = rels.map((r) => ({
    id: `rel:${r.from_id}->${r.to_id}`,
    from: `srv:${r.from_id}`,
    to: `srv:${r.to_id}`,
    caption: "CONNECTED_TO",
    captionSize: 0.7,
    color: REL_COLOR,
    width: 2,
  }));

  LOG("renderSnapshot — current NVL state:", {
    nodes: nvl.getNodes().map((n) => n.id),
    rels: nvl.getRelationships().map((r) => r.id),
  });

  // Diff against current graph: remove what's gone, add/update what's new.
  const currentNodeIds = new Set(nvl.getNodes().map((n) => n.id));
  const currentRelIds = new Set(nvl.getRelationships().map((r) => r.id));
  const nextNodeIds = new Set(nodePayload.map((n) => n.id));
  const nextRelIds = new Set(relPayload.map((r) => r.id));

  const removeRels = [...currentRelIds].filter((id) => !nextRelIds.has(id));
  const removeNodes = [...currentNodeIds].filter((id) => !nextNodeIds.has(id));
  if (removeRels.length) {
    LOG("removing rels:", removeRels);
    nvl.removeRelationshipsWithIds(removeRels);
  }
  if (removeNodes.length) {
    LOG("removing nodes:", removeNodes);
    nvl.removeNodesWithIds(removeNodes);
  }

  if (nodePayload.length || relPayload.length) {
    LOG("adding/updating:", { nodes: nodePayload, rels: relPayload });
    try {
      nvl.addAndUpdateElementsInGraph(nodePayload, relPayload);
    } catch (err) {
      console.error("[timeslice] addAndUpdateElementsInGraph failed:", err);
      showToast(`NVL render failed: ${err.message}`, "error", 5000);
    }
    LOG("post-add NVL state:", {
      nodes: nvl.getNodes().map((n) => n.id),
      rels: nvl.getRelationships().map((r) => r.id),
      container: describeContainer(canvas),
    });

    // Center the camera on the current set after a tick so layout has placed nodes.
    setTimeout(() => {
      try {
        nvl.fit(nodePayload.map((n) => n.id), { animated: true });
        LOG("nvl.fit called. scale=", nvl.getScale(), "pan=", nvl.getPan());
      } catch (err) {
        console.warn("[timeslice] nvl.fit failed:", err);
      }
    }, 120);
  }

  canvas.dataset.empty = nodes.length === 0 ? "true" : "false";
  statsEl.textContent = `${nodes.length} node${nodes.length === 1 ? "" : "s"} · ${rels.length} relationship${rels.length === 1 ? "" : "s"}`;
}

// ─── Slider ──────────────────────────────────────────────────────────────────

function sliderToDate(value) {
  const t = Number(value) / 1000;
  const ms = CONFIG.windowStart + t * (CONFIG.windowEnd - CONFIG.windowStart);
  return new Date(ms);
}

function dateToSliderValue(date) {
  const ms = date instanceof Date ? date.getTime() : date;
  const span = CONFIG.windowEnd - CONFIG.windowStart;
  return Math.round(((ms - CONFIG.windowStart) / span) * 1000);
}

function formatAt(date) {
  const day = date.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });
  const time = date.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit", timeZone: "UTC" });
  return `${day} · ${time} UTC`;
}

// ─── Cypher tokenizer (for the query inspector) ──────────────────────────────

const CYPHER_KEYWORDS = new Set([
  "CALL", "MATCH", "WHERE", "RETURN", "WITH", "UNWIND", "OPTIONAL",
  "AND", "OR", "NOT", "IS", "NULL", "IN", "AS", "DISTINCT", "ORDER", "BY",
  "LIMIT", "SKIP", "MERGE", "CREATE", "SET", "DELETE", "DETACH", "REMOVE",
  "FOREACH", "CASE", "WHEN", "THEN", "ELSE", "END", "TRUE", "FALSE",
  "NONE", "ANY", "ALL", "EXISTS", "ON", "USING", "INDEX", "CONSTRAINT",
  "REQUIRE", "UNIQUE", "IF", "FOR", "OF", "CONTAINS", "STARTS", "ENDS",
]);
const CYPHER_FUNCS = new Set([
  "duration", "count", "collect", "sum", "max", "min", "avg",
  "datetime", "date", "time", "localdatetime", "localtime",
  "elementid", "id", "labels", "type", "keys", "properties",
  "size", "coalesce", "timestamp", "tostring", "tointeger", "tofloat",
]);

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function highlightCypher(code) {
  // One token at a time. Order matters: comments & strings first (they
  // can swallow other syntax), then params/labels/properties, then words.
  const re = /(\/\*[\s\S]*?\*\/|\/\/[^\n]*)|('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")|(\$\w+)|(:\w+)|(\.\w+)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_]\w*)/g;
  let out = "";
  let last = 0;
  let m;
  while ((m = re.exec(code)) !== null) {
    out += escapeHtml(code.slice(last, m.index));
    const [full, comment, str, param, label, prop, num, word] = m;
    if (comment) {
      out += `<span class="tok-comment">${escapeHtml(comment)}</span>`;
    } else if (str) {
      out += `<span class="tok-string">${escapeHtml(str)}</span>`;
    } else if (param) {
      out += `<span class="tok-param">${escapeHtml(param)}</span>`;
    } else if (label) {
      out += `<span class="tok-label">${escapeHtml(label)}</span>`;
    } else if (prop) {
      out += `<span class="tok-property">${escapeHtml(prop)}</span>`;
    } else if (num) {
      out += `<span class="tok-number">${escapeHtml(num)}</span>`;
    } else if (word) {
      const up = word.toUpperCase();
      if (CYPHER_KEYWORDS.has(up)) {
        out += `<span class="tok-keyword">${escapeHtml(word)}</span>`;
      } else if (CYPHER_FUNCS.has(word.toLowerCase())) {
        out += `<span class="tok-function">${escapeHtml(word)}</span>`;
      } else {
        out += escapeHtml(word);
      }
    }
    last = m.index + full.length;
  }
  out += escapeHtml(code.slice(last));
  return out;
}

function populateQueryInspector() {
  if (queryCypherEl && ASSETS.snapshot) {
    queryCypherEl.innerHTML = highlightCypher(ASSETS.snapshot);
  }
}

function updateCurrentCallReadout(at) {
  if (!queryCurrentCallEl) return;
  if (at === null) {
    queryCurrentCallEl.innerHTML = `snapshot.cypher &middot; <span class="tok-param">$at</span> = —`;
    return;
  }
  const iso = at instanceof Date ? at.toISOString() : new Date(at).toISOString();
  queryCurrentCallEl.innerHTML =
    `snapshot.cypher &middot; <span class="tok-param">$at</span> = ` +
    `<span class="tok-string">datetime('${escapeHtml(iso)}')</span>`;
}

// ─── Slider bounds ───────────────────────────────────────────────────────────

function maxAllowedSliderValue() {
  if (state.latestIngestedMs === null) return 0;
  return dateToSliderValue(state.latestIngestedMs);
}

function applySliderBounds() {
  const maxVal = maxAllowedSliderValue();
  const pct = (maxVal / 1000) * 100;
  sliderEl.style.setProperty("--available-pct", `${pct}%`);

  if (state.latestIngestedMs === null) {
    sliderEl.disabled = true;
    sliderEl.value = 0;
    sliderReadout.textContent = "Ingest a day to enable time travel →";
    return;
  }
  sliderEl.disabled = false;
  if (Number(sliderEl.value) > maxVal) sliderEl.value = maxVal;
}

async function onSliderInput(rawValue) {
  const maxVal = maxAllowedSliderValue();
  const clamped = Math.min(Number(rawValue), maxVal);
  if (clamped !== Number(sliderEl.value)) sliderEl.value = clamped;

  if (state.latestIngestedMs === null) {
    sliderReadout.textContent = "Ingest a day to enable time travel →";
    updateCurrentCallReadout(null);
    return;
  }

  const at = sliderToDate(clamped);
  sliderReadout.textContent = formatAt(at);
  updateCurrentCallReadout(at);
  try {
    const snap = await snapshotAt(at);
    renderSnapshot(snap);
  } catch (err) {
    console.error(err);
    showToast(`Snapshot error: ${err.message}`, "error", 5000);
  }
}

// Debounce slider while dragging to avoid swamping the DB.
let sliderPending = null;
function scheduleSliderRefresh(value) {
  clearTimeout(sliderPending);
  sliderPending = setTimeout(() => onSliderInput(value), 40);
}

// ─── Day buttons ─────────────────────────────────────────────────────────────

async function onDayClick(btn) {
  if (btn.dataset.state === "ingested") return;
  btn.disabled = true;
  const runTimeIso = btn.dataset.at;
  const label = btn.dataset.label;
  try {
    await ingestDay(runTimeIso);
    btn.dataset.state = "ingested";
    showToast(`Ingested ${label} scan`, "success", 1500);

    // Extend the slider's reachable range and snap to this day so the user
    // immediately sees the effect.
    const runTimeMs = new Date(runTimeIso).getTime();
    if (state.latestIngestedMs === null || runTimeMs > state.latestIngestedMs) {
      state.latestIngestedMs = runTimeMs;
    }
    applySliderBounds();
    sliderEl.value = dateToSliderValue(runTimeMs);
    await onSliderInput(sliderEl.value);
  } catch (err) {
    btn.disabled = false;
    console.error(err);
    showToast(`Ingest failed: ${err.message}`, "error", 5000);
  }
}

function populateDayPreviews() {
  for (const btn of document.querySelectorAll(".day-btn")) {
    const rt = btn.dataset.at;
    const obs = ASSETS.observationsByRun.get(rt) ?? { servers: [], relationships: [] };
    const preview = document.querySelector(`#day-preview-${btn.dataset.day}`);
    if (preview) {
      preview.textContent = obs.servers.length === 0
        ? "no scan data"
        : `${obs.servers.map((s) => s.id).join(", ")} · ${obs.relationships.length} relationship${obs.relationships.length === 1 ? "" : "s"}`;
    }
  }
}

// ─── Reset ───────────────────────────────────────────────────────────────────

async function resetAll() {
  if (!confirm("Wipe the timeslice database and reset schema?")) return;
  try {
    await wipeDb();
    await setupSchema();
    for (const btn of document.querySelectorAll(".day-btn")) {
      btn.dataset.state = "";
      btn.disabled = false;
    }
    state.latestIngestedMs = null;
    applySliderBounds();
    renderSnapshot({ nodes: [], rels: [] });
    showToast("Database reset", "success", 1500);
  } catch (err) {
    console.error(err);
    showToast(`Reset failed: ${err.message}`, "error", 5000);
  }
}

// ─── Boot ────────────────────────────────────────────────────────────────────

async function boot() {
  try {
    console.log("[timeslice] boot: loading assets");
    await loadAssets();
    console.log("[timeslice] boot: connecting to Neo4j");
    await connect();
    console.log("[timeslice] boot: applying schema");
    await setupSchema();
    populateDayPreviews();
    populateQueryInspector();
    initNvl();
    console.log("[timeslice] boot: restoring UI state from DB (if any)");
    await restoreStateFromDb();
    console.log("[timeslice] boot: ready");

    sliderEl.addEventListener("input", (e) => {
      const maxVal = maxAllowedSliderValue();
      const clamped = Math.min(Number(e.target.value), maxVal);
      if (clamped !== Number(e.target.value)) e.target.value = clamped;
      if (state.latestIngestedMs !== null) {
        const at = sliderToDate(clamped);
        sliderReadout.textContent = formatAt(at);
        updateCurrentCallReadout(at);
      }
      scheduleSliderRefresh(clamped);
    });
    document.querySelectorAll(".day-btn").forEach((btn) => {
      btn.addEventListener("click", () => onDayClick(btn));
    });
    document.getElementById("btn-reset").addEventListener("click", resetAll);

    applySliderBounds();
    if (state.latestIngestedMs !== null) {
      // Restored from prior session: snap the slider to the latest known moment
      // and render the graph as it was then.
      sliderEl.value = dateToSliderValue(state.latestIngestedMs);
      await onSliderInput(sliderEl.value);
    } else {
      renderSnapshot({ nodes: [], rels: [] });
    }
  } catch (err) {
    console.error(err);
    showToast(`Startup error: ${err.message}`, "error", 10000);
  }
}

boot();
