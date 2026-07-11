# GeoSphere India — About
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

st.set_page_config(page_title="About — GeoSphere India", page_icon="🥚", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Geology", "About & Archive", "CREDITS, DATA SOURCES & BUILD INFO")

st.session_state.about_visited = True

st.markdown("<div class='section-heading'>About GeoSphere India</div>", unsafe_allow_html=True)

# Centred about card
st.markdown("""
<div class='glass-card' style='text-align:center;max-width:680px;margin:0 auto 24px;padding:32px 36px;'>
    <div style='font-size:2.8rem;margin-bottom:12px;'>🌍</div>
    <div style='color:#c9a84c;font-family:Playfair Display,Georgia,serif;font-size:1.4rem;
        font-weight:700;margin-bottom:14px;'>GeoSphere India</div>
    <div style='color:#94a3b8;font-size:0.9rem;line-height:1.9;font-family:Spectral,Georgia,serif;'>
        An interactive Earth Science intelligence platform built for geology students, researchers,
        and enthusiasts — with a special focus on Indian geology, the BHU NEP Earth Science curriculum,
        and the extraordinary geological story of the Indian subcontinent.
    </div>
    <div style='margin-top:20px;display:flex;justify-content:center;gap:12px;flex-wrap:wrap;'>
        <span class='hero-badge'>🪨 Petrology</span>
        <span class='hero-badge'>💎 Mineralogy</span>
        <span class='hero-badge'>🌋 Volcanology</span>
        <span class='hero-badge'>🗺️ Structural Geology</span>
        <span class='hero-badge'>🌊 Oceanography</span>
    </div>
</div>""", unsafe_allow_html=True)

# System information — no dots, clean table style
sc1, sc2 = st.columns(2)
with sc1:
    st.markdown("""
    <div class='glass-card'>
        <div style='color:#c9a84c;font-family:Playfair Display,Georgia,serif;
            font-size:0.95rem;font-weight:700;margin-bottom:16px;'>Platform Details</div>
        <table style='width:100%;border-collapse:collapse;font-family:Source Sans 3,sans-serif;'>
            <tr><td style='color:#475569;font-size:0.8rem;padding:5px 0;'>Platform</td>
                <td style='color:#e2e8f0;font-size:0.8rem;padding:5px 0;text-align:right;'>GeoSphere India</td></tr>
            <tr><td style='color:#475569;font-size:0.8rem;padding:5px 0;'>Purpose</td>
                <td style='color:#e2e8f0;font-size:0.8rem;padding:5px 0;text-align:right;'>Earth Science · Learning</td></tr>
            <tr><td style='color:#475569;font-size:0.8rem;padding:5px 0;'>Modules</td>
                <td style='color:#e2e8f0;font-size:0.8rem;padding:5px 0;text-align:right;'>20 Interactive Sections</td></tr>
            <tr><td style='color:#475569;font-size:0.8rem;padding:5px 0;'>Data Sources</td>
                <td style='color:#e2e8f0;font-size:0.8rem;padding:5px 0;text-align:right;'>GSI · USGS · Wikipedia</td></tr>
            <tr><td style='color:#475569;font-size:0.8rem;padding:5px 0;'>Built With</td>
                <td style='color:#e2e8f0;font-size:0.8rem;padding:5px 0;text-align:right;'>Streamlit · Plotly · Python</td></tr>
            <tr><td style='color:#475569;font-size:0.8rem;padding:5px 0;'>Coordinates</td>
                <td style='color:#e2e8f0;font-size:0.8rem;padding:5px 0;text-align:right;'>25.2677°N · 82.9913°E</td></tr>
        </table>
    </div>""", unsafe_allow_html=True)

with sc2:
    st.markdown("""
    <div class='glass-card' style='text-align:center;padding:28px 20px;'>
        <div style='color:#c9a84c;font-family:Playfair Display,Georgia,serif;
            font-size:0.95rem;font-weight:700;margin-bottom:16px;'>Syllabus Coverage</div>
        <div style='color:#94a3b8;font-size:0.8rem;line-height:2.2;font-family:Source Sans 3,sans-serif;'>
            BHU NEP Earth Science<br>
            B.Sc. (Honours) 4-Year Programme<br>
            <span style='color:#c9a84c;'>Semesters 1–8</span><br>
            All Major Electives Included<br>
            <span style='color:#10b981;font-size:0.72rem;'>✓ Syllabus synced from NEP PDF</span>
        </div>
    </div>""", unsafe_allow_html=True)

st.markdown("<hr style='border-color:rgba(201,168,76,0.12);margin:20px 0;'>", unsafe_allow_html=True)

# Build version — always visible (previously invisible pre-easter-egg;
# the readable version number and the secret rare-mode toggle are two
# separate things, so the text stays legible even before the logo-click
# discovery gate opens).
st.markdown("""
<div style='text-align:center;color:#4a4230;font-size:0.65rem;
    margin-bottom:8px;font-family:Source Sans 3,sans-serif;letter-spacing:1px;'>
Build · v08.09.08.11
</div>""", unsafe_allow_html=True)

# Achievement trigger — the *clickable* toggle stays hidden until the
# logo-click easter egg (8+ clicks) is found; the version text above is
# always readable regardless.
if st.session_state.logo_clicks >= 8:
    col_v1, col_v2, col_v3 = st.columns([2,1,2])
    with col_v2:
        if st.button("v08.09.08.11", key="version_btn"):
            st.session_state.rare_mode  = not st.session_state.rare_mode
            st.session_state.rare_timer = time.time()
            st.session_state.ambient_sound = st.session_state.rare_mode  # play the theme when achievement mode unlocks
            st.rerun()

st.markdown("<hr style='border-color:rgba(201,168,76,0.1);margin:18px 0;'>", unsafe_allow_html=True)

# Hidden Gem — click to reveal fact WITH a Wikipedia photo illustrating it
gem_data = [
    ("Earth's Core Temperature",   "🌍", "The core is as hot as the surface of the Sun — 5,500°C. Both unreachable. Both magnificent."),
    ("Stardust",                    "💙", "Every atom of calcium in your bones was forged in a dying star. You are literally made of stardust."),
    ("Diamond",                     "💎", "A diamond takes over a billion years to form, then reaches the surface in hours via kimberlite eruption."),
    ("Mount Everest",               "🏔️", "Everest's summit limestone once sat at the bottom of an ancient ocean — the Tethys Sea."),
    ("Fulgurite",                   "🔥", "Lightning can fuse sand into glass instantly, creating natural tubes called fulgurites."),
    ("Petrified wood",              "🌳", "Some petrified wood retains its original cell structure in perfect detail, replaced atom by atom with silica."),
    ("Pumice",                      "🌋", "Pumice is the only rock that can float on water, thanks to its trapped volcanic gas bubbles."),
    ("Granite",                     "🪨", "Granite takes millions of years to cool from magma — its large crystals are a direct record of that slow journey."),
    ("Glacier",                     "🧊", "Glaciers can be blue because ice absorbs red light and scatters blue — the same reason the sky is blue."),
    ("Mariana Trench",              "🌊", "The Mariana Trench is so deep that Everest could fit inside it with over 2 km of water above the peak."),
    ("Basalt",                      "🌋", "Basalt is the most common rock on Earth — and also on the Moon and Mars. It's universal."),
    ("Permineralization",           "🦴", "Most fossils aren't bone — minerals slowly replace bone after burial, a process called permineralization."),
    ("Salt dome",                   "🧂", "Salt domes trap oil and gas so effectively that geologists actively search for them during petroleum exploration."),
    ("Geological Survey of India",  "⭐", "GSI (est. 1851) is one of the world's oldest geological surveys — it mapped India's entire mineral wealth."),
    ("Cambrian explosion",          "🌐", "If Earth's 4.6 Ga history were 24 hours, complex animals appear at 9pm — and humans at 11:59:58pm."),
]

st.markdown("<div style='text-align:center;margin-bottom:6px;'>", unsafe_allow_html=True)
cx1, cx2, cx3 = st.columns([2,1,2])
with cx2:
    if st.button("🥚 Hidden Gem", use_container_width=True):
        st.session_state.easter_count += 1
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.easter_count > 0:
    prev = st.session_state.get("last_gem_idx", -1)
    gi = random.randrange(len(gem_data))
    while gi == prev and len(gem_data) > 1:
        gi = random.randrange(len(gem_data))
    st.session_state.last_gem_idx = gi
    wiki_term, em, fact_text = gem_data[gi]

    gem_img = get_wiki_image(wiki_term)
    g1, g2 = st.columns([1, 2])
    with g1:
        if gem_img:
            try:
                st.image(gem_img, use_container_width=True)
            except Exception:
                st.markdown(f"<div style='font-size:3rem;text-align:center;'>{em}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='font-size:3rem;text-align:center;padding:20px;'>{em}</div>", unsafe_allow_html=True)
    with g2:
        st.markdown(f"""
        <div class='glass-card' style='border-color:rgba(201,168,76,0.35);height:100%;'>
            <div style='font-size:1.8rem;margin-bottom:8px;'>{em}</div>
            <div style='color:#c9a84c;font-family:Playfair Display,Georgia,serif;
                font-size:1.05rem;line-height:1.8;font-style:italic;'>{fact_text}</div>
            <div style='color:#475569;font-size:0.7rem;margin-top:12px;'>
                📷 Photo: Wikipedia · Click button again for another gem
            </div>
        </div>""", unsafe_allow_html=True)

# Footer
st.markdown(f"""
<div style='text-align:center;color:#1e1a12;font-size:0.62rem;
    padding:20px 0 8px;line-height:2.2;font-family:Source Sans 3,sans-serif;'>
    GeoSphere India · Earth Science Platform<br>
    Lat: 25.2677°N · Lon: 82.9913°E<br>
    <span style='color:#c9a84c;opacity:0.4;'>Dedicated to Curiosity.</span>
</div>""", unsafe_allow_html=True)


st.markdown("<div class='section-heading'>CREDITS & DATA SOURCES</div>", unsafe_allow_html=True)
credits = [
    ("🌍","USGS Earthquake Hazards Program","earthquake.usgs.gov","Real-time M4.5+ earthquake data, historical seismicity"),
    ("💎","Geological Survey of India (GSI)","gsi.gov.in","Mineral deposit locations, geological province data (est. 1851)"),
    ("📖","Wikipedia / Wikimedia Commons","wikipedia.org","Mineral, rock, volcano, and geography reference photos (CC-licensed)"),
    ("🎓","BHU NEP Earth Science Syllabus","bhu.ac.in","Semester-wise syllabus content, subject codes, examination framework"),
    ("🗺️","OpenStreetMap / Overpass API","openstreetmap.org","River path coordinates, geographical features"),
    ("🛰️","Esri World Imagery","esri.com","Satellite tile layers in Folium maps"),
    ("🤖","Google Gemini API","ai.google.dev","AI Geo Assistant — real-time geology Q&A"),
    ("📊","Plotly & Streamlit","plotly.com · streamlit.io","Interactive charts, 3D globe, app framework"),
    ("🔬","Three.js","threejs.org","3D mineral crystal viewer"),
]
for em, source, url, desc in credits:
    st.markdown(f"""
    <div class='glass-card' style='padding:11px 14px;display:flex;align-items:start;gap:12px;'>
        <span style='font-size:1.4rem;flex-shrink:0;'>{em}</span>
        <div>
            <div style='color:#c9a84c;font-size:0.82rem;font-weight:600;'>{source}
                <span style='color:#475569;font-size:0.7rem;margin-left:8px;'>{url}</span>
            </div>
            <div style='color:#94a3b8;font-size:0.75rem;margin-top:2px;'>{desc}</div>
        </div>
    </div>""", unsafe_allow_html=True)
st.caption("GeoSphere India is an independent educational project and is not officially affiliated with GSI, USGS, Wikipedia, Esri, Google, or BHU.")
