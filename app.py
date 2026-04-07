import streamlit as st
import requests
import json

# Theme definitions
THEMES = {
    "🟢 CIA Classic": {
        "bg": "#0a0a0a",
        "primary": "#00ff41",
        "secondary": "#111111",
        "text": "#ffffff",
        "border": "#00ff41",
        "card_bg": "#111111",
        "alert": "#00ff41"
    },
    "💻 Cyber Hacker": {
        "bg": "#000000",
        "primary": "#00bfff",
        "secondary": "#0a0a2e",
        "text": "#ffffff",
        "border": "#00bfff",
        "card_bg": "#0a0a2e",
        "alert": "#ff00ff"
    },
    "🚨 Red Alert": {
        "bg": "#0a0000",
        "primary": "#ff0000",
        "secondary": "#1a0000",
        "text": "#ffffff",
        "border": "#ff0000",
        "card_bg": "#1a0000",
        "alert": "#ff4444"
    },
    "📄 Classified": {
        "bg": "#000820",
        "primary": "#ffd700",
        "secondary": "#000d35",
        "text": "#ffffff",
        "border": "#ffd700",
        "card_bg": "#000d35",
        "alert": "#ffd700"
    },
    "🌧️ Matrix": {
        "bg": "#000000",
        "primary": "#00ff41",
        "secondary": "#001a00",
        "text": "#00ff41",
        "border": "#003300",
        "card_bg": "#001400",
        "alert": "#00ff41"
    },
    "⚡ Threat Level": {
        "bg": "#0a0a0a",
        "primary": "#ff6600",
        "secondary": "#1a0a00",
        "text": "#ffffff",
        "border": "#ff6600",
        "card_bg": "#1a0a00",
        "alert": "#ff0000"
    }
}

# Page config
st.set_page_config(
    page_title="SENTINEL AI",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Theme selector in MAIN page!
col_t1, col_t2, col_t3 = st.columns([1,2,1])
with col_t2:
    selected_theme = st.selectbox(
        "🎨 SELECT THEME",
        list(THEMES.keys()),
        index=0
    )

theme = THEMES[selected_theme]

# Dynamic CSS based on theme
st.markdown(f"""
<style>
    .stApp {{
        background-color: {theme['bg']};
        color: {theme['primary']};
    }}

    .main-header {{
        text-align: center;
        padding: 20px;
        border-bottom: 2px solid {theme['primary']};
        margin-bottom: 30px;
    }}

    .main-title {{
        font-size: 3em;
        font-weight: bold;
        color: {theme['primary']};
        font-family: 'Courier New', monospace;
        letter-spacing: 10px;
        text-shadow: 0 0 20px {theme['primary']};
    }}

    .sub-title {{
        color: #888888;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
        letter-spacing: 3px;
    }}

    .stTextInput input {{
        background-color: {theme['secondary']} !important;
        color: {theme['primary']} !important;
        border: 1px solid {theme['primary']} !important;
        border-radius: 5px !important;
        font-family: 'Courier New', monospace !important;
    }}

    .stButton button {{
        background-color: {theme['primary']} !important;
        color: {theme['bg']} !important;
        border: none !important;
        border-radius: 5px !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold !important;
        width: 100% !important;
    }}

    .stButton button:hover {{
        box-shadow: 0 0 15px {theme['primary']} !important;
    }}

    .story-card {{
        background-color: {theme['card_bg']};
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        font-family: 'Courier New', monospace;
    }}

    .high-conf {{
        border-left: 5px solid #00ff41;
        box-shadow: 0 0 15px rgba(0,255,65,0.2);
    }}

    .medium-conf {{
        border-left: 5px solid #ffff00;
        box-shadow: 0 0 15px rgba(255,255,0,0.2);
    }}

    .low-conf {{
        border-left: 5px solid #ff4444;
        box-shadow: 0 0 15px rgba(255,68,68,0.2);
    }}

    .stats-bar {{
        background-color: {theme['card_bg']};
        border: 1px solid {theme['border']};
        border-radius: 10px;
        padding: 15px;
        margin: 20px 0;
        font-family: 'Courier New', monospace;
        color: {theme['primary']};
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    /* Sidebar styling */
    .css-1d391kg {{
        background-color: {theme['secondary']} !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: {theme['secondary']} !important;
        border-right: 1px solid {theme['primary']} !important;
    }}

    section[data-testid="stSidebar"] * {{
        color: {theme['primary']} !important;
        font-family: 'Courier New', monospace !important;
    }}
</style>
""", unsafe_allow_html=True)


def show_news_ticker(stories: list):
    """Show scrolling news ticker"""

    if not stories:
        return

    # Build ticker text
    ticker_items = []
    for story in stories:
        conf = story.get("confidence", "LOW")
        title = story["titles"][0]

        if conf == "HIGH":
            emoji = "✅"
        elif conf == "MEDIUM":
            emoji = "⚠️"
        else:
            emoji = "🔴"

        ticker_items.append(f"{emoji} {title}")

    ticker_text = "     |     ".join(ticker_items)

    st.markdown(f"""
    <div style="
        background-color: #111111;
        border-top: 1px solid #00ff41;
        border-bottom: 1px solid #00ff41;
        padding: 10px 0;
        overflow: hidden;
        white-space: nowrap;
    ">
        <div style="
            display: inline-block;
            animation: scroll 30s linear infinite;
            color: #00ff41;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        ">
            🕵️ SENTINEL AI LIVE FEED &nbsp;&nbsp;&nbsp;
            {ticker_text} &nbsp;&nbsp;&nbsp;
            {ticker_text}
        </div>
    </div>

    <style>
        @keyframes scroll {{
            0%   {{ transform: translateX(100%); }}
            100% {{ transform: translateX(-100%); }}
        }}
    </style>
    """, unsafe_allow_html=True)


# Header
st.markdown(f"""
<div class="main-header">
    <div class="main-title">🕵️ SENTINEL AI</div>
    <div class="sub-title">
        MILITARY INTELLIGENCE & NEWS VERIFICATION PLATFORM
    </div>
    <div class="sub-title" style="color: {theme['primary']}; margin-top: 5px;">
        ● SYSTEM ONLINE | CLASSIFIED LEVEL: OPEN SOURCE
    </div>
</div>
""", unsafe_allow_html=True)

# Search Section
col1, col2 = st.columns([4, 1])

with col1:
    query = st.text_input(
        "",
        placeholder="🔍 Enter military/geopolitical query...",
        label_visibility="collapsed"
    )

with col2:
    search_btn = st.button("🔍 SEARCH INTEL")

# Divider
st.markdown("---")

# Search Logic
if search_btn and query:
    with st.spinner("🕵️ SENTINEL AI gathering intelligence..."):
        try:
            # Call FastAPI
            response = requests.post(
                "http://127.0.0.1:8000/api/v1/news",
                json={"query": query},
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()

                # Stats Bar
                st.markdown(f"""
                <div class="stats-bar">
                    📊 INTELLIGENCE REPORT |
                    Query: "{query}" |
                    Articles: {data['total_articles']} |
                    Stories: {data['total_stories']} |
                    Contradictions: {len(data['contradictions'])}
                </div>
                """, unsafe_allow_html=True)

                # Metrics
                results = data["results"]
                high = sum(1 for r in results
                          if r["confidence"] == "HIGH")
                medium = sum(1 for r in results
                            if r["confidence"] == "MEDIUM")
                low = sum(1 for r in results
                         if r["confidence"] == "LOW")

                m1, m2, m3, m4 = st.columns(4)

                with m1:
                    st.metric("✅ HIGH", high)
                with m2:
                    st.metric("⚠️ MEDIUM", medium)
                with m3:
                    st.metric("🔴 LOW", low)
                with m4:
                    st.metric(
                        "⚡ CONTRADICTIONS",
                        len(data['contradictions'])
                    )

                # News ticker
                show_news_ticker(results)
                st.markdown("---")

                st.markdown("### 📰 INTELLIGENCE FEED")

                # Display stories
                for i, story in enumerate(results):
                    conf = story["confidence"]
                    verdict = story.get("verdict", "UNKNOWN")
                    sources = ", ".join(story["sources"])
                    title = story["titles"][0]

                    # Card style
                    if conf == "HIGH":
                        card_class = "high-conf"
                        conf_emoji = "✅"
                    elif conf == "MEDIUM":
                        card_class = "medium-conf"
                        conf_emoji = "⚠️"
                    else:
                        card_class = "low-conf"
                        conf_emoji = "🔴"

                    if "DISPUTED" in verdict:
                        card_class = "disputed"
                        conf_emoji = "⚡"

                    st.markdown(f"""
                    <div class="story-card {card_class}">
                        <h3 style="color: #ffffff;
                                   margin: 0 0 10px 0;">
                            {conf_emoji} {title}
                        </h3>
                        <p style="color: #888888;
                                  margin: 5px 0;">
                            🌐 Sources: {sources}
                        </p>
                        <p style="color: #888888;
                                  margin: 5px 0;">
                            📊 Source Count:
                            {story['source_count']}
                        </p>
                        <p style="margin: 5px 0;">
                            🏆 Verdict:
                            <strong>{verdict}</strong>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Show articles
                    if st.button(
                        f"🔍 ANALYZE INTEL",
                        key=f"btn_{i}"
                    ):
                        st.session_state.selected_story = story
                        st.session_state.show_modal = True

                # Contradictions
                if data["contradictions"]:
                    st.markdown("---")
                    st.markdown("### ⚡ CONTRADICTIONS DETECTED")
                    for c in data["contradictions"]:
                        st.warning(
                            f"⚡ **{c['conflict']}**\n\n"
                            f"Story 1: {c['story1']}\n\n"
                            f"Story 2: {c['story2']}"
                        )

            else:
                st.error("❌ API Error! Is the server running?")

        except Exception as e:
            st.error(f"❌ Connection Error: {str(e)}")
            st.info("💡 Make sure FastAPI is running: "
                   "python -m uvicorn api.main:app --reload")

elif search_btn and not query:
    st.warning("⚠️ Enter a query first Commander!")

else:
    # Default screen
    st.markdown("""
    <div style="text-align: center;
                padding: 50px;
                font-family: 'Courier New', monospace;
                color: #333333;">
        <p style="font-size: 1.2em;">
            ● AWAITING ORDERS COMMANDER...
        </p>
        <p>Enter a query to begin intelligence gathering</p>
        <br>
        <p style="color: #00ff41;">
            Example queries:
        </p>
        <p>"Iran war latest 2026"</p>
        <p>"Russia Ukraine conflict"</p>
        <p>"China Taiwan military"</p>
        <p>"Middle East latest news"</p>
    </div>
    """, unsafe_allow_html=True)

# Modal popup - outside everything!
if st.session_state.get("show_modal"):
    story = st.session_state.selected_story

    st.markdown("---")
    st.markdown(f"""
    <div style="
        background: rgba(0,0,0,0.95);
        border: 2px solid {theme['primary']};
        border-radius: 15px;
        padding: 30px;
        margin: 20px 0;
        font-family: 'Courier New', monospace;
        box-shadow: 0 0 30px {theme['primary']};
    ">
        <h2 style="color: {theme['primary']};">
            🕵️ INTELLIGENCE ANALYSIS
        </h2>
        <hr style="border-color: {theme['primary']};">
        <h3 style="color: #ffffff;">
            📰 {story['titles'][0]}
        </h3>
        <p style="color: {theme['primary']};">
            🌐 Sources: {', '.join(story['sources'])}
        </p>
        <p style="color: {theme['primary']};">
            📊 Confidence: {story['confidence']}
        </p>
        <p style="color: {theme['primary']};">
            🏆 Verdict: {story.get('verdict', 'UNKNOWN')}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # AI Summary
    st.markdown("### 🤖 AI INTELLIGENCE BRIEF")

    with st.spinner("🕵️ Analyzing intel..."):
        from tools.summarizer import summarize_article
        article = story["articles"][0]
        summary = summarize_article(
            article["title"],
            article.get("content", ""),
            article["source"]
        )

    st.markdown(f"""
    <div style="
        background: {theme['card_bg']};
        border-left: 4px solid {theme['primary']};
        padding: 20px;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        color: #ffffff;
        white-space: pre-wrap;
    ">
        {summary}
    </div>
    """, unsafe_allow_html=True)

    # Articles
    st.markdown("### 📰 SOURCE ARTICLES")
    for article in story["articles"]:
        st.markdown(f"""
        <div style="
            background: {theme['card_bg']};
            border: 1px solid {theme['border']};
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
        ">
            <p style="color: {theme['primary']};
                      font-weight: bold;">
                📰 {article['title']}
            </p>
            <p style="color: #888888;">
                🌐 {article['source']}
            </p>
            <a href="{article['url']}"
               target="_blank"
               style="color: {theme['primary']};">
                🔗 Read Full Article
            </a>
        </div>
        """, unsafe_allow_html=True)

    # Close button
    if st.button("❌ CLOSE ANALYSIS"):
        st.session_state.show_modal = False
        del st.session_state.selected_story
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center;
            font-family: 'Courier New', monospace;
            color: #333333;
            font-size: 0.8em;">
    SENTINEL AI v1.0.0 |
    CLASSIFIED: OPEN SOURCE |
    BUILT BY: NIKHIL 🔥
</div>
""", unsafe_allow_html=True)
