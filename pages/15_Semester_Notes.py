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

st.markdown("<div class='section-heading'>📝 LIKELY EXAM QUESTIONS — WITH MODEL ANSWERS</div>", unsafe_allow_html=True)
_exam_qs = [
    ("Semester 1–2","Describe the internal structure of the Earth. How is it determined using seismic waves?",
     "Earth has three main compositional layers — crust (5–70 km), mantle (to 2,900 km), and core (to 6,371 km) — "
     "further divided mechanically into lithosphere, asthenosphere, and inner/outer core. Structure is determined "
     "from seismic wave behaviour: P-waves speed up sharply at the Mohorovičić discontinuity (crust–mantle) due to "
     "a density/composition change, and S-waves disappear entirely through the outer core because S-waves cannot "
     "travel through liquid — proving the outer core is molten. P-wave speed-up again at ~5,150 km marks the solid "
     "inner core (Lehmann discontinuity)."),
    ("Semester 1–2","Explain the significance of the Mohorovičić and Gutenberg discontinuities.",
     "The Mohorovičić discontinuity ('Moho'), found by Andrija Mohorovičić in 1909, marks the crust–mantle boundary "
     "where P-wave velocity jumps from ~7 to ~8 km/s due to the compositional change from crustal silicates to "
     "denser mantle peridotite. The Gutenberg discontinuity (~2,900 km depth) marks the mantle–core boundary, "
     "identified by the 'S-wave shadow zone' where S-waves vanish entirely — direct proof the outer core is liquid, "
     "since shear waves cannot propagate through a fluid."),
    ("Semester 2–3","Describe the physical and optical properties of quartz. How does it appear in PPL vs XPL?",
     "Quartz (SiO₂) has hardness 7, conchoidal fracture, no cleavage, vitreous lustre, and trigonal/hexagonal "
     "crystal system. In PPL (plane-polarised light) it is colourless and relief-free (relief matches Canada "
     "balsam/resin closely). In XPL (crossed polars) it shows low first-order grey/white interference colours and "
     "characteristic undulatory extinction when strained (a diagnostic sign of tectonic deformation)."),
    ("Semester 3","Explain the factors controlling drainage patterns. Give examples from India.",
     "Drainage pattern is controlled by underlying rock type, structure (fault/fold/joint orientation), and slope. "
     "Dendritic patterns form on uniform, flat-lying rock (Gangetic plains); trellis patterns follow folded "
     "sedimentary belts with alternating hard/soft rock (parts of the Himalayan foothills); radial patterns "
     "develop off a central high point (Amarkantak plateau, source of the Narmada and Son); and rectangular "
     "patterns follow joint/fault intersections (parts of the Peninsular shield)."),
    ("Semester 3–4","Write a detailed note on the Gondwana Supergroup of India, with its stratigraphic sequence.",
     "The Gondwana Supergroup (Upper Carboniferous–Lower Cretaceous) is India's principal coal-bearing sequence, "
     "deposited in fault-bounded intracratonic basins (Damodar, Son-Mahanadi, Godavari valleys). It is divided "
     "into Lower Gondwana (Talchir tillites → Barakar coal measures → Barren Measures) reflecting a glacial-to-"
     "warm climate transition, and Upper Gondwana (Mahadeva, Rajmahal, Umia) dominated by fluvial sandstones and, "
     "later, Rajmahal Trap volcanics. It preserves the Glossopteris flora linking India to Gondwanaland."),
    ("Semester 4","Describe Bowen's Reaction Series and its significance in igneous petrology.",
     "N.L. Bowen (1922) showed that minerals crystallise from a cooling basaltic melt in a predictable sequence: "
     "a discontinuous branch (olivine → pyroxene → amphibole → biotite) where each mineral reacts with the melt to "
     "form the next, and a continuous branch where plagioclase feldspar progressively changes composition from "
     "calcium-rich to sodium-rich. It explains why certain minerals are never found together, predicts the order "
     "of crystallisation in a magma chamber, and underpins the classification of igneous rocks by mineral content."),
    ("Semester 4","Distinguish between conformity, disconformity, angular unconformity, and nonconformity.",
     "A conformity is continuous, parallel deposition with no time gap. A disconformity is a gap between parallel "
     "layers (erosion or non-deposition, but no tilting) — often hard to spot without fossil/dating evidence. An "
     "angular unconformity shows older layers tilted/eroded before younger flat layers were deposited on top — "
     "visually the clearest type. A nonconformity is sedimentary rock deposited directly on eroded igneous or "
     "metamorphic basement rock."),
    ("Semester 5","Explain the concept of metamorphic facies. Describe the Barrovian zones with index minerals.",
     "A metamorphic facies is a set of mineral assemblages that forms under a specific pressure–temperature range, "
     "regardless of the original rock's composition — allowing geologists to read P-T history from mineralogy "
     "alone (e.g. greenschist, amphibolite, granulite, eclogite facies). Barrovian zones (George Barrow, 1893) map "
     "increasing metamorphic grade across Scotland using index minerals in a fixed order: chlorite → biotite → "
     "garnet → staurolite → kyanite → sillimanite, each appearing at a higher temperature threshold."),
    ("Semester 5","Write an account of the Deccan Traps — its extent, age, composition, and significance.",
     "The Deccan Traps cover ~500,000 km² of west-central India with tholeiitic flood basalt erupted mainly "
     "~66 Ma, right at the Cretaceous–Paleogene (K-Pg) boundary. Individual flows are 10–50 m thick, stacked up to "
     "2 km, with columnar jointing and zeolite-filled vesicles (source of India's finest zeolites and amethyst). "
     "Their eruption is considered a major contributing factor — alongside the Chicxulub asteroid impact — to the "
     "end-Cretaceous mass extinction that killed the non-avian dinosaurs."),
    ("Semester 6","Describe the different types of hydrothermal ore deposits with Indian examples.",
     "Hydrothermal deposits form when hot mineral-rich fluids precipitate ore in fractures/pore spaces. Types "
     "include vein deposits (Kolar gold fields, Karnataka — quartz-gold veins in greenstone belts), porphyry "
     "deposits (disseminated copper around an intrusion — Malanjkhand, Madhya Pradesh), and volcanogenic massive "
     "sulphide (VMS) deposits (Rajpura-Dariba, Rajasthan — zinc-lead-copper in metavolcanics). Fluid source, "
     "temperature, and host-rock chemistry determine which ore minerals precipitate."),
    ("Semester 6","Write a note on the Indian stratigraphy from Precambrian to Quaternary.",
     "India's stratigraphic column spans the Archaean Dharwar/Singhbhum cratons (>3 Ga gneiss-greenstone), "
     "Proterozoic Aravalli-Delhi and Cuddapah-Vindhyan basins (metasediments, limestone), Gondwana Supergroup "
     "(Carboniferous–Cretaceous coal measures), Deccan Traps (66 Ma flood basalt), Siwalik Group (Miocene–"
     "Pleistocene Himalayan foreland molasse), and Quaternary alluvium of the Indo-Gangetic plains — together "
     "recording almost the entire span of Earth history on one landmass."),
    ("Semester 7–8","Explain the theory of Plate Tectonics and its relevance to Indian geology.",
     "Plate tectonics holds that the lithosphere is broken into rigid plates moving over the plastic asthenosphere, "
     "driven by mantle convection, interacting at divergent, convergent, and transform boundaries. It directly "
     "explains India's geological history: rifting from Gondwana (~180 Ma), rapid northward drift over the "
     "Réunion hotspot (Deccan Traps, 66 Ma), and continent-continent collision with Eurasia (~50 Ma) that is "
     "still building the Himalayas today at ~5 cm/yr."),
    ("Semester 7–8","Describe the Indian Ocean circulation pattern and its relationship to the monsoon.",
     "Unlike other oceans, Indian Ocean surface currents reverse seasonally because they are driven by monsoon "
     "winds rather than fixed trade winds: the Southwest Monsoon Current flows east in summer, while the "
     "Northeast Monsoon Current flows west in winter. This coupling exists because the Asian landmass heats and "
     "cools faster than the ocean, driving the pressure differences that create the monsoon winds, which in turn "
     "drive the currents — a unique two-way ocean–atmosphere feedback found nowhere else."),
]
for sem, q, ans in _exam_qs:
    st.markdown(f"""
    <div class='glass-card' style='padding:10px 14px;margin-bottom:2px;display:flex;gap:12px;align-items:start;'>
        <span style='background:rgba(201,168,76,0.12);color:#c9a84c;font-size:0.68rem;padding:2px 8px;
            border-radius:10px;white-space:nowrap;flex-shrink:0;'>{sem}</span>
        <div style='color:#e2e8f0;font-size:0.8rem;line-height:1.55;'>{q}</div>
    </div>""", unsafe_allow_html=True)
    with st.expander("✅ Show model answer"):
        st.markdown(f"<div style='color:#94a3b8;font-size:0.78rem;line-height:1.7;'>{ans}</div>", unsafe_allow_html=True)
