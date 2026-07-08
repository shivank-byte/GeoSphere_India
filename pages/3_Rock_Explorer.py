# GeoSphere India — Rock Explorer
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

st.set_page_config(page_title="Rock Explorer — GeoSphere India", page_icon="🪨", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Rock (geology)", "Rock Explorer", "IGNEOUS · SEDIMENTARY · METAMORPHIC")

st.markdown("<div class='section-heading'>ROCK EXPLORER — IGNEOUS · SEDIMENTARY · METAMORPHIC</div>", unsafe_allow_html=True)

c_map = {"Igneous":"#f87171","Sedimentary":"#fbbf24","Metamorphic":"#a78bfa"}
tabs  = st.tabs(["🌋 Igneous", "🏜️ Sedimentary", "💫 Metamorphic", "🔍 Search"])

for tab, rtype in zip(tabs[:3], ["Igneous","Sedimentary","Metamorphic"]):
    with tab:
        cols = st.columns(3)
        for i, r in enumerate(ROCKS[rtype]):
            with cols[i % 3]:
                show_wiki_photo(r["name"], caption=r["name"])
                st.markdown(f"""
                <div class='mineral-card' style='border-color:{c_map[rtype]}33;'>
                    <div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>
                        <span style='font-size:1.5rem;'>{r["emoji"]}</span>
                        <span class='mineral-name' style='color:{c_map[rtype]};'>{r["name"]}</span>
                    </div>
                    <div style='color:#94a3b8;font-size:0.73rem;line-height:1.5;'>
                    <b style='color:#e2e8f0;'>Texture:</b> {r["texture"]}<br>
                    <b style='color:#e2e8f0;'>Composition:</b> {r["composition"]}<br>
                    <b style='color:#e2e8f0;'>Formation:</b> {r["formation"]}<br>
                    <b style='color:#e2e8f0;'>India:</b> {r["india"]}<br>
                    <b style='color:#e2e8f0;'>Uses:</b> {r["use"]}
                    </div>
                </div>""", unsafe_allow_html=True)
                with st.expander(f"📍 Where to find {r['name']} in India"):
                    render_location_dot_map(r["india"], r["name"], height=200)

with tabs[3]:
    search_r = st.text_input("🔍 Search any rock", placeholder="e.g. Granite, Basalt, Marble...")
    all_rocks = [(rtype, r) for rtype, rs in ROCKS.items() for r in rs]
    if search_r:
        res = [(rt, r) for rt, r in all_rocks if search_r.lower() in r["name"].lower() or
               search_r.lower() in r["composition"].lower() or search_r.lower() in r["formation"].lower()
               or search_r.lower() in r["use"].lower() or search_r.lower() in r["india"].lower()]
        if not res:
            st.warning("No rocks found. Try different keywords.")
        else:
            for rt, r in res:
                show_wiki_photo(r["name"], caption=r["name"])
                st.markdown(f"""
                <div class='glass-card'>
                    <div style='display:flex;justify-content:space-between;align-items:start;'>
                        <div style='font-size:1.5rem;'>{r["emoji"]}</div>
                        <span style='font-size:0.68rem;background:{c_map[rt]}22;padding:2px 8px;
                            border-radius:10px;color:{c_map[rt]};'>{rt}</span>
                    </div>
                    <div style='color:{c_map[rt]};font-family:Orbitron,sans-serif;font-size:0.9rem;margin:6px 0;'>{r["name"]}</div>
                    <div style='color:#94a3b8;font-size:0.8rem;line-height:1.7;'>
                    🔬 <b style='color:#e2e8f0;'>Texture:</b> {r["texture"]}<br>
                    🧱 <b style='color:#e2e8f0;'>Composition:</b> {r["composition"]}<br>
                    🌋 <b style='color:#e2e8f0;'>Formation:</b> {r["formation"]}<br>
                    🇮🇳 <b style='color:#e2e8f0;'>India:</b> {r["india"]}<br>
                    🏗️ <b style='color:#e2e8f0;'>Uses:</b> {r["use"]}
                    </div>
                </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#475569;text-align:center;padding:30px;'>Type a rock name to search</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  HAND SPECIMEN vs THIN SECTION COMPARISON
# ═══════════════════════════════════════════════════════════════
st.markdown("<div class='section-heading'>🪨 HAND SPECIMEN vs THIN SECTION</div>", unsafe_allow_html=True)
st.markdown("""<div class='glass-card' style='padding:10px 16px;margin-bottom:12px;'>
<span style='color:#94a3b8;font-size:0.76rem;'>See a rock the way you would in the field or lab, side by side
with what the same rock reveals at 0.03mm thickness under the polarising microscope.</span></div>""",
    unsafe_allow_html=True)
rock_names_all = [r["name"] for rs in ROCKS.values() for r in rs]
hs_pick = st.selectbox("Choose a rock", rock_names_all, key="rock_hs_pick")
hs_col1, hs_col2 = st.columns(2)
with hs_col1:
    st.markdown("<div style='color:#c9a84c;font-size:0.8rem;margin-bottom:4px;'>👁 HAND SPECIMEN</div>", unsafe_allow_html=True)
    show_wiki_photo(hs_pick, caption=f"{hs_pick} — hand specimen")
with hs_col2:
    st.markdown("<div style='color:#00d4ff;font-size:0.8rem;margin-bottom:4px;'>🔬 THIN SECTION (XPL)</div>", unsafe_allow_html=True)
    show_wiki_photo(f"{hs_pick} thin section micrograph", caption=f"{hs_pick} — thin section, crossed polars")
st.caption("Tip: visit the Thin Section Gallery for full PPL/XPL optical properties of the minerals inside each rock.")
