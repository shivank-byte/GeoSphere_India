# GeoSphere India — app.py (Mission Control)
# Multipage Streamlit Architecture
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import math, time, datetime, random, re, requests, base64

from utils import *
try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

st.set_page_config(
    page_title="GeoSphere India",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
inject_css()


# JavaScript: actively find and style the sidebar toggle regardless of Streamlit version
st.markdown("""
<script>
(function fixSidebarToggle() {
    function applyFix() {
        // Try every known selector across Streamlit versions
        const selectors = [
            '[data-testid="collapsedControl"]',
            '[data-testid="stSidebarCollapsedControl"]',
            'button[aria-label*="sidebar"]',
            'button[aria-label*="Sidebar"]',
        ];
        let found = false;
        for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el) {
                el.style.cssText = `
                    position: fixed !important;
                    top: 50% !important;
                    left: 0 !important;
                    transform: translateY(-50%) !important;
                    z-index: 2147483647 !important;
                    opacity: 1 !important;
                    visibility: visible !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    width: 42px !important;
                    min-height: 66px !important;
                    background: rgba(201,168,76,0.25) !important;
                    border: 1.5px solid rgba(201,168,76,0.6) !important;
                    border-radius: 0 12px 12px 0 !important;
                    pointer-events: auto !important;
                    cursor: pointer !important;
                `;
                found = true;
            }
        }
        return found;
    }
    // Try immediately, then keep retrying for 5 seconds
    if (!applyFix()) {
        let tries = 0;
        const interval = setInterval(() => {
            tries++;
            if (applyFix() || tries > 50) clearInterval(interval);
        }, 100);
    }
    // Also re-apply on any DOM change (Streamlit re-renders frequently)
    const observer = new MutationObserver(() => applyFix());
    observer.observe(document.body, {childList: true, subtree: true});
})();
</script>
""", unsafe_allow_html=True)

if not st.session_state.loading_done:
    ph = st.empty()
    with ph.container():
        st.markdown("""
        <style>
        @keyframes pulse-ring {
            0%   { transform:scale(0.8); opacity:0.8; }
            50%  { transform:scale(1.1); opacity:0.4; }
            100% { transform:scale(0.8); opacity:0.8; }
        }
        @keyframes text-reveal {
            0%   { opacity:0; transform:translateY(18px); }
            100% { opacity:1; transform:translateY(0); }
        }
        @keyframes bar-fill {
            0%   { width:0%; }
            100% { width:100%; }
        }
        @keyframes dot-pulse {
            0%,80%,100% { transform:scale(0); opacity:0; }
            40%          { transform:scale(1); opacity:1; }
        }
        .splash-wrap {
            position:fixed;top:0;left:0;width:100vw;height:100vh;
            background:radial-gradient(ellipse at 30% 40%, #0c1428 0%, #070b18 60%, #030510 100%);
            display:flex;flex-direction:column;align-items:center;justify-content:center;
            z-index:9999999;
        }
        .splash-globe {
            font-size:5rem;margin-bottom:24px;
            animation:pulse-ring 2.4s ease-in-out infinite;
            filter:drop-shadow(0 0 32px rgba(201,168,76,0.6));
        }
        .splash-title {
            font-family:'Playfair Display',Georgia,serif;font-size:2.6rem;font-weight:900;
            background:linear-gradient(90deg,#c9a84c,#f0d878,#e8c96a,#c9a84c);
            background-size:200%;
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            background-clip:text;letter-spacing:5px;
            animation:text-reveal 0.8s ease forwards, shimmer 3s linear infinite;
        }
        .splash-sub {
            color:#a89968;font-size:0.72rem;letter-spacing:4px;
            font-family:'Source Sans 3',sans-serif;margin:8px 0 32px;
            animation:text-reveal 1s ease 0.3s both;
        }
        .splash-bar-wrap {
            width:260px;height:3px;background:rgba(201,168,76,0.12);
            border-radius:3px;overflow:hidden;margin-bottom:20px;
        }
        .splash-bar {
            height:3px;background:linear-gradient(90deg,#c9a84c,#f0d878,#c9a84c);
            border-radius:3px;animation:bar-fill 1.4s ease-out 0.5s both;
        }
        .splash-status {
            color:#a89968;font-size:0.65rem;letter-spacing:2px;
            font-family:'Source Sans 3',sans-serif;
            animation:text-reveal 0.6s ease 1s both;
        }
        .splash-status span { color:#c9a84c; }
        </style>
        <div class='splash-wrap'>
            <div class='splash-globe'>🌍</div>
            <div class='splash-title'>GeoSphere India</div>
            <div class='splash-sub'>EARTH SCIENCE INTELLIGENCE PLATFORM</div>
            <div class='splash-bar-wrap'><div class='splash-bar'></div></div>
            <div class='splash-status'>
                Initialising geological systems &nbsp;·&nbsp;
                Loading mineral database &nbsp;·&nbsp;
                <span>Ready</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(1.8)
    ph.empty()
    st.session_state.loading_done = True

render_sidebar()

st.markdown("<div class='shimmer-bar'></div>", unsafe_allow_html=True)

# app.py is always the Mission Control root page — pages/*.py are separate
# Streamlit multipage scripts. (Fixes a previously undefined `page` NameError.)
page = "🌌 Mission Control"
page_label = page.split(" ", 1)[1] if " " in page else page
rare_quote = RARE_LINES.get(page_label, "")

if st.session_state.rare_mode:
    # ── Achievement mode hero ──
    st.markdown(f"""
    <div class='hero-banner' style='border-color:rgba(58,123,213,0.45);
        background:linear-gradient(135deg,rgba(0,15,50,0.95),rgba(0,8,35,0.98));'>
        <p class='hero-title' style='
            background:linear-gradient(90deg,#3a7bd5,#6ea8fe,#a8c8ff);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            background-clip:text;font-size:2.4rem;font-family:Playfair Display,Georgia,serif;
            letter-spacing:3px;font-style:italic;'>
            The Story Between The Lines
        </p>
        <p class='rare-text' style='font-size:1.05rem;'>"{rare_quote}"</p>
        <span class='hero-badge' style='border-color:rgba(58,123,213,0.5);color:#6ea8fe;
            background:rgba(58,123,213,0.1);'>
            ✨ RARE EVENT · {datetime.datetime.now().strftime("%d %b %Y")} ✨
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Final quote card
    st.markdown("""
    <div style='
        background:linear-gradient(135deg,rgba(0,12,40,0.95),rgba(0,5,25,0.98));
        border:1px solid rgba(58,123,213,0.3);border-radius:16px;
        padding:32px 36px;text-align:center;margin:0 auto 20px;max-width:640px;
        box-shadow:0 0 40px rgba(58,123,213,0.12);'>
        <div style='font-family:Playfair Display,Georgia,serif;font-size:1.15rem;
            color:#a8c8ff;font-style:italic;line-height:2;letter-spacing:0.3px;'>
            "Some stories never ask to be remembered.<br>
            Yet somehow&hellip; they always are."
        </div>
        <div style='color:#6a85b8;font-size:0.68rem;margin-top:16px;letter-spacing:2px;'>
            — Achievement Unlocked · The Surprise Was Worth It
        </div>
    </div>""", unsafe_allow_html=True)

elif IS_BIRTHDAY:
    st.markdown(f"""
    <div class='hero-banner'>
        <p class='hero-title'>A Rare Sky</p>
        <p class='hero-sub'>FOR A RARE DAY · EARTH SCIENCE · EXPLORATION</p>
        <span class='hero-badge'>EARTH SCIENCE · {datetime.datetime.now().strftime("%d %b %Y")}</span>
    </div>
    """, unsafe_allow_html=True)
else:
    # Note: rare_mode is always False here — when it's True, the branch at
    # the top of this if/elif/else (around line 172) handles the hero
    # banner instead, and correctly shows the RARE_LINES quote there.
    st.markdown(f"""
    <div class='hero-banner'>
        <p class='hero-title'>GeoSphere India</p>
        <p class='hero-sub'>EARTH SCIENCE INTELLIGENCE PLATFORM</p>
        <span class='hero-badge'>EARTH SCIENCE · {datetime.datetime.now().strftime("%d %b %Y")}</span>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE ROUTING — sidebar pages + sub_page from radial dial
# ═══════════════════════════════════════════════════════════════
# Sub-page overrides sidebar selection when set from radial dial
effective_page = st.session_state.get("sub_page") or page

# Reliable in-app "Home" button — phone back-gesture can't be intercepted
# inside a Streamlit single-page app, so this is the dependable way back.
if effective_page != "🌌 Mission Control":
    home_col1, home_col2 = st.columns([1, 8])
    with home_col1:
        if st.button("⬅ Home", key="global_home_btn"):
            st.session_state.sub_page = None
            st.rerun()


if effective_page not in [
    "🗺️ Geological Map","🌋 Plate Tectonics","💎 Mineral Explorer",
    "🌍 Earthquake Dashboard","📅 Geological Time Scale","🧪 Soil Explorer",
    "🪙 Economic Geology","🪨 Rock Explorer","🌋 Volcano Explorer",
    "🧭 Structural Tools","🌿 Geography Explorer","🌊 Watershed Explorer",
    "🌊 Oceanography","🔬 Thin Section Gallery","📚 Semester Notes",
    "🧠 Geo Quiz","🃏 Flashcards","🤖 AI Assistant","📓 Field Diary",
    "🥚 About & Archive"
] or effective_page == "🌌 Mission Control":
    # Clear sub_page so sidebar works normally after
    if st.session_state.get("sub_page") == "🌌 Mission Control":
        st.session_state.sub_page = None

    render_hero_image("Earth", "Mission Control", "EARTH AT A GLANCE")
    st.markdown("<div class='section-heading'>Mission Control — Earth at a Glance</div>", unsafe_allow_html=True)

    # ── Rotating 3D Earth globe ──
    st.markdown("<div class='section-heading'>Rotating Earth — Tectonic Plates</div>", unsafe_allow_html=True)
    plate_centers = {
        "Pacific":(-10,-170),"North American":(50,-100),"South American":(-15,-60),
        "Eurasian":(50,60),"African":(5,25),"Australian":(-25,130),
        "Antarctic":(-75,0),"Indian":(20,75),"Arabian":(25,45),
        "Caribbean":(15,-75),"Nazca":(-15,-85),"Philippine":(15,130),
    }
    lats_g = [v[0] for v in plate_centers.values()]
    lons_g = [v[1] for v in plate_centers.values()]
    names_g = list(plate_centers.keys())
    fig_globe = go.Figure()
    fig_globe.add_trace(go.Scattergeo(
        lat=lats_g, lon=lons_g, text=names_g,
        mode="markers+text", textposition="top center",
        marker=dict(size=10, color="#c9a84c",
                    line=dict(width=1.5, color="rgba(240,216,120,0.6)")),
        textfont=dict(color="#f0e6d0", size=9, family="Source Sans 3"),
        hovertemplate="<b>%{text}</b> Plate<extra></extra>",
        name="Plates"
    ))
    fig_globe.add_trace(go.Scattergeo(
        lat=[20.5937], lon=[78.9629], text=["India"],
        mode="markers+text",
        marker=dict(size=14, color="#e8c96a", symbol="star"),
        textfont=dict(color="#e8c96a", size=12, family="Playfair Display"),
        hovertemplate="<b>India</b> — Indian Plate — Moving NNE ~5 cm/yr<extra></extra>",
        name="India"
    ))
    fig_globe.update_geos(
        projection_type="orthographic",
        showland=True,  landcolor="#1a2a18",
        showocean=True, oceancolor="#070b18",
        showlakes=True, lakecolor="#0c1428",
        showcountries=True, countrycolor="rgba(201,168,76,0.15)",
        showcoastlines=True, coastlinecolor="rgba(201,168,76,0.4)",
        bgcolor="rgba(0,0,0,0)", showframe=False,
        projection_rotation=dict(lon=78, lat=20, roll=0),
    )
    fig_globe.update_layout(
        height=460, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0"),
        margin=dict(l=0,r=0,t=0,b=0), showlegend=False,
        updatemenus=[dict(
            type="buttons", showactive=False, direction="left",
            buttons=[
                dict(
                    label="▶ Rotate",
                    method="animate",
                    args=[None, dict(frame=dict(duration=80, redraw=True),
                                      fromcurrent=True, mode="immediate",
                                      transition=dict(duration=0))]
                ),
                dict(
                    label="⏸ Pause",
                    method="animate",
                    args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode="immediate",
                                        transition=dict(duration=0))]
                ),
            ],
            x=0.05, y=0.05, bgcolor="rgba(201,168,76,0.15)",
            font=dict(color="#c9a84c", size=11),
            bordercolor="rgba(201,168,76,0.3)", borderwidth=1,
        )]
    )
    # Add animation frames for rotation
    frames = []
    for lon_r in range(0, 360, 4):
        frames.append(go.Frame(
            layout=dict(geo=dict(projection_rotation=dict(lon=lon_r, lat=20, roll=0)))
        ))
    fig_globe.frames = frames
    st.plotly_chart(fig_globe, use_container_width=True)

    # ── Radial dial menu for remaining pages ──
    st.markdown("<div class='section-heading'>Explore — All Sections</div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='color:#8a7d65;font-size:0.85rem;margin-bottom:16px;font-family:Source Sans 3,sans-serif;'>
    Click any section below to open it directly from Mission Control.
    </div>
    <style>
    div[data-testid="stButton"] > button {
        transition: box-shadow 0.25s ease, border-color 0.25s ease, transform 0.15s ease;
    }
    div[data-testid="stButton"] > button:hover {
        box-shadow: 0 0 14px rgba(201,168,76,0.55), 0 0 28px rgba(0,212,255,0.18);
        border-color: rgba(201,168,76,0.6) !important;
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)

    EXTRA_PAGES = [
        ("🗺️","Geological Map",      "pages/1_Geological_Map.py"),
        ("🌋","Plate Tectonics",     "pages/2_Plate_Tectonics.py"),
        ("🪨","Rock Explorer",       "pages/3_Rock_Explorer.py"),
        ("💎","Mineral Explorer",    "pages/4_Mineral_Explorer.py"),
        ("🌍","Earthquake Dashboard","pages/5_Earthquake_Dashboard.py"),
        ("🌋","Volcano Explorer",    "pages/6_Volcano_Explorer.py"),
        ("📅","Geological Time Scale","pages/7_Geological_Time_Scale.py"),
        ("🧭","Structural Tools",    "pages/8_Structural_Tools.py"),
        ("🌿","Geography Explorer",  "pages/9_Geography_Explorer.py"),
        ("🌊","Watershed Explorer",  "pages/10_Watershed_Explorer.py"),
        ("🧪","Soil Explorer",       "pages/11_Soil_Explorer.py"),
        ("🪙","Economic Geology",    "pages/12_Economic_Geology.py"),
        ("🌊","Oceanography",        "pages/13_Oceanography.py"),
        ("🔬","Thin Section Gallery","pages/14_Thin_Section_Gallery.py"),
        ("📚","Semester Notes",      "pages/15_Semester_Notes.py"),
        ("🧠","Geo Quiz",            "pages/16_Geo_Quiz.py"),
        ("🃏","Flashcards",          "pages/17_Flashcards.py"),
        ("🤖","AI Assistant",        "pages/18_AI_Assistant.py"),
        ("📓","Field Diary",         "pages/19_Field_Diary.py"),
        ("🥚","About & Archive",     "pages/20_About.py"),
    ]
    dial_cols = st.columns(4)
    for i, (em, name, page_file) in enumerate(EXTRA_PAGES):
        with dial_cols[i % 4]:
            btn_label = urdu_label(f"{em} {name}")
            if st.button(btn_label, key=f"dial_{i}", use_container_width=True):
                st.switch_page(page_file)

    st.markdown("<br>", unsafe_allow_html=True)

# ── Today in Geology ─────────────────────────────────────────────────────────
import hashlib
_TODAY_EVENTS = [
    ("Jan 23","1556 — Shaanxi earthquake, China. ~830,000 deaths. Deadliest earthquake in recorded history."),
    ("Jan 17","1995 — Great Hanshin earthquake, Japan. M6.9. 6,434 dead. Triggered major reforms in seismic engineering."),
    ("Feb 28","1969 — M7.9 earthquake off Portugal coast — generated a tsunami affecting the Iberian Peninsula."),
    ("Mar 11","2011 — Tōhoku earthquake & tsunami, Japan. M9.0. 15,897 dead. Triggered Fukushima nuclear disaster."),
    ("Mar 27","1964 — Good Friday earthquake, Alaska. M9.2 — second largest ever recorded. Massive tsunamis."),
    ("Apr 18","1906 — San Francisco earthquake. M7.9. ~3,000 deaths. Defined modern understanding of fault systems."),
    ("Apr 25","2015 — Nepal earthquake. M7.8. 8,964 deaths. Caused Everest avalanche. India Plate collision zone."),
    ("May 18","1980 — Mt. St. Helens erupts, Washington. Largest volcanic eruption in US history — VEI 5."),
    ("May 22","1960 — Valdivia earthquake, Chile. M9.5. Strongest earthquake ever recorded. Tsunami hit India."),
    ("Jun 15","1991 — Mt. Pinatubo erupts, Philippines. VEI 6. Cooled global temperatures by 0.5°C for 2 years."),
    ("Jun 26","1941 — GSI (Geological Survey of India) began systematic seismic zoning of India."),
    ("Jul  1","1858 — Darwin & Wallace jointly present natural selection theory — built on geological uniformitarianism."),
    ("Jul 17","1998 — Papua New Guinea tsunami. M7.0 submarine landslide. 2,200 deaths. Changed tsunami science."),
    ("Aug  8","1950 — Assam earthquake, India. M8.6. Brahmaputra valley. Changed river course permanently."),
    ("Aug 27","1883 — Krakatoa eruption. Heard 4,800 km away. Caused 'Year Without Summer' globally."),
    ("Sep  1","1923 — Great Kantō earthquake, Japan. M7.9. 142,807 dead. Tokyo and Yokohama destroyed."),
    ("Sep  8","1905 — Kangra earthquake, India. M7.8 — one of India's deadliest. ~19,800 deaths."),
    ("Oct  8","2005 — Kashmir earthquake. M7.6. 73,000+ deaths. Pakistan-India plate boundary."),
    ("Oct 23","2011 — Van earthquake, Turkey. M7.1. Alpine-Himalayan belt — same system as Indian Himalayas."),
    ("Nov 18","1929 — Grand Banks submarine landslide. Generated transatlantic telegraph cable breaks + tsunami."),
    ("Dec 26","2004 — Indian Ocean earthquake & tsunami. M9.1. 227,898 deaths across 14 countries."),
    ("Dec 28","1908 — Messina earthquake, Italy. M7.1. ~75,000-200,000 deaths. Led to first modern building codes."),
]
import datetime as _dt
_today = _dt.datetime.now()
_key = f"{_today.month:02d}-{_today.day:02d}"
_event = None
for date_str, event in _TODAY_EVENTS:
    _m, _d = date_str.strip().split()
    _months = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
    if _months.get(_m) == _today.month and int(_d) == _today.day:
        _event = event
        break
if not _event:
    # Pick a random but deterministic event for the day
    _idx = int(hashlib.md5(f"{_today.month}{_today.day}".encode()).hexdigest(), 16) % len(_TODAY_EVENTS)
    _event = _TODAY_EVENTS[_idx][1]

# Today in Geology card
st.markdown(f"""
<div class='glass-card' style='border-color:rgba(220,38,38,0.3);padding:14px 18px;margin-bottom:16px;'>
    <div style='color:#f87171;font-size:0.62rem;letter-spacing:2px;margin-bottom:6px;'>📅 TODAY IN GEOLOGY — {_today.strftime("%d %B")}</div>
    <div style='color:#f0e6d0;font-size:0.85rem;line-height:1.7;font-family:Spectral,Georgia,serif;font-style:italic;'>{_event}</div>
</div>""", unsafe_allow_html=True)

# Live USGS earthquake count (last 24h, M2.5+ worldwide) — real-time metric, cached 2 min
_live_eq_count = fetch_usgs_earthquake_count(days_back=1, min_magnitude=2.5)
_eq_val = f"{_live_eq_count}" if _live_eq_count is not None else "—"
_eq_sub = "M2.5+ · last 24h · live" if _live_eq_count is not None else "USGS feed unavailable"

metrics = [
    ("🌍","6,371 km","Earth Radius","Mean"),
    ("🏔️","8,849 m","Everest","World's highest"),
    ("🌊","11,034 m","Mariana Trench","Ocean floor"),
    ("⛰️","4.56 Ga","Earth Age","Billion years"),
    ("🌡️","5,500°C","Inner Core","Estimated temp"),
    ("🔢","15","Major Plates","Tectonic"),
    ("🌎", _eq_val, "Earthquakes Today", _eq_sub),
    ("🇮🇳","3.287M km²","India Area","7th largest"),
]
cols = st.columns(4)
for i, (ico, val, lbl, sub) in enumerate(metrics):
    with cols[i % 4]:
        live_dot = "<span style='display:inline-block;width:6px;height:6px;border-radius:50%;background:#10b981;margin-left:5px;animation:dot-pulse 1.6s infinite;box-shadow:0 0 6px #10b981;'></span>" if lbl == "Earthquakes Today" and _live_eq_count is not None else ""
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-icon'>{ico}</div>
            <div class='metric-value'>{val}{live_dot}</div>
            <div class='metric-label'>{lbl}</div>
            <div class='metric-delta'>{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
c1, c2 = st.columns([3, 2])
with c1:
    st.markdown("<div class='section-heading'>EARTH'S INTERIOR STRUCTURE</div>", unsafe_allow_html=True)
    layers     = ["Inner Core","Outer Core","Lower Mantle","Upper Mantle","Crust"]
    thick      = [1221, 2259, 2200, 640, 30]
    col_e      = ["#ff4444","#ff8800","#cc6600","#886622","#336633"]
    temps      = ["~5,500°C","~4,000–5,000°C","~1,000–3,700°C","~500–900°C","~0–200°C"]
    fig_e = go.Figure()
    for lay, th, cl, te in zip(layers, thick, col_e, temps):
        fig_e.add_trace(go.Bar(name=lay, x=[th], y=["Interior"], orientation="h",
            marker_color=cl, hovertemplate=f"<b>{lay}</b><br>Thickness: {th} km<br>Temp: {te}<extra></extra>"))
    fig_e.update_layout(barmode="stack", height=150,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0", family="Source Sans 3"),
        legend=dict(orientation="h", y=-1.1, font=dict(size=9, color="#f0e6d0"), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=5, r=5, t=5, b=90),
        xaxis=dict(title="Depth (km)", gridcolor="rgba(255,255,255,0.05)", color="#8a7d65"),
        yaxis=dict(visible=False))
    st.plotly_chart(fig_e, use_container_width=True)

    st.markdown("<div class='section-heading'>INDIA TECTONIC HIGHLIGHTS</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='glass-card' style='padding:10px 16px;margin-bottom:10px;'>
        <span style='color:#94a3b8;font-size:0.78rem;'>
        🗺️ Six defining tectonic features that shaped the subcontinent — tap any card to open its full profile,
        photos, and field trivia.
        </span>
    </div>""", unsafe_allow_html=True)
    facts_detail = [
        ("🏔️","Himalayas","Himalayas",
         "India–Eurasia collision ~50 Ma. Still rising 5mm/yr.",
         "Age","~50 Ma to present (Cenozoic)",
         "Rock Types","Sedimentary (Tethys shelf), Metamorphic (MCT zone), Granitic intrusions",
         "Key Structures","Main Central Thrust (MCT), Main Boundary Thrust (MBT), Main Frontal Thrust (MFT)",
         "Minerals","Gold placers, copper, lead-zinc, tourmaline, beryl in pegmatites",
         "Did you know?","The crustal root under the Himalayas is ~100 km thick — like an iceberg, most of the mountain is underground.",
         "Mount Everest"),
        ("🌋","Deccan Traps","Deccan Traps",
         "500,000 km² flood basalt erupted 66 Ma, linked to K-Pg extinction.",
         "Age","66–60 Ma (Late Cretaceous to Early Paleogene)",
         "Rock Types","Tholeiitic basalt — individual lava flows 10–50 m thick, stacked up to 2 km",
         "Key Structures","Dyke swarms, sills, columnar jointing, vesicles filled with zeolites & amethyst",
         "Minerals","Zeolites, amethyst (geode capital: Pune region), calcite, iron ore",
         "Did you know?","Ajanta and Ellora caves are carved entirely into Deccan basalt. The Lonar crater (Maharashtra) was created by a meteorite impact into Deccan Traps.",
         "Ellora Caves"),
        ("🪨","Indian Shield","Dharwar Craton",
         "Precambrian craton — some rocks 3.3 Ga old. India's stable geological core.",
         "Age","3.3 Ga (Archaean) to 600 Ma (Late Proterozoic)",
         "Rock Types","Gneiss, greenstone belts, granites, schists — Dharwar & Singhbhum cratons",
         "Key Structures","Greenstone belts (BIF iron ore), shear zones, charnockite massifs",
         "Minerals","Iron ore (BIF), gold (Kolar), manganese, chromite, copper",
         "Did you know?","The Dharwar craton contains some of India's oldest exposed rocks (~3.3 Ga) near the Karnataka–Andhra Pradesh border. Jack Hills, Australia has older zircons (4.4 Ga) but no exposed rock that old.",
         "Banded iron formation"),
        ("💎","Eastern Ghats","Eastern Ghats",
         "High-grade granulite belt — charnockites, khondalites. Rich in industrial minerals.",
         "Age","Proterozoic (1.6–0.5 Ga)",
         "Rock Types","Charnockite, khondalite, leptynite, quartzofeldspathic gneiss — granulite facies",
         "Key Structures","Banded gneisses, migmatites, shear zones parallel to coast",
         "Minerals","Graphite, corundum, chromite, bauxite, sillimanite, garnet",
         "Did you know?","Charnockite is unique to India — named after Job Charnock's tombstone in Chennai (St. Thomas Mount). It's the deepest crustal rock exposed at the surface anywhere.",
         "Charnockite"),
        ("🌊","Andaman Arc","Barren Island",
         "Active subduction zone. Barren Island volcano. 2004 M9.1 tsunami epicentre.",
         "Age","Cenozoic (50 Ma to present)",
         "Rock Types","Ophiolite (peridotite, gabbro, basalt), volcanic arc andesites, flysch sediments",
         "Key Structures","Trench, forearc basin, volcanic arc, backarc basin — classic subduction geometry",
         "Minerals","Chromite in ophiolite, manganese nodules on seafloor",
         "Did you know?","The 2004 Indian Ocean tsunami (M9.1) ruptured ~1,300 km of the Andaman-Sumatra subduction zone. The seafloor moved up to 15 m horizontally and 5 m vertically in minutes.",
         "2004 Indian Ocean earthquake and tsunami"),
        ("🔥","Koyna Seismic Zone","Koyna Dam",
         "Reservoir-triggered seismicity (RTS). India's deadliest intraplate quake M6.5 in 1967.",
         "Age","Active — post-dam construction (1962 onward)",
         "Rock Types","Deccan basalt (hard, brittle) — stress concentrates along pre-existing fault lines",
         "Key Structures","NE-trending faults reactivated by water load of Koyna reservoir",
         "Minerals","Not applicable — significance is seismic hazard, not mineral resources",
         "Did you know?","Before Koyna (1967), scientists didn't think filling a reservoir could trigger a large earthquake. It changed seismic hazard assessment worldwide — now all large dams are monitored for RTS.",
         "1967 Koynanagar earthquake"),
    ]

    fc_cols = st.columns(3)
    for i, fd in enumerate(facts_detail):
        em, nm, hero_topic, short = fd[0], fd[1], fd[2], fd[3]
        with fc_cols[i % 3]:
            st.markdown(f"""
            <div style='background:rgba(15,30,60,0.75);border:1px solid rgba(0,212,255,0.18);border-radius:14px 14px 0 0;
                padding:12px 14px 10px;margin-bottom:0;'>
                <div style='font-size:1.3rem;margin-bottom:5px;'>{em}</div>
                <div style='color:#00d4ff;font-weight:600;font-size:0.82rem;margin-bottom:3px;'>{nm}</div>
                <div style='color:#94a3b8;font-size:0.74rem;line-height:1.5;'>{short}</div>
            </div>""", unsafe_allow_html=True)
            show_wiki_photo(hero_topic, caption=nm)
            with st.expander(f"📖 Full profile — {nm}"):
                age_lbl, age_val   = fd[4], fd[5]
                rock_lbl, rock_val = fd[6], fd[7]
                struct_lbl, struct_val = fd[8], fd[9]
                min_lbl, min_val   = fd[10], fd[11]
                did_lbl, did_val   = fd[12], fd[13]
                detail_topic       = fd[14]
                show_wiki_photo(detail_topic, caption=f"{nm} — related feature")
                st.markdown(f"""
                <div style='color:#94a3b8;font-size:0.78rem;line-height:2;'>
                🕐 <b style='color:#e2e8f0;'>{age_lbl}:</b> {age_val}<br>
                🪨 <b style='color:#e2e8f0;'>{rock_lbl}:</b> {rock_val}<br>
                🔩 <b style='color:#e2e8f0;'>{struct_lbl}:</b> {struct_val}<br>
                💎 <b style='color:#e2e8f0;'>{min_lbl}:</b> {min_val}
                </div>
                <div style='color:#f59e0b;margin-top:10px;font-size:0.78rem;'><b>💡 {did_lbl}</b></div>
                <div style='color:#cbd5e1;font-style:italic;font-size:0.76rem;line-height:1.6;'>{did_val}</div>
                """, unsafe_allow_html=True)

with c2:
    st.markdown("<div class='section-heading'>MINERAL RESERVES</div>", unsafe_allow_html=True)
    m_in = {"Iron Ore":28,"Coal":22,"Bauxite":12,"Limestone":11,"Copper":9,"Manganese":8,"Zinc-Lead":6,"Others":4}
    fig_p = go.Figure(go.Pie(labels=list(m_in.keys()), values=list(m_in.values()), hole=0.42,
        marker=dict(colors=["#ef4444","#374151","#92400e","#e5e7eb","#f97316","#7c3aed","#6b7280","#10b981"])))
    fig_p.update_traces(textfont_color="#f0e6d0",
        hovertemplate="<b>%{label}</b><br>Share: %{percent}<extra></extra>")
    fig_p.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#f0e6d0", family="Source Sans 3"),
        legend=dict(font=dict(size=9, color="#f0e6d0"), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=5,r=5,t=5,b=5), height=270,
        annotations=[dict(text="India", x=0.5, y=0.5, showarrow=False,
            font=dict(color="#8a7d65", size=11))])
    st.plotly_chart(fig_p, use_container_width=True)

    st.markdown("<div class='section-heading'>SEISMIC ZONES</div>", unsafe_allow_html=True)
    sz = {"Zone II\n(Low)":10,"Zone III\n(Moderate)":30,"Zone IV\n(High)":25,"Zone V\n(Very High)":35}
    fig_sz = go.Figure(go.Bar(x=list(sz.keys()), y=list(sz.values()),
        marker_color=["#10b981","#f59e0b","#f87171","#dc2626"],
        text=[f"{v}%" for v in sz.values()], textposition="outside", textfont_color="#f0e6d0"))
    fig_sz.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a7d65", family="Source Sans 3"), height=230,
        margin=dict(l=5,r=5,t=5,b=5),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        xaxis=dict(tickfont=dict(size=9)))
    st.plotly_chart(fig_sz, use_container_width=True)

