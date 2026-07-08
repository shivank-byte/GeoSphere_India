# GeoSphere India — Economic Geology
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

st.set_page_config(page_title="Economic Geology — GeoSphere India", page_icon="🪙", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Economic geology", "Economic Geology", "INDIA'S MINERAL WEALTH")

st.markdown("<div class='section-heading'>ECONOMIC GEOLOGY — INDIA'S MINERAL WEALTH</div>", unsafe_allow_html=True)

sel_min = st.selectbox("Select Mineral/Resource", list(ECONOMIC_MINERALS.keys()))
emin    = ECONOMIC_MINERALS[sel_min]

c1, c2 = st.columns([1, 1])
with c1:
    show_wiki_photo(sel_min, caption=f"{sel_min} — reference photo (Wikipedia)")
    st.markdown(f"""
    <div class='glass-card' style='border-color:{emin["color"]}44;'>
        <div style='font-size:2rem;margin-bottom:8px;'>{emin["emoji"]}</div>
        <div style='color:#00d4ff;font-family:Orbitron;font-size:0.9rem;margin-bottom:12px;'>{sel_min}</div>
        <div style='color:#94a3b8;font-size:0.8rem;line-height:2;'>
        🏭 <b style='color:#e2e8f0;'>Primary Uses:</b> {emin["use"]}<br>
        🌏 <b style='color:#e2e8f0;'>India Rank:</b> {emin["india_rank"]}<br>
        </div>
    </div>""", unsafe_allow_html=True)

with c2:
    fig_em = go.Figure(go.Pie(
        labels=list(emin["states"].keys()),
        values=list(emin["states"].values()),
        hole=0.4,
        marker=dict(colors=["#00d4ff","#7c3aed","#f59e0b","#10b981","#f87171","#a78bfa","#fbbf24"])
    ))
    fig_em.update_traces(textfont_color="#f0e6d0",
        hovertemplate="<b>%{label}</b>: %{value}% share<extra></extra>")
    fig_em.update_layout(paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0", family="Source Sans 3"),
        legend=dict(font=dict(size=9, color="#f0e6d0"), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=5,r=5,t=5,b=5), height=270,
        title=dict(text=f"{sel_min} — State-wise Share", font=dict(size=11, color="#8a7d65")))
    st.plotly_chart(fig_em, use_container_width=True)

# All minerals radar
st.markdown("<div class='section-heading'>RESOURCE IMPORTANCE COMPARISON</div>", unsafe_allow_html=True)
importance = {"Coal":9,"Iron Ore":9,"Bauxite":7,"Copper":5,"Zinc-Lead":8,"Chromite":7,"Gold":6,"Limestone":8}
fig_rad = go.Figure(go.Scatterpolar(
    r=list(importance.values()) + [list(importance.values())[0]],
    theta=list(importance.keys()) + [list(importance.keys())[0]],
    fill="toself", line_color="#00d4ff",
    fillcolor="rgba(0,212,255,0.1)", name="Economic Value"))
fig_rad.update_layout(polar=dict(
    bgcolor="rgba(0,0,0,0)",
    radialaxis=dict(visible=True, range=[0,10], color="#475569", gridcolor="rgba(255,255,255,0.06)"),
    angularaxis=dict(color="#8a7d65", gridcolor="rgba(255,255,255,0.06)")),
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f0e6d0", family="Source Sans 3"), showlegend=False,
    height=360, margin=dict(l=40,r=40,t=20,b=20))
st.plotly_chart(fig_rad, use_container_width=True)

st.markdown("<div class='section-heading'>HOW IT'S MINED + INDIA'S TRADE</div>", unsafe_allow_html=True)
_mining_data = {
    "Coal":      {"method":"Underground longwall + opencast strip mining","import_mt":247,"export_mt":2,"note":"India imports coking coal (high-grade) for steel from Australia/USA"},
    "Iron Ore":  {"method":"Open-cast (bench mining) — BIF deposits are shallow","import_mt":0,"export_mt":52,"note":"India is a net exporter. Exports mainly to China, Japan, South Korea"},
    "Bauxite":   {"method":"Open-cast — laterite cappings stripped first","import_mt":0,"export_mt":8,"note":"India exports to UAE smelters. Domestic aluminium industry is growing"},
    "Copper":    {"method":"Open-pit + underground block caving","import_mt":2,"export_mt":0,"note":"India imports 95% of copper needs despite domestic deposits"},
    "Zinc-Lead": {"method":"Underground cut-and-fill + open stoping (Rampura-Agucha)","import_mt":0,"export_mt":1,"note":"India is world's #1 zinc producer — Hindustan Zinc dominates"},
    "Chromite":  {"method":"Open-cast + underground (Sukinda — world's largest)","import_mt":0,"export_mt":0.5,"note":"India supplies ~16% of world chromite. Used in stainless steel"},
    "Gold":      {"method":"Deep underground reef mining (KGF went to 3.8 km depth)","import_mt":0.8,"export_mt":0,"note":"India imports ~800 tonnes gold/year — world's 2nd largest consumer"},
    "Limestone": {"method":"Quarrying (large open-cast benches)","import_mt":0,"export_mt":0,"note":"India is world's 2nd largest cement producer — fully self-sufficient"},
}
_min_names = list(_mining_data.keys())
_mg_sel = st.selectbox("Select mineral for trade data", _min_names, key="mg_sel")
_md = _mining_data[_mg_sel]
st.markdown(f"""
<div class='glass-card'>
    <div style='color:#c9a84c;font-size:0.82rem;font-weight:600;margin-bottom:10px;'>⛏️ Mining Method</div>
    <div style='color:#e2e8f0;font-size:0.8rem;margin-bottom:12px;'>{_md["method"]}</div>
    <div style='display:flex;gap:20px;margin-bottom:10px;'>
        <div><div style='color:#94a3b8;font-size:0.7rem;'>IMPORT (MT/yr)</div>
            <div style='color:{"#dc2626" if _md["import_mt"]>0 else "#10b981"};font-family:Orbitron;font-size:1.1rem;'>{_md["import_mt"]}</div></div>
        <div><div style='color:#94a3b8;font-size:0.7rem;'>EXPORT (MT/yr)</div>
            <div style='color:{"#10b981" if _md["export_mt"]>0 else "#94a3b8"};font-family:Orbitron;font-size:1.1rem;'>{_md["export_mt"]}</div></div>
    </div>
    <div style='color:#94a3b8;font-size:0.77rem;border-top:1px solid rgba(255,255,255,0.07);padding-top:8px;'>{_md["note"]}</div>
</div>""", unsafe_allow_html=True)

st.markdown("""
<div class='glass-card' style='margin-top:10px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;'>
    <span style='color:#94a3b8;font-size:0.78rem;'>🗺️ See exactly where these deposits are on the map, with GSI grade details.</span>
</div>""", unsafe_allow_html=True)
if st.button("🗺️ Open GSI Mineral Deposits Map →", key="cross_link_gsi"):
    st.switch_page("pages/1_Geological_Map.py")
