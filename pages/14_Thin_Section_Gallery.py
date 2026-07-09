# GeoSphere India — Thin Section Gallery
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

st.set_page_config(page_title="Thin Section Gallery — GeoSphere India", page_icon="🔬", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Thin section", "Thin Section Gallery", "OPTICAL MINERALOGY")

st.markdown("<div class='section-heading'>THIN SECTION GALLERY — OPTICAL MINERALOGY</div>", unsafe_allow_html=True)
st.markdown("""
<div class='glass-card' style='padding:10px 16px;margin-bottom:12px;'>
    <span style='color:#94a3b8;font-size:0.78rem;'>
    🔬 <b style='color:#00d4ff;'>PPL</b> = Plane Polarised Light &nbsp;·&nbsp;
    <b style='color:#c084fc;'>XPL</b> = Cross Polarised Light (crossed nicols) &nbsp;·&nbsp;
    Slide thickness: <b style='color:#e2e8f0;'>0.03mm</b> &nbsp;·&nbsp;
    Photos sourced from Wikipedia/Wikimedia Commons (CC-licensed)
    </span>
</div>""", unsafe_allow_html=True)

ts_filter = st.selectbox("Filter by category",
    ["All","Silicates — Framework","Silicates — Sheet/Chain","Carbonates & Others","Rock Types"],
    key="ts_filter")

# Thin section entries with Wikipedia search terms for photos
ts_extended = [
    {"name":"Quartz","wiki":"Quartz","border":"#94a3b8","category":"Silicates — Framework",
     "ppl":"Colourless, glassy. High relief. No cleavage. Irregular fracture.",
     "xpl":"Low 1st-order grey/white interference colours. No twinning. Undulatory extinction in deformed rocks.",
     "uses":"Sand, glass, electronics (oscillators), gemstone (amethyst, citrine, rose quartz). Most abundant crustal mineral.",
     "india":"Pegmatite veins across India. Quartzite (metamorphosed sandstone) in Aravallis, Rajasthan."},
    {"name":"Plagioclase Feldspar","wiki":"Plagioclase","border":"#e2e8f0","category":"Silicates — Framework",
     "ppl":"White/grey, two cleavage directions at ~90°. Moderate relief.",
     "xpl":"Polysynthetic (albite) twinning — parallel bands, alternating light/dark. Key identification feature.",
     "uses":"Major component of granite, diorite, anorthosite. Used in ceramics. Ca-rich end (anorthite) in basalt.",
     "india":"Abundant in Deccan basalt (labradorite). Anorthosite bodies in Eastern Ghats belt."},
    {"name":"Orthoclase (K-Feldspar)","wiki":"Orthoclase","border":"#fbbf24","category":"Silicates — Framework",
     "ppl":"Pale pink/cream. Two cleavages at 90°. Low relief.",
     "xpl":"Low grey interference colours. Carlsbad twinning (two large halves). Perthite texture (Na-K exsolution).",
     "uses":"Ceramics, glass manufacture. Major mineral in granite and syenite. Potassium source.",
     "india":"Granites of Rajasthan (Jalore, Siwana), Tamil Nadu, Chhattisgarh. Pegmatites in AP."},
    {"name":"Biotite","wiki":"Biotite","border":"#92400e","category":"Silicates — Sheet/Chain",
     "ppl":"Brown to reddish-brown. Strong pleochroism (colour changes with rotation). Perfect basal cleavage.",
     "xpl":"High 2nd–3rd order interference colours (masked by body colour). Bird's-eye extinction.",
     "uses":"Insulation (electrical), lubricants, cosmetics, construction material. Index mineral in Barrovian metamorphism.",
     "india":"Widespread in Himalayan schists. Mica belts of Jharkhand–AP (world's former mica capital)."},
    {"name":"Muscovite","wiki":"Muscovite","border":"#e8c96a","category":"Silicates — Sheet/Chain",
     "ppl":"Colourless. Perfect basal cleavage. Slightly higher relief than quartz.",
     "xpl":"High 2nd-order interference colours (yellow, orange, pink). Parallel extinction.",
     "uses":"Electrical insulation (capacitors), windows (Russia glass), pigment, cosmetics.",
     "india":"Nellore Mica Belt (AP), Jharkhand, Rajasthan — major world supplier historically."},
    {"name":"Hornblende (Amphibole)","wiki":"Hornblende","border":"#1f2937","category":"Silicates — Sheet/Chain",
     "ppl":"Dark green to black. Strong pleochroism. Two cleavages at ~60°/120° — diagnostic.",
     "xpl":"High interference colours (masked). Inclined extinction (~15–25°). Columnar habit.",
     "uses":"Component of igneous rocks (diorite, amphibolite). Geothermobarometry indicator in metamorphics.",
     "india":"Common in Himalayan amphibolite-grade metamorphics. Deccan basalt secondary minerals."},
    {"name":"Augite (Pyroxene)","wiki":"Augite","border":"#374151","category":"Silicates — Sheet/Chain",
     "ppl":"Pale green to brown. Two cleavages at ~90° — distinguishes pyroxene from amphibole.",
     "xpl":"Moderate to high grey-pink interference colours. Simple twinning. Near-parallel extinction.",
     "uses":"Major mineral in basalt, gabbro, peridotite. Geochemistry tracer for mantle source rocks.",
     "india":"Abundant in Deccan Traps basalt. Garnet-pyroxene granulites in Eastern Ghats (eclogites)."},
    {"name":"Olivine","wiki":"Olivine","border":"#84cc16","category":"Silicates — Framework",
     "ppl":"Colourless to pale green. High positive relief. Irregular fractures. No cleavage.",
     "xpl":"Vivid 2nd–3rd order interference colours. Parallel extinction. Often altered to serpentine/iddingsite at margins.",
     "uses":"Refractory material (foundry sand), gemstone (peridot), source of Mg in geochemistry.",
     "india":"Dunites and peridotites in Andaman ophiolite. Kimberlite mantle xenoliths."},
    {"name":"Calcite","wiki":"Calcite","border":"#e5e7eb","category":"Carbonates & Others",
     "ppl":"Colourless. Very high relief. Rhombic cleavage (3 directions). Twinkling effect on stage rotation.",
     "xpl":"Extreme high-order 'pearly white' interference colours. Polysynthetic twins.",
     "uses":"Cement, lime, building stone, optical instruments (Iceland spar). Reacts with HCl.",
     "india":"Limestone formations across India (Rajasthan, AP, Karnataka). Marble (Makrana, Rajasthan)."},
    {"name":"Garnet","wiki":"Almandine","border":"#dc2626","category":"Silicates — Framework",
     "ppl":"Pink-red-brown. Very high relief. Isotropic (cubic system) — no birefringence.",
     "xpl":"Remains dark under XPL (isotropic). Diagnostic — any high-relief isotropic coloured mineral = garnet.",
     "uses":"Abrasive (garnet paper), gemstone (almandine, pyrope, spessartine, grossular). Geothermobarometry.",
     "india":"Rajasthan, Odisha, Tamil Nadu — major garnet producers. Beach placer deposits."},
    {"name":"Muscovite Schist (Rock)","wiki":"Schist","border":"#6b7280","category":"Rock Types",
     "ppl":"Foliated texture — aligned muscovite + quartz. Lepidoblastic texture.",
     "xpl":"Micas show high interference colours. Quartz shows low grey. Fabric clearly visible.",
     "uses":"Study of metamorphic grade (greenschist to amphibolite facies). Barrovian zone indicator.",
     "india":"Himalayan Lesser Himalaya zone. Aravalli metamorphic belt, Rajasthan."},
    {"name":"Basalt (Rock)","wiki":"Basalt","border":"#1e293b","category":"Rock Types",
     "ppl":"Fine-grained groundmass of pyroxene + plagioclase. May show vesicles (amygdaloidal).",
     "xpl":"Plagioclase laths show twinning. Ophitic texture (plagioclase enclosed in pyroxene). Flow alignment.",
     "uses":"Construction aggregate, road base. Study of mantle melting, flood volcanism.",
     "india":"Deccan Traps — 500,000 km², up to 3km thick. India's dominant extrusive rock."},
]

if ts_filter != "All":
    ts_show = [t for t in ts_extended if t["category"] == ts_filter]
else:
    ts_show = ts_extended

ts_cols = st.columns(2)
for i, ts in enumerate(ts_show):
    with ts_cols[i % 2]:
        show_wiki_photo(ts["wiki"], caption=f"{ts['name']} — Wikipedia/Wikimedia")
        st.markdown(f"""
        <div class='mineral-card' style='border-color:{ts["border"]}55;'>
            <div class='mineral-name' style='color:{ts["border"]};margin-bottom:8px;'>{ts["name"]}</div>
            <div style='font-size:0.72rem;color:#475569;margin-bottom:6px;'>
                <span style='background:rgba(0,212,255,0.1);color:#00d4ff;padding:2px 7px;border-radius:10px;'>{ts["category"]}</span>
            </div>
            <div style='color:#94a3b8;font-size:0.75rem;line-height:1.65;'>
            <b style='color:#00d4ff;'>PPL:</b> {ts["ppl"]}<br>
            <b style='color:#c084fc;'>XPL:</b> {ts["xpl"]}<br>
            <b style='color:#e8c96a;'>Uses:</b> {ts["uses"]}<br>
            <b style='color:#34d399;'>India:</b> {ts["india"]}
            </div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div class='section-heading'>INTERFERENCE COLOUR CHART (MICHEL-LÉVY)</div>", unsafe_allow_html=True)
min_names = ["Chlorite\n(0.005–0.012)","Quartz\n(0.009)","Plagioclase\n(0.007–0.012)",
             "Calcite\n(0.172)","Olivine\n(0.035)","Biotite\n(0.03–0.045)"]
biref_vals = [0.009, 0.009, 0.01, 0.172, 0.035, 0.04]
colors_br  = ["#10b981","#f59e0b","#94a3b8","#a78bfa","#84cc16","#f87171"]
fig_ml = go.Figure()
for nm, bv, cl in zip(min_names, biref_vals, colors_br):
    fig_ml.add_trace(go.Bar(x=[nm], y=[bv], marker_color=cl, name=nm,
        hovertemplate=f"<b>{nm}</b><br>Birefringence: {bv}<extra></extra>"))
fig_ml.add_shape(type="line", x0=-0.5, x1=5.5, y0=0.04, y1=0.04,
    line=dict(color="#00d4ff", width=1.5, dash="dash"))
fig_ml.add_annotation(x=5.5, y=0.04, text="2nd/3rd Order boundary", showarrow=False,
    font=dict(size=9, color="#00d4ff"), xanchor="right")
fig_ml.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8a7d65", family="Source Sans 3"), height=280,
    margin=dict(l=5,r=5,t=5,b=5), showlegend=False,
    title=dict(text="Mineral Birefringence Values (δ) — determines XPL interference colour",
               font=dict(size=10, color="#94a3b8")),
    xaxis=dict(tickfont=dict(size=9, color="#8a7d65")),
    yaxis=dict(title=dict(text="Birefringence (δ)", font=dict(color="#8a7d65")),
               gridcolor="rgba(255,255,255,0.05)"))
st.plotly_chart(fig_ml, use_container_width=True)
st.markdown("""
<div class='glass-card' style='padding:10px 16px;'>
<span style='color:#94a3b8;font-size:0.76rem;line-height:1.7;'>
<b style='color:#e2e8f0;'>Reading the chart:</b> Birefringence (δ = n<sub>max</sub> − n<sub>min</sub>) × section thickness (0.03mm) = retardation → Michel-Lévy chart gives the interference colour seen under XPL.
Calcite's extreme δ (0.172) explains its distinctive 'pearl-white' high-order colour. Quartz's low δ (0.009) gives only grey-white 1st-order colours.
</span></div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  ROTATING STAGE SIMULATION — colour change under XPL as stage rotates
# ═══════════════════════════════════════════════════════════════
st.markdown("<div class='section-heading'>ROTATING STAGE SIMULATION (XPL)</div>", unsafe_allow_html=True)
st.markdown("""
<div class='glass-card' style='padding:10px 16px;margin-bottom:12px;'>
<span style='color:#94a3b8;font-size:0.76rem;'>
Under crossed polars, a birefringent mineral goes through extinction (dark) four times per
360° rotation of the stage, with interference colours brightening between each extinction position.
Pick a mineral below and watch a simplified simulation of what you'd see down the microscope.</span>
</div>""", unsafe_allow_html=True)

stage_options = {t["name"]: t for t in ts_extended if t["category"] != "Rock Types"}
stage_pick = st.selectbox("Mineral to simulate", list(stage_options.keys()), key="stage_pick")
stage_mineral = stage_options[stage_pick]

stage_colour_cycles = {
    "Quartz": ["#0b0b0f","#7d8a99","#c7cdd4","#7d8a99"],
    "Plagioclase Feldspar": ["#0b0b0f","#5b6b7a","#b7c4d1","#5b6b7a"],
    "Orthoclase (K-Feldspar)": ["#0b0b0f","#6b6b7a","#9ea3c4","#6b6b7a"],
    "Biotite": ["#0b0b0f","#7a4a1f","#b06a2b","#7a4a1f"],
    "Muscovite": ["#0b0b0f","#d4b23c","#f2d97a","#d4b23c"],
    "Hornblende (Amphibole)": ["#0b0b0f","#2f6b4f","#4fae7d","#2f6b4f"],
    "Augite (Pyroxene)": ["#0b0b0f","#a3607a","#d68fae","#a3607a"],
    "Olivine": ["#0b0b0f","#7fae2f","#c6ea6a","#7fae2f"],
    "Calcite": ["#0b0b0f","#e6c9e6","#fdf4ff","#e6c9e6"],
    "Garnet": ["#0b0b0f","#0b0b0f","#0b0b0f","#0b0b0f"],
}
cyc = stage_colour_cycles.get(stage_pick, ["#0b0b0f","#8a7d65","#c9a84c","#8a7d65"])
anim_name = "stagecyc_" + re.sub(r'[^a-zA-Z0-9]', '', stage_pick)
isotropic_note = " — <b>isotropic</b>: stays dark at every angle (diagnostic!)" if stage_pick == "Garnet" else ""

col_sim, col_note = st.columns([1, 1.4])
with col_sim:
    st.markdown(f"""
    <style>
    @keyframes {anim_name} {{
        0%   {{ background:{cyc[0]}; transform:rotate(0deg); }}
        25%  {{ background:{cyc[1]}; transform:rotate(90deg); }}
        50%  {{ background:{cyc[2]}; transform:rotate(180deg); }}
        75%  {{ background:{cyc[3]}; transform:rotate(270deg); }}
        100% {{ background:{cyc[0]}; transform:rotate(360deg); }}
    }}
    </style>
    <div style='width:180px;height:180px;border-radius:50%;margin:10px auto;
        border:3px solid #c9a84c55;position:relative;overflow:hidden;
        display:flex;align-items:center;justify-content:center;'>
        <div style='width:100%;height:100%;animation:{anim_name} 4s linear infinite;
            display:flex;align-items:center;justify-content:center;'>
            <div style='width:70%;height:12%;background:rgba(0,0,0,0.35);border-radius:3px;'></div>
        </div>
    </div>
    <div style='text-align:center;color:#475569;font-size:0.68rem;'>Simplified simulation — not measured colour data</div>
    """, unsafe_allow_html=True)
with col_note:
    st.markdown(f"""
    <div class='mineral-card'>
    <div style='color:#c9a84c;font-weight:700;margin-bottom:6px;'>{stage_pick}</div>
    <div style='color:#94a3b8;font-size:0.78rem;line-height:1.7;'>
    As the stage rotates through 360°, {stage_pick.lower()} passes through <b>4 positions of extinction</b>
    (dark, every 90°) and 4 positions of maximum interference colour (at 45° between each extinction){isotropic_note}.
    <br><br><b style='color:#e2e8f0;'>XPL description:</b> {stage_mineral["xpl"]}
    </div></div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  "IDENTIFY THIS MINERAL" QUIZ MODE
# ═══════════════════════════════════════════════════════════════
st.markdown("<div class='section-heading'>🔎 IDENTIFY THIS MINERAL — QUIZ MODE</div>", unsafe_allow_html=True)

if "ts_quiz_q" not in st.session_state:
    st.session_state.ts_quiz_q = random.choice(ts_extended)
if "ts_quiz_score" not in st.session_state:
    st.session_state.ts_quiz_score = [0, 0]
if "ts_quiz_answered" not in st.session_state:
    st.session_state.ts_quiz_answered = False

q = st.session_state.ts_quiz_q
qc1, qc2 = st.columns([1, 1.3])
with qc1:
    show_wiki_photo(q["wiki"], caption="Guess this mineral / rock")
with qc2:
    st.markdown(f"""<div class='glass-card' style='padding:8px 14px;margin-bottom:8px;'>
        <span style='color:#94a3b8;font-size:0.78rem;'><b style='color:#00d4ff;'>PPL clue:</b> {q["ppl"]}</span>
    </div>""", unsafe_allow_html=True)
    other_names = [t["name"] for t in ts_extended if t["name"] != q["name"]]
    choices = random.sample(other_names, min(3, len(other_names))) + [q["name"]]
    random.shuffle(choices)
    guess = st.radio("Your answer:", choices, key=f"ts_guess_{id(q)}", index=None)
    gcol1, gcol2 = st.columns(2)
    with gcol1:
        if st.button("Submit answer", key="ts_quiz_submit") and guess is not None and not st.session_state.ts_quiz_answered:
            st.session_state.ts_quiz_answered = True
            st.session_state.ts_quiz_score[1] += 1
            if guess == q["name"]:
                st.session_state.ts_quiz_score[0] += 1
                st.success(f"✅ Correct — it's {q['name']}!")
            else:
                st.error(f"❌ Not quite — that was {q['name']}.")
    with gcol2:
        if st.button("Next mineral ▶", key="ts_quiz_next"):
            st.session_state.ts_quiz_q = random.choice(ts_extended)
            st.session_state.ts_quiz_answered = False
            st.rerun()
    c, t_ = st.session_state.ts_quiz_score
    st.markdown(f"<span style='color:#8a7d65;font-size:0.75rem;'>Score: <b style='color:#c9a84c;'>{c}/{t_}</b></span>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  HAND SPECIMEN vs THIN SECTION COMPARISON
# ═══════════════════════════════════════════════════════════════
st.markdown("<div class='section-heading'>🪨 HAND SPECIMEN vs THIN SECTION</div>", unsafe_allow_html=True)
st.markdown("""<div class='glass-card' style='padding:10px 16px;margin-bottom:12px;'>
<span style='color:#94a3b8;font-size:0.76rem;'>What you see in the field/lab with the naked eye vs what the
same material reveals at 0.03mm thickness under the polarising microscope.</span></div>""", unsafe_allow_html=True)

compare_pick = st.selectbox("Compare a rock/mineral", [t["name"] for t in ts_extended], key="compare_pick")
comp = next(t for t in ts_extended if t["name"] == compare_pick)
cc1, cc2 = st.columns(2)
with cc1:
    st.markdown("<div style='color:#c9a84c;font-size:0.8rem;margin-bottom:4px;'>👁 HAND SPECIMEN</div>", unsafe_allow_html=True)
    show_wiki_photo(comp["wiki"], caption=f"{comp['name']} — hand specimen view")
with cc2:
    st.markdown("<div style='color:#00d4ff;font-size:0.8rem;margin-bottom:4px;'>🔬 THIN SECTION (XPL)</div>", unsafe_allow_html=True)
    # A real "X thin section micrograph" photo essentially never exists as a
    # standalone Wikipedia article, so instead of a doomed/risky search, show
    # an accurate interference-colour swatch using the same data as the
    # Rotating Stage Simulation above.
    _xpl_swatch_colors = {
        "Quartz": "#c7cdd4", "Plagioclase Feldspar": "#b7c4d1", "Orthoclase (K-Feldspar)": "#9ea3c4",
        "Biotite": "#b06a2b", "Muscovite": "#f2d97a", "Hornblende (Amphibole)": "#4fae7d",
        "Augite (Pyroxene)": "#d68fae", "Olivine": "#c6ea6a", "Calcite": "#fdf4ff", "Garnet": "#0b0b0f",
    }
    _swatch = _xpl_swatch_colors.get(comp["name"], "#8a7d65")
    st.markdown(f"""
    <div style='width:100%;aspect-ratio:1;border-radius:10px;margin-bottom:6px;
        background:{_swatch};border:2px solid #c9a84c55;
        display:flex;align-items:center;justify-content:center;'>
        <div style='width:65%;height:10%;background:rgba(0,0,0,0.35);border-radius:3px;'></div>
    </div>
    <div style='text-align:center;color:#475569;font-size:0.68rem;'>{comp['name']} — under crossed polars, illustrative colour</div>
    """, unsafe_allow_html=True)
st.markdown(f"""<div class='glass-card' style='padding:10px 16px;'>
<span style='color:#94a3b8;font-size:0.76rem;'>
<b style='color:#e2e8f0;'>Macro → Micro:</b> In hand specimen you judge {comp['name'].lower()} by colour, lustre and
cleavage with the naked eye or a hand lens. At thin-section scale, the same grain reveals its true optical
identity — {comp['xpl'].lower()}</span></div>""", unsafe_allow_html=True)
# ═══════════════════════════════════════════════════════════════