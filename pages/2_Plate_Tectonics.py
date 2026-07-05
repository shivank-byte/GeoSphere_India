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
    🌋 Schematic animation of an oceanic plate subducting beneath a continental/arc plate —
    the same process active today along the Andaman–Sunda Arc. Press ▶ Play.
    </span>
</div>""", unsafe_allow_html=True)

_sub_frames = []
_n_steps = 20
for step in range(_n_steps + 1):
    t = step / _n_steps
    # Oceanic slab dips progressively deeper as it "subducts" left-to-right
    slab_x = [0 + t*4, 6 + t*3, 10 + t*2]
    slab_y = [0, -3 - t*10, -8 - t*22]
    trench_x = 6 + t*3
    volcano_x = 10 + t*2 + 4
    _sub_frames.append(go.Frame(
        data=[
            go.Scatter(x=[-2, 22, 22, -2], y=[0, 0, 6, 6], fill="toself",
                       fillcolor="rgba(120,53,15,0.55)", line=dict(width=0), hoverinfo="skip", showlegend=False),
            go.Scatter(x=slab_x, y=slab_y, mode="lines", line=dict(color="#0284c7", width=10),
                       name="Subducting Oceanic Plate", hoverinfo="name"),
            go.Scatter(x=[volcano_x], y=[6], mode="markers+text", marker=dict(size=22, color="#dc2626", symbol="triangle-up"),
                       text=["🌋"], textposition="top center", name="Volcanic Arc", hoverinfo="name"),
            go.Scatter(x=[trench_x], y=[0.3], mode="markers+text", marker=dict(size=10, color="#0ea5e9"),
                       text=["Trench"], textposition="bottom center", textfont=dict(color="#0ea5e9", size=10),
                       name="Trench", hoverinfo="skip"),
        ],
        name=str(step)
    ))

fig_sub = go.Figure(
    data=_sub_frames[0].data,
    frames=_sub_frames,
)
fig_sub.update_layout(
    height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(4,10,24,0.4)",
    font=dict(color="#f0e6d0"),
    xaxis=dict(visible=False, range=[-2, 22]),
    yaxis=dict(visible=False, range=[-32, 10]),
    margin=dict(l=5,r=5,t=5,b=5), showlegend=True,
    legend=dict(bgcolor="rgba(10,22,40,0.85)", font=dict(size=10, color="#f0e6d0"), orientation="h", y=-0.05),
    updatemenus=[dict(
        type="buttons", showactive=False, direction="left",
        buttons=[
            dict(label="▶ Play", method="animate",
                 args=[None, dict(frame=dict(duration=120, redraw=True), fromcurrent=True, mode="immediate")]),
            dict(label="⏸ Pause", method="animate",
                 args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")]),
        ],
        x=0.02, y=1.08, bgcolor="rgba(201,168,76,0.15)",
        font=dict(color="#c9a84c", size=11), bordercolor="rgba(201,168,76,0.3)", borderwidth=1,
    )]
)
st.plotly_chart(fig_sub, use_container_width=True)
st.caption("As the denser oceanic plate sinks into the mantle (subducts), melting above the slab feeds a chain of volcanoes on the overriding plate — this is exactly the setup beneath Barren Island in the Andaman Sea.")

# ═══════════════════════════════════════════════════════════════
#  PAGE: ROCK EXPLORER
# ═══════════════════════════════════════════════════════════════