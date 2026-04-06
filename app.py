import streamlit as st
import requests
import json

# Page config
st.set_page_config(
    page_title="SENTINEL AI",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark CIA style CSS
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0a0a0a;
        color: #00ff41;
    }
    
    /* Header */
    .main-header {
        text-align: center;
        padding: 20px;
        border-bottom: 2px solid #00ff41;
        margin-bottom: 30px;
    }
    
    .main-title {
        font-size: 3em;
        font-weight: bold;
        color: #00ff41;
        font-family: 'Courier New', monospace;
        letter-spacing: 10px;
        text-shadow: 0 0 20px #00ff41;
    }
    
    .sub-title {
        color: #888888;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
        letter-spacing: 3px;
    }

    /* Search bar */
    .stTextInput input {
        background-color: #1a1a1a !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 5px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 1em !important;
        padding: 10px !important;
    }

    /* Button */
    .stButton button {
        background-color: #00ff41 !important;
        color: #0a0a0a !important;
        border: none !important;
        border-radius: 5px !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold !important;
        font-size: 1em !important;
        width: 100% !important;
        padding: 10px !important;
    }

    .stButton button:hover {
        background-color: #00cc33 !important;
        box-shadow: 0 0 15px #00ff41 !important;
    }

    /* Cards */
    .story-card {
        background-color: #111111;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        font-family: 'Courier New', monospace;
    }

    .high-conf {
        border-left: 5px solid #00ff41;
        box-shadow: 0 0 15px rgba(0,255,65,0.2);
    }

    .medium-conf {
        border-left: 5px solid #ffff00;
        box-shadow: 0 0 15px rgba(255,255,0,0.2);
    }

    .low-conf {
        border-left: 5px solid #ff4444;
        box-shadow: 0 0 15px rgba(255,68,68,0.2);
    }

    .disputed {
        border-left: 5px solid #ff8800;
        box-shadow: 0 0 15px rgba(255,136,0,0.2);
    }

    /* Stats bar */
    .stats-bar {
        background-color: #111111;
        border: 1px solid #333333;
        border-radius: 10px;
        padding: 15px;
        margin: 20px 0;
        font-family: 'Courier New', monospace;
    }

    /* Metrics */
    .metric-box {
        text-align: center;
        padding: 10px;
        border-radius: 5px;
        background-color: #1a1a1a;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <div class="main-title">🕵️ SENTINEL AI</div>
    <div class="sub-title">
        MILITARY INTELLIGENCE & NEWS VERIFICATION PLATFORM
    </div>
    <div class="sub-title" style="color: #00ff41; margin-top: 5px;">
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
                
                st.markdown("---")
                st.markdown("### 📰 INTELLIGENCE FEED")
                
                # Display stories
                for story in results:
                    conf = story["confidence"]
                    verdict = story.get(
                        "verdict", "UNKNOWN"
                    )
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
                    with st.expander(
                        f"📄 View {len(story['articles'])} article(s)"
                    ):
                        for article in story["articles"]:
                            st.markdown(f"""
                            **📰 {article['title']}**  
                            🔗 [{article['url']}]({article['url']})  
                            🌐 Source: `{article['source']}`  
                            ---
                            """)
                
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