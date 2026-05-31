# SENTINEL 2.0 — Military Intelligence & OSINT Platform

> Open Source Intelligence platform that aggregates, verifies, and analyzes global military and geopolitical news using AI.

## Live Demo
> Deployed link coming soon — MongoDB Atlas + Render + Vercel

## What It Does
User searches "Russia Ukraine conflict"
↓
Tavily searches 10 trusted sources
(Reuters, BBC, Al Jazeera)
↓
AI verifier scores confidence
HIGH / MEDIUM / LOW
↓
Results shown with source links
Contradictions detected automatically!

## Features

### 📰 News Feed
- Real-time OSINT news aggregation
- AI confidence scoring (HIGH/MEDIUM/LOW)
- Contradiction detection across sources
- Source verification (Reuters, BBC, Al Jazeera)

### 🌍 Country Military Dossiers
- 90+ countries supported
- Army, Navy, Airforce, Budget, Global Rank
- Clickable weapon categories:
  - 🚀 Missiles (with history — BrahMos named after Brahmaputra + Moskva!)
  - 🤿 Submarines (patrol areas, class, year)
  - ✈️ Fighter Jets (variants, history)
  - 🚂 Tanks (combat history)
  - 🛳️ Warships (notable operations)
- 🕵️ Special Forces & Intelligence Units
- All generated dynamically by LLM + cached in MongoDB!

### 👤 World Leader Statements
- Real-time leader statement interception
- Sentiment analysis (Aggressive/Diplomatic/Neutral/Warning)
- Click any leader → Modal popup with full AI analysis
- Geopolitical context and assessment

### ⚔️ Military Comparison
- Select any 2 countries
- Side-by-side military stats
- AI-powered winner analysis

## Tech Stack

### Frontend (SENTINEL 2.0 Cinematic UI)
- Pure HTML + CSS + JavaScript
- Matrix rain background animation
- Animated boot sequence
- Glowing HUD panels
- No framework needed!

### Backend
- **FastAPI** — REST API backend
- **Tavily** — Real-time news search (K=10)
- **OpenRouter** — Gemini 2.0 Flash LLM
- **MongoDB** — Caching layer (1hr TTL for news)
- **LangChain Agents** — Collector + Verifier
- **Wikipedia** — Military profile data

### AI Pipeline
Collector Agent → Tavily search (K=10 sources)
↓
Verifier Agent → Confidence scoring
↓
MongoDB cache → Fast repeated queries
↓
LLM Analysis → Weapon details, leader analysis
↓
SENTINEL UI → Cinematic display

## Architecture
```
frontend/
├── index.html         → Cinematic UI structure
├── style.css          → HUD effects, matrix rain
└── app.js             → FastAPI integration
api/
├── main.py            → FastAPI app + CORS
└── routes/
├── news.py        → News search endpoint
└── country.py     → Country/weapons/leaders endpoints
agents/
├── collector_agent.py → Tavily news collector
└── verifier_agent.py  → AI confidence verifier
tools/
├── wikipedia_tool.py  → Military profiles
├── leader_tracker.py  → Leader statements
├── weapons_detail_tool.py → Weapon details (LLM)
└── special_forces_tool.py → Special forces (LLM)
```

## Setup

### 1. Clone
```bash
git clone https://github.com/NIKHIL-956653/sentinel-ai.git
cd sentinel-ai
```

### 2. Virtual environment
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Environment variables
OPENROUTER_API_KEY=your_key
TAVILY_API_KEY=your_key
MONGODB_URI=mongodb://localhost:27017

### 4. Run

**Terminal 1 — FastAPI:**
```bash
$env:PYTHONPATH = "C:\path\to\sentinel-ai"
python -m uvicorn api.main:app --reload
```

**Terminal 2 — Open frontend:**
```bash
cd frontend
start index.html
```

## Key Metrics
K=10 Tavily sources per query
1hr MongoDB TTL cache
90+ countries supported
4 weapon categories per country
Real-time leader sentiment analysis
OSINT only — public sources

## Confidence Scoring
HIGH   → 3+ sources corroborate
MEDIUM → 2 sources agree
LOW    → Single source only
CONTRADICTIONS → Sources disagree!

## Why SENTINEL?

> "In times of conflict, no one knows the truth.
> SENTINEL cross-references multiple public sources
> and uses AI to show you what's verified,
> what's uncertain, and what's contradicted."

Not affiliated with any government or intelligence agency.
Analyzes publicly available news for educational purposes.

## Author

**Nikhil Chandra Sairam Tokala**
AI/ML Engineer | GenAI Engineer | DevOps
Dubai, UAE
[LinkedIn](https://linkedin.com/in/nikhil-chandra-133ncsr200233) |
[GitHub](https://github.com/NIKHIL-956653)
