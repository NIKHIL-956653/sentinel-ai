import streamlit as st
import streamlit.components.v1 as components
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
    "📄 Classified": {
        "bg": "#000820",
        "primary": "#ffd700",
        "secondary": "#000d35",
        "text": "#ffffff",
        "border": "#ffd700",
        "card_bg": "#000d35",
        "alert": "#ffd700"
    }
}

# Page config
st.set_page_config(
    page_title="SENTINEL AI",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Top navigation bar
st.markdown("""
<div style="font-family: 'Courier New', monospace; padding: 8px 0;">
    <div style="font-size: 1.8em; font-weight: bold; letter-spacing: 6px;">
        🕵️ SENTINEL AI
    </div>
    <div style="color: #888888; font-size: 0.8em; letter-spacing: 2px;">
        Military Intelligence &amp; News Verification Platform
    </div>
    <div style="font-size: 0.75em; margin-top: 4px; color: #00ff41;">
        ● SYSTEM ONLINE | CLASSIFIED LEVEL: OPEN SOURCE
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation tabs
tab_col1, tab_col2, tab_col3, tab_col4 = st.columns([1,1,1,3])

with tab_col1:
    if st.button("📰 NEWS FEED", use_container_width=True):
        st.session_state.page = "news"

with tab_col2:
    if st.button("🌍 COUNTRIES", use_container_width=True):
        st.session_state.page = "countries"

with tab_col3:
    if st.button("👤 LEADERS", use_container_width=True):
        st.session_state.page = "leaders"

# Fix selected_page and selected_theme
selected_page = st.session_state.get("page", "news")
selected_theme = "🟢 CIA Classic"

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

if selected_theme == "🌧️ Matrix":
    components.html("""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body { margin: 0; overflow: hidden; 
               background: transparent; }
        canvas { position: fixed; top: 0; 
                 left: 0; }
    </style>
    </head>
    <body>
    <canvas id="c"></canvas>
    <script>
    var c = document.getElementById('c');
    var ctx = c.getContext('2d');
    c.height = window.screen.height;
    c.width = window.screen.width;
    var matrix = '0101日本語漢字武器戦争機密軍事';
    matrix = matrix.split('');
    var font_size = 16;
    var columns = c.width/font_size;
    var drops = [];
    for(var x = 0; x < columns; x++)
        drops[x] = 1;
    function draw() {
        ctx.fillStyle = 'rgba(0,0,0,0.04)';
        ctx.fillRect(0, 0, c.width, c.height);
        ctx.fillStyle = '#00ff41';
        ctx.font = font_size + 'px monospace';
        for(var i = 0; i < drops.length; i++) {
            var text = matrix[
                Math.floor(Math.random()*matrix.length)
            ];
            ctx.fillText(text, i*font_size, 
                        drops[i]*font_size);
            if(drops[i]*font_size > c.height 
               && Math.random() > 0.975)
                drops[i] = 0;
            drops[i]++;
        }
    }
    setInterval(draw, 35);
    </script>
    </body>
    </html>
    """, height=500, scrolling=False)


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


def show_leader_statements(theme):
    """World Leader Statements Page"""

    st.markdown(f"""
    <div style="
        font-family: 'Courier New', monospace;
        color: {theme['primary']};
        font-size: 1.5em;
        font-weight: bold;
        margin-bottom: 20px;
    ">
        👤 WORLD LEADER STATEMENTS
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh Statements"):
        # Clear cache so fresh fetch happens
        keys_to_clear = [k for k in st.session_state
                         if k == "leader_statements_cache"]
        for k in keys_to_clear:
            del st.session_state[k]

    with st.spinner("🕵️ Loading leader statements..."):
        from tools.leader_tracker import (
            get_latest_statements,
            get_sentiment_emoji
        )
        statements = get_latest_statements()

    if not statements:
        st.warning("⚠️ No statements found. Try refreshing!")
        return

    st.markdown(f"### 📊 {len(statements)} STATEMENTS INTERCEPTED")
    st.markdown("---")

    # Sentiment border colors
    sentiment_colors = {
        "aggressive": "#ff0000",
        "warning":    "#ff6600",
        "defensive":  "#ffff00",
        "diplomatic": "#00ff41",
        "neutral":    "#ffffff",
    }

    for s in statements:
        flag      = s.get("flag", "🌍")
        leader    = s.get("leader", "Unknown")
        role      = s.get("role", "")
        country   = s.get("country", "")
        statement = s.get("statement", "")
        context   = s.get("context", "")
        sentiment = s.get("sentiment", "neutral").lower()
        source    = s.get("source", "")

        border_color = sentiment_colors.get(sentiment, "#ffffff")
        sent_emoji   = get_sentiment_emoji(sentiment)

        st.markdown(f"""
        <div style="
            background: {theme['card_bg']};
            border-left: 5px solid {border_color};
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            box-shadow: 0 0 10px {border_color}44;
        ">
            <div style="
                color: {theme['primary']};
                font-size: 1.1em;
                font-weight: bold;
                margin-bottom: 8px;
            ">
                {flag} {leader}
                <span style="color: #888888;
                             font-size: 0.85em;
                             font-weight: normal;">
                    &nbsp;·&nbsp;{role}, {country}
                </span>
            </div>
            <div style="
                color: {border_color};
                font-size: 0.85em;
                margin-bottom: 10px;
            ">
                {sent_emoji} {sentiment.upper()}
            </div>
            <div style="
                color: #ffffff;
                font-size: 1em;
                font-style: italic;
                margin-bottom: 10px;
                border-left: 2px solid {theme['primary']};
                padding-left: 12px;
            ">
                "{statement}"
            </div>
            <div style="color: #888888; font-size: 0.85em;">
                📌 {context}
            </div>
            <div style="
                color: #555555;
                font-size: 0.75em;
                margin-top: 8px;
            ">
                📰 {source}
            </div>
        </div>
        """, unsafe_allow_html=True)


def show_country_profiles(theme):
    """Country Military Profiles Page"""

    # Matrix rain background CSS
    st.markdown("""
    <style>
    .matrix-gap {
        position: relative;
        overflow: hidden;
        height: 80px;
        margin: 0;
        padding: 0;
    }
    .scrollable-box {
        height: 200px;
        overflow-y: auto;
        scrollbar-width: thin;
        scrollbar-color: #00ff41 #111111;
    }
    .scrollable-box::-webkit-scrollbar {
        width: 6px;
    }
    .scrollable-box::-webkit-scrollbar-track {
        background: #111111;
    }
    .scrollable-box::-webkit-scrollbar-thumb {
        background-color: #00ff41;
        border-radius: 3px;
    }
    .mil-box {
        background: #0a0a0a;
        border: 1px solid #00ff41;
        border-radius: 10px;
        padding: 15px;
        font-family: 'Courier New', monospace;
        box-shadow: 0 0 15px rgba(0,255,65,0.15);
        margin-bottom: 10px;
    }
    .mil-box-title {
        color: #00ff41;
        font-size: 0.85em;
        font-weight: bold;
        letter-spacing: 2px;
        margin-bottom: 8px;
        border-bottom: 1px solid #003300;
        padding-bottom: 6px;
    }
    .mil-box-value {
        color: #ffffff;
        font-size: 1.1em;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="font-family:'Courier New',monospace;
                color:{theme['primary']};
                font-size:1.5em;
                font-weight:bold;
                margin-bottom:20px;
                text-shadow: 0 0 10px {theme['primary']};">
        🌍 COUNTRY MILITARY PROFILES
    </div>
    """, unsafe_allow_html=True)

    countries = [
        "Select Country...",
        "United States", "Russia", "China",
        "India", "UAE", "Israel", "Iran",
        "Saudi Arabia", "Turkey", "Pakistan",
        "United Kingdom", "France", "Germany",
        "North Korea", "South Korea", "Japan"
    ]

    selected = st.selectbox("🌍 SELECT COUNTRY", countries)

    if selected != "Select Country...":
        with st.spinner(f"🔍 Fetching {selected} military profile..."):
            from tools.wikipedia_tool import get_country_military_profile
            profile = get_country_military_profile(selected)

        # ── ROW 1: Profile + Army + Navy ──────────────────────
        r1c1, r1c2, r1c3 = st.columns([2, 1, 1])

        with r1c1:
            st.markdown(f"""
            <div class="mil-box">
                <div class="mil-box-title">
                    🌍 {profile['country'].upper()} MILITARY PROFILE
                </div>
                <div class="scrollable-box">
                    <div class="mil-box-value"
                         style="font-size:0.9em; color:#cccccc;">
                        {profile['military_summary']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with r1c2:
            st.markdown(f"""
            <div class="mil-box" style="text-align:center; padding:12px;">
                <div class="mil-box-title">🪖 ARMY</div>
                <div style="color:#00ff41; font-size:1.4em; font-weight:bold;">
                    {profile['army_strength']}
                </div>
                <div style="color:#888888; font-size:0.75em;">
                    ACTIVE PERSONNEL
                </div>
            </div>
            """, unsafe_allow_html=True)

        with r1c3:
            st.markdown(f"""
            <div class="mil-box" style="text-align:center; padding:12px;">
                <div class="mil-box-title">⚓ NAVY</div>
                <div style="color:#00bfff; font-size:1.4em; font-weight:bold;">
                    {profile['navy_strength']}
                </div>
                <div style="color:#888888; font-size:0.75em;">
                    NAVAL PERSONNEL
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── MATRIX RAIN GAP ───────────────────────────────────
        components.html("""
        <div style="background:#000000; height:60px;
                    overflow:hidden; position:relative;">
        <canvas id="rain1"></canvas>
        <script>
        var c=document.getElementById('rain1');
        var ctx=c.getContext('2d');
        c.width=window.innerWidth; c.height=60;
        var cols=Math.floor(c.width/16);
        var drops=Array(cols).fill(0);
        var chars='01アイウエオカキク軍事機密戦争';
        function draw(){
            ctx.fillStyle='rgba(0,0,0,0.1)';
            ctx.fillRect(0,0,c.width,c.height);
            ctx.fillStyle='#00ff41';
            ctx.font='14px monospace';
            drops.forEach(function(y,i){
                var ch=chars[Math.floor(Math.random()*chars.length)];
                ctx.fillText(ch,i*16,y*16);
                if(y*16>c.height&&Math.random()>0.9) drops[i]=0;
                else drops[i]++;
            });
        }
        setInterval(draw,50);
        </script>
        </div>
        """, height=65)

        # ── ROW 2: Airforce + Budget + Rank ───────────────────
        r2c1, r2c2, r2c3 = st.columns(3)

        with r2c1:
            st.markdown(f"""
            <div class="mil-box" style="text-align:center; padding:12px;">
                <div class="mil-box-title">✈️ AIRFORCE</div>
                <div style="color:#ff6600; font-size:1.4em; font-weight:bold;">
                    {profile['airforce_strength']}
                </div>
                <div style="color:#888888; font-size:0.75em;">
                    AIR PERSONNEL
                </div>
            </div>
            """, unsafe_allow_html=True)

        with r2c2:
            st.markdown(f"""
            <div class="mil-box" style="text-align:center; padding:12px;">
                <div class="mil-box-title">💰 DEFENSE BUDGET</div>
                <div style="color:#ffd700; font-size:1.1em; font-weight:bold;">
                    {profile['defense_budget']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Hardcoded ranks for accuracy
        known_ranks = {
            "United States": 1,
            "Russia": 2,
            "China": 3,
            "India": 4,
            "United Kingdom": 5,
            "South Korea": 6,
            "Pakistan": 7,
            "Japan": 8,
            "France": 9,
            "Italy": 10,
            "Turkey": 11,
            "Israel": 17,
            "Iran": 14,
            "UAE": 38,
            "Saudi Arabia": 22,
            "Germany": 19,
            "North Korea": 36,
        }
        actual_rank = known_ranks.get(selected, profile['global_rank'])

        with r2c3:
            st.markdown(f"""
            <div class="mil-box" style="text-align:center; padding:12px;">
                <div class="mil-box-title">🏆 GLOBAL RANK</div>
                <div style="color:#ff0000; font-size:2em; font-weight:bold;">
                    #{actual_rank}
                </div>
                <div style="color:#888888; font-size:0.75em;">
                    WORLD MILITARY POWER
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── MATRIX RAIN GAP 2 ─────────────────────────────────
        components.html("""
        <div style="background:#000000; height:60px;
                    overflow:hidden; position:relative;">
        <canvas id="rain2"></canvas>
        <script>
        var c=document.getElementById('rain2');
        var ctx=c.getContext('2d');
        c.width=window.innerWidth; c.height=60;
        var cols=Math.floor(c.width/16);
        var drops=Array(cols).fill(0);
        var chars='01アイウエオカキク軍事機密戦争';
        function draw(){
            ctx.fillStyle='rgba(0,0,0,0.1)';
            ctx.fillRect(0,0,c.width,c.height);
            ctx.fillStyle='#003300';
            ctx.font='14px monospace';
            drops.forEach(function(y,i){
                var ch=chars[Math.floor(Math.random()*chars.length)];
                ctx.fillText(ch,i*16,y*16);
                if(y*16>c.height&&Math.random()>0.9) drops[i]=0;
                else drops[i]++;
            });
        }
        setInterval(draw,50);
        </script>
        </div>
        """, height=65)

        # ── ROW 3: Combat Stats with Expandable Details ───────
        st.markdown("### ⚔️ COMBAT ARSENAL — Click for Details")

        r3c1, r3c2, r3c3, r3c4 = st.columns(4)

        fighters = profile.get('fighters', 'N/A')
        if 'Stock:' in str(fighters):
            fighters = fighters.split('Stock:')[1].split('(')[0].strip()

        tanks = profile.get('tanks', 'N/A')
        if 'Stock:' in str(tanks):
            tanks = tanks.split('Stock:')[1].split('\n')[0].strip()

        subs = profile.get('submarines', 'N/A')
        carriers = profile.get('aircraft_carriers', '0')

        for col, icon, label, val, color, category in [
            (r3c1, "✈️", "FIGHTER JETS", fighters, "#00bfff", "fighter_jets"),
            (r3c2, "🚂", "TANKS", tanks, "#ff6600", "tanks"),
            (r3c3, "🤿", "SUBMARINES", subs, "#00ff41", "submarines"),
            (r3c4, "🛳️", "CARRIERS", carriers, "#ffd700", "warships"),
        ]:
            with col:
                st.markdown(f"""
                <div class="mil-box" style="text-align:center;
                                            cursor:pointer;">
                    <div class="mil-box-title">{icon} {label}</div>
                    <div style="color:{color};
                                font-size:1.6em;
                                font-weight:bold;
                                padding:8px 0;
                                text-shadow: 0 0 10px {color};">
                        {val}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Expandable details for each category
        exp1, exp2, exp3, exp4 = st.columns(4)

        categories = [
            (exp1, "✈️ FIGHTER JET DETAILS", "fighter_jets"),
            (exp2, "🚂 TANK DETAILS", "tanks"),
            (exp3, "🤿 SUBMARINE DETAILS", "submarines"),
            (exp4, "🛳️ WARSHIP DETAILS", "warships"),
        ]

        for col, label, category in categories:
            with col:
                with st.expander(f"🔍 {label}"):
                    with st.spinner(f"Loading classified data..."):
                        from tools.weapons_detail_tool import get_weapon_category_details
                        details = get_weapon_category_details(
                            selected, category
                        )

                    for item in details:
                        name = item.get('name', 'Unknown')
                        year = item.get('year', 'N/A')
                        history = item.get('history', '')
                        role = item.get('role', item.get('type', ''))
                        patrol = item.get('patrol_areas', '')

                        st.markdown(f"""
                        <div style="
                            border-left: 3px solid #00ff41;
                            padding: 8px 12px;
                            margin: 8px 0;
                            background: #0a1a0a;
                            border-radius: 0 5px 5px 0;
                        ">
                            <div style="color:#00ff41;
                                        font-weight:bold;
                                        font-size:0.95em;">
                                {name}
                            </div>
                            <div style="color:#888888;
                                        font-size:0.8em;">
                                📅 {year}
                                {f' | 🎯 {role}' if role else ''}
                                {f' | 🌊 {patrol}' if patrol else ''}
                            </div>
                            <div style="color:#cccccc;
                                        font-size:0.82em;
                                        margin-top:4px;">
                                {history}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

        # Missiles section
        components.html("""
        <div style="background:#000000; height:40px; overflow:hidden;">
        <canvas id="rain_missiles"></canvas>
        <script>
        var c=document.getElementById('rain_missiles');
        var ctx=c.getContext('2d');
        c.width=window.innerWidth; c.height=40;
        var cols=Math.floor(c.width/16);
        var drops=Array(cols).fill(0);
        var chars='01ミサイル核弾頭軍事機密';
        function draw(){
            ctx.fillStyle='rgba(0,0,0,0.1)';
            ctx.fillRect(0,0,c.width,c.height);
            ctx.fillStyle='#ff000044';
            ctx.font='12px monospace';
            drops.forEach(function(y,i){
                var ch=chars[Math.floor(Math.random()*chars.length)];
                ctx.fillText(ch,i*16,y*12);
                if(y*12>c.height&&Math.random()>0.9) drops[i]=0;
                else drops[i]++;
            });
        }
        setInterval(draw,50);
        </script>
        </div>
        """, height=45)

        # Missiles expander
        with st.expander("🚀 MISSILE ARSENAL — Click to view classified data"):
            with st.spinner("🔍 Decrypting missile database..."):
                from tools.weapons_detail_tool import get_weapon_category_details
                missiles = get_weapon_category_details(selected, "missiles")

            for missile in missiles:
                name = missile.get('name', 'Unknown')
                mtype = missile.get('type', '')
                mrange = missile.get('range', '')
                year = missile.get('year', '')
                history = missile.get('history', '')

                st.markdown(f"""
                <div style="
                    border-left: 4px solid #ff0000;
                    padding: 10px 14px;
                    margin: 10px 0;
                    background: #1a0000;
                    border-radius: 0 8px 8px 0;
                    font-family: 'Courier New', monospace;
                ">
                    <div style="color:#ff4444;
                                font-weight:bold;
                                font-size:1em;">
                        🚀 {name}
                    </div>
                    <div style="color:#888888; font-size:0.8em; margin:4px 0;">
                        {f'Type: {mtype}' if mtype else ''}
                        {f' | Range: {mrange}' if mrange else ''}
                        {f' | Deployed: {year}' if year else ''}
                    </div>
                    <div style="color:#cccccc; font-size:0.85em; margin-top:6px;">
                        {history}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── ROW 4: Key Weapons ─────────────────────────────────
        weapons = [w for w in profile.get('key_weapons', [])
                   if w and w != "Officially Not Available"
                   and w != "N/A" and len(w) > 3]

        if weapons:
            weapons_html = ""
            for w in weapons:
                weapons_html += f"<div style='border-left:3px solid #00ff41;padding:6px 12px;margin:6px 0;color:#ffffff;font-size:0.9em;background:#0d1a0d;border-radius:0 5px 5px 0;'>🚀 {w}</div>"

            st.markdown(f"""
            <div class="mil-box">
                <div class="mil-box-title">🚀 KEY WEAPONS ARSENAL</div>
                <div class="scrollable-box">
                    {weapons_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Weapon detail expanders
            st.markdown("#### 🔍 WEAPON DETAILS")
            from tools.weapons_tool import get_weapon_details
            for weapon in weapons:
                with st.expander(f"🚀 {weapon}", expanded=False):
                    cache_key = f"weapon_{weapon}_{selected}"
                    if cache_key not in st.session_state:
                        with st.spinner(f"Loading {weapon}..."):
                            st.session_state[cache_key] = \
                                get_weapon_details(weapon, selected)
                    weapon_data = st.session_state[cache_key]

                    if weapon_data:
                        if weapon_data.get('image'):
                            st.image(weapon_data['image'], width=300)
                        if weapon_data.get('description'):
                            st.markdown(f"""
                            <div style="
                                background:{theme['card_bg']};
                                border-left:4px solid {theme['primary']};
                                padding:12px; border-radius:5px;
                                color:{theme['text']};
                                font-family:'Courier New',monospace;
                                margin-bottom:10px;">
                                {weapon_data['description']}
                            </div>""", unsafe_allow_html=True)
                        specs = {k: v for k, v
                                 in weapon_data.get('specifications',
                                                    {}).items()
                                 if v and v != "N/A"
                                 and v != "Officially Not Available"}
                        if specs:
                            st.markdown("### ⚙️ SPECIFICATIONS")
                            for k, v in specs.items():
                                st.markdown(
                                    f"<span style='color:{theme['primary']};"
                                    f"font-family:Courier New,monospace;'>"
                                    f"<b>{k.title()}:</b></span> {v}",
                                    unsafe_allow_html=True)
                        if weapon_data.get('fun_fact'):
                            st.markdown(f"""
                            <div style="
                                background:{theme['secondary']};
                                border:1px solid {theme['primary']};
                                padding:10px; border-radius:5px;
                                color:{theme['primary']};
                                font-family:'Courier New',monospace;
                                margin-top:10px;">
                                💡 {weapon_data['fun_fact']}
                            </div>""", unsafe_allow_html=True)
                        if weapon_data.get('source_url'):
                            st.markdown(
                                f"[📖 Wikipedia]({weapon_data['source_url']})")
                    else:
                        st.warning(f"No data for {weapon}")

        # Notable facts
        if profile['notable_facts']:
            facts_html = ""
            for fact in profile['notable_facts']:
                facts_html += f"<div style='padding:6px 0;border-bottom:1px solid #1a1a1a;color:#cccccc;font-size:0.9em;'>▸ {fact}</div>"

            st.markdown(f"""
            <div class="mil-box" style="margin-top:10px;">
                <div class="mil-box-title">📌 NOTABLE FACTS</div>
                <div class="scrollable-box">
                    {facts_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Special Forces Section — Dynamic LLM lookup
        from tools.special_forces_tool import get_special_forces
        with st.spinner(f"🕵️ Loading classified intel for {selected}..."):
            forces = get_special_forces(selected)
        if forces:
            components.html("""
            <div style="background:#000000; height:40px; overflow:hidden;">
            <canvas id="rain_sf"></canvas>
            <script>
            var c=document.getElementById('rain_sf');
            var ctx=c.getContext('2d');
            c.width=window.innerWidth; c.height=40;
            var cols=Math.floor(c.width/16);
            var drops=Array(cols).fill(0);
            var chars='01アイウエオ軍事機密';
            function draw(){
                ctx.fillStyle='rgba(0,0,0,0.1)';
                ctx.fillRect(0,0,c.width,c.height);
                ctx.fillStyle='#004400';
                ctx.font='12px monospace';
                drops.forEach(function(y,i){
                    var ch=chars[Math.floor(Math.random()*chars.length)];
                    ctx.fillText(ch,i*16,y*12);
                    if(y*12>c.height&&Math.random()>0.9) drops[i]=0;
                    else drops[i]++;
                });
            }
            setInterval(draw,50);
            </script>
            </div>
            """, height=45)

            forces_html = ""
            for force in forces:
                forces_html += f"<div style='padding:6px 10px;border-left:3px solid #00ff41;margin:5px 0;color:#ffffff;font-size:0.9em;background:#0a1a0a;border-radius:0 5px 5px 0;'>{force}</div>"

            st.markdown(f"""
            <div class="mil-box">
                <div class="mil-box-title">
                    🕵️ SPECIAL FORCES & INTELLIGENCE UNITS
                </div>
                <div style="max-height:250px; overflow-y:auto;
                            scrollbar-width:thin;
                            scrollbar-color:#00ff41 #111111;">
                    {forces_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Source
        if profile.get('source_url'):
            st.markdown(f"""
            <div style="margin-top:10px;
                        font-family:'Courier New',monospace;
                        color:#888888; font-size:0.8em;">
                📊 Source: Wikipedia |
                <a href="{profile['source_url']}"
                   target="_blank"
                   style="color:{theme['primary']};">
                    View Source
                </a>
            </div>
            """, unsafe_allow_html=True)


if st.session_state.page == "news":
    # Search Section
    with st.container():
        col1, col2 = st.columns([2, 1])

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

                    # Small stats on right side
                    st.markdown(f"""
<div style="
    display: flex;
    justify-content: flex-end;
    gap: 20px;
    font-family: 'Courier New', monospace;
    font-size: 0.85em;
    padding: 8px 0;
">
    <span style="color:#00ff41;">
        ✅ HIGH: {high}
    </span>
    <span style="color:#ffff00;">
        ⚠️ MEDIUM: {medium}
    </span>
    <span style="color:#ff4444;">
        🔴 LOW: {low}
    </span>
    <span style="color:#ff6600;">
        ⚡ CONTRADICTIONS: {len(data['contradictions'])}
    </span>
</div>
""", unsafe_allow_html=True)

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
    show_leader_statements(theme)

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
