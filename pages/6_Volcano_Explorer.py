# GeoSphere India — Volcano Explorer
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

st.set_page_config(page_title="Volcano Explorer — GeoSphere India", page_icon="🌋", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Volcano", "Volcano Explorer", "BARREN ISLAND · NARCONDAM · GLOBAL")

st.markdown("<div class='section-heading'>VOLCANO EXPLORER — BARREN ISLAND · NARCONDAM · GLOBAL</div>", unsafe_allow_html=True)

# ── Volcano eruption video (real footage, replaces the old CSS animation) ──
_volcano_video_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "volcano_eruption.mp4")
_volcano_video_b64 = None
try:
    with open(_volcano_video_path, "rb") as _vf:
        _volcano_video_b64 = base64.b64encode(_vf.read()).decode()
except Exception:
    _volcano_video_b64 = None

import streamlit.components.v1 as _vc
if _volcano_video_b64:
    _vc.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background:#070b18; }}
    .vwrap {{
        position:relative; width:100%; height:260px; border-radius:14px; overflow:hidden;
        border:1px solid rgba(201,168,76,0.25); box-shadow:0 0 30px rgba(220,38,38,0.15);
    }}
    video {{ width:100%; height:100%; object-fit:cover; display:block; }}
    .vlabel {{
        position:absolute; bottom:12px; left:50%; transform:translateX(-50%);
        color:#f0e6d0; font-family:'Orbitron',monospace; font-size:11px;
        letter-spacing:2px; white-space:nowrap; background:rgba(7,11,24,0.55);
        padding:5px 14px; border-radius:20px; text-shadow:0 0 8px rgba(220,38,38,0.6);
    }}
    </style>
    </head>
    <body>
    <div class='vwrap'>
        <video id='volcanoVid' autoplay muted loop playsinline webkit-playsinline="true" disablepictureinpicture disableremoteplayback>
            <source src='data:video/mp4;base64,{_volcano_video_b64}' type='video/mp4'>
        </video>
        <div class='vlabel'>🌋 BARREN ISLAND — INDIA'S ONLY ACTIVE VOLCANO</div>
    </div>
    <script>
    // Belt-and-braces: some mobile browsers ignore the autoplay attribute inside
    // an iframe unless .play() is also called explicitly in JS. This guarantees
    // it behaves like a looping GIF — never a click-to-play video.
    var __v = document.getElementById('volcanoVid');
    function __tryPlay() {{ var p = __v.play(); if (p !== undefined) {{ p.catch(function(){{}}); }} }}
    __v.addEventListener('loadedmetadata', __tryPlay);
    __v.addEventListener('canplay', __tryPlay);
    document.addEventListener('visibilitychange', function() {{ if (!document.hidden) __tryPlay(); }});
    __tryPlay();
    </script>
    </body>
    </html>
    """, height=270, scrolling=False)
else:
    show_wiki_photo("Barren Island (India)", caption="Barren Island — India's only active volcano")

fig_v = go.Figure()
for v in VOLCANOES:
    color = "#dc2626" if v["status"] == "Active" else "#f59e0b"
    size  = 17 if v["country"] == "India" else 12
    fig_v.add_trace(go.Scattergeo(
        lat=[v["lat"]], lon=[v["lon"]],
        mode="markers+text", text=[v["name"]],
        textposition="top center",
        marker=dict(size=size, color=color, symbol="triangle-up",
                    line=dict(width=2, color="rgba(255,255,255,0.6)")),
        textfont=dict(color="#ffffff", size=12 if v["country"]=="India" else 10, family="Arial Black"),
        name=v["name"],
        hovertemplate=f"<b>{v['name']}</b><br>Country: {v['country']}<br>Status: {v['status']}<br>Type: {v['type']}<br>Last eruption: {v['last_eruption']}<extra></extra>",
    ))

fig_v.update_geos(showland=True, landcolor="#0f1e0f", showocean=True, oceancolor="#020817",
    showcountries=True, countrycolor="rgba(255,255,255,0.1)",
    showcoastlines=True, coastlinecolor="rgba(0,212,255,0.3)",
    bgcolor="rgba(0,0,0,0)", showframe=False)
fig_v.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
st.plotly_chart(fig_v, use_container_width=True)

st.markdown("<div class='section-heading'>VOLCANO PROFILES</div>", unsafe_allow_html=True)
v_cols = st.columns(2)
for i, v in enumerate(VOLCANOES):
    with v_cols[i % 2]:
        status_color = "#dc2626" if v["status"] == "Active" else "#f59e0b"
        india_badge = "🇮🇳" if v["country"] == "India" else "🌍"
        show_wiki_photo(v.get("wiki_photo", v["name"]), caption=v["name"])
        st.markdown(f"""
        <div class='mineral-card' style='border-color:{status_color}33;'>
            <div style='display:flex;justify-content:space-between;align-items:start;'>
                <div style='color:{status_color};font-family:Orbitron;font-size:0.82rem;'>
                🌋 {v["name"]} {india_badge}
                </div>
                <span style='font-size:0.65rem;background:{status_color}22;padding:2px 8px;
                border-radius:10px;color:{status_color};'>{v["status"]}</span>
            </div>
            <div style='color:#94a3b8;font-size:0.75rem;line-height:1.8;margin-top:8px;'>
            🏔️ Type: {v["type"]}<br>
            🌏 Location: {v["country"]}<br>
            🔥 Last Eruption: {v["last_eruption"]}<br>
            📋 {v["desc"]}
            </div>
        </div>""", unsafe_allow_html=True)


st.markdown("<div class='section-heading'>VEI — VOLCANIC EXPLOSIVITY INDEX</div>", unsafe_allow_html=True)
_vei = [
    (0,"Hawaiian","Barren Island","#ef4444","Continuous gentle effusion. Lava flows, no explosion."),
    (1,"Hawaiian/Strombolian","Stromboli","#f97316","Gentle. Small ash clouds. Very frequent."),
    (2,"Strombolian","Sakurajima","#f59e0b","Explosive bursts. Ash to 1 km. Eruptions every few weeks."),
    (3,"Vulcanian","Soufrière Hills","#eab308","Moderate. Ash to 3-15 km. Once per year globally."),
    (4,"Sub-Plinian","Eyjafjallajökull 2010","#84cc16","Large eruption. 10-25 km ash column. Disrupts air travel."),
    (5,"Plinian","Mt. St. Helens 1980","#10b981","Very large. 25 km column. Once per 10 years."),
    (6,"Ultra-Plinian","Pinatubo 1991","#0ea5e9","Massive. Cooled global climate 0.5°C. Once per century."),
    (7,"Ultra-Plinian","Tambora 1815","#6366f1","Catastrophic. Year Without Summer. Once per 1,000 yrs."),
    (8,"Mega-colossal","Yellowstone (prehistoric)","#8b5cf6","Supervolcano. Civilisation-scale event. Once per 10,000+ yrs."),
]
_vei_cols = st.columns([1,3,2,3])
_vei_cols[0].markdown("<div style='color:#c9a84c;font-size:0.72rem;font-weight:600;'>VEI</div>", unsafe_allow_html=True)
_vei_cols[1].markdown("<div style='color:#c9a84c;font-size:0.72rem;font-weight:600;'>Type</div>", unsafe_allow_html=True)
_vei_cols[2].markdown("<div style='color:#c9a84c;font-size:0.72rem;font-weight:600;'>Example</div>", unsafe_allow_html=True)
_vei_cols[3].markdown("<div style='color:#c9a84c;font-size:0.72rem;font-weight:600;'>Description</div>", unsafe_allow_html=True)
for vei, vtype, example, col, desc in _vei:
    c1,c2,c3,c4 = st.columns([1,3,2,3])
    c1.markdown(f"<div style='color:{col};font-family:Orbitron;font-size:0.9rem;font-weight:700;padding:4px 0;'>{vei}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='color:#e2e8f0;font-size:0.78rem;padding:4px 0;'>{vtype}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='color:#94a3b8;font-size:0.75rem;padding:4px 0;'>{example}</div>", unsafe_allow_html=True)
    c4.markdown(f"<div style='color:#94a3b8;font-size:0.75rem;padding:4px 0;'>{desc}</div>", unsafe_allow_html=True)

st.markdown("<div class='section-heading'>BARREN ISLAND — INDIA'S ONLY ACTIVE VOLCANO</div>", unsafe_allow_html=True)
show_wiki_photo("Barren Island (India)", caption="Barren Island — India's only active volcano")
st.markdown("""
<div class='glass-card'>
    <div style='display:grid;grid-template-columns:1fr 1fr;gap:14px;'>
        <div style='color:#94a3b8;font-size:0.8rem;line-height:2;'>
            📍 <b style='color:#e2e8f0;'>Location:</b> Andaman Sea, 135 km NE of Port Blair<br>
            🌋 <b style='color:#e2e8f0;'>Type:</b> Stratovolcano (composite cone)<br>
            📏 <b style='color:#e2e8f0;'>Height:</b> 354 m above sea level<br>
            ⚗️ <b style='color:#e2e8f0;'>Magma type:</b> Basaltic-andesitic (subduction zone)<br>
            🧭 <b style='color:#e2e8f0;'>Setting:</b> Andaman-Sumatra subduction arc<br>
            🏝️ <b style='color:#e2e8f0;'>Access:</b> Day trips from Port Blair with permit
        </div>
        <div style='color:#94a3b8;font-size:0.8rem;line-height:2;'>
            📅 <b style='color:#e2e8f0;'>Eruption History:</b><br>
            1787 — First recorded eruption<br>
            1991 — Major eruption after 200-year dormancy<br>
            1994–95 — Continued activity<br>
            2005 — Activity after 2004 tsunami (M9.1)<br>
            2008–09 — Extended eruption period<br>
            2017 — Most recent confirmed activity<br>
        </div>
    </div>
    <div style='color:#94a3b8;font-size:0.78rem;margin-top:10px;border-top:1px solid rgba(255,255,255,0.07);padding-top:8px;line-height:1.7;'>
        <b style='color:#dc2626;'>Geological significance:</b> Barren Island sits on the Andaman arc, 
        formed by subduction of the Indian Plate beneath the Burma Plate. It is the only confirmed 
        active volcano in India and the broader South Asian region. The 2004 M9.1 earthquake 
        (same subduction zone) may have reactivated its magmatic system.
    </div>
</div>""", unsafe_allow_html=True)
