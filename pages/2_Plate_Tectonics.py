# GeoSphere India — Plate Tectonics
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

st.set_page_config(page_title="Plate Tectonics — GeoSphere India", page_icon="🌋", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Plate tectonics", "Plate Tectonics", "INDIA'S TECTONIC JOURNEY")

st.markdown("<div class='section-heading'>PLATE TECTONICS SIMULATOR — INDIA'S TECTONIC JOURNEY</div>", unsafe_allow_html=True)

if "pt_animating" not in st.session_state:
    st.session_state.pt_animating = False
if "pt_ma" not in st.session_state:
    st.session_state.pt_ma = 50

pcol1, pcol2 = st.columns([1, 5])
with pcol1:
    if st.session_state.pt_animating:
        if st.button("⏸ Pause"):
            st.session_state.pt_animating = False
            st.rerun()
    else:
        if st.button("▶ Animate"):
            st.session_state.pt_animating = True
            st.rerun()
with pcol2:
    ma = st.slider("⏱️ Time (Million Years Ago → Present)", min_value=0, max_value=100,
                   value=st.session_state.pt_ma, step=5, format="%d Ma",
                   disabled=st.session_state.pt_animating)
    if not st.session_state.pt_animating:
        st.session_state.pt_ma = ma
    else:
        ma = st.session_state.pt_ma
    st.caption("◀ 100 Ma (Gondwana breakup)  ·  ·  ·  Present day (0 Ma) ▶")

# Interpolate India plate position
india_lat_start = -10  # 100 Ma — southern hemisphere
india_lat_end   =  20  # 0 Ma — present
india_lat = india_lat_start + (india_lat_end - india_lat_start) * (1 - ma / 100)

eurasia_lat = 45

stage = "Moving northward through the Tethys Ocean"
if ma <= 10:   stage = "Active collision — Himalayas rising rapidly"
elif ma <= 50: stage = "Continental collision phase — suture forming"
elif ma <= 80: stage = "Rapid northward drift — 15–20 cm/yr!"

fig_tec = go.Figure()
# Eurasian plate
fig_tec.add_trace(go.Scattergeo(
    lat=[eurasia_lat, eurasia_lat, eurasia_lat+12, eurasia_lat+12, eurasia_lat],
    lon=[60, 110, 110, 60, 60],
    fill="toself", fillcolor="rgba(245,158,11,0.2)",
    line=dict(color="#f59e0b", width=2), name="Eurasian Plate", mode="lines",
    hoverinfo="name"
))
# Indian plate
fig_tec.add_trace(go.Scattergeo(
    lat=[india_lat, india_lat, india_lat+16, india_lat+16, india_lat],
    lon=[68, 98, 98, 68, 68],
    fill="toself", fillcolor="rgba(0,212,255,0.2)",
    line=dict(color="#00d4ff", width=2), name="Indian Plate", mode="lines",
    hoverinfo="name"
))
# Movement arrow
if ma > 0:
    fig_tec.add_trace(go.Scattergeo(
        lat=[india_lat + 8, india_lat + 14],
        lon=[83, 83],
        mode="lines+markers",
        line=dict(color="#10b981", width=3),
        marker=dict(size=[0, 14], symbol=["circle", "arrow-up"], color="#10b981"),
        name="Movement Direction", hoverinfo="skip"
    ))
# Himalaya label
if ma <= 50:
    fig_tec.add_trace(go.Scattergeo(
        lat=[32], lon=[78],
        mode="markers+text",
        marker=dict(size=12, color="#f59e0b", symbol="triangle-up"),
        text=["🏔️ Himalayas"], textfont=dict(color="#f59e0b", size=11),
        textposition="top right", name="Himalayas", hoverinfo="skip"
    ))

fig_tec.update_geos(
    lonaxis_range=[50, 120], lataxis_range=[-20, 65],
    showland=True, landcolor="#1a2a1a",
    showocean=True, oceancolor="#020817",
    showcountries=True, countrycolor="rgba(255,255,255,0.1)",
    showcoastlines=True, coastlinecolor="rgba(0,212,255,0.3)",
    bgcolor="rgba(0,0,0,0)", showframe=False,
)
fig_tec.update_layout(
    height=450, paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f0e6d0"),
    margin=dict(l=0,r=0,t=0,b=0),
    legend=dict(bgcolor="rgba(10,22,40,0.85)", font=dict(size=11, color="#f0e6d0"))
)
st.plotly_chart(fig_tec, use_container_width=True)

if st.session_state.pt_animating:
    time.sleep(0.5)
    st.session_state.pt_ma = (st.session_state.pt_ma - 5) % 105
    if st.session_state.pt_ma > 100:
        st.session_state.pt_ma = 0
    st.rerun()

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-icon'>⏱️</div>
        <div class='metric-value'>{ma} Ma</div>
        <div class='metric-label'>Time</div>
    </div>""", unsafe_allow_html=True)
with c2:
    drift = round(5 + (ma / 100) * 15, 1)
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-icon'>🚀</div>
        <div class='metric-value'>{drift} cm/yr</div>
        <div class='metric-label'>Drift Speed</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-icon'>🌋</div>
        <div class='metric-value'>{round(india_lat, 1)}°</div>
        <div class='metric-label'>India Latitude</div>
    </div>""", unsafe_allow_html=True)

st.markdown(f"""
<div class='glass-card' style='text-align:center;margin-top:8px;'>
    <span style='color:#00d4ff;font-family:Orbitron,sans-serif;font-size:0.75rem;letter-spacing:2px;'>
    TECTONIC STAGE:</span><br>
    <span style='color:#e2e8f0;font-size:0.9rem;margin-top:6px;display:block;'>{stage}</span>
</div>""", unsafe_allow_html=True)

# Key events timeline — now with Wikipedia photos per event
st.markdown("<div class='section-heading'>KEY TECTONIC EVENTS</div>", unsafe_allow_html=True)
events = [
    (180,"Gondwana Breakup","India begins separating from Antarctica/Africa","Gondwana"),
    (130,"India Rift","India + Madagascar separate from main Gondwana","Madagascar"),
    (90,"Rapid Drift","India alone — moves 15–20 cm/yr northward","Indian Ocean"),
    (66,"Deccan Traps","Hotspot volcanism as India passes over Réunion hotspot","Deccan Traps"),
    (50,"First Contact","India touches Eurasia — Tethys Sea closes","Tethys Ocean"),
    (40,"Suture Formed","Indus-Tsangpo suture zone — ocean completely closed","Yarlung Tsangpo"),
    (20,"Himalayas Rise","Thrust faults active — mountains rapidly gaining height","Himalayas"),
    (0,"Present","India still moving 5 cm/yr NNE; Himalayas still growing","Mount Everest"),
]
ev_cols = st.columns(4)
for i, (ma_e, title, detail, wiki_topic) in enumerate(events):
    with ev_cols[i % 4]:
        show_wiki_photo(wiki_topic, caption=f"{ma_e} Ma — {title}")
        st.markdown(f"""
        <div class='glass-card' style='padding:10px 12px;margin-top:-6px;'>
            <div style='color:#00d4ff;font-size:0.72rem;font-weight:600;'>{ma_e} Ma · {title}</div>
            <div style='color:#94a3b8;font-size:0.7rem;line-height:1.5;margin-top:4px;'>{detail}</div>
        </div>""", unsafe_allow_html=True)

# ── Subduction cross-section animation (Andaman–Sunda arc style) ──────────────
st.markdown("<div class='section-heading'>SUBDUCTION CROSS-SECTION — HOW IT WORKS</div>", unsafe_allow_html=True)
st.markdown("""
<div class='glass-card' style='padding:10px 16px;margin-bottom:10px;'>
    <span style='color:#94a3b8;font-size:0.78rem;'>
    🌋 The oceanic plate (blue) continuously sinks beneath the overriding plate at the trench. As it
    descends, it releases fluids that melt the mantle above it — that melt rises and feeds the volcanoes
    of the overriding arc. This is exactly the setup active today beneath Barren Island in the Andaman Sea.
    </span>
</div>""", unsafe_allow_html=True)

import streamlit.components.v1 as _subc
_subc.html("""
<!DOCTYPE html>
<html>
<head>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#070b18; overflow:hidden; }
svg { width:100%; height:340px; display:block; }

/* Oceanic plate + subducting slab conveyor motion */
.slab { animation: slabmove 4s linear infinite; }
@keyframes slabmove {
  0%   { transform: translate(0px, 0px); }
  100% { transform: translate(-14px, 7px); }
}

/* Magma blobs rising from slab to volcano conduit */
.magma { offset-rotate: 0deg; animation: rise 3.2s linear infinite; opacity:0; }
.magma.m2 { animation-delay: 0.8s; }
.magma.m3 { animation-delay: 1.6s; }
.magma.m4 { animation-delay: 2.4s; }
@keyframes rise {
  0%   { offset-distance: 0%;  opacity: 0; }
  8%   { opacity: 1; }
  92%  { opacity: 1; }
  100% { offset-distance: 100%; opacity: 0; }
}

/* Volcano crater glow pulse */
.craterglow { animation: glow 2.4s ease-in-out infinite; }
@keyframes glow {
  0%,100% { opacity: 0.5; r: 7; }
  50%     { opacity: 1;   r: 11; }
}

/* Smoke puffs from the volcano */
.smoke { animation: smoke 4s ease-out infinite; opacity:0; }
.smoke.s2 { animation-delay: 1.3s; }
.smoke.s3 { animation-delay: 2.6s; }
@keyframes smoke {
  0%   { transform: translate(0,0) scale(0.4); opacity: 0; }
  15%  { opacity: 0.55; }
  100% { transform: translate(8px,-70px) scale(1.6); opacity: 0; }
}

.lbl { font-family: Arial, sans-serif; fill:#f0e6d0; }
</style>
</head>
<body>
<svg viewBox="0 0 700 340" preserveAspectRatio="xMidYMid meet">
  <!-- Mantle background -->
  <rect x="0" y="0" width="700" height="340" fill="#1a0f05"/>
  <rect x="0" y="0" width="700" height="150" fill="#070b18"/>

  <!-- Continental / arc plate (right, overriding) -->
  <path d="M330,150 L420,150 L470,60 L520,150 L700,150 L700,220 L330,220 Z" fill="#4b3621"/>
  <!-- Volcano cone on the arc -->
  <path d="M420,150 L470,60 L520,150 Z" fill="#5a4530"/>
  <circle class="craterglow" cx="470" cy="66" r="8" fill="#ff6600"/>

  <!-- Oceanic plate + subducting slab (moving group) -->
  <g class="slab">
    <path d="M0,150 L330,150 L470,300 L470,340 L0,340 Z" fill="#0c4a6e"/>
    <path d="M0,150 L330,150 L470,300 L440,300 L20,165 L0,165 Z" fill="#0284c7"/>
  </g>

  <!-- Trench marker -->
  <path d="M320,150 L340,150 L330,168 Z" fill="#0ea5e9"/>
  <text x="270" y="185" class="lbl" font-size="13">Trench</text>

  <!-- Motion path for rising magma (invisible guide) -->
  <path id="magmaPath" d="M300,250 Q380,170 465,100" fill="none" stroke="none"/>
  <circle class="magma m1" r="5" fill="#f59e0b" style="offset-path:path('M300,250 Q380,170 465,100');"/>
  <circle class="magma m2" r="4" fill="#fbbf24" style="offset-path:path('M300,250 Q380,170 465,100');"/>
  <circle class="magma m3" r="5" fill="#f59e0b" style="offset-path:path('M300,250 Q380,170 465,100');"/>
  <circle class="magma m4" r="4" fill="#fbbf24" style="offset-path:path('M300,250 Q380,170 465,100');"/>

  <!-- Smoke from crater -->
  <circle class="smoke s1" cx="470" cy="55" r="9" fill="#8a7d65" opacity="0.5"/>
  <circle class="smoke s2" cx="470" cy="55" r="9" fill="#8a7d65" opacity="0.5"/>
  <circle class="smoke s3" cx="470" cy="55" r="9" fill="#8a7d65" opacity="0.5"/>

  <!-- Labels -->
  <text x="60"  y="230" class="lbl" font-size="14" font-weight="bold" fill="#0ea5e9">Subducting Oceanic Plate</text>
  <text x="520" y="230" class="lbl" font-size="14" font-weight="bold" fill="#c9a84c">Overriding Plate (Arc)</text>
  <text x="430" y="45"  class="lbl" font-size="13" fill="#dc2626">Volcanic Arc</text>
  <text x="340" y="200" class="lbl" font-size="11" fill="#94a3b8">Rising melt →</text>
  <text x="15"  y="30"  class="lbl" font-size="11" fill="#475569">Mantle</text>
</svg>
</body>
</html>
""", height=350, scrolling=False)
st.caption("Magma rises continuously from the subducting slab to feed the volcanic arc — press nothing, it just runs, like the real process (only much faster).")
