# GeoSphere India — Semester Notes
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

st.set_page_config(page_title="Semester Notes — GeoSphere India", page_icon="📚", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Geology", "Semester Notes", "B.Sc. EARTH SCIENCE SYLLABUS")

st.markdown("<div class='section-heading'>SEMESTER-WISE NOTES — B.Sc. EARTH SCIENCE (4-YEAR UG)</div>", unsafe_allow_html=True)

sem_tabs = st.tabs(list(NOTES.keys()))
for tab, (sem, subjects) in zip(sem_tabs, NOTES.items()):
    with tab:
        for subject, points in subjects.items():
            with st.expander(f"📖 {subject}", expanded=False):
                for pt in points:
                    st.markdown(f"""
                    <div class='glass-card' style='padding:12px 16px;margin-bottom:8px;'>
                        <div style='color:#94a3b8;font-size:0.8rem;line-height:1.65;'>{pt}</div>
                    </div>""", unsafe_allow_html=True)

                # Recommended books for this subject — link out via Google Books search
                matching_books = [b for b in BOOKS if subject.lower() in b["subject"].lower()
                                   or b["subject"].split("–")[-1].strip().lower() in subject.lower()]
                if matching_books:
                    st.markdown("<div style='color:#c9a84c;font-size:0.78rem;margin:10px 0 6px;font-weight:600;'>📚 Recommended Reading</div>", unsafe_allow_html=True)
                    for b in matching_books:
                        gbooks_url = "https://www.google.com/search?tbm=bks&q=" + \
                                     (b["title"] + " " + b["author"]).replace(" ", "+")
                        stars = "⭐" * b["stars"]
                        st.markdown(f"""
                        <a href="{gbooks_url}" target="_blank" style="text-decoration:none;">
                        <div class='glass-card' style='padding:10px 14px;margin-bottom:6px;
                            border-color:rgba(201,168,76,0.25);transition:border-color 0.2s;'>
                            <div style='color:#e8c96a;font-size:0.82rem;font-weight:600;'>{b["title"]} <span style='font-size:0.7rem;color:#8a7d65;'>↗</span></div>
                            <div style='color:#8a7d65;font-size:0.72rem;'>{b["author"]} · {stars}</div>
                        </div>
                        </a>""", unsafe_allow_html=True)

st.markdown("<div class='section-heading'>EXAM QUICK REFERENCE</div>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.markdown("""
    <div class='glass-card'>
        <div style='color:#00d4ff;font-family:Orbitron;font-size:0.8rem;margin-bottom:10px;'>GEOLOGIC TIME SCALE</div>
        <div style='color:#94a3b8;font-size:0.76rem;line-height:2;'>
        🟡 Quaternary – 2.6 Ma–present<br>
        🟠 Neogene – 23–2.6 Ma<br>
        🟡 Paleogene – 66–23 Ma<br>
        🟢 Cretaceous – 145–66 Ma<br>
        🟢 Jurassic – 201–145 Ma<br>
        🟢 Triassic – 252–201 Ma<br>
        🔵 Permian – 299–252 Ma<br>
        🔵 Carboniferous – 359–299 Ma<br>
        🔵 Devonian – 419–359 Ma<br>
        🔵 Silurian – 444–419 Ma<br>
        🔵 Ordovician – 485–444 Ma<br>
        🔵 Cambrian – 541–485 Ma
        </div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div class='glass-card'>
        <div style='color:#f59e0b;font-family:Orbitron;font-size:0.8rem;margin-bottom:10px;'>INDIA KEY FACTS</div>
        <div style='color:#94a3b8;font-size:0.76rem;line-height:2;'>
        ⛰️ Highest Peak: Kangchenjunga (8,586m)<br>
        🌊 Longest River: Ganga (2,525 km in India)<br>
        💎 Oldest Rocks: Dharwar craton (~3.3 Ga)<br>
        🌋 Only Active Volcano: Barren Island<br>
        ⛏️ Largest Coal State: Jharkhand<br>
        🥇 Largest Gold Mines: Karnataka (KGF)<br>
        💎 Largest Mica: Andhra Pradesh<br>
        🟤 Largest Diamond Mine: Majhgawan (MP)<br>
        🧪 Deepest Mine: KGF (~3.8 km depth)<br>
        🌋 Biggest Flood Basalt: Deccan Traps<br>
        </div>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: GEO QUIZ
# ═══════════════════════════════════════════════════════════════

st.markdown("<div class='section-heading'>🔑 KEY TERMS QUICK REFERENCE</div>", unsafe_allow_html=True)
_key_terms = {
    "Uniformitarianism": "The present is the key to the past — geological processes operating today also operated in the past at similar rates (Hutton, 1795).",
    "Lithostratigraphy": "Classification of rock sequences based on rock type (lithology) — the fundamental basis for geological mapping.",
    "Isostasy": "Gravitational equilibrium where crustal blocks float on denser mantle — mountains have deep roots like icebergs.",
    "Metamorphic Facies": "A set of mineral assemblages formed under specific P-T conditions — used to reconstruct burial depth and temperature history.",
    "Mohorovičić Discontinuity": "The seismic boundary between Earth's crust and mantle — detected by P-wave velocity increase at ~35 km depth under continents.",
    "Bowen's Reaction Series": "The sequence in which minerals crystallise from a cooling silicate melt — explains igneous rock mineralogy (N.L. Bowen, 1922).",
    "Superposition": "In an undisturbed sequence, younger rock layers lie above older ones — the foundational principle of stratigraphy.",
    "Pangaea": "The supercontinent that existed ~335-175 Ma, containing virtually all Earth's landmass before breaking into Laurasia and Gondwana.",
    "Batholith": "A large (>100 km²) igneous intrusion that crystallised deep in the crust — typically granitic, exposed by long-term erosion.",
    "Turbidite": "Graded sedimentary bed deposited by an underwater avalanche (turbidity current) — characteristic of deep marine slopes.",
    "Graben": "A down-dropped block between two parallel normal faults — forms rift valleys (Narmada graben, East African Rift).",
    "Barrovian Zones": "Metamorphic zones of increasing grade mapped by chlorite → biotite → garnet → staurolite → kyanite → sillimanite (George Barrow, 1893).",
}
_kt_cols = st.columns(2)
for i,(term,defn) in enumerate(_key_terms.items()):
    with _kt_cols[i%2]:
        st.markdown(f"""
        <div class='glass-card' style='padding:11px 14px;margin-bottom:8px;'>
            <div style='color:#c9a84c;font-size:0.82rem;font-weight:600;margin-bottom:4px;'>{term}</div>
            <div style='color:#94a3b8;font-size:0.76rem;line-height:1.55;'>{defn}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div class='section-heading'>📝 LIKELY EXAM QUESTIONS</div>", unsafe_allow_html=True)
_exam_qs = [
    ("Semester 1–2","Describe the internal structure of the Earth. How is it determined using seismic waves?"),
    ("Semester 1–2","Explain the significance of the Mohorovičić and Gutenberg discontinuities."),
    ("Semester 2–3","Describe the physical and optical properties of quartz. How does it appear in PPL vs XPL?"),
    ("Semester 3","Explain the factors controlling drainage patterns. Give examples from India."),
    ("Semester 3–4","Write a detailed note on the Gondwana Supergroup of India, with its stratigraphic sequence."),
    ("Semester 4","Describe Bowen's Reaction Series and its significance in igneous petrology."),
    ("Semester 4","Distinguish between conformity, disconformity, angular unconformity, and nonconformity."),
    ("Semester 5","Explain the concept of metamorphic facies. Describe the Barrovian zones with index minerals."),
    ("Semester 5","Write an account of the Deccan Traps — its extent, age, composition, and significance."),
    ("Semester 6","Describe the different types of hydrothermal ore deposits with Indian examples."),
    ("Semester 6","Write a note on the Indian stratigraphy from Precambrian to Quaternary."),
    ("Semester 7–8","Explain the theory of Plate Tectonics and its relevance to Indian geology."),
    ("Semester 7–8","Describe the Indian Ocean circulation pattern and its relationship to the monsoon."),
]
for sem, q in _exam_qs:
    st.markdown(f"""
    <div class='glass-card' style='padding:10px 14px;display:flex;gap:12px;align-items:start;'>
        <span style='background:rgba(201,168,76,0.12);color:#c9a84c;font-size:0.68rem;padding:2px 8px;
            border-radius:10px;white-space:nowrap;flex-shrink:0;'>{sem}</span>
        <div style='color:#e2e8f0;font-size:0.8rem;line-height:1.55;'>{q}</div>
    </div>""", unsafe_allow_html=True)
