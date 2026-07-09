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
# Hand Specimen vs Thin Section reference — maps each rock to a representative
# constituent mineral (for a photo that actually exists on Wikipedia) plus
# real PPL/XPL descriptive text. A synthetic search like "Granite thin
# section micrograph" almost never matches a real Wikipedia article, so
# this curated approach replaces that dead-end guess.
ROCK_THIN_SECTION_INFO = {
    "Granite":      {"mineral": "Orthoclase", "ppl": "Interlocking quartz, feldspar & mica grains — equigranular texture.",
                      "xpl": "Quartz shows grey 1st-order colours; K-feldspar often shows perthitic exsolution; mica is high-birefringent."},
    "Basalt":       {"mineral": "Augite", "ppl": "Fine groundmass of plagioclase laths + pyroxene, may show vesicles.",
                      "xpl": "Ophitic texture — plagioclase laths enclosed by pyroxene; flow alignment often visible."},
    "Obsidian":     {"mineral": "Volcanic glass", "ppl": "Isotropic glass — no crystals, may show flow banding & conchoidal fractures.",
                      "xpl": "Stays black/extinct at all stage angles — true glass has no crystal structure to bend light."},
    "Pumice":       {"mineral": "Volcanic glass", "ppl": "Highly vesicular glass — a froth of thin glass walls around gas bubbles.",
                      "xpl": "Isotropic (dark) like obsidian — same glassy composition, just full of trapped gas voids."},
    "Rhyolite":     {"mineral": "Quartz", "ppl": "Fine-grained to glassy groundmass, may show flow banding and small phenocrysts.",
                      "xpl": "Quartz phenocrysts show low grey interference colours in an otherwise fine/glassy matrix."},
    "Gabbro":       {"mineral": "Olivine", "ppl": "Coarse, equigranular plagioclase + pyroxene ± olivine.",
                      "xpl": "Plagioclase twinning prominent; pyroxene shows 2nd-order interference colours."},
    "Diorite":      {"mineral": "Hornblende", "ppl": "Salt-and-pepper texture — plagioclase with dark hornblende/biotite.",
                      "xpl": "Plagioclase shows twinning; hornblende shows characteristic 2nd-order greens."},
    "Pegmatite":    {"mineral": "Muscovite", "ppl": "Very coarse interlocking crystals — same minerals as granite but much larger.",
                      "xpl": "Muscovite shows brilliant high-order interference colours; large single-crystal domains."},
    "Sandstone":    {"mineral": "Quartz", "ppl": "Rounded to sub-angular quartz grains cemented by silica/calcite.",
                      "xpl": "Individual detrital quartz grains show low grey interference colours; cement fills pore spaces."},
    "Limestone":    {"mineral": "Calcite", "ppl": "Fine to coarse calcite, may preserve bioclasts (shell fragments).",
                      "xpl": "High-order pearly colours; micritic (fine) vs sparry (coarse) calcite textures distinguishable."},
    "Shale":        {"mineral": "Clay minerals", "ppl": "Very fine, often opaque with organic matter; strong parallel lamination.",
                      "xpl": "Clay platelets too fine to resolve individually — overall low, patchy birefringence."},
    "Conglomerate": {"mineral": "Quartz", "ppl": "Rounded pebbles (often quartz/chert) set in a finer sandy/muddy matrix.",
                      "xpl": "Each pebble shows its own parent-rock optical properties — quartz pebbles show low grey colours."},
    "Coal":         {"mineral": "Vitrinite", "ppl": "Opaque to translucent brown organic material — banded (bright/dull layers).",
                      "xpl": "Mostly isotropic/opaque under crossed polars — organic macerals don't behave like mineral crystals."},
    "Chalk":        {"mineral": "Coccolithophore", "ppl": "Very fine microcrystalline calcite from countless microfossil plates.",
                      "xpl": "Overall high-order pearly calcite colours, but individual coccoliths need an electron microscope to resolve."},
    "Chert":        {"mineral": "Chalcedony", "ppl": "Cryptocrystalline silica — grains far too fine to distinguish individually.",
                      "xpl": "Fibrous chalcedony shows a characteristic sweeping/radiating extinction pattern."},
    "Marble":       {"mineral": "Calcite", "ppl": "Interlocking calcite crystals, granoblastic texture, no original fossils preserved.",
                      "xpl": "Extreme high-order 'pearly' interference colours diagnostic of calcite; rhombic cleavage traces."},
    "Slate":        {"mineral": "Chlorite", "ppl": "Very fine mica/chlorite flakes, strong parallel alignment (slaty cleavage).",
                      "xpl": "Fine-grained micas show a uniform sheen; cleavage-parallel alignment visible as banding."},
    "Schist":       {"mineral": "Biotite", "ppl": "Strongly foliated — aligned mica flakes wrap around quartz grains.",
                      "xpl": "Mica shows high 2nd–3rd order colours; lepidoblastic fabric clearly visible."},
    "Quartzite":    {"mineral": "Quartz", "ppl": "Interlocking quartz grains, sutured boundaries, original sand texture erased.",
                      "xpl": "Undulatory extinction in strained quartz grains — diagnostic of metamorphism."},
    "Gneiss":       {"mineral": "Orthoclase", "ppl": "Coarse banding of light (quartz-feldspar) and dark (biotite-hornblende) layers.",
                      "xpl": "Gneissose banding visible in cross-polars; feldspar may show Carlsbad twinning."},
    "Phyllite":     {"mineral": "Muscovite", "ppl": "Fine mica flakes with a characteristic silky sheen, between slate and schist in grain size.",
                      "xpl": "Fine mica shows moderate interference colours; crenulated cleavage often visible."},
    "Charnockite":  {"mineral": "Hypersthene", "ppl": "Massive, dark greenish, coarse-grained granulite-facies rock.",
                      "xpl": "Hypersthene (orthopyroxene) shows characteristic pink-green pleochroism — diagnostic of this rock type."},
}

st.markdown("<div class='section-heading'>🪨 HAND SPECIMEN vs THIN SECTION</div>", unsafe_allow_html=True)
st.markdown("""<div class='glass-card' style='padding:10px 16px;margin-bottom:12px;'>
<span style='color:#94a3b8;font-size:0.76rem;'>See a rock the way you would in the field or lab, side by side
with what its key mineral reveals at 0.03mm thickness under the polarising microscope.</span></div>""",
    unsafe_allow_html=True)
rock_names_all = [r["name"] for rs in ROCKS.values() for r in rs]
hs_pick = st.selectbox("Choose a rock", rock_names_all, key="rock_hs_pick")
hs_col1, hs_col2 = st.columns(2)
_ts_ref = ROCK_THIN_SECTION_INFO.get(hs_pick)
with hs_col1:
    st.markdown("<div style='color:#c9a84c;font-size:0.8rem;margin-bottom:4px;'>👁 HAND SPECIMEN</div>", unsafe_allow_html=True)
    show_wiki_photo(hs_pick, caption=f"{hs_pick} — hand specimen")
with hs_col2:
    st.markdown("<div style='color:#00d4ff;font-size:0.8rem;margin-bottom:4px;'>🔬 THIN SECTION (XPL)</div>", unsafe_allow_html=True)
    if _ts_ref:
        show_wiki_photo(_ts_ref["mineral"], caption=f"{hs_pick} — key mineral: {_ts_ref['mineral']} (crossed polars)")
    else:
        show_wiki_photo(f"{hs_pick} thin section micrograph", caption=f"{hs_pick} — thin section, crossed polars", strict=True)
if _ts_ref:
    st.markdown(f"""
    <div class='glass-card' style='padding:10px 14px;'>
        <span style='color:#00d4ff;font-size:0.72rem;'><b>PPL:</b></span>
        <span style='color:#94a3b8;font-size:0.75rem;'> {_ts_ref["ppl"]}</span><br>
        <span style='color:#c084fc;font-size:0.72rem;'><b>XPL:</b></span>
        <span style='color:#94a3b8;font-size:0.75rem;'> {_ts_ref["xpl"]}</span>
    </div>""", unsafe_allow_html=True)
st.caption("Tip: visit the Thin Section Gallery for full PPL/XPL optical properties of the minerals inside each rock.")
