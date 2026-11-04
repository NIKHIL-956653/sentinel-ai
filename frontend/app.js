// ───── CONFIG ─────
// Backend URL resolution:
//  1. window.SENTINEL_API_BASE (set in index.html) if given — e.g. frontend on GitHub Pages, API on Render
//  2. same origin when this page is served by FastAPI itself (http://host/app/)
//  3. http://127.0.0.1:8000 when opened as a file:// during local dev
const API_BASE = (window.SENTINEL_API_BASE
  || (location.protocol.startsWith("http") ? location.origin : "http://127.0.0.1:8000")) + "/api/v1";
const API_KEY = window.SENTINEL_API_KEY || "";

// All backend calls go through here: attaches the API key and turns 401/429 into readable errors.
async function apiFetch(url, opts = {}) {
  const headers = Object.assign({}, opts.headers || {});
  if (API_KEY) headers["X-API-Key"] = API_KEY;
  const res = await fetch(url, Object.assign({}, opts, { headers }));
  if (res.status === 401) throw new Error("API key missing or invalid (set window.SENTINEL_API_KEY)");
  if (res.status === 429) throw new Error("Rate limit reached — wait a minute and try again");
  return res;
}

// Same-origin download helper for the export endpoints (needs the X-API-Key header, so no plain <a href>).
async function downloadFile(url, filename) {
  try {
    const res = await apiFetch(url);
    if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = filename; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  } catch (e) { alert("Export failed: " + e.message); }
}

const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
// Resolved CSS variable (Leaflet / canvas need real colour strings, not var()).
const cssVar = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const confColor = c => ({ HIGH: cssVar("--green"), MEDIUM: cssVar("--amber") }[(c || "").toUpperCase()] || cssVar("--red"));

// ───── THEME + MOTION ─────
const root = document.documentElement;
function setTheme(t) {
  root.setAttribute("data-theme", t);
  try { localStorage.setItem("sentinel-theme", t); } catch (e) {}
  document.querySelector('meta[name="theme-color"]').setAttribute("content", t === "light" ? "#f3f6f4" : "#03060a");
  if (window.map) replotAll();
}
function toggleTheme() { setTheme(root.getAttribute("data-theme") === "light" ? "dark" : "light"); }
function setMotion(on) {
  root.setAttribute("data-motion", on ? "on" : "off");
  try { localStorage.setItem("sentinel-motion", on ? "on" : "off"); } catch (e) {}
}
function toggleMotion() { setMotion(root.getAttribute("data-motion") === "off"); }
(function initMotion() {
  let pref = null;
  try { pref = localStorage.getItem("sentinel-motion"); } catch (e) {}
  if (pref) setMotion(pref === "on");
  else if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) setMotion(false);
  else root.setAttribute("data-motion", "on");
})();
const motionOn = () => root.getAttribute("data-motion") !== "off";

// Country flag emojis
const countryFlags = {
  "United States": "🇺🇸", "Russia": "🇷🇺", "China": "🇨🇳",
  "India": "🇮🇳", "UAE": "🇦🇪", "Israel": "🇮🇱",
  "Iran": "🇮🇷", "Pakistan": "🇵🇰", "United Kingdom": "🇬🇧",
  "France": "🇫🇷", "Germany": "🇩🇪", "Japan": "🇯🇵",
  "South Korea": "🇰🇷", "North Korea": "🇰🇵", "Turkey": "🇹🇷",
  "Saudi Arabia": "🇸🇦", "Ukraine": "🇺🇦", "Italy": "🇮🇹",
  "Spain": "🇪🇸", "Canada": "🇨🇦", "Australia": "🇦🇺",
  "Brazil": "🇧🇷", "Mexico": "🇲🇽", "Egypt": "🇪🇬",
  "Indonesia": "🇮🇩", "Vietnam": "🇻🇳", "Thailand": "🇹🇭",
  "Poland": "🇵🇱", "Netherlands": "🇳🇱", "Sweden": "🇸🇪",
  "Switzerland": "🇨🇭", "Greece": "🇬🇷", "Portugal": "🇵🇹",
  "Norway": "🇳🇴", "Finland": "🇫🇮", "Denmark": "🇩🇰",
  "Belgium": "🇧🇪", "Austria": "🇦🇹", "Iraq": "🇮🇶",
  "Syria": "🇸🇾", "Lebanon": "🇱🇧", "Jordan": "🇯🇴",
  "Qatar": "🇶🇦", "Kuwait": "🇰🇼", "Bahrain": "🇧🇭",
  "Oman": "🇴🇲", "Yemen": "🇾🇪", "Afghanistan": "🇦🇫",
  "Bangladesh": "🇧🇩", "Sri Lanka": "🇱🇰", "Myanmar": "🇲🇲",
  "Malaysia": "🇲🇾", "Singapore": "🇸🇬", "Philippines": "🇵🇭",
  "Taiwan": "🇹🇼", "Kazakhstan": "🇰🇿", "Uzbekistan": "🇺🇿",
  "Azerbaijan": "🇦🇿", "Armenia": "🇦🇲", "Georgia": "🇬🇪",
  "Belarus": "🇧🇾", "Romania": "🇷🇴", "Bulgaria": "🇧🇬",
  "Hungary": "🇭🇺", "Czech Republic": "🇨🇿", "Serbia": "🇷🇸",
  "Croatia": "🇭🇷", "Albania": "🇦🇱", "Lithuania": "🇱🇹",
  "South Africa": "🇿🇦", "Nigeria": "🇳🇬", "Kenya": "🇰🇪",
  "Ethiopia": "🇪🇹", "Sudan": "🇸🇩", "Libya": "🇱🇾",
  "Algeria": "🇩🇿", "Morocco": "🇲🇦", "Tunisia": "🇹🇳",
  "Ghana": "🇬🇭", "Argentina": "🇦🇷", "Chile": "🇨🇱",
  "Colombia": "🇨🇴", "Peru": "🇵🇪", "Venezuela": "🇻🇪",
  "Cuba": "🇨🇺", "Bolivia": "🇧🇴", "Ecuador": "🇪🇨",
  "New Zealand": "🇳🇿", "Ireland": "🇮🇪", "Cambodia": "🇰🇭",
  "Angola": "🇦🇴", "Cameroon": "🇨🇲", "Uganda": "🇺🇬",
  "Zimbabwe": "🇿🇼", "Andorra": "🇦🇩", "Bosnia and Herzegovina": "🇧🇦",
  "Kyrgyzstan": "🇰🇬", "Tajikistan": "🇹🇯", "Turkmenistan": "🇹🇲"
};
function getFlag(country) { return countryFlags[country] || "🏳️"; }
const COUNTRY_LIST = Array.from(document.querySelectorAll("#countrySelect option")).map(o => o.value).filter(Boolean);

// ───── BOOT SEQUENCE ─────
const bootLines = [
  "> initializing secure uplink...",
  "> loading OSINT modules... OK",
  "> connecting to news sources... OK",
  "> calibrating AI verification... OK",
  "> establishing FastAPI link... OK",
  "> SENTINEL 2.2 ONLINE"
];
let bootIndex = 0;
const bootLog = document.getElementById("bootLog");
const bootDelay = motionOn() ? 400 : 60;

function runBoot() {
  if (bootIndex < bootLines.length) {
    bootLog.innerHTML += bootLines[bootIndex] + "<br>";
    bootIndex++;
    setTimeout(runBoot, bootDelay);
  } else {
    setTimeout(() => {
      document.getElementById("bootScreen").style.display = "none";
      document.getElementById("mainApp").style.display = "block";
      if (window.SENTINEL_DEMO) document.getElementById("demoBanner").style.display = "block";
      startBgRain();
      initMap();          // container is visible now, so Leaflet measures the real size
      loadSystemStats();  // real numbers for SOURCES / VERIFIED / intel feed / ticker / map
      loadWatchlist();
      handleRoute();      // deep link (#/country/India etc.)
    }, motionOn() ? 600 : 100);
  }
}

// ───── MATRIX RAIN ─────
function makeRain(canvasId) {
  const cv = document.getElementById(canvasId);
  if (!cv) return;
  const ctx = cv.getContext("2d");
  cv.width = window.innerWidth;
  cv.height = window.innerHeight;
  const chars = "01アイウエオカキク軍事機密戦争";
  const fs = 14;
  const cols = Math.floor(cv.width / fs);
  const drops = Array(cols).fill(0).map(() => Math.random() * cv.height);

  setInterval(() => {
    if (!motionOn() || document.hidden) return;
    ctx.fillStyle = root.getAttribute("data-theme") === "light" ? "rgba(243,246,244,0.12)" : "rgba(3,6,10,0.08)";
    ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = cssVar("--green");
    ctx.font = fs + "px monospace";
    drops.forEach((y, i) => {
      const ch = chars[Math.floor(Math.random() * chars.length)];
      ctx.fillText(ch, i * fs, y);
      if (y > cv.height && Math.random() > 0.975) drops[i] = 0;
      drops[i] += fs;
    });
  }, 45);
}
function startBgRain() { makeRain("bgRain"); }

makeRain("bootRain");
runBoot();

// ───── CLOCK ─────
setInterval(() => {
  const clock = document.getElementById("clock");
  if (clock) clock.textContent = new Date().toUTCString().slice(17, 25);
}, 1000);

// ───── NAV SWITCHING + HASH ROUTER ─────
function showScreen(name, pushHash = true) {
  const btn = document.querySelector(`.nav-btn[data-screen="${name}"]`);
  if (!btn) return;
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById("screen-" + name).classList.add("active");
  if (name === "nuclear") setTimeout(renderNuclear, 100);
  if (name === "alliances") setTimeout(renderAlliances, 100);
  if (name === "home") setTimeout(() => { if (map) map.invalidateSize(true); }, 100);
  if (name === "brief" && !window.__briefLoaded) loadBrief(false);
  if (name === "graph" && !window.__graphLoaded) loadGraph();
  if (name === "sources" && !window.__sourcesLoaded) loadSources();
  if (pushHash && !location.hash.startsWith("#/" + name)) setHash("#/" + name);
}
document.querySelectorAll(".nav-btn").forEach(btn => btn.addEventListener("click", () => showScreen(btn.dataset.screen)));

let _settingHash = false;
function setHash(h) {
  if (location.hash === h) return;
  _settingHash = true;
  history.replaceState(null, "", h);
  setTimeout(() => { _settingHash = false; }, 0);
}
function parseHash() {
  const h = location.hash.replace(/^#\/?/, "");
  const [path, qs] = h.split("?");
  const parts = path.split("/").filter(Boolean).map(decodeURIComponent);
  const params = new URLSearchParams(qs || "");
  return { parts, params };
}
function handleRoute() {
  const { parts, params } = parseHash();
  const screen = parts[0] || "home";
  const known = Array.from(document.querySelectorAll(".nav-btn")).map(b => b.dataset.screen);
  if (!known.includes(screen)) return;
  showScreen(screen, false);
  if (screen === "news" && params.get("q")) {
    document.getElementById("newsQuery").value = params.get("q");
    searchNews();
  } else if (screen === "country" || (screen === "countries" && parts[1])) {
    const c = parts[1];
    if (c) { document.getElementById("countrySelect").value = c; loadCountry(c); }
  } else if (screen === "compare" && parts[1] && parts[2]) {
    document.getElementById("compare1").value = parts[1];
    document.getElementById("compare2").value = parts[2];
    runCompare();
  } else if (screen === "graph" && params.get("q")) {
    window.__graphQuery = params.get("q");
    loadGraph();
  }
}
// "#/country/India" is an alias of "#/countries/India"
window.addEventListener("hashchange", () => {
  if (_settingHash) return;
  const { parts } = parseHash();
  if (parts[0] === "country") { location.hash = "#/countries/" + encodeURIComponent(parts[1] || ""); return; }
  handleRoute();
});

// ───── WATCHLIST ─────
async function loadWatchlist() {
  const panel = document.getElementById("watchPanel");
  const list = document.getElementById("watchList");
  const meta = document.getElementById("watchMeta");
  if (!panel) return;
  try {
    const res = await apiFetch(`${API_BASE}/watchlist`);
    const data = await res.json();
    const watches = data.watches || [];
    panel.style.display = watches.length ? "block" : "none";
    meta.textContent = `every ${data.interval_minutes} min · Telegram ${data.telegram_configured ? "connected" : "not configured"}`;
    list.innerHTML = watches.map(w => `
      <span style="border:1px solid var(--amber); border-radius:14px; padding:4px 10px; font-size:12px; color:var(--amber);">
        🔔 <a href="#/news?q=${encodeURIComponent(w.query)}" style="color:inherit; text-decoration:none;">${esc(w.query)}</a>
        <span class="muted" style="font-size:10px;">${w.last_run ? "· last " + new Date(w.last_run).toUTCString().slice(5, 22) : "· never run"} · ${w.seen_count} seen${w.disputed_count ? " · " + w.disputed_count + " ⚡" : ""}</span>
        <button onclick="removeWatch(${JSON.stringify(w.query).replace(/"/g, "&quot;")})" style="background:none; border:none; color:var(--red); cursor:pointer; margin-left:4px;">✕</button>
      </span>`).join("");
  } catch (err) { /* backend offline — panel stays hidden */ }
}

async function addWatch(query) {
  const q = (query || document.getElementById("newsQuery").value).trim();
  const status = document.getElementById("watchStatus");
  if (!q) return;
  try {
    const res = await apiFetch(`${API_BASE}/watchlist`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: q }) });
    const data = await res.json();
    if (status) status.textContent = data.status === "exists" ? "already watching" : data.status;
    loadWatchlist();
  } catch (err) { if (status) status.textContent = err.message; }
}

async function removeWatch(q) {
  try { await apiFetch(`${API_BASE}/watchlist?query=${encodeURIComponent(q)}`, { method: "DELETE" }); } catch (e) {}
  loadWatchlist();
}

async function runWatchlist() {
  const status = document.getElementById("watchStatus");
  status.textContent = "running…";
  try {
    const res = await apiFetch(`${API_BASE}/watchlist/run`, { method: "POST" });
    const r = await res.json();
    status.textContent = r.status === "already_running" ? "already running" : `${r.watches} watches · ${r.alerts} alerts sent` + (r.errors && r.errors.length ? ` · ${r.errors.length} errors` : "");
    loadWatchlist(); loadSystemStats();
  } catch (err) { status.textContent = err.message; }
}

async function testAlert() {
  const status = document.getElementById("watchStatus");
  try {
    const res = await apiFetch(`${API_BASE}/watchlist/test-alert`, { method: "POST" });
    status.textContent = res.ok ? "test message sent ✔" : (await res.json()).detail;
  } catch (err) { status.textContent = err.message; }
}

const watchBtn = document.getElementById("watchBtn");
if (watchBtn) watchBtn.addEventListener("click", () => addWatch());

// ───── NEWS SEARCH (SSE with HUD; falls back to plain POST) ─────
const searchBtn = document.getElementById("searchBtn");
if (searchBtn) {
  searchBtn.addEventListener("click", () => searchNews());
  document.getElementById("newsQuery").addEventListener("keypress", e => { if (e.key === "Enter") searchNews(); });
}

function hudInit(query, stages) {
  const hud = document.getElementById("pipelineHud");
  const ol = document.getElementById("pipelineStages");
  document.getElementById("pipelineQuery").textContent = query;
  ol.innerHTML = stages.map(s => `<li data-stage="${s.id}"><span class="st"></span><span>${esc(s.label)}</span><span class="detail"></span></li>`).join("");
  hud.style.display = "block";
}
function hudStage(name, detail) {
  const items = Array.from(document.querySelectorAll("#pipelineStages li"));
  const idx = items.findIndex(li => li.dataset.stage === name);
  items.forEach((li, i) => {
    if (name === "done") { if (li.classList.contains("active")) li.classList.add("done"); li.classList.remove("active"); if (!li.classList.contains("done")) li.classList.add("skipped"); return; }
    if (idx < 0) return;
    if (i < idx) { li.classList.remove("active"); if (!li.classList.contains("done")) li.classList.add("done"); }
    else if (i === idx) { li.classList.add("active"); li.querySelector(".detail").textContent = detail || ""; }
  });
  if (name === "done") {
    const hud = document.getElementById("pipelineHud");
    const note = document.createElement("div");
    note.className = "muted"; note.style.cssText = "font-size:10px; margin-top:6px;";
    note.textContent = "✔ " + (detail || "done");
    hud.appendChild(note);
    setTimeout(() => { hud.style.display = "none"; note.remove(); }, 2500);
  }
}

async function searchNews(query) {
  query = (query || document.getElementById("newsQuery").value).trim();
  if (!query) return;
  document.getElementById("newsQuery").value = query;
  setHash("#/news?q=" + encodeURIComponent(query));
  const results = document.getElementById("newsResults");
  results.innerHTML = '<div class="loading">SENTINEL gathering intelligence</div>';
  document.getElementById("timelinePanel").style.display = "none";
  if (searchBtn) searchBtn.disabled = true;

  try {
    let data = null;
    try {
      data = await streamNews(query);
    } catch (streamErr) {
      // Streaming unsupported by a proxy / old browser → plain request, same result
      console.warn("stream failed, falling back:", streamErr.message);
      const res = await apiFetch(`${API_BASE}/news`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query }) });
      if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
      data = await res.json();
    }
    renderNews(data);
    loadSystemStats();
    loadTimeline(query);
  } catch (err) {
    document.getElementById("pipelineHud").style.display = "none";
    results.innerHTML = `<div class="news-card low">❌ ${esc(err.message)}<br><br>Make sure the FastAPI backend is running!</div>`;
  } finally { if (searchBtn) searchBtn.disabled = false; }
}

// POST + ReadableStream SSE parser (EventSource only does GET).
async function streamNews(query) {
  const headers = { "Content-Type": "application/json", "Accept": "text/event-stream" };
  if (API_KEY) headers["X-API-Key"] = API_KEY;
  const res = await fetch(`${API_BASE}/news/stream`, { method: "POST", headers, body: JSON.stringify({ query }) });
  if (res.status === 401) throw new Error("API key missing or invalid");
  if (res.status === 429) { const e = new Error("Rate limit reached — wait a minute and try again"); e.fatal = true; throw e; }
  if (!res.ok || !res.body || !(res.headers.get("content-type") || "").includes("text/event-stream")) throw new Error("no stream");
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "", result = null;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let idx;
    while ((idx = buf.indexOf("\n\n")) >= 0) {
      const chunk = buf.slice(0, idx); buf = buf.slice(idx + 2);
      let ev = "message", data = "";
      chunk.split("\n").forEach(line => {
        if (line.startsWith("event:")) ev = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      });
      if (!data) continue;
      const payload = JSON.parse(data);
      if (ev === "stages") hudInit(query, payload.stages);
      else if (ev === "stage") hudStage(payload.stage, payload.detail);
      else if (ev === "result") result = payload;
      else if (ev === "error") { const e = new Error(payload.detail); e.fatal = true; throw e; }
    }
  }
  if (!result) throw new Error("stream ended without a result");
  return result;
}

// ── Verdict explanation ("why this verdict") ─────────────────────────────
function whyPanel(story) {
  const t = story.trust || { trusted: [], unknown: [], unreliable: [] };
  const conf = (story.confidence || "").toUpperCase();
  const n = story.source_count || (story.sources || []).length;
  const score = story.trust_score ?? 0;
  const list = (arr, color) => arr.length
    ? arr.map(s => `<span style="color:${color};">${esc(s)}</span>`).join(", ")
    : `<span class="dim">none</span>`;

  // the exact rule from agents/verifier_agent.py, in words
  let rule;
  if (t.trusted.length && score >= 2 && (conf === "HIGH" || conf === "MEDIUM"))
    rule = `VERIFIED: at least one trusted outlet, trust score ${score} ≥ 2, and ${n} independent source${n===1?"":"s"} (${conf}).`;
  else if (t.unreliable.length)
    rule = `DISPUTED: ${t.unreliable.length} source${t.unreliable.length===1?"":"s"} on the unreliable list and not enough trusted coverage to outweigh it.`;
  else if (conf === "LOW")
    rule = `UNVERIFIED: only one source reports this so far.`;
  else
    rule = `NEEDS REVIEW: ${n} sources agree but none is on the trusted list — corroboration without a known-reliable outlet.`;

  return `
    <div class="why-panel" style="display:none;">
      <div><b>Confidence</b> ${conf} — ${n} distinct source${n===1?"":"s"} cover this story (HIGH = 3+, MEDIUM = 2, LOW = 1)</div>
      <div><b>Trusted</b> ${list(t.trusted, "var(--green)")} <span class="dim">(+2 each)</span></div>
      <div><b>Unknown</b> ${list(t.unknown, "var(--amber)")} <span class="dim">(+1 each)</span></div>
      <div><b>Unreliable</b> ${list(t.unreliable, "var(--red)")} <span class="dim">(−2 each)</span></div>
      <div><b>Trust score</b> ${score}</div>
      <div style="margin-top:6px; color:var(--cyan);">→ ${rule}</div>
    </div>`;
}

function toggleWhy(btn) {
  const panel = btn.closest(".news-card").querySelector(".why-panel");
  const open = panel.style.display !== "none";
  panel.style.display = open ? "none" : "block";
  btn.textContent = open ? "WHY?" : "HIDE";
}

function claimsHtml(story, allStories) {
  const claims = story.claims || [];
  if (!claims.length) return "";
  const ref = idxs => (idxs || []).map(i => `<span class="refs" title="${esc((allStories[i]?.titles || [""])[0])}">#${i + 1}</span>`).join("");
  return `<div class="claims"><div class="claims-title">// CLAIMS — cross-source corroboration</div>
    ${claims.map(c => `<div class="claim ${c.status}"><span class="tag">${c.status === "corroborated" ? "✔ CORROBORATED" : c.status === "disputed" ? "⚡ DISPUTED" : "◌ SINGLE SOURCE"}</span>${esc(c.text)}
      ${c.supported_by?.length ? `<span class="refs">supported by ${ref(c.supported_by)}</span>` : ""}
      ${c.contradicted_by?.length ? `<span class="refs" style="color:var(--orange);">contradicted by ${ref(c.contradicted_by)}</span>` : ""}</div>`).join("")}
  </div>`;
}

function entityChips(story) {
  const ents = story.entities || [];
  if (!ents.length) return "";
  return `<div class="chips">${ents.map(e => {
    const isCountry = e.type === "place" && COUNTRY_LIST.includes(e.name);
    const go = isCountry ? `location.hash='#/countries/${encodeURIComponent(e.name)}'` : `openGraphFor(${JSON.stringify(window.__lastQuery || "")})`;
    return `<span class="chip ${e.type}" onclick="${go.replace(/"/g, "&quot;")}" title="${e.type}${isCountry ? " · open dossier" : " · open in graph"}">${esc(e.name)}</span>`;
  }).join("")}</div>`;
}

function renderNews(data) {
  const results = document.getElementById("newsResults");
  const stories = data.results || [];
  window.__lastQuery = data.query;

  if (stories.length === 0) {
    results.innerHTML = '<div class="news-card">No intelligence found for this query.</div>';
    return;
  }

  const srcEl = document.getElementById("srcCount");
  if (srcEl && data.total_articles) srcEl.textContent = data.total_articles;

  let high = 0, medium = 0, low = 0;
  stories.forEach(s => {
    const c = (s.confidence || "").toUpperCase();
    if (c === "HIGH") high++; else if (c === "MEDIUM") medium++; else low++;
  });
  const cs = data.claim_summary || {};
  const q = encodeURIComponent(data.query || "");

  let html = `
    <div class="panel">
      <div class="panel-title">// INTELLIGENCE REPORT — ${data.total_articles || 0} ARTICLES // ${data.total_stories || 0} STORIES ${data.status === "cached" ? '<span class="muted">(cached)</span>' : ""}</div>
      <div style="display:flex; gap:20px; justify-content:flex-end; font-size:13px; margin-top:8px; flex-wrap:wrap;">
        <span class="green">✅ HIGH: ${high}</span>
        <span class="amber">⚠️ MEDIUM: ${medium}</span>
        <span class="red">🔴 LOW: ${low}</span>
        <span style="color:var(--orange);">⚡ CONTRADICTIONS: ${(data.contradictions || []).length}</span>
        ${cs.total ? `<span class="cyan">🧾 CLAIMS: ${cs.corroborated}/${cs.total} corroborated${cs.disputed ? `, ${cs.disputed} disputed` : ""}</span>` : ""}
      </div>
      ${(data.contradictions || []).length ? `
      <div style="margin-top:10px; border-top:1px solid var(--border); padding-top:8px;">
        ${data.contradictions.map(c => `
          <div class="contra">
            <b>⚡ ${esc(c.conflict || "conflicting claims")}</b>
            <span class="dim" style="font-size:10px; margin-left:6px;">[${(c.method || "keyword").toUpperCase()} JUDGE]</span>
            <div class="dim" style="margin-top:3px;">“${esc(c.story1)}” <span style="color:var(--orange);">vs</span> “${esc(c.story2)}”</div>
          </div>`).join("")}
      </div>` : ""}
      <div class="report-actions">
        <button class="why-btn" onclick="downloadFile('${API_BASE}/export/news?q=${q}&format=md', 'sentinel-report.md')">⬇ MARKDOWN REPORT</button>
        <button class="why-btn" onclick="downloadFile('${API_BASE}/export/news?q=${q}&format=json', 'sentinel-report.json')">⬇ JSON</button>
        <button class="why-btn" onclick="window.print()">🖨 PRINT / PDF</button>
        <button class="why-btn" onclick="openGraphFor(${JSON.stringify(data.query || "").replace(/"/g, "&quot;")})">🕸 GRAPH</button>
        <button class="why-btn" onclick="navigator.clipboard && navigator.clipboard.writeText(location.href.split('#')[0] + '#/news?q=${q}'); this.textContent='LINK COPIED'">🔗 SHARE</button>
      </div>
    </div>`;

  stories.forEach((story, i) => {
    const conf = (story.confidence || "medium").toLowerCase();
    const sources = story.sources || [];
    const articles = story.articles || [];

    html += `
      <div class="news-card ${conf}" id="story-${i}">
        <div class="news-title"><span class="dim" style="font-size:11px;">#${i + 1}</span> ${esc(story.titles ? story.titles[0] : "Story")}</div>
        <div class="news-meta">
          <span class="badge ${conf}">${conf.toUpperCase()}</span>
          | ${esc(story.verdict || "")}
          | 📡 ${story.source_count || sources.length} SOURCES
          | 🛡️ TRUST: ${story.trust_score ?? 0}
          ${story.geo ? `| 📍 <a href="#/countries/${encodeURIComponent(story.geo.country)}" style="text-decoration:none;">${story.geo.place ? esc(story.geo.place) + ", " : ""}${esc(story.geo.country)}</a>${story.geo.precision === "city" ? '<span class="dim" style="font-size:9px;"> city</span>' : ""}` : ""}
          <button class="why-btn" onclick="toggleWhy(this)">WHY?</button>
        </div>
        ${whyPanel(story)}
        ${claimsHtml(story, stories)}
        ${entityChips(story)}
        <div style="margin-top:10px;">`;

    articles.forEach(a => {
      const content = (a.content || "").slice(0, 250);
      html += `
        <div class="article">
          <div class="article-title">${esc(a.title || "Untitled")}</div>
          <div class="article-meta">📡 ${esc(a.source || "")} ${a.url ? `| <a href="${esc(a.url)}" target="_blank" rel="noopener">READ SOURCE</a>` : ""}</div>
          <div class="article-body">${esc(content)}...</div>
        </div>`;
    });
    html += `</div></div>`;
  });

  results.innerHTML = html;
  updateTicker(stories);
}

// ───── TIMELINE ─────
async function loadTimeline(query) {
  const panel = document.getElementById("timelinePanel");
  const body = document.getElementById("timelineBody");
  const meta = document.getElementById("timelineMeta");
  try {
    const res = await apiFetch(`${API_BASE}/news/timeline?q=${encodeURIComponent(query)}&days=30`);
    const tl = await res.json();
    const runs = tl.runs || [];
    if (runs.length < 2) { panel.style.display = "none"; return; }
    meta.textContent = `${runs.length} runs over the last 30 days · each cell = one run · colour = confidence · orange ring = disputed claim`;
    const fmt = ts => ts ? new Date(ts).toUTCString().slice(5, 22) : "?";
    body.innerHTML = `
      <div class="tl-runs">${runs.map((r, i) => `<span title="${fmt(r.timestamp)}">run ${i + 1}: ${r.total_stories} stories · ${r.high} high · ${r.verified} verified · ${r.contradictions} ⚡</span>`).join("")}</div>
      <table class="tl-table">
        <tr><th>story</th><th>trend</th>${runs.map((r, i) => `<th title="${fmt(r.timestamp)}">${i + 1}</th>`).join("")}<th>seen</th></tr>
        ${(tl.stories || []).slice(0, 25).map(s => `
          <tr>
            <td>${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener" style="text-decoration:none; color:inherit;">${esc(s.title)}</a>` : esc(s.title)}</td>
            <td class="tl-trend ${s.trend}">${s.trend === "up" ? "▲" : s.trend === "down" ? "▼" : "▬"}</td>
            ${s.cells.map(c => c ? `<td><span class="tl-cell ${c.confidence} ${c.disputed_claims ? "disputed" : ""}" title="${c.confidence} · ${esc(c.verdict)} · ${c.sources} sources"></span></td>` : "<td><span class='tl-cell'></span></td>").join("")}
            <td class="muted">${s.runs_seen}/${runs.length}</td>
          </tr>`).join("")}
      </table>`;
    panel.style.display = "block";
  } catch (e) { panel.style.display = "none"; }
}

// ───── BRIEF ─────
function renderBrief(b) {
  const el = document.getElementById("briefResults");
  const s = b.sections || {};
  const c = b.counts || {};
  const ref = txt => esc(txt).replace(/\[(\d+)\]/g, (m, n) => `<span class="ref" title="${esc((b.stories[n] || {}).title || "")}" onclick="document.querySelector('#bsrc-${n}')?.scrollIntoView({behavior:'smooth'})">[${n}]</span>`);
  const sec = (key, title) => (s[key] || []).length ? `<div class="brief-sec"><h4>// ${title}</h4><ul>${s[key].map(x => `<li>${ref(x)}</li>`).join("")}</ul></div>` : "";
  el.innerHTML = `
    <div class="panel">
      <div class="brief-head">${esc(s.headline || "")}</div>
      <div class="muted" style="font-size:10px; margin-bottom:10px;">
        ${new Date(b.generated_at).toUTCString().slice(0, 22)} · window ${b.window_hours}h · ${c.stories} stories · ${c.sources} sources ·
        ${c.verified} verified · ${c.disputed} disputed · ${c.contradictions} contradictions ·
        ${b.model ? "summary by " + esc(b.model) : '<span class="amber">LLM unavailable — deterministic fallback</span>'}${b.cached ? " · cached" : ""}
      </div>
      <div class="brief-assess">${esc(s.assessment || "")}</div>
      ${sec("top_developments", "TOP DEVELOPMENTS")}
      ${sec("contradictions", "CONTRADICTIONS")}
      ${sec("leader_statements", "LEADER STATEMENTS")}
      ${sec("watch_items", "WATCH — NEXT 24H")}
      ${(b.regions || []).length ? `<div class="brief-sec"><h4>// ACTIVE REGIONS</h4><div class="chips">${b.regions.map(([r, n]) => `<span class="chip place" onclick="location.hash='#/countries/${encodeURIComponent(r)}'">${esc(r)} · ${n}</span>`).join("")}</div></div>` : ""}
      ${(b.disputed_claims || []).length ? `<div class="brief-sec"><h4>// DISPUTED CLAIMS</h4><ul>${b.disputed_claims.map(d => `<li>⚡ ${esc(d.claim)} <span class="muted">— ${esc(d.story)}</span></li>`).join("")}</ul></div>` : ""}
    </div>
    <div class="panel">
      <div class="panel-title">// SOURCES (${(b.stories || []).length})</div>
      ${(b.stories || []).map((st, i) => `<div class="brief-src" id="bsrc-${i}">[${i}] <b>${esc(st.title)}</b> — ${esc(st.confidence || "")} · ${esc(st.verdict || "")}${st.country ? " · " + esc(st.country) : ""}
        ${st.url ? `<a href="${esc(st.url)}" target="_blank" rel="noopener"> ↗</a>` : ""} <a href="#/news?q=${encodeURIComponent(st.query || "")}" class="muted" style="text-decoration:none;">(${esc(st.query || "")})</a></div>`).join("")}
    </div>`;
}

async function loadBrief(refresh) {
  const el = document.getElementById("briefResults");
  const status = document.getElementById("briefStatus");
  el.innerHTML = `<div class="loading">${refresh ? "Regenerating" : "Loading"} situation report</div>`;
  status.textContent = "";
  try {
    const res = await apiFetch(`${API_BASE}/brief${refresh ? "?refresh=true" : ""}`);
    if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
    const b = await res.json();
    window.__briefLoaded = true;
    if (!b.counts || !b.counts.stories) {
      el.innerHTML = `<div class="news-card">No archived stories in the last ${b.window_hours}h — run a search or add watches, then come back.</div>`;
      return;
    }
    renderBrief(b);
  } catch (e) { el.innerHTML = `<div class="news-card low">❌ ${esc(e.message)}</div>`; }
}
document.getElementById("briefRefresh")?.addEventListener("click", () => loadBrief(true));
document.getElementById("briefDownload")?.addEventListener("click", () => downloadFile(`${API_BASE}/brief?format=md`, "sentinel-brief.md"));
document.getElementById("briefSend")?.addEventListener("click", async () => {
  const status = document.getElementById("briefStatus");
  status.textContent = "sending…";
  try {
    const res = await apiFetch(`${API_BASE}/brief/send`, { method: "POST" });
    const r = await res.json();
    status.textContent = res.ok ? (r.sent ? "sent to Telegram ✔" : "Telegram rejected the message") : r.detail;
  } catch (e) { status.textContent = e.message; }
});

// ───── KNOWLEDGE GRAPH (canvas force layout, no dependencies) ─────
const graph = { nodes: [], edges: [], running: false, drag: null, hover: null, w: 0, h: 0, raf: null };

function openGraphFor(query) {
  window.__graphQuery = query || "";
  showScreen("graph");
  loadGraph();
}

async function loadGraphQueries() {
  const sel = document.getElementById("graphQuery");
  try {
    const res = await apiFetch(`${API_BASE}/news/queries?days=7`);
    const data = await res.json();
    const cur = window.__graphQuery || "";
    sel.innerHTML = `<option value="">ALL RECENT SEARCHES</option>` + (data.queries || []).map(q => `<option value="${esc(q.query)}">${esc(q.query)} (${q.runs})</option>`).join("");
    if (cur) {
      if (!Array.from(sel.options).some(o => o.value === cur)) sel.insertAdjacentHTML("beforeend", `<option value="${esc(cur)}">${esc(cur)}</option>`);
      sel.value = cur;
    }
  } catch (e) {}
}

async function loadGraph() {
  await loadGraphQueries();
  const q = document.getElementById("graphQuery").value || window.__graphQuery || "";
  window.__graphQuery = q;
  const hours = document.getElementById("graphHours").value;
  const meta = document.getElementById("graphMeta");
  meta.textContent = "building…";
  setHash("#/graph" + (q ? "?q=" + encodeURIComponent(q) : ""));
  try {
    const res = await apiFetch(`${API_BASE}/graph?hours=${hours}${q ? "&q=" + encodeURIComponent(q) : ""}`);
    const g = await res.json();
    window.__graphLoaded = true;
    meta.textContent = `${g.stats.stories} stories · ${g.stats.entities} entities · ${g.stats.edges} links`;
    if (!g.nodes.length) meta.textContent += " — run a search first (entities are extracted per search)";
    startGraph(g);
  } catch (e) { meta.textContent = e.message; }
}
document.getElementById("graphBtn")?.addEventListener("click", () => { window.__graphQuery = document.getElementById("graphQuery").value; loadGraph(); });

function nodeColor(n) {
  if (n.type === "story") return confColor(n.confidence);
  return { place: cssVar("--green"), person: cssVar("--amber"), weapon: cssVar("--red"), organisation: cssVar("--violet") }[n.type] || cssVar("--cyan");
}

function startGraph(g) {
  const cv = document.getElementById("graphCanvas");
  const rect = cv.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  cv.width = rect.width * dpr; cv.height = rect.height * dpr;
  graph.w = rect.width; graph.h = rect.height;
  const ctx = cv.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const idx = {};
  graph.nodes = g.nodes.map((n, i) => {
    idx[n.id] = i;
    const r = n.type === "story" ? 6 : Math.min(6 + (n.degree || 1) * 2, 18);
    return Object.assign({}, n, { x: graph.w / 2 + (Math.random() - 0.5) * graph.w * 0.6, y: graph.h / 2 + (Math.random() - 0.5) * graph.h * 0.6, vx: 0, vy: 0, r });
  });
  graph.edges = g.edges.filter(e => idx[e.from] !== undefined && idx[e.to] !== undefined).map(e => ({ a: idx[e.from], b: idx[e.to], rel: e.rel }));
  graph.alpha = 1;
  if (graph.raf) cancelAnimationFrame(graph.raf);

  function step() {
    const N = graph.nodes;
    const k = 0.9;
    // repulsion
    for (let i = 0; i < N.length; i++) for (let j = i + 1; j < N.length; j++) {
      const a = N[i], b = N[j];
      let dx = b.x - a.x, dy = b.y - a.y, d2 = dx * dx + dy * dy + 0.01, d = Math.sqrt(d2);
      const f = 1800 / d2;
      dx /= d; dy /= d;
      a.vx -= dx * f; a.vy -= dy * f; b.vx += dx * f; b.vy += dy * f;
    }
    // springs
    graph.edges.forEach(e => {
      const a = N[e.a], b = N[e.b];
      const dx = b.x - a.x, dy = b.y - a.y, d = Math.sqrt(dx * dx + dy * dy) + 0.01;
      const f = (d - 70) * 0.02;
      a.vx += dx / d * f; a.vy += dy / d * f; b.vx -= dx / d * f; b.vy -= dy / d * f;
    });
    // gravity to centre + integrate
    N.forEach(n => {
      if (graph.drag === n) { n.vx = n.vy = 0; return; }
      n.vx += (graph.w / 2 - n.x) * 0.003; n.vy += (graph.h / 2 - n.y) * 0.003;
      n.vx *= 0.82; n.vy *= 0.82;
      n.x += n.vx * k * graph.alpha; n.y += n.vy * k * graph.alpha;
      n.x = Math.max(n.r, Math.min(graph.w - n.r, n.x)); n.y = Math.max(n.r, Math.min(graph.h - n.r, n.y));
    });
    graph.alpha = Math.max(0.05, graph.alpha * 0.995);
  }

  function draw() {
    ctx.clearRect(0, 0, graph.w, graph.h);
    const border = cssVar("--border"), text = cssVar("--text"), dim = cssVar("--dim");
    ctx.lineWidth = 1;
    graph.edges.forEach(e => {
      const a = graph.nodes[e.a], b = graph.nodes[e.b];
      const hi = graph.hover && (graph.hover === a || graph.hover === b);
      ctx.strokeStyle = hi ? cssVar("--cyan") : border;
      ctx.globalAlpha = hi ? 1 : 0.7;
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    });
    ctx.globalAlpha = 1;
    graph.nodes.forEach(n => {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
      ctx.fillStyle = nodeColor(n);
      ctx.globalAlpha = n.type === "story" ? 0.75 : 0.9;
      ctx.fill();
      ctx.globalAlpha = 1;
      if (n.country || n === graph.hover) { ctx.strokeStyle = cssVar("--bright"); ctx.lineWidth = n === graph.hover ? 2 : 1; ctx.stroke(); }
      if (n.type !== "story" && (n.r >= 10 || n === graph.hover)) {
        ctx.fillStyle = n === graph.hover ? cssVar("--bright") : text;
        ctx.font = (n.r >= 14 ? "12px" : "10px") + " 'Courier New', monospace";
        ctx.fillText(n.label, n.x + n.r + 3, n.y + 4);
      }
    });
    if (!graph.nodes.length) {
      ctx.fillStyle = dim; ctx.font = "12px 'Courier New', monospace"; ctx.textAlign = "center";
      ctx.fillText("no graph yet — run a search in NEWS FEED first", graph.w / 2, graph.h / 2); ctx.textAlign = "left";
    }
  }

  function loop() {
    if (motionOn() || graph.alpha > 0.3 || graph.drag) step();
    draw();
    graph.raf = requestAnimationFrame(loop);
  }
  loop();

  const pos = ev => { const r = cv.getBoundingClientRect(); const p = ev.touches ? ev.touches[0] : ev; return { x: p.clientX - r.left, y: p.clientY - r.top }; };
  const hit = p => graph.nodes.find(n => (n.x - p.x) ** 2 + (n.y - p.y) ** 2 <= (n.r + 3) ** 2);
  const tip = document.getElementById("graphTip");
  cv.onmousemove = ev => {
    const p = pos(ev);
    if (graph.drag) { graph.drag.x = p.x; graph.drag.y = p.y; graph.alpha = 0.6; return; }
    const n = hit(p);
    graph.hover = n || null;
    cv.style.cursor = n ? "pointer" : "grab";
    if (n) {
      const links = graph.edges.filter(e => graph.nodes[e.a] === n || graph.nodes[e.b] === n).length;
      tip.innerHTML = n.type === "story"
        ? `<b style="color:${nodeColor(n)}">${n.confidence}</b> ${esc(n.verdict)}<br>${esc(n.label)}<br><span class="muted">query: ${esc(n.query || "")}${n.url ? " · click to open source" : ""}</span>`
        : `<b>${esc(n.label)}</b> <span class="muted">${n.type}${n.country ? " · click for dossier" : ""}</span><br>${links} link${links === 1 ? "" : "s"}`;
      tip.style.display = "block"; tip.style.left = Math.min(p.x + 14, graph.w - 330) + "px"; tip.style.top = (p.y + 14) + "px";
    } else tip.style.display = "none";
  };
  cv.onmousedown = ev => { const n = hit(pos(ev)); if (n) { graph.drag = n; graph.dragStart = Date.now(); } };
  window.addEventListener("mouseup", () => {
    if (graph.drag && Date.now() - graph.dragStart < 250) {
      const n = graph.drag;
      if (n.type === "story" && n.url) window.open(n.url, "_blank", "noopener");
      else if (n.country && COUNTRY_LIST.includes(n.label)) location.hash = "#/countries/" + encodeURIComponent(n.label);
    }
    graph.drag = null;
  });
  cv.ontouchstart = ev => { const n = hit(pos(ev)); if (n) { graph.drag = n; ev.preventDefault(); } };
  cv.ontouchmove = ev => { if (graph.drag) { const p = pos(ev); graph.drag.x = p.x; graph.drag.y = p.y; graph.alpha = 0.6; ev.preventDefault(); } };
  cv.ontouchend = () => { graph.drag = null; };
  cv.onmouseleave = () => { graph.hover = null; tip.style.display = "none"; };
}

// ───── SOURCES (outlet reliability) ─────
async function loadSources() {
  const el = document.getElementById("sourcesResults");
  const hours = document.getElementById("sourcesHours").value;
  el.innerHTML = '<div class="loading">Scoring outlets from the archive</div>';
  try {
    const res = await apiFetch(`${API_BASE}/sources?hours=${hours}`);
    if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
    const d = await res.json();
    window.__sourcesLoaded = true;
    const rows = d.sources || [];
    if (!rows.length) { el.innerHTML = `<div class="news-card">No archived stories in this window — run a few searches first.</div>`; return; }
    const bar = (v, color) => `<span class="src-bar"><i style="width:${Math.round(v * 100)}%; background:${color};"></i></span> <span class="dim">${Math.round(v * 100)}%</span>`;
    el.innerHTML = `
      <div class="panel">
        <div class="muted" style="font-size:11px; line-height:1.6; margin-bottom:10px;">
          ${d.stories} stories in the last ${d.hours}h. <b>Reliability</b> = ${esc(d.method)}.<br>
          ${(d.caveats || []).map(c => "⚠ " + esc(c)).join("<br>")}
        </div>
        <table class="src-table">
          <tr><th>OUTLET</th><th>LIST</th><th>STORIES</th><th>CORROBORATED</th><th>VERIFIED</th><th>DISPUTED</th><th>SOLO</th><th>RELIABILITY</th></tr>
          ${rows.map(r => `<tr>
            <td><b>${esc(r.domain)}</b>${r.sample_note ? ` <span class="dim" style="font-size:9px;">${esc(r.sample_note)}</span>` : ""}</td>
            <td><span class="pill ${r.list}">${r.list.toUpperCase()}</span></td>
            <td>${r.stories} <span class="dim">(${r.appearances} articles)</span></td>
            <td>${bar(r.corroboration_rate, "var(--cyan)")}</td>
            <td>${bar(r.verified_rate, "var(--green)")}</td>
            <td>${bar(r.disputed_rate, "var(--orange)")}</td>
            <td>${bar(r.solo_rate, "var(--dim)")}</td>
            <td><b style="color:${r.reliability >= 0.7 ? "var(--green)" : r.reliability >= 0.4 ? "var(--amber)" : "var(--red)"};">${r.reliability.toFixed(2)}</b></td>
          </tr>`).join("")}
        </table>
      </div>`;
  } catch (e) { el.innerHTML = `<div class="news-card low">❌ ${esc(e.message)}</div>`; }
}
document.getElementById("sourcesBtn")?.addEventListener("click", loadSources);

// ───── COUNTRIES ─────
const countrySelect = document.getElementById("countrySelect");
if (countrySelect) countrySelect.addEventListener("change", () => { if (countrySelect.value) loadCountry(countrySelect.value); });

async function loadCountry(country) {
  const results = document.getElementById("countryResults");
  results.innerHTML = '<div class="loading">Decrypting military dossier</div>';
  setHash("#/countries/" + encodeURIComponent(country));
  try {
    const res = await apiFetch(`${API_BASE}/country/${encodeURIComponent(country)}`);
    if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
    const data = await res.json();
    renderCountry(data);
  } catch (err) {
    results.innerHTML = `<div class="news-card low">❌ Error: ${esc(err.message)}</div>`;
  }
}

function sparkline(series, label) {
  if (!series || series.length < 2) return "";
  const W = 600, H = 70, pad = 4;
  const vals = series.map(p => p.value);
  const min = Math.min(...vals), max = Math.max(...vals);
  const x = i => pad + i * (W - 2 * pad) / (series.length - 1);
  const y = v => H - pad - (max === min ? 0.5 : (v - min) / (max - min)) * (H - 2 * pad);
  const pts = series.map((p, i) => `${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(" ");
  const first = series[0], last = series[series.length - 1];
  const pct = first.value ? ((last.value - first.value) / first.value * 100) : 0;
  const fmt = v => v >= 1e12 ? `$${(v / 1e12).toFixed(2)}T` : v >= 1e9 ? `$${(v / 1e9).toFixed(1)}B` : `$${(v / 1e6).toFixed(0)}M`;
  return `<div class="spark-wrap">
    <div class="spark-label"><span>📈 ${esc(label)}</span><span>${first.year} ${fmt(first.value)} → ${last.year} ${fmt(last.value)} <b class="${pct >= 0 ? "green" : "red"}">${pct >= 0 ? "+" : ""}${pct.toFixed(0)}%</b></span></div>
    <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
      <polyline points="${pts}" fill="none" stroke="var(--cyan)" stroke-width="2"/>
      <polygon points="${x(0)},${H - pad} ${pts} ${x(series.length - 1)},${H - pad}" fill="var(--cyan)" opacity="0.12"/>
      ${series.map((p, i) => `<circle cx="${x(i)}" cy="${y(p.value)}" r="2.5" fill="var(--cyan)"><title>${p.year}: ${fmt(p.value)}</title></circle>`).join("")}
    </svg>
    <div class="spark-label"><span>${first.year}</span><span class="dim">World Bank · SIPRI · current US$</span><span>${last.year}</span></div>
  </div>`;
}

function renderCountry(p) {
  const results = document.getElementById("countryResults");
  let fighters = p.fighters || "N/A";
  if (fighters.includes("Stock:")) fighters = fighters.split("Stock:")[1].split("\n")[0].trim();
  let tanks = p.tanks || "N/A";
  if (tanks.includes("Stock:")) tanks = tanks.split("Stock:")[1].split("\n")[0].trim();
  const c = JSON.stringify(p.country || "").replace(/"/g, "&quot;");
  const enc = encodeURIComponent(p.country || "");

  results.innerHTML = `
    <div class="panel">
      <div class="panel-title">${getFlag(p.country)} // ${esc((p.country || "").toUpperCase())} — MILITARY DOSSIER</div>
      <div style="color:var(--text); font-size:13px; margin-bottom:16px; line-height:1.6;">${esc(p.military_summary || "")}</div>

      <div class="stat-grid" style="grid-template-columns:repeat(3,1fr); margin-bottom:12px;">
        <div class="stat-box"><div class="stat-label">🪖 ARMY</div><div class="stat-val green">${esc(p.army_strength || "N/A")}</div></div>
        <div class="stat-box"><div class="stat-label">⚓ NAVY</div><div class="stat-val cyan">${esc(p.navy_strength || "N/A")}</div></div>
        <div class="stat-box"><div class="stat-label">✈️ AIRFORCE</div><div class="stat-val amber">${esc(p.airforce_strength || "N/A")}</div></div>
        <div class="stat-box"><div class="stat-label">💰 BUDGET</div><div class="stat-val" style="color:var(--gold);font-size:16px;">${esc(p.defense_budget || "N/A")}</div></div>
        <div class="stat-box"><div class="stat-label">🏆 RANK${p.global_rank_basis ? " (SPEND)" : ""}</div><div class="stat-val red">${p.global_rank && p.global_rank !== "N/A" ? "#" + esc(p.global_rank) : "N/A"}</div></div>
        <div class="stat-box"><div class="stat-label">👥 ACTIVE</div><div class="stat-val green" style="font-size:16px;">${esc(p.active_personnel || "N/A")}</div></div>
      </div>
      ${sparkline(p.expenditure_series, "MILITARY EXPENDITURE — " + (p.expenditure_series ? p.expenditure_series.length : 0) + " YEARS")}
      <div class="muted" style="font-size:10px; margin:-4px 0 12px; line-height:1.5;">
        📊 ${esc(p.data_source || "source unknown")}${p.data_provenance && p.data_provenance.fetched_at ? " · dataset fetched " + esc(p.data_provenance.fetched_at.slice(0, 10)) : ""}
        ${p.defense_budget_gdp_pct ? " · " + esc(p.defense_budget_gdp_pct) : ""}
        ${!p.expenditure_series ? " · no yearly series in the dataset (re-run scripts/fetch_open_data.py)" : ""}
        ${p.estimates_note ? "<br>ℹ️ " + esc(p.estimates_note) : ""}
      </div>

      <div class="stat-grid" style="grid-template-columns:repeat(4,1fr); margin-bottom:16px;">
        <div class="stat-box" style="cursor:pointer;" onclick="loadWeapons(${c},'fighter_jets')">
          <div class="stat-label">✈️ FIGHTERS</div><div class="stat-val cyan">${esc(fighters)}</div><div class="muted" style="font-size:10px;margin-top:4px;">CLICK FOR DETAILS</div>
        </div>
        <div class="stat-box" style="cursor:pointer;" onclick="loadWeapons(${c},'tanks')">
          <div class="stat-label">🚂 TANKS</div><div class="stat-val amber">${esc(tanks)}</div><div class="muted" style="font-size:10px;margin-top:4px;">CLICK FOR DETAILS</div>
        </div>
        <div class="stat-box" style="cursor:pointer;" onclick="loadWeapons(${c},'submarines')">
          <div class="stat-label">🤿 SUBMARINES</div><div class="stat-val green">${esc(p.submarines || "N/A")}</div><div class="muted" style="font-size:10px;margin-top:4px;">CLICK FOR DETAILS</div>
        </div>
        <div class="stat-box" style="cursor:pointer;" onclick="loadWeapons(${c},'missiles')">
          <div class="stat-label">🚀 MISSILES</div><div class="stat-val red">CLASSIFIED</div><div class="muted" style="font-size:10px;margin-top:4px;">CLICK FOR DETAILS</div>
        </div>
      </div>

      <div style="display:flex; gap:10px; flex-wrap:wrap;">
        <button class="btn-primary" onclick="loadSpecialForces(${c})">🕵️ SPECIAL FORCES</button>
        <button class="btn-primary btn-cyan" onclick="loadWeapons(${c},'warships')">🛳️ WARSHIPS</button>
        <button class="btn-primary btn-cyan" onclick="downloadFile('${API_BASE}/export/country/${enc}?format=md', 'sentinel-dossier-${enc}.md')">⬇ DOSSIER (MD)</button>
        <button class="btn-primary btn-cyan" onclick="window.print()">🖨 PRINT / PDF</button>
        <button class="btn-primary btn-amber" onclick="searchNews(${c} + ' military')">📰 LATEST NEWS</button>
      </div>
    </div>

    ${p.notable_facts && p.notable_facts.length ? `
    <div class="panel" style="margin-top:12px;">
      <div class="panel-title">// NOTABLE FACTS</div>
      ${p.notable_facts.map(f => `<div style="border-left:2px solid var(--border); padding:6px 12px; margin:6px 0; color:var(--text); font-size:13px;">▸ ${esc(f)}</div>`).join("")}
    </div>` : ""}

    <div id="weaponDetail" style="margin-top:12px;"></div>
  `;
}

// Grounding tag for LLM-generated items (weapons, special forces)
function groundingTag(item) {
  if (item && item.source_url) {
    return `<a href="${esc(item.source_url)}" target="_blank" rel="noopener" style="font-size:10px; margin-left:6px;">📖 WIKIPEDIA</a>`;
  }
  return `<span style="color:var(--amber); font-size:10px; margin-left:6px; border:1px solid var(--amber); padding:1px 5px; border-radius:3px;">AI-GENERATED · UNVERIFIED</span>`;
}

async function loadWeapons(country, category) {
  const detail = document.getElementById("weaponDetail");
  detail.innerHTML = '<div class="loading">Decrypting classified arsenal</div>';
  detail.scrollIntoView({ behavior: motionOn() ? "smooth" : "auto" });
  try {
    const res = await apiFetch(`${API_BASE}/weapons/${encodeURIComponent(country)}/${category}`);
    const data = await res.json();
    const items = data.data || [];
    const icons = { missiles: "🚀", submarines: "🤿", fighter_jets: "✈️", tanks: "🚂", warships: "🛳️" };
    const g = data.grounding || {};
    let html = `
      <div class="panel">
        <div class="panel-title">${icons[category] || "⚔️"} ${esc(country.toUpperCase())} — ${category.replace("_", " ").toUpperCase()}</div>
        <div class="muted" style="font-size:10px; margin:4px 0 8px;">
          🤖 AI-generated list · ${g.grounded ?? 0}/${g.total ?? items.length} verified against Wikipedia · unverified items are marked
        </div>`;
    items.forEach(item => {
      html += `
        <div style="border-left:3px solid ${item.grounded ? "var(--green)" : "var(--amber)"}; padding:10px 14px; margin:10px 0; background:var(--panel2); border-radius:0 8px 8px 0;">
          <div style="color:var(--green); font-weight:bold; font-size:14px;">${esc(item.name || "Unknown")} ${groundingTag(item)}</div>
          <div class="dim" style="font-size:11px; margin:4px 0;">
            ${item.year ? "📅 " + esc(item.year) : ""}
            ${item.type ? " | 🎯 " + esc(item.type) : ""}
            ${item.range ? " | 📡 Range: " + esc(item.range) : ""}
            ${item.role ? " | ⚡ " + esc(item.role) : ""}
            ${item.patrol_areas ? " | 🌊 " + esc(item.patrol_areas) : ""}
          </div>
          <div style="color:var(--text); font-size:12px; margin-top:6px; line-height:1.5;">${esc(item.history || "")}</div>
        </div>`;
    });
    detail.innerHTML = html + `</div>`;
  } catch (err) {
    detail.innerHTML = `<div class="news-card low">❌ Error: ${esc(err.message)}</div>`;
  }
}

async function loadSpecialForces(country) {
  const detail = document.getElementById("weaponDetail");
  detail.innerHTML = '<div class="loading">Accessing classified personnel files</div>';
  detail.scrollIntoView({ behavior: motionOn() ? "smooth" : "auto" });
  try {
    const res = await apiFetch(`${API_BASE}/special-forces/${encodeURIComponent(country)}`);
    const data = await res.json();
    const forces = data.forces || [];
    const g = data.grounding || {};
    let html = `
      <div class="panel">
        <div class="panel-title">🕵️ ${esc(country.toUpperCase())} — SPECIAL FORCES & INTELLIGENCE</div>
        <div class="muted" style="font-size:10px; margin:4px 0 8px;">
          🤖 AI-generated list · ${g.grounded ?? 0}/${g.total ?? forces.length} verified against Wikipedia · unverified items are marked
        </div>`;
    forces.forEach(f => {
      const isObj = f && typeof f === "object";
      const label = isObj ? `${f.emoji || "⚔️"} <b style="color:var(--cyan);">${esc(f.name || "")}</b> — ${esc(f.description || "")} ${groundingTag(f)}` : esc(f);
      html += `<div style="border-left:3px solid ${isObj && f.grounded ? "var(--cyan)" : "var(--amber)"}; padding:8px 12px; margin:8px 0; background:var(--panel3); border-radius:0 8px 8px 0; color:var(--text); font-size:13px;">${label}</div>`;
    });
    detail.innerHTML = html + `</div>`;
  } catch (err) {
    detail.innerHTML = `<div class="news-card low">❌ Error: ${esc(err.message)}</div>`;
  }
}

// ───── LEADERS ─────
const loadLeaders = document.getElementById("loadLeaders");
if (loadLeaders) {
  loadLeaders.addEventListener("click", async () => {
    const results = document.getElementById("leaderResults");
    results.innerHTML = '<div class="loading">Intercepting statements</div>';
    try {
      const res = await apiFetch(`${API_BASE}/leaders`);
      const data = await res.json();
      renderLeaders(data);
    } catch (err) {
      results.innerHTML = `<div class="news-card low">❌ Error: ${esc(err.message)}</div>`;
    }
  });
}

function renderLeaders(data) {
  const results = document.getElementById("leaderResults");
  const statements = data.statements || [];
  if (statements.length === 0) { results.innerHTML = '<div class="news-card">No statements found.</div>'; return; }

  let html = `<div class="panel"><div class="panel-title">// ${statements.length} WORLD LEADER STATEMENTS INTERCEPTED</div></div>`;
  statements.forEach((s, index) => {
    const sentiment = (s.sentiment || "neutral").toLowerCase();
    const color = { aggressive: "var(--red)", diplomatic: "var(--green)", neutral: "var(--amber)", warning: "var(--orange)" }[sentiment] || "var(--green)";
    html += `
      <div class="leader-card" onclick="openLeaderModal(${index})">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div>
            <div style="color:var(--bright); font-size:15px; font-weight:bold;">👤 ${esc(s.leader || "Unknown")} — ${esc(s.role || "")}</div>
            <div style="color:var(--text); font-style:italic; font-size:13px; margin:8px 0;">"${esc(s.statement || "")}"</div>
          </div>
          <span style="color:${color}; font-size:11px; font-weight:bold; letter-spacing:1px; white-space:nowrap; margin-left:12px;">${esc((s.sentiment || "").toUpperCase())}</span>
        </div>
        <div class="muted" style="font-size:11px; margin-top:6px;">📡 ${esc(s.source || "")} | 🖱️ CLICK FOR FULL INTEL</div>
      </div>`;
  });
  results.innerHTML = html;
  window._leaderStatements = statements;
}

function openLeaderModal(index) {
  const s = window._leaderStatements[index];
  if (!s) return;
  const sentiment = (s.sentiment || "neutral").toLowerCase();
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.id = "leaderModal";
  overlay.innerHTML = `
    <div class="modal-box">
      <button class="modal-close" onclick="closeModal()">✕ CLOSE</button>
      <div class="modal-leader-name">👤 ${esc(s.leader || "Unknown")}</div>
      <div class="modal-role">${esc(s.role || "")}</div>
      <span class="sentiment-badge sentiment-${sentiment}">${esc((s.sentiment || "NEUTRAL").toUpperCase())}</span>
      <div class="modal-section-title">// INTERCEPTED STATEMENT</div>
      <div class="modal-statement">"${esc(s.statement || "")}"</div>
      <div class="modal-section-title">// CONTEXT & BACKGROUND</div>
      <div class="modal-context">${esc(s.context || "No additional context available.")}</div>
      <div class="modal-section-title">// SOURCE</div>
      <div style="color:var(--cyan); font-size:12px; margin-bottom:16px;">📡 ${esc(s.source || "Unknown source")}</div>
      <div class="modal-section-title">// AI ANALYSIS</div>
      <div class="modal-analysis" id="modalAnalysis"><span class="loading">Analyzing statement</span></div>
    </div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener("click", e => { if (e.target === overlay) closeModal(); });
  loadLeaderAnalysis(s);
}

async function loadLeaderAnalysis(s) {
  const analysisEl = document.getElementById("modalAnalysis");
  if (!analysisEl) return;
  try {
    const res = await apiFetch(`${API_BASE}/leader-analysis`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ leader: s.leader, role: s.role, statement: s.statement, context: s.context, sentiment: s.sentiment })
    });
    const data = await res.json();
    analysisEl.textContent = data.analysis || "Analysis unavailable.";
  } catch (err) {
    analysisEl.textContent = "Analysis unavailable — check API connection.";
  }
}

function closeModal() {
  const modal = document.getElementById("leaderModal");
  if (modal) modal.remove();
}

// ───── COMPARE ─────
const compareBtn = document.getElementById("compareBtn");
if (compareBtn) compareBtn.addEventListener("click", runCompare);

async function runCompare() {
  const c1 = document.getElementById("compare1").value;
  const c2 = document.getElementById("compare2").value;
  if (!c1 || !c2) return;
  if (c1 === c2) { alert("Select two different countries!"); return; }
  setHash(`#/compare/${encodeURIComponent(c1)}/${encodeURIComponent(c2)}`);
  const results = document.getElementById("compareResults");
  results.innerHTML = '<div class="loading">Analyzing military balance</div>';
  try {
    const [r1, r2] = await Promise.all([
      apiFetch(`${API_BASE}/country/${encodeURIComponent(c1)}`).then(r => r.json()),
      apiFetch(`${API_BASE}/country/${encodeURIComponent(c2)}`).then(r => r.json())
    ]);
    await renderCompare(r1, r2);
  } catch (err) {
    results.innerHTML = `<div class="news-card low">❌ Error: ${esc(err.message)}</div>`;
  }
}

async function renderCompare(a, b) {
  const results = document.getElementById("compareResults");
  let winnerHtml = "";
  try {
    const res = await apiFetch(`${API_BASE}/compare-analysis`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ country1: a, country2: b })
    });
    const data = await res.json();
    winnerHtml = `
      <div class="panel" style="border-color:var(--gold); margin-top:14px;">
        <div class="panel-title" style="color:var(--gold);">// AI MILITARY ANALYSIS</div>
        <div style="color:var(--text); font-size:13px; line-height:1.6;">${esc(data.analysis || "")}</div>
      </div>`;
  } catch (e) {}

  const col = (p, color, dot) => `
      <div class="panel" style="border-color:${color};">
        <div class="panel-title" style="color:${color};">${dot} ${getFlag(p.country)} ${esc((p.country || "").toUpperCase())}</div>
        <div class="stat-box" style="margin-bottom:8px;"><div class="stat-label">🪖 ARMY</div><div class="stat-val green">${esc(p.army_strength || "N/A")}</div></div>
        <div class="stat-box" style="margin-bottom:8px;"><div class="stat-label">⚓ NAVY</div><div class="stat-val cyan">${esc(p.navy_strength || "N/A")}</div></div>
        <div class="stat-box" style="margin-bottom:8px;"><div class="stat-label">✈️ AIRFORCE</div><div class="stat-val amber">${esc(p.airforce_strength || "N/A")}</div></div>
        <div class="stat-box" style="margin-bottom:8px;"><div class="stat-label">💰 BUDGET</div><div class="stat-val" style="color:var(--gold); font-size:14px;">${esc(p.defense_budget || "N/A")}</div></div>
        <div class="stat-box"><div class="stat-label">🏆 RANK</div><div class="stat-val red">#${esc(p.global_rank || "N/A")}</div></div>
        ${sparkline(p.expenditure_series, "SPEND TREND")}
      </div>`;
  results.innerHTML = `<div class="grid-2">${col(a, "var(--cyan)", "🔵")}${col(b, "var(--red)", "🔴")}</div>${winnerHtml}`;
}

// ───── WORLD MAP ─────
let map = null;
let storyLayer = null;
let tileLayer = null;

function tileUrl() {
  return root.getAttribute("data-theme") === "light"
    ? "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
    : "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
}

function initMap() {
  if (map || typeof L === "undefined") return;   // Leaflet CDN blocked/offline → app still works without the map
  map = L.map("worldMap", { center: [28, 35], zoom: 3, zoomControl: true, attributionControl: false });
  tileLayer = L.tileLayer(tileUrl(), { maxZoom: 18, subdomains: "abcd" }).addTo(map);
  storyLayer = L.layerGroup().addTo(map);
  plotStories(window.__lastStories || []);
  setTimeout(() => map.invalidateSize(true), 300);
  updateThreatBars();
}

function replotAll() {
  if (typeof L === "undefined") return;
  if (tileLayer) tileLayer.setUrl(tileUrl());
  if (allianceTiles) allianceTiles.setUrl(tileUrl());
  plotStories(window.__lastStories || []);
}

function updateThreatBars(stories) {
  stories = stories || window.__lastStories || [];
  const c = { high: 0, medium: 0, low: 0 };
  stories.forEach(s => { const k = (s.confidence || "LOW").toLowerCase(); if (c[k] !== undefined) c[k]++; });
  const total = stories.length || 1;
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.style.width = (v / total * 100) + "%"; };
  const txt = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  set("highBar", c.high); set("medBar", c.medium); set("lowBar", c.low);
  txt("highNum", c.high); txt("medNum", c.medium); txt("lowNum", c.low);
  txt("alertCount", (stories.filter(s => (s.verdict || "").startsWith("DISPUTED")).length));
  const countries = new Set(stories.filter(s => s.geo).map(s => s.geo.country));
  const lvl = document.getElementById("threatLevel");
  if (lvl) lvl.textContent = stories.length ? `${countries.size} REGION${countries.size === 1 ? "" : "S"}` : "STANDBY";
}

function plotStories(stories) {
  if (!map || !storyLayer) return;
  storyLayer.clearLayers();
  const empty = document.getElementById("mapEmpty");
  const geo = stories.filter(s => s.geo && typeof s.geo.lat === "number");
  if (empty) empty.style.display = geo.length ? "none" : "flex";
  if (!geo.length) return;

  // group by place when known (city precision), else by country centroid
  const byCountry = {};
  geo.forEach(s => { const k = s.geo.place ? s.geo.place + "|" + s.geo.country : s.geo.country; (byCountry[k] = byCountry[k] || { geo: s.geo, stories: [] }).stories.push(s); });

  Object.values(byCountry).forEach(({ geo: g, stories: list }) => {
    const top = list.reduce((a, b) => rank(b.confidence) > rank(a.confidence) ? b : a, list[0]);
    const color = confColor(top.confidence);
    const radius = Math.min(6 + list.length * 3, 18);
    const items = list.slice(0, 5).map(s => {
      const a = (s.articles || [])[0] || {};
      return `<div style="margin:4px 0;">
        <span style="color:${confColor(s.confidence)}; font-weight:bold; font-size:10px;">${(s.confidence || "").toUpperCase()}</span>
        <span style="font-size:11px;">${esc(s.titles ? s.titles[0] : "")}</span>
        ${a.url ? `<a href="${esc(a.url)}" target="_blank" rel="noopener" style="font-size:10px; margin-left:4px;">↗</a>` : ""}
      </div>`;
    }).join("");
    L.circleMarker([g.lat, g.lng], { radius, color, fillColor: color, fillOpacity: 0.55, weight: 2 })
      .addTo(storyLayer)
      .bindPopup(`
        <div style="font-family:'Courier New',monospace; min-width:240px;">
          <div style="color:${color}; font-weight:bold; font-size:13px; margin-bottom:4px;">${g.place ? esc(g.place) + ", " : ""}${esc(g.country)} · ${list.length} stor${list.length === 1 ? "y" : "ies"}${g.precision === "city" ? ' <span style="font-size:9px; opacity:.7;">CITY</span>' : ""}
            ${COUNTRY_LIST.includes(g.country) ? `<a href="#/countries/${encodeURIComponent(g.country)}" style="font-size:10px; margin-left:6px;">DOSSIER ↗</a>` : ""}</div>
          ${items}${list.length > 5 ? `<div class="dim" style="font-size:10px;">+${list.length - 5} more</div>` : ""}
        </div>`);
  });
}
function rank(c) { return { HIGH: 3, MEDIUM: 2, LOW: 1 }[(c || "").toUpperCase()] || 0; }

// ───── INTEL FEED + SYSTEM STATS (real data from cached searches + runtime metrics) ─────
let intelItems = [{ level: "low", text: "[SYS] No intel cached yet — run a search in NEWS FEED" }];

async function loadSystemStats() {
  const src = document.getElementById("srcCount");
  const ver = document.getElementById("verifiedPct");
  try {
    const res = await apiFetch(`${API_BASE}/recent`);
    const data = await res.json();
    const searches = data.searches || [];
    const stories = [];
    searches.forEach(s => (s.results || []).forEach(st => { st.query = s.query; stories.push(st); }));

    const sources = new Set();
    stories.forEach(st => (st.sources || []).forEach(x => sources.add(x)));
    const verified = stories.filter(st => (st.verdict || "").startsWith("VERIFIED")).length;

    if (src) src.textContent = sources.size;
    if (ver) ver.textContent = stories.length ? Math.round(verified / stories.length * 100) + "%" : "—";
    window.__lastStories = stories;
    plotStories(stories);
    updateThreatBars(stories);

    if (stories.length) {
      const lvl = c => c === "HIGH" ? "high" : c === "MEDIUM" ? "medium" : "low";
      const tag = c => c === "HIGH" ? "HIGH" : c === "MEDIUM" ? "MED" : "LOW";
      intelItems = stories.slice(0, 12).map(st => ({
        level: lvl(st.confidence),
        text: `[${tag(st.confidence)}] ${(st.sources || [])[0] || "source"}: ${(st.titles || [])[0] || ""}`
      }));
      updateTicker(stories);
    }
  } catch (err) {
    if (src) src.textContent = "—";
    if (ver) ver.textContent = "—";
    intelItems = [{ level: "low", text: "[SYS] Backend offline — start FastAPI to see live intel" }];
    updateThreatBars([]);
  }
  loadRuntimeStats();
}

async function loadRuntimeStats() {
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  try {
    const res = await apiFetch(`${API_BASE}/stats`);
    const s = await res.json();
    const l = s.llm || {}, p = s.pipeline || {};
    set("llmCalls", l.calls ?? 0);
    const tok = (l.prompt_tokens || 0) + (l.completion_tokens || 0);
    set("llmTokens", tok >= 1000 ? (tok / 1000).toFixed(1) + "k" : tok);
    set("llmCost", "$" + (l.cost_usd ?? 0).toFixed(3) + (l.cost_is_estimate ? "~" : ""));
    set("cacheHit", p.searches ? Math.round((p.cache_hits || 0) / p.searches * 100) + "%" : "—");
    const note = document.getElementById("statsNote");
    const b = s.budget || {};
    if (note) note.textContent = `since start ${Math.round((s.uptime_s || 0) / 60)} min · model ${s.model || "?"} · avg LLM ${l.avg_ms || 0} ms · ${l.errors || 0} LLM errors` +
      (b.limit_usd ? ` · budget $${(b.spent_today_usd || 0).toFixed(3)} / $${b.limit_usd} today${b.blocked_calls_today ? " · " + b.blocked_calls_today + " blocked" : ""}` : "") + " · /metrics for Prometheus";
  } catch (e) { set("llmCalls", "—"); set("llmTokens", "—"); set("llmCost", "—"); set("cacheHit", "—"); }
}
setInterval(loadRuntimeStats, 30000);

let intelIndex = 0;
function updateIntelFeed() {
  const feed = document.getElementById("intelFeed");
  if (!feed || document.hidden) return;
  const item = intelItems[intelIndex % intelItems.length];
  const now = new Date().toUTCString().slice(17, 25);
  const div = document.createElement("div");
  div.className = `intel-item ${item.level}`;
  div.textContent = `${now} ${item.text}`;
  feed.insertBefore(div, feed.firstChild);
  if (feed.children.length > 8) feed.removeChild(feed.lastChild);
  intelIndex++;
}
setInterval(updateIntelFeed, 2500);

// ───── RADAR SWEEP ─────
let radarAngle = 0;
function animateRadar() {
  if (motionOn() && !document.hidden) {
    radarAngle = (radarAngle + 2) % 360;
    const sweep = document.getElementById("radarSweep");
    if (sweep) sweep.style.transform = `rotate(${radarAngle}deg)`;
  }
  requestAnimationFrame(animateRadar);
}
animateRadar();

// ───── NEWS TICKER UPDATE ─────
function updateTicker(stories) {
  const ticker = document.getElementById("tickerContent");
  if (!ticker || !stories || !stories.length) return;
  ticker.textContent = stories.map(story => ` ⚡ [${(story.confidence || "").toUpperCase()}] ${story.titles ? story.titles[0] : ""} — `).join("");
}

// ───── NUCLEAR ARSENAL ─────
const nuclearData = [
  { country: "Russia", flag: "🇷🇺", warheads: 5580, triad: true, treaty: "New START (suspended 2023)" },
  { country: "United States", flag: "🇺🇸", warheads: 5044, triad: true, treaty: "New START (suspended)" },
  { country: "China", flag: "🇨🇳", warheads: 600, triad: true, treaty: "No-first-use policy declared" },
  { country: "France", flag: "🇫🇷", warheads: 290, triad: false, treaty: "NPT signatory" },
  { country: "United Kingdom", flag: "🇬🇧", warheads: 225, triad: false, treaty: "NPT signatory" },
  { country: "India", flag: "🇮🇳", warheads: 180, triad: true, treaty: "No-first-use policy" },
  { country: "Pakistan", flag: "🇵🇰", warheads: 170, triad: false, treaty: "Non-NPT state" },
  { country: "Israel", flag: "🇮🇱", warheads: 90, triad: false, treaty: "Undeclared (estimated)" },
  { country: "North Korea", flag: "🇰🇵", warheads: 50, triad: false, treaty: "Withdrew from NPT 2003" },
];

function renderNuclear() {
  const bars = document.getElementById("nuclearBars");
  if (!bars || bars.children.length > 0) return;
  const max = nuclearData[0].warheads;
  bars.innerHTML = nuclearData.map(n => {
    const pct = (n.warheads / max * 100).toFixed(1);
    const color = n.warheads > 1000 ? "var(--red)" : n.warheads > 200 ? "var(--amber)" : "var(--green)";
    return `
      <div style="display:flex; align-items:center; gap:12px; margin:10px 0;">
        <div style="width:160px; color:var(--bright); font-size:13px; white-space:nowrap; cursor:pointer;" onclick="location.hash='#/countries/${encodeURIComponent(n.country)}'">${n.flag} ${n.country}</div>
        <div style="flex:1; height:18px; background:var(--border2); border-radius:4px; overflow:hidden;">
          <div style="width:${pct}%; height:100%; background:${color}; box-shadow:0 0 10px ${color}; border-radius:4px; transition:width 1.5s ease;"></div>
        </div>
        <div style="width:70px; color:${color}; font-size:14px; font-weight:bold; text-align:right;">${n.warheads.toLocaleString()}</div>
      </div>`;
  }).join("");

  document.getElementById("triadList").innerHTML = nuclearData.filter(n => n.triad).map(n => `
    <div style="border-left:3px solid var(--red); padding:8px 12px; margin:8px 0; background:var(--panel2); color:var(--bright); font-size:13px;">
      ${n.flag} <b>${n.country}</b>
      <div class="dim" style="font-size:11px; margin-top:2px;">☢️ Land + Sea + Air launch capability</div>
    </div>`).join("");

  document.getElementById("treatyList").innerHTML = nuclearData.map(n => `
    <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid var(--border2); font-size:12px;">
      <span style="color:var(--bright);">${n.flag} ${n.country}</span>
      <span class="dim">${n.treaty}</span>
    </div>`).join("");
}

// ───── ALLIANCES ─────
const alliances = [
  { name: "NATO", color: "#4fd1ff", hq: "Brussels, Belgium", members: 32,
    keyMembers: "🇺🇸 USA, 🇬🇧 UK, 🇫🇷 France, 🇩🇪 Germany, 🇹🇷 Turkey, 🇵🇱 Poland",
    info: "North Atlantic Treaty Organization. Article 5: attack on one = attack on all.",
    coords: [[50.85, 4.35], [38.9, -77.0], [51.5, -0.1], [48.85, 2.35], [52.5, 13.4], [39.9, 32.8]] },
  { name: "CSTO", color: "#ff4d6d", hq: "Moscow, Russia", members: 6,
    keyMembers: "🇷🇺 Russia, 🇧🇾 Belarus, 🇰🇿 Kazakhstan, 🇦🇲 Armenia",
    info: "Collective Security Treaty Organization. Russia-led security bloc.",
    coords: [[55.75, 37.6], [53.9, 27.5], [51.1, 71.4], [40.18, 44.5]] },
  { name: "SCO", color: "#ffb300", hq: "Beijing, China", members: 10,
    keyMembers: "🇨🇳 China, 🇷🇺 Russia, 🇮🇳 India, 🇵🇰 Pakistan, 🇮🇷 Iran",
    info: "Shanghai Cooperation Organisation. Eurasian political-military bloc.",
    coords: [[39.9, 116.4], [55.75, 37.6], [28.6, 77.2], [33.7, 73.0], [35.7, 51.4]] },
  { name: "QUAD", color: "#00c47a", hq: "Informal alliance", members: 4,
    keyMembers: "🇺🇸 USA, 🇮🇳 India, 🇯🇵 Japan, 🇦🇺 Australia",
    info: "Quadrilateral Security Dialogue. Indo-Pacific strategic forum.",
    coords: [[38.9, -77.0], [28.6, 77.2], [35.7, 139.7], [-35.3, 149.1]] },
];
let allianceMapObj = null, allianceTiles = null;

function renderAlliances() {
  const cards = document.getElementById("allianceCards");
  if (cards && !cards.children.length) {
    cards.innerHTML = alliances.map(a => `
      <div class="panel" style="border-color:${a.color};">
        <div class="panel-title" style="color:${a.color};">// ${a.name} — ${a.members} MEMBERS</div>
        <div style="color:var(--bright); font-size:13px; margin-bottom:6px;">${a.keyMembers}</div>
        <div class="dim" style="font-size:12px; line-height:1.5;">${a.info}</div>
        <div class="muted" style="font-size:11px; margin-top:8px;">📍 HQ: ${a.hq}</div>
      </div>`).join("");
  }
  if (allianceMapObj) { setTimeout(() => allianceMapObj.invalidateSize(true), 100); return; }
  if (typeof L === "undefined") return;
  allianceMapObj = L.map("allianceMap", { center: [35, 40], zoom: 2, attributionControl: false });
  allianceTiles = L.tileLayer(tileUrl(), { maxZoom: 18, subdomains: "abcd" }).addTo(allianceMapObj);
  alliances.forEach(a => a.coords.forEach(c => {
    L.circleMarker(c, { radius: 7, color: a.color, fillColor: a.color, fillOpacity: 0.8, weight: 2 })
      .addTo(allianceMapObj).bindPopup(`<b style="color:${a.color};">${a.name}</b>`);
  }));
  setTimeout(() => allianceMapObj.invalidateSize(true), 300);
}

// ───── COMMAND PALETTE (Ctrl+K) ─────
const palette = { el: document.getElementById("palette"), input: document.getElementById("paletteInput"), list: document.getElementById("paletteList"), items: [], sel: 0 };

function paletteCommands(text) {
  const q = text.trim();
  const ql = q.toLowerCase();
  const words = ql.split(/\s+/).filter(Boolean);
  const out = [];
  const matchCountry = w => COUNTRY_LIST.filter(c => c.toLowerCase().startsWith(w) || c.toLowerCase().split(" ").some(p => p.startsWith(w)));
  const verb = words[0] || "";
  const rest = q.slice(verb.length).trim();

  if (["dossier", "country", "c"].includes(verb) || (!verb && false)) {
    matchCountry(rest.toLowerCase()).slice(0, 8).forEach(c => out.push({ label: `${getFlag(c)} Dossier: ${c}`, hint: "countries", run: () => { location.hash = "#/countries/" + encodeURIComponent(c); } }));
  }
  if (["compare", "vs"].includes(verb)) {
    const parts = rest.split(/\s+(?:vs|v|and|,)?\s*/i).filter(Boolean);
    const a = matchCountry((parts[0] || "").toLowerCase())[0], b = matchCountry((parts[1] || "").toLowerCase())[0];
    if (a && b) out.push({ label: `⚔️ Compare ${a} vs ${b}`, hint: "compare", run: () => { location.hash = `#/compare/${encodeURIComponent(a)}/${encodeURIComponent(b)}`; } });
    else out.push({ label: "⚔️ compare <country> <country>", hint: "e.g. compare india pakistan", run: null });
  }
  if (["watch", "w"].includes(verb) && rest) out.push({ label: `🔔 Watch “${rest}”`, hint: "watchlist + Telegram alerts", run: () => { showScreen("news"); document.getElementById("newsQuery").value = rest; addWatch(rest); } });
  if (["news", "search", "n", "s"].includes(verb) && rest) out.push({ label: `📰 Search “${rest}”`, hint: "news feed", run: () => { showScreen("news"); searchNews(rest); } });
  if (["graph", "g"].includes(verb)) out.push({ label: `🕸️ Knowledge graph${rest ? " for “" + rest + "”" : ""}`, hint: "graph", run: () => openGraphFor(rest) });
  if (["brief", "sitrep", "b"].includes(verb)) out.push({ label: "🗞️ Daily intelligence brief", hint: "brief", run: () => showScreen("brief") });
  if (["sources", "outlets", "reliability"].includes(verb)) out.push({ label: "📡 Outlet reliability", hint: "sources", run: () => showScreen("sources") });
  if (["theme", "light", "dark"].includes(verb)) out.push({ label: "◐ Toggle light / dark theme", hint: "theme", run: toggleTheme });
  if (["motion", "animations", "calm"].includes(verb)) out.push({ label: "◴ Toggle animations", hint: "motion", run: toggleMotion });
  if (["go", "open"].includes(verb) || !out.length) {
    const screens = { home: "🌍 Threat grid", news: "📰 News feed", brief: "🗞️ Brief", graph: "🕸️ Graph", sources: "📡 Sources", countries: "🗂️ Countries", leaders: "👤 Leaders", compare: "⚔️ Compare", nuclear: "☢️ Nuclear", alliances: "🤝 Alliances" };
    Object.entries(screens).filter(([k, v]) => !ql || k.startsWith(rest.toLowerCase() || ql) || v.toLowerCase().includes(ql)).forEach(([k, v]) => out.push({ label: v, hint: "#/" + k, run: () => showScreen(k) }));
  }
  if (!verb) {
    out.unshift({ label: "◐ Toggle theme", hint: "theme", run: toggleTheme });
    out.push({ label: "📖 Commands: dossier <country> · compare <a> <b> · news <query> · watch <query> · graph · brief · theme · motion", hint: "", run: null });
  } else if (!out.length || (out.length && !["dossier", "country", "c", "compare", "vs", "watch", "w", "news", "search", "n", "s", "graph", "g", "brief", "sitrep", "b", "theme", "light", "dark", "motion", "go", "open"].includes(verb))) {
    // bare text: offer countries + search
    matchCountry(ql).slice(0, 5).forEach(c => out.unshift({ label: `${getFlag(c)} Dossier: ${c}`, hint: "countries", run: () => { location.hash = "#/countries/" + encodeURIComponent(c); } }));
    out.push({ label: `📰 Search news for “${q}”`, hint: "news", run: () => { showScreen("news"); searchNews(q); } });
  }
  return out.slice(0, 12);
}

function paletteRender() {
  palette.items = paletteCommands(palette.input.value);
  palette.sel = Math.min(palette.sel, Math.max(palette.items.length - 1, 0));
  palette.list.innerHTML = palette.items.map((it, i) => `<li class="${i === palette.sel ? "sel" : ""}" data-i="${i}"><span>${esc(it.label)}</span><small>${esc(it.hint)}</small></li>`).join("");
}
function paletteOpen() { palette.el.style.display = "flex"; palette.input.value = ""; palette.sel = 0; paletteRender(); setTimeout(() => palette.input.focus(), 0); }
function paletteClose() { palette.el.style.display = "none"; }
function paletteRun(i) { const it = palette.items[i]; if (it && it.run) { paletteClose(); it.run(); } }

document.getElementById("paletteBtn").addEventListener("click", paletteOpen);
document.getElementById("themeBtn").addEventListener("click", toggleTheme);
document.getElementById("motionBtn").addEventListener("click", toggleMotion);
palette.input.addEventListener("input", () => { palette.sel = 0; paletteRender(); });
palette.input.addEventListener("keydown", e => {
  if (e.key === "ArrowDown") { palette.sel = (palette.sel + 1) % Math.max(palette.items.length, 1); paletteRender(); e.preventDefault(); }
  else if (e.key === "ArrowUp") { palette.sel = (palette.sel - 1 + palette.items.length) % Math.max(palette.items.length, 1); paletteRender(); e.preventDefault(); }
  else if (e.key === "Enter") { paletteRun(palette.sel); e.preventDefault(); }
  else if (e.key === "Escape") paletteClose();
});
palette.list.addEventListener("click", e => { const li = e.target.closest("li"); if (li) paletteRun(+li.dataset.i); });
palette.el.addEventListener("click", e => { if (e.target === palette.el) paletteClose(); });
window.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); palette.el.style.display === "flex" ? paletteClose() : paletteOpen(); }
  else if (e.key === "Escape") { paletteClose(); closeModal(); }
});

// (map is initialised in runBoot() once #mainApp is visible)
