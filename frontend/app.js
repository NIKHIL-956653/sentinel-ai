// ───── CONFIG ─────
const API_BASE = "http://127.0.0.1:8000/api/v1";

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
    const res = await fetch(`${API_BASE}/news`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query })
    });
    const data = await res.json();
    renderNews(data);
  } catch (err) {
    results.innerHTML = `<div class="news-card low">❌ Connection Error: ${err.message}<br><br>Make sure FastAPI backend is running!</div>`;
  }
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
          | 📡 ${story.source_count || sources.length} SOURCES
          | 🛡️ TRUST: ${story.trust_score || 0}
        </div>
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
      const res = await fetch(`${API_BASE}/country/${encodeURIComponent(country)}`);
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
        <div class="stat-box"><div class="stat-label">🏆 GLOBAL RANK</div><div class="stat-val red">#${p.global_rank||"N/A"}</div></div>
        <div class="stat-box"><div class="stat-label">👥 ACTIVE</div><div class="stat-val green">${p.active_personnel||"N/A"}</div></div>
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

// Load weapons popup
async function loadWeapons(country, category, clickedEl) {
  const detail = document.getElementById("weaponDetail");
  detail.innerHTML = '<div class="loading">Decrypting classified arsenal</div>';

  // Scroll to detail
  detail.scrollIntoView({ behavior: "smooth" });

  try {
    const res = await fetch(`${API_BASE}/weapons/${encodeURIComponent(country)}/${category}`);
    const data = await res.json();
    const items = data.data || [];

    const icons = {
      missiles: "🚀", submarines: "🤿",
      fighter_jets: "✈️", tanks: "🚂",
      warships: "🛳️"
    };

    let html = `
      <div class="panel">
        <div class="panel-title">${icons[category]||"⚔️"} ${country.toUpperCase()} — ${category.replace("_"," ").toUpperCase()}</div>`;

    items.forEach(item => {
      html += `
        <div style="border-left:3px solid #00ff9c; padding:10px 14px; margin:10px 0; background:#0a1a0a; border-radius:0 8px 8px 0;">
          <div style="color:#00ff9c; font-weight:bold; font-size:14px;">${item.name||"Unknown"}</div>
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
    const res = await fetch(`${API_BASE}/special-forces/${encodeURIComponent(country)}`);
    const data = await res.json();
    const forces = data.forces || [];

    let html = `
      <div class="panel">
        <div class="panel-title">🕵️ ${country.toUpperCase()} — SPECIAL FORCES & INTELLIGENCE</div>`;

    forces.forEach(f => {
      html += `
        <div style="border-left:3px solid #4fd1ff; padding:8px 12px; margin:8px 0; background:#050f1a; border-radius:0 8px 8px 0; color:#cccccc; font-size:13px;">
          ${f}
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
      const res = await fetch(`${API_BASE}/leaders`);
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
    const res = await fetch(`${API_BASE}/leader-analysis`, {
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
        fetch(`${API_BASE}/country/${encodeURIComponent(c1)}`).then(r => r.json()),
        fetch(`${API_BASE}/country/${encodeURIComponent(c2)}`).then(r => r.json())
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
    const res = await fetch(`${API_BASE}/compare-analysis`, {
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

// Conflict zones with coordinates
const conflictZones = [
  // 🔴 ACTIVE WAR ZONES
  { lat: 49.0, lng: 31.0, name: "Ukraine — Russia War", level: "high", radius: 500000, info: "Active war since Feb 2022. Russian forces vs Ukrainian Armed Forces." },
  { lat: 31.5, lng: 34.8, name: "Gaza — Israel War", level: "high", radius: 80000, info: "Active military operations. IDF vs Hamas since Oct 2023." },
  { lat: 32.5, lng: 53.0, name: "Iran — US/Israel Conflict", level: "high", radius: 600000, info: "US + Israeli strikes on Iran began Feb 2026. Active conflict." },
  { lat: 33.5, lng: 35.8, name: "Lebanon — Israel Border", level: "high", radius: 150000, info: "Cross-border military activity. Hezbollah vs IDF." },
  { lat: 15.0, lng: 42.0, name: "Yemen — Houthi War", level: "high", radius: 300000, info: "Houthi forces attacking Red Sea shipping. US/UK strikes ongoing." },
  { lat: 15.5, lng: 32.5, name: "Sudan Civil War", level: "high", radius: 400000, info: "SAF vs RSF civil war. Humanitarian crisis ongoing." },

  // 🟡 ELEVATED TENSION ZONES
  { lat: 23.5, lng: 120.0, name: "Taiwan Strait", level: "medium", radius: 200000, info: "PLA military exercises near Taiwan. High tension." },
  { lat: 35.0, lng: 128.0, name: "Korean Peninsula", level: "medium", radius: 300000, info: "North Korea missile tests. DMZ tensions elevated." },
  { lat: 25.0, lng: 55.0, name: "UAE — Persian Gulf", level: "medium", radius: 200000, info: "Iranian drone/missile attacks on UAE infrastructure." },
  { lat: 24.0, lng: 45.0, name: "Saudi Arabia", level: "medium", radius: 300000, info: "Houthi missile attacks on Saudi territory ongoing." },
  { lat: 26.0, lng: 50.5, name: "Bahrain — Gulf", level: "medium", radius: 150000, info: "US 5th Fleet HQ. Regional tension monitoring." },
  { lat: 37.0, lng: 35.0, name: "Syria", level: "medium", radius: 250000, info: "Multiple factions. Israeli airstrikes. Turkish operations." },
];

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
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    { maxZoom: 18 }
  ).addTo(map);

  // Dark overlay
  L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    { maxZoom: 18, subdomains: "abcd", opacity: 0.9 }
  ).addTo(map);

  // Add conflict zones as colored regions
  conflictZones.forEach(zone => {
    const color = zone.level === "high" ? "#ff4d6d" :
                  zone.level === "medium" ? "#ffb300" : "#00ff9c";

    const opacity = zone.level === "high" ? 0.35 : 0.20;

    // Glowing circle region
    L.circle([zone.lat, zone.lng], {
      color: color,
      fillColor: color,
      fillOpacity: opacity,
      radius: zone.radius,
      weight: 2,
    }).addTo(map).bindPopup(`
      <div style="background:#06100c; color:#ffffff;
                  font-family:'Courier New',monospace;
                  padding:10px; border:1px solid ${color};
                  border-radius:4px; min-width:200px;">
        <div style="color:${color}; font-weight:bold;
                    font-size:13px; margin-bottom:6px;">
          ${zone.name}
        </div>
        <div style="color:#cccccc; font-size:11px;
                    line-height:1.5;">
          ${zone.info}
        </div>
        <div style="margin-top:6px;">
          <span style="background:${color}33; color:${color};
                       padding:2px 8px; border-radius:3px;
                       font-size:10px; font-weight:bold;">
            ${zone.level.toUpperCase()} ALERT
          </span>
        </div>
      </div>
    `);

    // Center dot
    L.circleMarker([zone.lat, zone.lng], {
      radius: zone.level === "high" ? 6 : 4,
      color: color,
      fillColor: color,
      fillOpacity: 1,
      weight: 2
    }).addTo(map);
  });

  // Fix grey area
  setTimeout(() => map.invalidateSize(), 300);
  updateThreatBars();

  // Force fix grey tiles
  setTimeout(() => {
    map.invalidateSize(true);
    map.setView([28, 35], 3);
  }, 500);

  setTimeout(() => {
    map.invalidateSize(true);
  }, 1000);

  setTimeout(() => {
    map.invalidateSize(true);
  }, 2000);
}

function updateThreatBars() {
  const high = conflictZones.filter(z => z.level === "high").length;
  const med = conflictZones.filter(z => z.level === "medium").length;
  const low = conflictZones.filter(z => z.level === "low").length;
  const total = conflictZones.length;

  setTimeout(() => {
    const hb = document.getElementById("highBar");
    const mb = document.getElementById("medBar");
    const lb = document.getElementById("lowBar");
    if (hb) hb.style.width = (high/total*100) + "%";
    if (mb) mb.style.width = (med/total*100) + "%";
    if (lb) lb.style.width = (low/total*100) + "%";
    const hn = document.getElementById("highNum");
    const mn = document.getElementById("medNum");
    const ln = document.getElementById("lowNum");
    if (hn) hn.textContent = high;
    if (mn) mn.textContent = med;
    if (ln) ln.textContent = low;
    const ac = document.getElementById("alertCount");
    if (ac) ac.textContent = high;
  }, 500);
}

// ───── INTEL FEED ─────
const intelItems = [
  { level: "high", text: "[HIGH] Reuters: Military movement detected near border" },
  { level: "medium", text: "[MED] BBC: Diplomatic talks scheduled for tomorrow" },
  { level: "high", text: "[HIGH] Al Jazeera: Airspace closure announced" },
  { level: "medium", text: "[MED] AP: Ceasefire negotiations ongoing" },
  { level: "high", text: "[HIGH] 3 sources confirm naval deployment" },
  { level: "low", text: "[LOW] Single source: Unverified troop movement" },
];

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

// Initialize map when home screen is active
document.querySelector('[data-screen="home"]').addEventListener("click", () => {
  setTimeout(initMap, 100);
});

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


// Init map on load
setTimeout(() => {
  initMap();
  setTimeout(() => { if(map) map.invalidateSize(true); }, 300);
  setTimeout(() => { if(map) map.invalidateSize(true); }, 800);
  setTimeout(() => { if(map) map.invalidateSize(true); }, 1500);
}, 500);