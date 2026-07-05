# GeoSphere India — Geological Time Scale
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

st.set_page_config(page_title="Geological Time Scale — GeoSphere India", page_icon="📅", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Geologic time scale", "Geological Time Scale", "4.6 BILLION YEARS")

st.markdown("<div class='section-heading'>GEOLOGICAL TIME SCALE — 4.6 BILLION YEARS</div>", unsafe_allow_html=True)

fig_ts = go.Figure()
for i, period in enumerate(GEOLOGIC_TIME):
    end   = GEOLOGIC_TIME[i-1]["start"] if i > 0 else 0
    start = period["start"]
    width = start - end
    fig_ts.add_trace(go.Bar(
        name=period["period"] if period["period"] != "—" else period["era"],
        x=[width], y=[f'{period["era"] if period["era"]!="—" else period["eon"]}'],
        orientation="h",
        marker_color=period["color"],
        hovertemplate=f"<b>{period['period']}</b><br>{period['eon']} Eon · {period['era']} Era<br>"
                      f"Start: {period['start']} Ma<br>Life: {period['life']}<extra></extra>",
    ))

fig_ts.update_layout(
    barmode="stack", height=350,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f0e6d0", family="Source Sans 3"),
    legend=dict(orientation="h", y=-0.5, font=dict(size=8, color="#f0e6d0"), bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=10,r=10,t=10,b=120),
    xaxis=dict(title="Millions of Years Ago", gridcolor="rgba(255,255,255,0.05)", color="#8a7d65",
               autorange="reversed"),
    yaxis=dict(color="#8a7d65"),
)
st.plotly_chart(fig_ts, use_container_width=True)

# Detail table
st.markdown("<div class='section-heading'>PERIOD DETAILS</div>", unsafe_allow_html=True)
sel_p = st.selectbox("Select a Period", [
    f"{g['period'] if g['period']!='—' else g['era']} ({g['start']} Ma)"
    for g in GEOLOGIC_TIME])
idx_p = [f"{g['period'] if g['period']!='—' else g['era']} ({g['start']} Ma)"
         for g in GEOLOGIC_TIME].index(sel_p)
gp = GEOLOGIC_TIME[idx_p]

st.markdown(f"""
<div class='glass-card' style='border-color:{gp["color"]}55;'>
    <div style='display:grid;grid-template-columns:1fr 1fr;gap:16px;'>
        <div>
            <div style='color:{gp["color"]};font-family:Orbitron;font-size:0.85rem;margin-bottom:10px;'>
            {gp["period"] if gp["period"]!="—" else gp["era"]}
            </div>
            <div style='color:#94a3b8;font-size:0.8rem;line-height:2;'>
            🌐 <b style='color:#e2e8f0;'>Eon:</b> {gp["eon"]}<br>
            🌍 <b style='color:#e2e8f0;'>Era:</b> {gp["era"]}<br>
            🕐 <b style='color:#e2e8f0;'>Start:</b> {gp["start"]} Ma
            </div>
        </div>
        <div style='color:#94a3b8;font-size:0.8rem;'>
            🦎 <b style='color:#e2e8f0;'>Life & Events:</b><br><br>
            <span style='line-height:1.8;'>{gp["life"]}</span>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

_period_key = gp["period"] if gp["period"] != "—" else gp["eon"]
_fossil_topic = INDEX_FOSSILS.get(_period_key)
fc1, fc2 = st.columns([1, 2])
with fc1:
    if _fossil_topic:
        show_wiki_photo(_fossil_topic, caption=f"Index fossil: {_fossil_topic}")
    else:
        st.info("No index fossil — Earth had not yet formed life at this stage.")
with fc2:
    st.markdown(f"""
    <div class='glass-card' style='height:100%;'>
        <div style='color:#c9a84c;font-size:0.75rem;letter-spacing:1.5px;margin-bottom:6px;'>🦴 INDEX FOSSIL</div>
        <div style='color:#e2e8f0;font-size:0.9rem;font-weight:600;'>{_fossil_topic or "None for this eon"}</div>
        <div style='color:#94a3b8;font-size:0.75rem;margin-top:8px;line-height:1.6;'>
        Index fossils are species that were geographically widespread but existed for a narrow time span —
        finding one in a rock layer pins down its age precisely, even across continents.
        </div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div class='section-heading'>INDIA'S STORY THROUGH GEOLOGICAL TIME</div>", unsafe_allow_html=True)
_india_tl = [
    ("Hadean–Archean","4600–2500 Ma","Formation of Dharwar & Singhbhum cratons — India's ancient stable cores. Oldest Indian rocks >3 Ga (Karnataka, Jharkhand).","23:58:43","17 sec before midnight"),
    ("Proterozoic","2500–541 Ma","Aravalli-Delhi orogeny. Vindhyan Supergroup deposition (sandstone, shale, limestone). India part of proto-Gondwana.","21:00","9 pm on the 24h scale"),
    ("Palaeozoic","541–252 Ma","India firmly in Gondwana. Gondwana Supergroup begins (coal swamps, Glossopteris flora across all southern continents).","22:30","10:30 pm"),
    ("Mesozoic","252–66 Ma","Gondwana breaks up. India drifts north as an island. Jurassic marine sediments in Kutch. Rajasaurus roams the subcontinent.","23:30","11:30 pm"),
    ("K-Pg Boundary","66 Ma","Deccan Traps erupt (500,000 km² basalt). Combined with Chicxulub asteroid — mass extinction wipes out 75% of species.","23:49","11:49 pm"),
    ("Cenozoic","66–0 Ma","India collides with Eurasia ~50 Ma → Himalayas rise. Indo-Gangetic plain forms. Human ancestors appear in Siwalik fauna 2 Ma.","23:59:58","2 sec before midnight"),
]
for eon, trange, story, clock, clabel in _india_tl:
    st.markdown(f"""
    <div class='glass-card' style='display:flex;gap:14px;padding:13px;align-items:start;'>
        <div style='min-width:90px;text-align:center;flex-shrink:0;'>
            <div style='color:#c9a84c;font-family:Orbitron;font-size:0.75rem;'>{eon}</div>
            <div style='color:#475569;font-size:0.62rem;margin-top:2px;'>{trange}</div>
            <div style='color:#10b981;font-size:0.65rem;margin-top:6px;border-top:1px solid rgba(16,185,129,0.2);padding-top:4px;'>🕐 {clock}</div>
            <div style='color:#475569;font-size:0.58rem;'>{clabel}</div>
        </div>
        <div style='color:#94a3b8;font-size:0.78rem;line-height:1.7;border-left:1px solid rgba(201,168,76,0.18);padding-left:13px;'>{story}</div>
    </div>""", unsafe_allow_html=True)
