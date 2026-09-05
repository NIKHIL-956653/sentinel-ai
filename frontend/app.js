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

function getFlag(country) {
  return countryFlags[country] || "🏳️";
}

// ───── BOOT SEQUENCE ─────
const bootLines = [
  "> initializing secure uplink...",
  "> loading OSINT modules... OK",
  "> connecting to news sources... OK",
  "> calibrating AI verification... OK",
  "> establishing FastAPI link... OK",
  "> SENTINEL 2.0 ONLINE"
];

let bootIndex = 0;
const bootLog = document.getElementById("bootLog");

function runBoot() {
  if (bootIndex < bootLines.length) {
    bootLog.innerHTML += bootLines[bootIndex] + "<br>";
    bootIndex++;
    setTimeout(runBoot, 400);
  } else {
    setTimeout(() => {
      document.getElementById("bootScreen").style.display = "none";
      document.getElementById("mainApp").style.display = "block";
      startBgRain();
      initMap();          // container is visible now, so Leaflet measures the real size
      loadSystemStats();  // real numbers for SOURCES / VERIFIED / intel feed / ticker / map
      loadWatchlist();
    }, 600);
  }
}

// ───── MATRIX RAIN ─────
function makeRain(canvasId, opacity) {
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
    ctx.fillStyle = "rgba(3,6,10,0.08)";
    ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = "#00ff9c";
    ctx.font = fs + "px monospace";
    drops.forEach((y, i) => {
      const ch = chars[Math.floor(Math.random() * chars.length)];
      ctx.fillText(ch, i * fs, y);
      if (y > cv.height && Math.random() > 0.975) drops[i] = 0;
      drops[i] += fs;
    });
  }, 45);
}

function startBgRain() {
  makeRain("bgRain");
}

// Boot rain
makeRain("bootRain");
runBoot();

// ───── CLOCK ─────
setInterval(() => {
  const clock = document.getElementById("clock");
  if (clock) clock.textContent = new Date().toUTCString().slice(17, 25);
}, 1000);


// ───── NAV SWITCHING ─────
document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("screen-" + btn.dataset.screen).classList.add("active");

    // Screen-specific renders
    if (btn.dataset.screen === "nuclear") setTimeout(renderNuclear, 100);
    if (btn.dataset.screen === "alliances") setTimeout(renderAlliances, 100);
    if (btn.dataset.screen === "home") setTimeout(() => { if(map) map.invalidateSize(true); }, 100);
  });
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
      <span style="border:1px solid #ffb30066; border-radius:14px; padding:4px 10px; font-size:12px; color:#ffb300;">
        🔔 ${w.query}
        <span style="color:#3a7a5c; font-size:10px;">${w.last_run ? "· last " + new Date(w.last_run).toUTCString().slice(5, 22) : "· never run"} · ${w.seen_count} seen</span>
        <button onclick="removeWatch('${w.query.replace(/'/g, "\\'")}')" style="background:none; border:none; color:#ff4d6d; cursor:pointer; margin-left:4px;">✕</button>
      </span>`).join("");
  } catch (err) { /* backend offline — panel stays hidden */ }
}

async function addWatch() {
  const q = document.getElementById("newsQuery").value.trim();
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
if (watchBtn) watchBtn.addEventListener("click", addWatch);

// ───── NEWS SEARCH ─────
const searchBtn = document.getElementById("searchBtn");
if (searchBtn) {
  searchBtn.addEventListener("click", searchNews);
  document.getElementById("newsQuery").addEventListener("keypress", e => {
    if (e.key === "Enter") searchNews();
  });
}

async function searchNews() {
  const query = document.getElementById("newsQuery").value;
  if (!query) return;
  const results = document.getElementById("newsResults");
  results.innerHTML = '<div class="loading">SENTINEL gathering intelligence</div>';

  try {
    const res = await apiFetch(`${API_BASE}/news`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query })
    });
    const data = await res.json();
    renderNews(data);
    loadSystemStats();
  } catch (err) {
    results.innerHTML = `<div class="news-card low">❌ Connection Error: ${err.message}<br><br>Make sure FastAPI backend is running!</div>`;
  }
}

// ── Verdict explanation ("why this verdict") ─────────────────────────────
function whyPanel(story) {
  const t = story.trust || { trusted: [], unknown: [], unreliable: [] };
  const conf = (story.confidence || "").toUpperCase();
  const n = story.source_count || (story.sources || []).length;
  const score = story.trust_score ?? 0;
  const list = (arr, color) => arr.length
    ? arr.map(s => `<span style="color:${color};">${s}</span>`).join(", ")
    : `<span style="color:#555;">none</span>`;

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
      <div><b>Trusted</b> ${list(t.trusted, "#00ff9c")} <span style="color:#555;">(+2 each)</span></div>
      <div><b>Unknown</b> ${list(t.unknown, "#ffb300")} <span style="color:#555;">(+1 each)</span></div>
      <div><b>Unreliable</b> ${list(t.unreliable, "#ff4d6d")} <span style="color:#555;">(−2 each)</span></div>
      <div><b>Trust score</b> ${score}</div>
      <div style="margin-top:6px; color:#4fd1ff;">→ ${rule}</div>
    </div>`;
}

function toggleWhy(btn) {
  const panel = btn.closest(".news-card").querySelector(".why-panel");
  const open = panel.style.display !== "none";
  panel.style.display = open ? "none" : "block";
  btn.textContent = open ? "WHY?" : "HIDE";
}

function renderNews(data) {
  const results = document.getElementById("newsResults");
  const stories = data.results || [];

  if (stories.length === 0) {
    results.innerHTML = '<div class="news-card">No intelligence found for this query.</div>';
    return;
  }

  // Update sources counter with real number
  const srcEl = document.getElementById("srcCount");
  if (srcEl && data.total_articles) {
    srcEl.textContent = data.total_articles;
  }

  let high = 0, medium = 0, low = 0;
  stories.forEach(s => {
    const c = (s.confidence || "").toUpperCase();
    if (c === "HIGH") high++;
    else if (c === "MEDIUM") medium++;
    else low++;
  });

  let html = `
    <div class="panel">
      <div class="panel-title">// INTELLIGENCE REPORT — ${data.total_articles || 0} ARTICLES // ${data.total_stories || 0} STORIES</div>
      <div style="display:flex; gap:20px; justify-content:flex-end; font-size:13px; margin-top:8px;">
        <span class="green">✅ HIGH: ${high}</span>
        <span class="amber">⚠️ MEDIUM: ${medium}</span>
        <span class="red">🔴 LOW: ${low}</span>
        <span style="color:#ff6600;">⚡ CONTRADICTIONS: ${(data.contradictions || []).length}</span>
      </div>
      ${(data.contradictions || []).length ? `
      <div style="margin-top:10px; border-top:1px solid #0d4a33; padding-top:8px;">
        ${data.contradictions.map(c => `
          <div style="border-left:3px solid #ff6600; padding:6px 10px; margin:6px 0; background:#1a0e05; font-size:12px; color:#ddd;">
            <span style="color:#ff6600; font-weight:bold;">⚡ ${c.conflict || "conflicting claims"}</span>
            <span style="color:#666; font-size:10px; margin-left:6px;">[${(c.method || "keyword").toUpperCase()} JUDGE]</span>
            <div style="color:#aaa; margin-top:3px;">“${c.story1}” <span style="color:#ff6600;">vs</span> “${c.story2}”</div>
          </div>`).join("")}
      </div>` : ""}
    </div>`;

  stories.forEach(story => {
    const conf = (story.confidence || "medium").toLowerCase();
    const sources = story.sources || [];
    const articles = story.articles || [];

    html += `
      <div class="news-card ${conf}">
        <div class="news-title">${story.titles ? story.titles[0] : "Story"}</div>
        <div class="news-meta">
          <span class="badge ${conf}">${conf.toUpperCase()}</span>
          | ${story.verdict || ""}
          | 📡 ${story.source_count || sources.length} SOURCES
          | 🛡️ TRUST: ${story.trust_score ?? 0}
          <button class="why-btn" onclick="toggleWhy(this)">WHY?</button>
        </div>
        ${whyPanel(story)}
        <div style="margin-top:10px;">`;

    articles.forEach(a => {
      const content = (a.content || "").slice(0, 250);
      html += `
        <div style="border-left:2px solid #0d4a33; padding:8px 12px; margin:8px 0; background:#0a1a0a;">
          <div style="color:#00ff9c; font-size:13px; font-weight:bold;">${a.title || "Untitled"}</div>
          <div style="color:#888; font-size:11px;">📡 ${a.source || ""} ${a.url ? `| <a href="${a.url}" target="_blank" style="color:#4fd1ff;">READ SOURCE</a>` : ""}</div>
          <div style="color:#ccc; font-size:12px; margin-top:4px;">${content}...</div>
        </div>`;
    });

    html += `</div></div>`;
  });

  results.innerHTML = html;
  updateTicker(stories);
}

// ───── COUNTRIES ─────
const countrySelect = document.getElementById("countrySelect");
if (countrySelect) {
  countrySelect.addEventListener("change", async () => {
    const country = countrySelect.value;
    if (!country) return;
    const results = document.getElementById("countryResults");
    results.innerHTML = '<div class="loading">Decrypting military dossier</div>';

    try {
      const res = await apiFetch(`${API_BASE}/country/${encodeURIComponent(country)}`);
      const data = await res.json();
      renderCountry(data);
    } catch (err) {
      results.innerHTML = `<div class="news-card low">❌ Error: ${err.message}</div>`;
    }
  });
}

function renderCountry(p) {
  const results = document.getElementById("countryResults");

  // Clean fighters/tanks data
  let fighters = p.fighters || "N/A";
  if (fighters.includes("Stock:")) fighters = fighters.split("Stock:")[1].split("\n")[0].trim();

  let tanks = p.tanks || "N/A";
  if (tanks.includes("Stock:")) tanks = tanks.split("Stock:")[1].split("\n")[0].trim();

  results.innerHTML = `
    <div class="panel">
      <div class="panel-title">${getFlag(p.country)} // ${(p.country||"").toUpperCase()} — MILITARY DOSSIER</div>
      <div style="color:#cccccc; font-size:13px; margin-bottom:16px; line-height:1.6;">
        ${p.military_summary || ""}
      </div>

      <div class="stat-grid" style="grid-template-columns:repeat(3,1fr); margin-bottom:12px;">
        <div class="stat-box"><div class="stat-label">🪖 ARMY</div><div class="stat-val green">${p.army_strength||"N/A"}</div></div>
        <div class="stat-box"><div class="stat-label">⚓ NAVY</div><div class="stat-val cyan">${p.navy_strength||"N/A"}</div></div>
        <div class="stat-box"><div class="stat-label">✈️ AIRFORCE</div><div class="stat-val amber">${p.airforce_strength||"N/A"}</div></div>
        <div class="stat-box"><div class="stat-label">💰 BUDGET</div><div class="stat-val" style="color:#ffd700;font-size:16px;">${p.defense_budget||"N/A"}</div></div>
        <div class="stat-box"><div class="stat-label">🏆 RANK${p.global_rank_basis ? " (SPEND)" : ""}</div><div class="stat-val red">${p.global_rank && p.global_rank !== "N/A" ? "#" + p.global_rank : "N/A"}</div></div>
        <div class="stat-box"><div class="stat-label">👥 ACTIVE</div><div class="stat-val green" style="font-size:16px;">${p.active_personnel||"N/A"}</div></div>
      </div>
      <div style="color:#3a7a5c; font-size:10px; margin:-4px 0 12px; line-height:1.5;">
        📊 ${p.data_source || "source unknown"}${p.data_provenance && p.data_provenance.fetched_at ? " · dataset fetched " + p.data_provenance.fetched_at.slice(0,10) : ""}
        ${p.defense_budget_gdp_pct ? " · " + p.defense_budget_gdp_pct : ""}
        ${p.estimates_note ? "<br>ℹ️ " + p.estimates_note : ""}
      </div>

      <div class="stat-grid" style="grid-template-columns:repeat(4,1fr); margin-bottom:16px;">
        <div class="stat-box" style="cursor:pointer;" onclick="loadWeapons('${p.country}','fighter_jets',this)">
          <div class="stat-label">✈️ FIGHTERS</div>
          <div class="stat-val cyan">${fighters}</div>
          <div style="color:#3a7a5c;font-size:10px;margin-top:4px;">CLICK FOR DETAILS</div>
        </div>
        <div class="stat-box" style="cursor:pointer;" onclick="loadWeapons('${p.country}','tanks',this)">
          <div class="stat-label">🚂 TANKS</div>
          <div class="stat-val amber">${tanks}</div>
          <div style="color:#3a7a5c;font-size:10px;margin-top:4px;">CLICK FOR DETAILS</div>
        </div>
        <div class="stat-box" style="cursor:pointer;" onclick="loadWeapons('${p.country}','submarines',this)">
          <div class="stat-label">🤿 SUBMARINES</div>
          <div class="stat-val green">${p.submarines||"N/A"}</div>
          <div style="color:#3a7a5c;font-size:10px;margin-top:4px;">CLICK FOR DETAILS</div>
        </div>
        <div class="stat-box" style="cursor:pointer;" onclick="loadWeapons('${p.country}','missiles',this)">
          <div class="stat-label">🚀 MISSILES</div>
          <div class="stat-val red">CLASSIFIED</div>
          <div style="color:#3a7a5c;font-size:10px;margin-top:4px;">CLICK FOR DETAILS</div>
        </div>
      </div>

      <div style="display:flex; gap:10px; flex-wrap:wrap;">
        <button class="btn-primary" onclick="loadSpecialForces('${p.country}')">🕵️ SPECIAL FORCES</button>
        <button class="btn-primary" style="background:#4fd1ff; color:#03060a;" onclick="loadWeapons('${p.country}','warships',null)">🛳️ WARSHIPS</button>
      </div>
    </div>

    <!-- Notable Facts -->
    ${p.notable_facts && p.notable_facts.length ? `
    <div class="panel" style="margin-top:12px;">
      <div class="panel-title">// NOTABLE FACTS</div>
      ${p.notable_facts.map(f => `
        <div style="border-left:2px solid #0d4a33; padding:6px 12px; margin:6px 0; color:#cccccc; font-size:13px;">▸ ${f}</div>
      `).join("")}
    </div>` : ""}

    <!-- Weapon/Forces Detail Area -->
    <div id="weaponDetail" style="margin-top:12px;"></div>
  `;
}

// Grounding tag for LLM-generated items (weapons, special forces)
function groundingTag(item) {
  if (item && item.source_url) {
    return `<a href="${item.source_url}" target="_blank" rel="noopener" style="color:#4fd1ff; font-size:10px; margin-left:6px;">📖 WIKIPEDIA</a>`;
  }
  return `<span style="color:#ffb300; font-size:10px; margin-left:6px; border:1px solid #ffb30055; padding:1px 5px; border-radius:3px;">AI-GENERATED · UNVERIFIED</span>`;
}

// Load weapons popup
async function loadWeapons(country, category, clickedEl) {
  const detail = document.getElementById("weaponDetail");
  detail.innerHTML = '<div class="loading">Decrypting classified arsenal</div>';

  // Scroll to detail
  detail.scrollIntoView({ behavior: "smooth" });

  try {
    const res = await apiFetch(`${API_BASE}/weapons/${encodeURIComponent(country)}/${category}`);
    const data = await res.json();
    const items = data.data || [];

    const icons = {
      missiles: "🚀", submarines: "🤿",
      fighter_jets: "✈️", tanks: "🚂",
      warships: "🛳️"
    };

    const g = data.grounding || {};
    let html = `
      <div class="panel">
        <div class="panel-title">${icons[category]||"⚔️"} ${country.toUpperCase()} — ${category.replace("_"," ").toUpperCase()}</div>
        <div style="color:#3a7a5c; font-size:10px; margin:4px 0 8px;">
          🤖 AI-generated list · ${g.grounded ?? 0}/${g.total ?? items.length} verified against Wikipedia · unverified items are marked
        </div>`;

    items.forEach(item => {
      html += `
        <div style="border-left:3px solid ${item.grounded ? "#00ff9c" : "#ffb300"}; padding:10px 14px; margin:10px 0; background:#0a1a0a; border-radius:0 8px 8px 0;">
          <div style="color:#00ff9c; font-weight:bold; font-size:14px;">${item.name||"Unknown"} ${groundingTag(item)}</div>
          <div style="color:#888; font-size:11px; margin:4px 0;">
            ${item.year ? "📅 "+item.year : ""}
            ${item.type ? " | 🎯 "+item.type : ""}
            ${item.range ? " | 📡 Range: "+item.range : ""}
            ${item.role ? " | ⚡ "+item.role : ""}
            ${item.patrol_areas ? " | 🌊 "+item.patrol_areas : ""}
          </div>
          <div style="color:#cccccc; font-size:12px; margin-top:6px; line-height:1.5;">${item.history||""}</div>
        </div>`;
    });

    html += `</div>`;
    detail.innerHTML = html;

  } catch (err) {
    detail.innerHTML = `<div class="news-card low">❌ Error: ${err.message}</div>`;
  }
}

// Load special forces
async function loadSpecialForces(country) {
  const detail = document.getElementById("weaponDetail");
  detail.innerHTML = '<div class="loading">Accessing classified personnel files</div>';
  detail.scrollIntoView({ behavior: "smooth" });

  try {
    const res = await apiFetch(`${API_BASE}/special-forces/${encodeURIComponent(country)}`);
    const data = await res.json();
    const forces = data.forces || [];

    let html = `
      <div class="panel">
        <div class="panel-title">🕵️ ${country.toUpperCase()} — SPECIAL FORCES & INTELLIGENCE</div>`;

    const g = data.grounding || {};
    html += `<div style="color:#3a7a5c; font-size:10px; margin:4px 0 8px;">
          🤖 AI-generated list · ${g.grounded ?? 0}/${g.total ?? forces.length} verified against Wikipedia · unverified items are marked
        </div>`;
    forces.forEach(f => {
      // legacy cache entries were plain strings; new ones are objects
      const isObj = f && typeof f === "object";
      const label = isObj ? `${f.emoji || "⚔️"} <b style="color:#4fd1ff;">${f.name || ""}</b> — ${f.description || ""} ${groundingTag(f)}` : f;
      html += `
        <div style="border-left:3px solid ${isObj && f.grounded ? "#4fd1ff" : "#ffb300"}; padding:8px 12px; margin:8px 0; background:#050f1a; border-radius:0 8px 8px 0; color:#cccccc; font-size:13px;">
          ${label}
        </div>`;
    });

    html += `</div>`;
    detail.innerHTML = html;

  } catch (err) {
    detail.innerHTML = `<div class="news-card low">❌ Error: ${err.message}</div>`;
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
      results.innerHTML = `<div class="news-card low">❌ Error: ${err.message}</div>`;
    }
  });
}

function renderLeaders(data) {
  const results = document.getElementById("leaderResults");
  const statements = data.statements || [];

  if (statements.length === 0) {
    results.innerHTML = '<div class="news-card">No statements found.</div>';
    return;
  }

  let html = `<div class="panel"><div class="panel-title">// ${statements.length} WORLD LEADER STATEMENTS INTERCEPTED</div></div>`;

  statements.forEach((s, index) => {
    const sentiment = (s.sentiment || "neutral").toLowerCase();
    const sentimentColors = {
      aggressive: "#ff4d6d",
      diplomatic: "#00ff9c",
      neutral: "#ffb300",
      warning: "#ff6600"
    };
    const color = sentimentColors[sentiment] || "#00ff9c";

    html += `
      <div class="leader-card" onclick="openLeaderModal(${index})">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div>
            <div style="color:#ffffff; font-size:15px; font-weight:bold;">
              👤 ${s.leader || "Unknown"} — ${s.role || ""}
            </div>
            <div style="color:#cccccc; font-style:italic; font-size:13px; margin:8px 0;">
              "${s.statement || ""}"
            </div>
          </div>
          <span style="color:${color}; font-size:11px; font-weight:bold; letter-spacing:1px; white-space:nowrap; margin-left:12px;">
            ${(s.sentiment||"").toUpperCase()}
          </span>
        </div>
        <div style="color:#3a7a5c; font-size:11px; margin-top:6px;">
          📡 ${s.source || ""} | 🖱️ CLICK FOR FULL INTEL
        </div>
      </div>`;
  });

  results.innerHTML = html;

  // Store statements globally for modal access
  window._leaderStatements = statements;
}

function openLeaderModal(index) {
  const s = window._leaderStatements[index];
  if (!s) return;

  const sentiment = (s.sentiment || "neutral").toLowerCase();

  // Create modal
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.id = "leaderModal";

  overlay.innerHTML = `
    <div class="modal-box">
      <button class="modal-close" onclick="closeModal()">✕ CLOSE</button>

      <div class="modal-leader-name">👤 ${s.leader || "Unknown"}</div>
      <div class="modal-role">${s.role || ""}</div>

      <span class="sentiment-badge sentiment-${sentiment}">
        ${(s.sentiment || "NEUTRAL").toUpperCase()}
      </span>

      <div class="modal-section-title">// INTERCEPTED STATEMENT</div>
      <div class="modal-statement">"${s.statement || ""}"</div>

      <div class="modal-section-title">// CONTEXT & BACKGROUND</div>
      <div class="modal-context">${s.context || "No additional context available."}</div>

      <div class="modal-section-title">// SOURCE</div>
      <div style="color:#4fd1ff; font-size:12px; margin-bottom:16px;">
        📡 ${s.source || "Unknown source"}
      </div>

      <div class="modal-section-title">// AI ANALYSIS</div>
      <div class="modal-analysis" id="modalAnalysis">
        <span class="loading">Analyzing statement</span>
      </div>
    </div>`;

  document.body.appendChild(overlay);

  // Close on overlay click
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeModal();
  });

  // Load AI analysis
  loadLeaderAnalysis(s);
}

async function loadLeaderAnalysis(s) {
  const analysisEl = document.getElementById("modalAnalysis");
  if (!analysisEl) return;

  try {
    const res = await apiFetch(`${API_BASE}/leader-analysis`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        leader: s.leader,
        role: s.role,
        statement: s.statement,
        context: s.context,
        sentiment: s.sentiment
      })
    });
    const data = await res.json();
    analysisEl.innerHTML = data.analysis || "Analysis unavailable.";
  } catch (err) {
    analysisEl.innerHTML = "Analysis unavailable — check API connection.";
  }
}

function closeModal() {
  const modal = document.getElementById("leaderModal");
  if (modal) modal.remove();
}

// ───── COMPARE ─────
const compareBtn = document.getElementById("compareBtn");
if (compareBtn) {
  compareBtn.addEventListener("click", async () => {
    const c1 = document.getElementById("compare1").value;
    const c2 = document.getElementById("compare2").value;
    if (!c1 || !c2) return;
    if (c1 === c2) {
      alert("Select two different countries!");
      return;
    }
    const results = document.getElementById("compareResults");
    results.innerHTML = '<div class="loading">Analyzing military balance</div>';

    try {
      const [r1, r2] = await Promise.all([
        apiFetch(`${API_BASE}/country/${encodeURIComponent(c1)}`).then(r => r.json()),
        apiFetch(`${API_BASE}/country/${encodeURIComponent(c2)}`).then(r => r.json())
      ]);
      await renderCompare(r1, r2);
    } catch (err) {
      results.innerHTML = `<div class="news-card low">❌ Error: ${err.message}</div>`;
    }
  });
}

async function renderCompare(a, b) {
  const results = document.getElementById("compareResults");

  // AI Winner Analysis
  let winnerHtml = "";
  try {
    const res = await apiFetch(`${API_BASE}/compare-analysis`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ country1: a, country2: b })
    });
    const data = await res.json();
    winnerHtml = `
      <div class="panel" style="border-color:#ffd700; margin-top:14px;">
        <div class="panel-title" style="color:#ffd700;">// AI MILITARY ANALYSIS</div>
        <div style="color:#cccccc; font-size:13px; line-height:1.6;">${data.analysis || ""}</div>
      </div>`;
  } catch(e) {}

  results.innerHTML = `
    <div class="grid-2">
      <div class="panel" style="border-color:#4fd1ff;">
        <div class="panel-title" style="color:#4fd1ff;">🔵 ${getFlag(a.country)} ${(a.country||"").toUpperCase()}</div>
        <div class="stat-box" style="margin-bottom:8px;"><div class="stat-label">🪖 ARMY</div><div class="stat-val green">${a.army_strength||"N/A"}</div></div>
        <div class="stat-box" style="margin-bottom:8px;"><div class="stat-label">⚓ NAVY</div><div class="stat-val cyan">${a.navy_strength||"N/A"}</div></div>
        <div class="stat-box" style="margin-bottom:8px;"><div class="stat-label">✈️ AIRFORCE</div><div class="stat-val amber">${a.airforce_strength||"N/A"}</div></div>
        <div class="stat-box" style="margin-bottom:8px;"><div class="stat-label">💰 BUDGET</div><div class="stat-val" style="color:#ffd700; font-size:14px;">${a.defense_budget||"N/A"}</div></div>
        <div class="stat-box"><div class="stat-label">🏆 RANK</div><div class="stat-val red">#${a.global_rank||"N/A"}</div></div>
      </div>
      <div class="panel" style="border-color:#ff4d6d;">
        <div class="panel-title" style="color:#ff4d6d;">🔴 ${getFlag(b.country)} ${(b.country||"").toUpperCase()}</div>
        <div class="stat-box" style="margin-bottom:8px;"><div class="stat-label">🪖 ARMY</div><div class="stat-val green">${b.army_strength||"N/A"}</div></div>
        <div class="stat-box" style="margin-bottom:8px;"><div class="stat-label">⚓ NAVY</div><div class="stat-val cyan">${b.navy_strength||"N/A"}</div></div>
        <div class="stat-box" style="margin-bottom:8px;"><div class="stat-label">✈️ AIRFORCE</div><div class="stat-val amber">${b.airforce_strength||"N/A"}</div></div>
        <div class="stat-box" style="margin-bottom:8px;"><div class="stat-label">💰 BUDGET</div><div class="stat-val" style="color:#ffd700; font-size:14px;">${b.defense_budget||"N/A"}</div></div>
        <div class="stat-box"><div class="stat-label">🏆 RANK</div><div class="stat-val red">#${b.global_rank||"N/A"}</div></div>
      </div>
    </div>
    ${winnerHtml}`;
}

// ───── WORLD MAP ─────
let map = null;
let newsMarkers = [];

// Live story markers (populated from /recent by plotStories) — replaces the old hardcoded zone list
let storyLayer = null;

function initMap() {
  if (map) return;

  map = L.map("worldMap", {
    center: [28, 35],
    zoom: 3,
    zoomControl: true,
    attributionControl: false
  });

  // Dark military map tiles
  L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    { maxZoom: 18, subdomains: "abcd" }
  ).addTo(map);

  storyLayer = L.layerGroup().addTo(map);
  plotStories(window.__lastStories || []);

  // One resize pass after layout settles (container is already visible at this point)
  setTimeout(() => map.invalidateSize(true), 300);
  updateThreatBars();
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

// ───── LIVE MAP MARKERS ─────
function plotStories(stories) {
  if (!map || !storyLayer) return;
  storyLayer.clearLayers();
  const empty = document.getElementById("mapEmpty");
  const geo = stories.filter(s => s.geo && typeof s.geo.lat === "number");
  if (empty) empty.style.display = geo.length ? "none" : "flex";
  if (!geo.length) return;

  // group by country so 5 stories about one place become one bigger marker
  const byCountry = {};
  geo.forEach(s => { (byCountry[s.geo.country] = byCountry[s.geo.country] || { geo: s.geo, stories: [] }).stories.push(s); });

  const colorFor = c => c === "HIGH" ? "#00ff9c" : c === "MEDIUM" ? "#ffb300" : "#ff4d6d";
  Object.values(byCountry).forEach(({ geo: g, stories: list }) => {
    const top = list.reduce((a, b) => rank(b.confidence) > rank(a.confidence) ? b : a, list[0]);
    const color = colorFor((top.confidence || "").toUpperCase());
    const radius = Math.min(6 + list.length * 3, 18);
    const items = list.slice(0, 5).map(s => {
      const a = (s.articles || [])[0] || {};
      return `<div style="margin:4px 0;">
        <span style="color:${colorFor((s.confidence||"").toUpperCase())}; font-weight:bold; font-size:10px;">${(s.confidence||"").toUpperCase()}</span>
        <span style="color:#ddd; font-size:11px;">${s.titles ? s.titles[0] : ""}</span>
        ${a.url ? `<a href="${a.url}" target="_blank" rel="noopener" style="color:#4fd1ff; font-size:10px; margin-left:4px;">↗</a>` : ""}
      </div>`;
    }).join("");
    L.circleMarker([g.lat, g.lng], { radius, color, fillColor: color, fillOpacity: 0.55, weight: 2 })
      .addTo(storyLayer)
      .bindPopup(`
        <div style="background:#06100c; color:#fff; font-family:'Courier New',monospace; padding:10px; border:1px solid ${color}; border-radius:4px; min-width:240px;">
          <div style="color:${color}; font-weight:bold; font-size:13px; margin-bottom:4px;">${g.country} · ${list.length} stor${list.length === 1 ? "y" : "ies"}</div>
          ${items}${list.length > 5 ? `<div style="color:#666; font-size:10px;">+${list.length - 5} more</div>` : ""}
        </div>`);
  });
}
function rank(c) { return { HIGH: 3, MEDIUM: 2, LOW: 1 }[(c || "").toUpperCase()] || 0; }

// ───── INTEL FEED + SYSTEM STATS (real data from cached searches) ─────
let intelItems = [
  { level: "low", text: "[SYS] No intel cached yet — run a search in NEWS FEED" },
];

async function loadSystemStats() {
  const src = document.getElementById("srcCount");
  const ver = document.getElementById("verifiedPct");
  try {
    const res = await apiFetch(`${API_BASE}/recent`);
    const data = await res.json();
    const searches = data.searches || [];
    const stories = [];
    searches.forEach(s => (s.results || []).forEach(st => stories.push(st)));

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
}

let intelIndex = 0;
function updateIntelFeed() {
  const feed = document.getElementById("intelFeed");
  if (!feed) return;
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
  radarAngle = (radarAngle + 2) % 360;
  const sweep = document.getElementById("radarSweep");
  if (sweep) {
    sweep.style.transform = `rotate(${radarAngle}deg)`;
  }
  requestAnimationFrame(animateRadar);
}
animateRadar();

// ───── NEWS TICKER UPDATE ─────
function updateTicker(stories) {
  const ticker = document.getElementById("tickerContent");
  if (!ticker || !stories || !stories.length) return;

  let text = "";
  stories.forEach(story => {
    const conf = (story.confidence || "").toUpperCase();
    const title = story.titles ? story.titles[0] : "";
    text += ` ⚡ [${conf}] ${title} — `;
  });
  ticker.textContent = text;
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
  let html = "";

  nuclearData.forEach(n => {
    const pct = (n.warheads / max * 100).toFixed(1);
    const color = n.warheads > 1000 ? "#ff4d6d" :
                  n.warheads > 200 ? "#ffb300" : "#00ff9c";
    html += `
      <div style="display:flex; align-items:center; gap:12px; margin:10px 0;">
        <div style="width:160px; color:#fff; font-size:13px; white-space:nowrap;">
          ${n.flag} ${n.country}
        </div>
        <div style="flex:1; height:18px; background:#0d2a1f; border-radius:4px; overflow:hidden;">
          <div style="width:${pct}%; height:100%; background:${color};
                      box-shadow:0 0 10px ${color}; border-radius:4px;
                      transition:width 1.5s ease;"></div>
        </div>
        <div style="width:70px; color:${color}; font-size:14px;
                    font-weight:bold; text-align:right;">
          ${n.warheads.toLocaleString()}
        </div>
      </div>`;
  });
  bars.innerHTML = html;

  // Triad list
  const triad = document.getElementById("triadList");
  triad.innerHTML = nuclearData.filter(n => n.triad).map(n => `
    <div style="border-left:3px solid #ff4d6d; padding:8px 12px; margin:8px 0;
                background:#1a0a0a; color:#fff; font-size:13px;">
      ${n.flag} <b>${n.country}</b>
      <div style="color:#888; font-size:11px; margin-top:2px;">
        ☢️ Land + Sea + Air launch capability
      </div>
    </div>`).join("");

  // Treaty list
  const treaty = document.getElementById("treatyList");
  treaty.innerHTML = nuclearData.map(n => `
    <div style="display:flex; justify-content:space-between; padding:6px 0;
                border-bottom:1px solid #0d2a1f; font-size:12px;">
      <span style="color:#fff;">${n.flag} ${n.country}</span>
      <span style="color:#888;">${n.treaty}</span>
    </div>`).join("");
}


// ───── ALLIANCES ─────
const alliances = [
  {
    name: "NATO",
    color: "#4fd1ff",
    hq: "Brussels, Belgium",
    members: 32,
    keyMembers: "🇺🇸 USA, 🇬🇧 UK, 🇫🇷 France, 🇩🇪 Germany, 🇹🇷 Turkey, 🇵🇱 Poland",
    info: "North Atlantic Treaty Organization. Article 5: attack on one = attack on all.",
    coords: [[50.85, 4.35], [38.9, -77.0], [51.5, -0.1], [48.85, 2.35], [52.5, 13.4], [39.9, 32.8]]
  },
  {
    name: "CSTO",
    color: "#ff4d6d",
    hq: "Moscow, Russia",
    members: 6,
    keyMembers: "🇷🇺 Russia, 🇧🇾 Belarus, 🇰🇿 Kazakhstan, 🇦🇲 Armenia",
    info: "Collective Security Treaty Organization. Russia-led security bloc.",
    coords: [[55.75, 37.6], [53.9, 27.5], [51.1, 71.4], [40.18, 44.5]]
  },
  {
    name: "SCO",
    color: "#ffb300",
    hq: "Beijing, China",
    members: 10,
    keyMembers: "🇨🇳 China, 🇷🇺 Russia, 🇮🇳 India, 🇵🇰 Pakistan, 🇮🇷 Iran",
    info: "Shanghai Cooperation Organisation. Eurasian political-military bloc.",
    coords: [[39.9, 116.4], [55.75, 37.6], [28.6, 77.2], [33.7, 73.0], [35.7, 51.4]]
  },
  {
    name: "QUAD",
    color: "#00ff9c",
    hq: "Informal alliance",
    members: 4,
    keyMembers: "🇺🇸 USA, 🇮🇳 India, 🇯🇵 Japan, 🇦🇺 Australia",
    info: "Quadrilateral Security Dialogue. Indo-Pacific strategic forum.",
    coords: [[38.9, -77.0], [28.6, 77.2], [35.7, 139.7], [-35.3, 149.1]]
  },
];

let allianceMapObj = null;

function renderAlliances() {
  // Cards
  const cards = document.getElementById("allianceCards");
  if (cards && !cards.children.length) {
    cards.innerHTML = alliances.map(a => `
      <div class="panel" style="border-color:${a.color};">
        <div class="panel-title" style="color:${a.color};">// ${a.name} — ${a.members} MEMBERS</div>
        <div style="color:#fff; font-size:13px; margin-bottom:6px;">${a.keyMembers}</div>
        <div style="color:#888; font-size:12px; line-height:1.5;">${a.info}</div>
        <div style="color:#3a7a5c; font-size:11px; margin-top:8px;">📍 HQ: ${a.hq}</div>
      </div>`).join("");
  }

  // Map
  if (allianceMapObj) return;
  allianceMapObj = L.map("allianceMap", {
    center: [35, 40], zoom: 2, attributionControl: false
  });
  L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    { maxZoom: 18, subdomains: "abcd" }
  ).addTo(allianceMapObj);

  alliances.forEach(a => {
    a.coords.forEach(c => {
      L.circleMarker(c, {
        radius: 7, color: a.color, fillColor: a.color,
        fillOpacity: 0.8, weight: 2
      }).addTo(allianceMapObj).bindPopup(
        `<b style="color:${a.color};">${a.name}</b>`
      );
    });
  });

  setTimeout(() => allianceMapObj.invalidateSize(true), 300);
}


// (map is initialised in runBoot() once #mainApp is visible)