# GeoSphere India — Watershed Explorer
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

st.set_page_config(page_title="Watershed Explorer — GeoSphere India", page_icon="🌊", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("River", "Watershed Explorer", "RIVER BASINS OF INDIA")

st.markdown("<div class='section-heading'>WATERSHED & RIVER BASIN EXPLORER</div>", unsafe_allow_html=True)

sel_r = st.selectbox("Select River", [r["name"] for r in RIVERS])
rdata = next(r for r in RIVERS if r["name"] == sel_r)

c1, c2 = st.columns([2, 1])
with c1:
    show_wiki_photo(f"{rdata['name']} River", caption=f"{rdata['name']} River — reference photo (Wikipedia)")
    st.markdown(f"""
    <div class='glass-card'>
        <div style='color:#00d4ff;font-family:Orbitron;font-size:1rem;margin-bottom:14px;'>🌊 {rdata["name"]} River</div>
        <div style='color:#94a3b8;font-size:0.82rem;line-height:2.2;'>
        📏 <b style='color:#e2e8f0;'>Length:</b> {rdata["length_km"]:,} km<br>
        🏔️ <b style='color:#e2e8f0;'>Origin:</b> {rdata["origin"]}<br>
        🌊 <b style='color:#e2e8f0;'>Joins:</b> {rdata["joins"]}<br>
        📐 <b style='color:#e2e8f0;'>Basin Area:</b> {rdata["basin_km2"]:,} km²<br>
        🌿 <b style='color:#e2e8f0;'>Drainage Pattern:</b> {rdata["pattern"]}<br>
        🗺️ <b style='color:#e2e8f0;'>States:</b> {", ".join(rdata["states"])}<br>
        🌊 <b style='color:#e2e8f0;'>Major Tributaries:</b> {", ".join(rdata["tributaries"])}<br>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class='glass-card'>
        <div style='color:#f59e0b;font-family:Orbitron;font-size:0.8rem;margin-bottom:10px;'>GEOLOGICAL NOTES</div>
        <div style='color:#94a3b8;font-size:0.8rem;line-height:1.7;'>{rdata["geo"]}</div>
    </div>""", unsafe_allow_html=True)

with c2:
    # Basin comparison chart
    basin_data = {r["name"]: r["basin_km2"] for r in RIVERS}
    fig_basin = go.Figure(go.Bar(
        y=list(basin_data.keys()), x=list(basin_data.values()),
        orientation="h",
        marker=dict(color=list(range(len(RIVERS))),
                    colorscale=[[0,"#00d4ff"],[0.5,"#7c3aed"],[1,"#f59e0b"]]),
        hovertemplate="<b>%{y}</b><br>Basin: %{x:,} km²<extra></extra>"))
    fig_basin.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a7d65", family="Source Sans 3"), height=280,
        margin=dict(l=5,r=5,t=5,b=5),
        title=dict(text="Basin Area (km²)", font=dict(size=11, color="#8a7d65")),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"), yaxis=dict())
    st.plotly_chart(fig_basin, use_container_width=True)

# Flow path map — origin to mouth for the selected river
if "path" in rdata:
    st.markdown("<div class='section-heading'>RIVER COURSE — ORIGIN TO MOUTH</div>", unsafe_allow_html=True)
    path = rdata["path"]
    plats = [p[0] for p in path]
    plons = [p[1] for p in path]
    fig_river = go.Figure()
    fig_river.add_trace(go.Scattergeo(
        lat=plats, lon=plons, mode="lines",
        line=dict(color="#00d4ff", width=3.5),
        hovertemplate=f"<b>{rdata['name']}</b><extra></extra>", showlegend=False))
    fig_river.add_trace(go.Scattergeo(
        lat=[plats[0]], lon=[plons[0]], mode="markers+text",
        text=["Origin"], textposition="top right",
        marker=dict(size=11, color="#34d399", symbol="circle"),
        textfont=dict(color="#34d399", size=10),
        name="Origin", hovertemplate=f"<b>Origin:</b> {rdata['origin']}<extra></extra>"))
    fig_river.add_trace(go.Scattergeo(
        lat=[plats[-1]], lon=[plons[-1]], mode="markers+text",
        text=["Mouth"], textposition="bottom right",
        marker=dict(size=11, color="#f87171", symbol="diamond"),
        textfont=dict(color="#f87171", size=10),
        name="Mouth", hovertemplate=f"<b>Joins:</b> {rdata['joins']}<extra></extra>"))
    fig_river.update_geos(scope="asia", lonaxis_range=[65, 98], lataxis_range=[5, 36],
        showland=True, landcolor="#1a2a1a", showocean=True, oceancolor="#020817",
        showcountries=True, countrycolor="rgba(255,255,255,0.18)",
        showcoastlines=True, coastlinecolor="rgba(0,212,255,0.4)",
        bgcolor="rgba(0,0,0,0)", showframe=False)
    fig_river.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
        legend=dict(bgcolor="rgba(10,22,40,0.85)", font=dict(size=10, color="#f0e6d0"),
                    bordercolor="rgba(0,212,255,0.3)", borderwidth=1))
    st.plotly_chart(fig_river, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: SOIL EXPLORER
# ═══════════════════════════════════════════════════════════════

st.markdown("<div class='section-heading'>ELEVATION PROFILE & SEASONAL FLOW</div>", unsafe_allow_html=True)
_elev_data = {
    "Ganga":        {"source_m":3892,"mouth_m":0,"length_km":2525,"monsoon_km3":468,"winter_km3":84},
    "Brahmaputra":  {"source_m":5330,"mouth_m":0,"length_km":2900,"monsoon_km3":537,"winter_km3":122},
    "Godavari":     {"source_m":1067,"mouth_m":0,"length_km":1465,"monsoon_km3":93, "winter_km3":8},
    "Krishna":      {"source_m":1337,"mouth_m":0,"length_km":1400,"monsoon_km3":58, "winter_km3":5},
    "Narmada":      {"source_m":1057,"mouth_m":0,"length_km":1312,"monsoon_km3":36, "winter_km3":4},
    "Indus":        {"source_m":4570,"mouth_m":0,"length_km":3180,"monsoon_km3":175,"winter_km3":62},
    "Yamuna":       {"source_m":3293,"mouth_m":100,"length_km":1376,"monsoon_km3":87,"winter_km3":14},
    "Mahanadi":     {"source_m":442,"mouth_m":0,"length_km":858,"monsoon_km3":52, "winter_km3":5},
    "Tapi":         {"source_m":752,"mouth_m":0,"length_km":724,"monsoon_km3":14, "winter_km3":2},
    "Sutlej":       {"source_m":4570,"mouth_m":180,"length_km":1450,"monsoon_km3":48,"winter_km3":18},
    "Chambal":      {"source_m":854,"mouth_m":120,"length_km":960,"monsoon_km3":22, "winter_km3":4},
    "Tungabhadra":  {"source_m":1198,"mouth_m":150,"length_km":531,"monsoon_km3":18, "winter_km3":2},
}
_sel_river_elev = st.selectbox("Select river for flow data", list(_elev_data.keys()), key="elev_sel")
_ed = _elev_data[_sel_river_elev]
_drop = _ed["source_m"] - _ed["mouth_m"]
_gradient = _drop / _ed["length_km"]

_ec1,_ec2,_ec3 = st.columns(3)
_ec1.metric("Source Elevation", f"{_ed['source_m']:,} m")
_ec2.metric("Total Drop", f"{_drop:,} m")
_ec3.metric("Avg Gradient", f"{_gradient:.2f} m/km")

fig_flow = go.Figure()
fig_flow.add_trace(go.Bar(x=["Monsoon (Jun–Sep)","Winter (Oct–May)"],
    y=[_ed["monsoon_km3"],_ed["winter_km3"]],
    marker_color=["#00d4ff","#6366f1"],
    text=[f"{_ed['monsoon_km3']} km³",f"{_ed['winter_km3']} km³"],
    textposition="outside", textfont=dict(color="#f0e6d0")))
fig_flow.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8a7d65"),height=220,margin=dict(l=5,r=5,t=30,b=5),
    title=dict(text=f"{_sel_river_elev} — Annual Discharge (km³)",font=dict(size=11,color="#94a3b8")),
    yaxis=dict(title=dict(text="Discharge (km³)",font=dict(color="#8a7d65")),gridcolor="rgba(255,255,255,0.05)"))
st.plotly_chart(fig_flow, use_container_width=True)
_ratio = _ed["monsoon_km3"]/max(_ed["winter_km3"],1)
st.markdown(f"""<div class='glass-card' style='padding:10px 14px;'>
<span style='color:#94a3b8;font-size:0.76rem;'>
Monsoon discharge is <b style='color:#00d4ff;'>{_ratio:.1f}×</b> higher than winter flow — 
{"highly seasonal (peninsular river, rain-fed)" if _ratio > 8 else "moderately seasonal (mix of snowmelt + rain)" if _ratio > 4 else "relatively perennial (glacier-fed Himalayan river)"}.
</span></div>""", unsafe_allow_html=True)
