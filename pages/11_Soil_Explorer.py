# GeoSphere India — Soil Explorer
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

st.set_page_config(page_title="Soil Explorer — GeoSphere India", page_icon="🧪", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Soil", "Soil Explorer", "INDIA'S MAJOR SOIL TYPES")

st.markdown("<div class='section-heading'>SOIL EXPLORER — INDIA'S 7 MAJOR SOIL TYPES</div>", unsafe_allow_html=True)

sel_s = st.selectbox("Select Soil Type", [s["name"] for s in SOILS])
soil  = next(s for s in SOILS if s["name"] == sel_s)

c1, c2 = st.columns([1, 1])
with c1:
    show_wiki_photo(soil.get("wiki_term", soil["name"]), caption=f"{soil['name']} — reference photo (Wikipedia)")
    st.markdown(f"""
    <div class='glass-card' style='border-color:{soil["color"]}55;'>
        <div style='display:flex;align-items:center;gap:12px;margin-bottom:14px;'>
            <div style='width:40px;height:40px;border-radius:8px;background:{soil["color"]};
                border:2px solid {soil["color"]}88;flex-shrink:0;display:flex;align-items:center;
                justify-content:center;font-size:1.3rem;'>{soil["emoji"]}</div>
            <div style='color:{soil["color"]};font-family:Orbitron;font-size:0.9rem;'>{soil["name"]}</div>
        </div>
        <div style='color:#94a3b8;font-size:0.8rem;line-height:2;'>
        📊 <b style='color:#e2e8f0;'>Area (% of India):</b> {soil["area_pct"]}%<br>
        🗺️ <b style='color:#e2e8f0;'>States:</b> {soil["states"]}<br>
        🌋 <b style='color:#e2e8f0;'>Formation:</b> {soil["formation"]}<br>
        🌾 <b style='color:#e2e8f0;'>Crops:</b> {soil["crops"]}<br>
        </div>
        <div style='color:#94a3b8;font-size:0.78rem;margin-top:10px;border-top:1px solid rgba(255,255,255,0.07);padding-top:8px;'>
        {soil["desc"]}
        </div>
    </div>""", unsafe_allow_html=True)

with c2:
    fig_soil = go.Figure(go.Pie(
        labels=[s["name"] for s in SOILS],
        values=[s["area_pct"] for s in SOILS],
        hole=0.4,
        marker=dict(colors=[s["color"] for s in SOILS],
                    line=dict(color="rgba(0,0,0,0.3)", width=2)),
    ))
    fig_soil.update_traces(textfont_color="#f0e6d0",
        hovertemplate="<b>%{label}</b><br>%{value}% of India<extra></extra>")
    fig_soil.update_layout(paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0", family="Source Sans 3"),
        legend=dict(font=dict(size=9, color="#f0e6d0"), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=5,r=5,t=5,b=5), height=320)
    st.plotly_chart(fig_soil, use_container_width=True)

# Soil distribution map of India — approximate regional spread by soil type
st.markdown("<div class='section-heading'>SOIL DISTRIBUTION ACROSS INDIA</div>", unsafe_allow_html=True)
soil_regions = {
    "Alluvial Soil":   [(28,77),(26,80),(25,83),(24,88),(27,94),(31,75)],
    "Black (Regur) Soil": [(19,74),(21,77),(17,79),(22,73)],
    "Red & Yellow Soil":  [(20,84),(22,85),(23,86),(15,78),(13,79)],
    "Laterite Soil":      [(10,76),(12,75.5),(25,91.5),(26,92.5),(11,76.5)],
    "Mountain Soil":      [(33,76),(31,78),(28,94),(27,93)],
    "Arid (Desert) Soil": [(27,71),(26,72),(28,73)],
    "Saline/Alkaline Soil": [(30,75),(29,76),(28,79)],
}
fig_smap = go.Figure()
for s in SOILS:
    pts = soil_regions.get(s["name"], [])
    if pts:
        fig_smap.add_trace(go.Scattergeo(
            lat=[p[0] for p in pts], lon=[p[1] for p in pts],
            mode="markers", marker=dict(size=14, color=s["color"], opacity=0.75,
                                         line=dict(width=1, color="rgba(255,255,255,0.4)")),
            name=s["name"], hovertemplate=f"<b>{s['name']}</b><extra></extra>"))
fig_smap.update_geos(scope="asia", lonaxis_range=[66, 98], lataxis_range=[6, 37],
    showland=True, landcolor="#1a2a1a", showocean=True, oceancolor="#020817",
    showcountries=True, countrycolor="rgba(255,255,255,0.18)",
    showcoastlines=True, coastlinecolor="rgba(0,212,255,0.4)",
    bgcolor="rgba(0,0,0,0)", showframe=False)
fig_smap.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
    legend=dict(bgcolor="rgba(10,22,40,0.85)", font=dict(size=10, color="#f0e6d0"),
                bordercolor="rgba(201,168,76,0.3)", borderwidth=1))
st.plotly_chart(fig_smap, use_container_width=True)
st.markdown("""
<div class='glass-card' style='padding:10px 16px;'>
    <span style='color:#94a3b8;font-size:0.76rem;'>
    🗺️ Markers show approximate regional concentration, not exact boundaries — actual soil
    distribution varies at much finer scale based on local geology, rainfall, and drainage.
    </span>
</div>""", unsafe_allow_html=True)

st.markdown("<div class='section-heading'>SOIL HEALTH INDICATORS</div>", unsafe_allow_html=True)
_sh = {
    "Alluvial Soil":        {"ph":"6.5–7.5","organic":"0.5–1.5%","water":"High","color":"#f59e0b"},
    "Black (Regur) Soil":   {"ph":"7.2–8.5","organic":"0.8–2.0%","water":"Very High (cracks when dry)","color":"#1f2937"},
    "Red & Yellow Soil":    {"ph":"5.5–7.0","organic":"0.3–0.8%","water":"Low (porous)","color":"#dc2626"},
    "Laterite Soil":        {"ph":"4.5–6.0","organic":"0.2–0.5%","water":"Low (leached)","color":"#92400e"},
    "Mountain Soil":        {"ph":"5.0–6.5","organic":"2.0–5.0%","water":"Moderate","color":"#4b5563"},
    "Arid (Desert) Soil":   {"ph":"7.5–9.0","organic":"<0.3%","water":"Very Low","color":"#fbbf24"},
    "Saline/Alkaline Soil": {"ph":"8.5–10.0","organic":"<0.5%","water":"Poor drainage","color":"#e5e7eb"},
}
_soil_names = list(_sh.keys())
_sh_sel = st.selectbox("Select soil for health data", _soil_names, key="sh_sel")
_sd = _sh[_sh_sel]
_shc = st.columns(3)
_shc[0].metric("pH Range", _sd["ph"])
_shc[1].metric("Organic Matter", _sd["organic"])
_shc[2].metric("Water Retention", _sd["water"])

st.markdown("<div class='section-heading'>CROP–SOIL PAIRING — WHY GEOLOGY DECIDES WHAT GROWS WHERE</div>", unsafe_allow_html=True)
_crop_reasons = {
    "Alluvial Soil": "Fine sediment + high water retention + regular flood renewal of nutrients suit thirsty, nutrient-hungry crops.",
    "Black (Regur) Soil": "High clay content retains moisture deep into the dry season — ideal for crops that need slow, sustained water release.",
    "Red & Yellow Soil": "Porous, iron-rich but nutrient-poor — favours hardy, drought-tolerant crops that don't need rich soil.",
    "Laterite Soil": "Heavily leached of nutrients by monsoon rain — only acid-tolerant plantation crops thrive without heavy fertilisation.",
    "Mountain Soil": "Thin, organic-rich but on steep slopes — supports terraced horticulture and forest-adapted crops.",
    "Arid (Desert) Soil": "Very low water retention and organic matter — only the most drought-resistant crops survive without irrigation.",
    "Saline/Alkaline Soil": "Excess salts restrict most roots — needs salt-tolerant crops or heavy reclamation before farming.",
}
for s in SOILS:
    reason = _crop_reasons.get(s["name"], "")
    st.markdown(f"""
    <div class='glass-card' style='padding:11px 16px;margin-bottom:6px;border-left:4px solid {s["color"]};'>
        <div style='display:flex;align-items:center;gap:10px;'>
            <span style='font-size:1.3rem;'>{s["emoji"]}</span>
            <span style='color:{s["color"]};font-weight:600;font-size:0.82rem;'>{s["name"]}</span>
            <span style='color:#e2e8f0;font-size:0.75rem;'>→ {s["crops"]}</span>
        </div>
        <div style='color:#94a3b8;font-size:0.72rem;margin-top:5px;line-height:1.5;'>🌍 {reason}</div>
    </div>""", unsafe_allow_html=True)
