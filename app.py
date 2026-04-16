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
# Top navigation bar
nav1, nav2, nav3, nav4, nav5 = st.columns([2,2,2,2,3])

with nav1:
    if st.button("📰 NEWS FEED",
                  use_container_width=True):
        st.session_state.page = "news"

with nav2:
    if st.button("🌍 COUNTRIES",
                  use_container_width=True):
        st.session_state.page = "countries"

with nav3:
    if st.button("🚀 WEAPONS",
                  use_container_width=True):
        st.session_state.page = "weapons"

with nav4:
    if st.button("👤 LEADERS",
                  use_container_width=True):
        st.session_state.page = "leaders"

with nav5:
    selected_theme = st.selectbox(
        "🎨",
        list(THEMES.keys()),
        index=0,
        label_visibility="collapsed"
    )

# Default page
if "page" not in st.session_state:
    st.session_state.page = "news"

st.markdown("---")

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


def show_country_profiles(theme):
    """Country Military Profiles Page"""

    st.markdown(f"""
    <div style="
        font-family: 'Courier New', monospace;
        color: {theme['primary']};
        font-size: 1.5em;
        font-weight: bold;
        margin-bottom: 20px;
    ">
        🌍 COUNTRY MILITARY PROFILES
    </div>
    """, unsafe_allow_html=True)

    # Country selector
    countries = [
        "Select Country...",
        "United States", "Russia", "China",
        "India", "UAE", "Israel", "Iran",
        "Saudi Arabia", "Turkey", "Pakistan",
        "United Kingdom", "France", "Germany",
        "North Korea", "South Korea", "Japan"
    ]

    selected = st.selectbox(
        "🌍 SELECT COUNTRY",
        countries
    )

    if selected != "Select Country...":
        with st.spinner(f"🔍 Fetching {selected} military profile..."):
            from tools.wikipedia_tool import get_country_military_profile
            profile = get_country_military_profile(selected)

        # Display profile
        st.markdown(f"""
        <div style="
            background: {theme['card_bg']};
            border: 2px solid {theme['primary']};
            border-radius: 15px;
            padding: 30px;
            font-family: 'Courier New', monospace;
            box-shadow: 0 0 20px {theme['primary']}44;
        ">
            <h2 style="color: {theme['primary']};">
                🌍 {profile['country'].upper()}
                MILITARY PROFILE
            </h2>
            <hr style="border-color: {theme['primary']};">
            <p style="color: #ffffff; font-size: 1.1em;">
                {profile['military_summary']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Stats columns
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""
            <div style="
                background: {theme['card_bg']};
                border: 1px solid {theme['primary']};
                border-radius: 10px;
                padding: 15px;
                text-align: center;
                font-family: 'Courier New', monospace;
            ">
                <p style="color: {theme['primary']};">🪖 ARMY</p>
                <p style="color: #ffffff; font-size: 1.2em;">
                    {profile['army_strength']}
                </p>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div style="
                background: {theme['card_bg']};
                border: 1px solid {theme['primary']};
                border-radius: 10px;
                padding: 15px;
                text-align: center;
                font-family: 'Courier New', monospace;
            ">
                <p style="color: {theme['primary']};">⚓ NAVY</p>
                <p style="color: #ffffff; font-size: 1.2em;">
                    {profile['navy_strength']}
                </p>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div style="
                background: {theme['card_bg']};
                border: 1px solid {theme['primary']};
                border-radius: 10px;
                padding: 15px;
                text-align: center;
                font-family: 'Courier New', monospace;
            ">
                <p style="color: {theme['primary']};">✈️ AIRFORCE</p>
                <p style="color: #ffffff; font-size: 1.2em;">
                    {profile['airforce_strength']}
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Budget + Rank
        b1, b2 = st.columns(2)
        with b1:
            st.metric("💰 Defense Budget",
                     profile['defense_budget'])
        with b2:
            st.metric("🏆 Global Rank",
                     profile['global_rank'])

        st.markdown("### ⚔️ COMBAT STRENGTH")

        c4, c5, c6 = st.columns(3)

        with c4:
            fighters = profile.get('fighters', 'N/A')
            if 'Stock:' in str(fighters):
                fighters = fighters.split('Stock:')[1].split('(')[0].strip()
            st.metric("✈️ Fighter Jets", fighters)
        with c5:
            tanks = profile.get('tanks', 'N/A')
            if 'Stock:' in str(tanks):
                tanks = tanks.split('Stock:')[1].split('\n')[0].strip()
            st.metric("🚂 Tanks", tanks)
        with c6:
            st.metric("🤿 Submarines",
                     profile.get('submarines', 'N/A'))

        # Aircraft carriers
        carriers = profile.get('aircraft_carriers', '0')
        if carriers and carriers != '0':
            st.metric("🛳️ Aircraft Carriers", carriers)

        # Weapons
        weapons = [w for w in profile.get('key_weapons', [])
                   if w and w != "Officially Not Available"
                   and w != "N/A"
                   and len(w) > 3]
        if weapons:
            profile['key_weapons'] = weapons
        if profile['key_weapons']:
            st.markdown(f"### 🚀 KEY WEAPONS")
            if isinstance(profile['key_weapons'], list):
                weapons_text = " | ".join(profile['key_weapons'])
            else:
                weapons_text = str(profile['key_weapons'])
            st.markdown(f"""
            <div style="
                background: {theme['card_bg']};
                border-left: 4px solid {theme['primary']};
                padding: 15px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                color: {theme['primary']};
            ">
                {weapons_text}
            </div>
            """, unsafe_allow_html=True)

            # Weapon detail expanders
            st.markdown("#### 🔍 WEAPON DETAILS")
            from tools.weapons_tool import get_weapon_details
            for weapon in profile['key_weapons']:
                with st.expander(f"🚀 {weapon}", expanded=False):
                    cache_key = f"weapon_{weapon}_{selected}"
                    if cache_key not in st.session_state:
                        with st.spinner(f"Loading {weapon}..."):
                            st.session_state[cache_key] = get_weapon_details(weapon, selected)
                    weapon_data = st.session_state[cache_key]

                    if weapon_data:
                        # Image
                        if weapon_data.get('image'):
                            st.image(weapon_data['image'], width=300)

                        # Description
                        if weapon_data.get('description'):
                            st.markdown(f"""
                            <div style="
                                background: {theme['card_bg']};
                                border-left: 4px solid {theme['primary']};
                                padding: 12px;
                                border-radius: 5px;
                                color: {theme['text']};
                                font-family: 'Courier New', monospace;
                                margin-bottom: 10px;
                            ">
                                {weapon_data['description']}
                            </div>
                            """, unsafe_allow_html=True)

                        # Specifications — non-N/A only
                        specs = weapon_data.get('specifications', {})
                        available_specs = {
                            k: v for k, v in specs.items()
                            if v and v != "N/A"
                            and v != "Officially Not Available"
                        }
                        if available_specs:
                            st.markdown("### ⚙️ SPECIFICATIONS")
                            primary = theme['primary']
                            for key, value in available_specs.items():
                                st.markdown(
                                    f"<span style='color:{primary};font-family:Courier New,monospace;'>"
                                    f"<b>{key.title()}:</b></span> {value}",
                                    unsafe_allow_html=True
                                )

                        # Fun fact
                        if weapon_data.get('fun_fact'):
                            st.markdown(f"""
                            <div style="
                                background: {theme['secondary']};
                                border: 1px solid {theme['primary']};
                                padding: 10px;
                                border-radius: 5px;
                                color: {theme['primary']};
                                font-family: 'Courier New', monospace;
                                margin-top: 10px;
                            ">
                                💡 {weapon_data['fun_fact']}
                            </div>
                            """, unsafe_allow_html=True)

                        # Source link
                        if weapon_data.get('source_url'):
                            st.markdown(
                                f"[📖 Wikipedia Source]({weapon_data['source_url']})"
                            )
                    else:
                        st.warning(f"No data found for {weapon}")

        # Notable facts
        if profile['notable_facts']:
            st.markdown(f"### 📌 NOTABLE FACTS")
            for fact in profile['notable_facts']:
                st.markdown(f"- {fact}")

        # Source
        if profile.get('source_url'):
            st.markdown(f"""
            <div style="
                margin-top: 20px;
                font-family: 'Courier New', monospace;
                color: #888888;
                font-size: 0.8em;
            ">
                📊 Data Source: Wikipedia |
                <a href="{profile['source_url']}"
                   target="_blank"
                   style="color: {theme['primary']};">
                    View Source
                </a>
            </div>
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

if st.session_state.page == "news":
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

                        with st.expander(f"🔍 ANALYZE INTEL - {title[:40]}..."):

                            # Story details
                            st.markdown(f"""
                            <div style="
                                background: {theme['card_bg']};
                                border: 2px solid {theme['primary']};
                                border-radius: 10px;
                                padding: 20px;
                                font-family: 'Courier New', monospace;
                                box-shadow: 0 0 20px {theme['primary']}44;
                            ">
                                <h3 style="color: {theme['primary']};">
                                    🕵️ INTELLIGENCE ANALYSIS
                                </h3>
                                <hr style="border-color: {theme['primary']};">
                                <p style="color: #ffffff;">
                                    📰 {story['titles'][0]}
                                </p>
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
                            st.markdown(f"### 🤖 AI INTELLIGENCE BRIEF")

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

                            # Source articles
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

elif st.session_state.page == "countries":
    show_country_profiles(theme)

elif st.session_state.page == "weapons":
    st.markdown("### 🚀 WEAPONS DATABASE")
    st.info("🔧 Coming soon!")

elif st.session_state.page == "leaders":
    st.markdown("### 👤 LEADER STATEMENTS")
    st.info("🔧 Coming soon!")

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
