# GeoSphere India — Mineral Explorer
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

st.set_page_config(page_title="Mineral Explorer — GeoSphere India", page_icon="💎", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Mineral", "Mineral Explorer", "PROPERTIES, PHOTOS & 3D CRYSTALS")

st.markdown("<div class='section-heading'>MINERAL EXPLORER — PROPERTIES, PHOTOS & 3D CRYSTALS</div>", unsafe_allow_html=True)

min_tab1, min_tab2, min_tab3 = st.tabs(["💎 Mineral Gallery", "🔮 3D Crystal Viewer", "🔍 Field Identification Guide"])

with min_tab2:
    st.markdown("<div style='color:#94a3b8;font-size:0.8rem;margin-bottom:10px;'>Interactive 3D crystal structure — drag to rotate, scroll to zoom. Each mineral system has a distinct geometry.</div>", unsafe_allow_html=True)
    crystal_choice = st.selectbox("Select Crystal System", [
        "Cubic — Garnet / Halite / Diamond",
        "Hexagonal — Quartz / Calcite / Apatite",
        "Tetragonal — Zircon / Rutile",
        "Orthorhombic — Olivine / Aragonite",
        "Monoclinic — Gypsum / Orthoclase",
        "Triclinic — Plagioclase / Kyanite",
    ], key="crystal_sys")

    crystal_configs = {
        "Cubic — Garnet / Halite / Diamond": {
            "color": "#dc2626", "name": "Cubic System",
            "shape": "cube", "mineral": "Garnet (Almandine)",
            "formula": "Fe₃Al₂(SiO₄)₃", "desc": "All 3 axes equal & at 90°. Forms cubes, octahedra, dodecahedra."
        },
        "Hexagonal — Quartz / Calcite / Apatite": {
            "color": "#e0f2fe", "name": "Hexagonal System",
            "shape": "hex", "mineral": "Quartz (α-Quartz)",
            "formula": "SiO₂", "desc": "6-fold symmetry axis. Prisms + pyramids. Most abundant crustal mineral."
        },
        "Tetragonal — Zircon / Rutile": {
            "color": "#fbbf24", "name": "Tetragonal System",
            "shape": "tet", "mineral": "Zircon",
            "formula": "ZrSiO₄", "desc": "2 equal axes + 1 different, all at 90°. Forms elongated prisms."
        },
        "Orthorhombic — Olivine / Aragonite": {
            "color": "#84cc16", "name": "Orthorhombic System",
            "shape": "ortho", "mineral": "Olivine (Forsterite)",
            "formula": "(Mg,Fe)₂SiO₄", "desc": "3 unequal axes all at 90°. Stubby crystals or granular."
        },
        "Monoclinic — Gypsum / Orthoclase": {
            "color": "#e8c96a", "name": "Monoclinic System",
            "shape": "mono", "mineral": "Orthoclase",
            "formula": "KAlSi₃O₈", "desc": "3 unequal axes, one inclined. Tabular or prismatic crystals."
        },
        "Triclinic — Plagioclase / Kyanite": {
            "color": "#94a3b8", "name": "Triclinic System",
            "shape": "tri", "mineral": "Plagioclase (Labradorite)",
            "formula": "NaAlSi₃O₈–CaAl₂Si₂O₈", "desc": "3 unequal axes, all inclined. Lowest symmetry. Polysynthetic twinning."
        },
    }

    cfg = crystal_configs[crystal_choice]

    # Three.js 3D crystal viewer as inline HTML
    crystal_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ margin:0; background:#070b18; overflow:hidden; }}
  canvas {{ display:block; }}
  #info {{
position:absolute; top:12px; left:50%; transform:translateX(-50%);
color:#c9a84c; font-family:'Arial',sans-serif; font-size:12px;
letter-spacing:2px; text-align:center; pointer-events:none;
text-shadow:0 0 10px rgba(201,168,76,0.6);
  }}
  #label {{
position:absolute; bottom:14px; left:50%; transform:translateX(-50%);
color:#94a3b8; font-family:'Arial',sans-serif; font-size:11px;
text-align:center; pointer-events:none;
  }}
</style>
</head>
<body>
<div id='info'>{cfg["name"].upper()}</div>
<div id='label'>{cfg["mineral"]} · {cfg["formula"]}</div>
<script src='https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'></script>
<script>
const W = window.innerWidth, H = window.innerHeight;
const renderer = new THREE.WebGLRenderer({{antialias:true, alpha:true}});
renderer.setSize(W, H);
renderer.setPixelRatio(window.devicePixelRatio);
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, W/H, 0.1, 100);
camera.position.set(0, 0, 4);

// Lighting
const amb = new THREE.AmbientLight(0xffffff, 0.3); scene.add(amb);
const pt1 = new THREE.PointLight(0xc9a84c, 1.8, 20); pt1.position.set(3,3,3); scene.add(pt1);
const pt2 = new THREE.PointLight(0x00d4ff, 0.8, 20); pt2.position.set(-3,-2,2); scene.add(pt2);
const pt3 = new THREE.PointLight(0xffffff, 0.5, 20); pt3.position.set(0,4,-2); scene.add(pt3);

// Wireframe overlay
const wfMat = new THREE.MeshBasicMaterial({{color:0xc9a84c, wireframe:true, transparent:true, opacity:0.18}});

// Crystal geometry based on system
const shape = '{cfg["shape"]}';
const crystalColor = '{cfg["color"]}';
let geo, geo2;

if (shape === 'cube') {{
  // Dodecahedron = garnet habit
  geo = new THREE.DodecahedronGeometry(1.1, 0);
  geo2 = new THREE.DodecahedronGeometry(1.12, 0);
}} else if (shape === 'hex') {{
  // Hexagonal prism + top pyramid = quartz habit
  geo = new THREE.CylinderGeometry(0.9, 0.9, 1.8, 6, 1);
  geo2 = new THREE.CylinderGeometry(0.92, 0.92, 1.82, 6, 1);
}} else if (shape === 'tet') {{
  // Elongated octahedron = tetragonal
  geo = new THREE.CylinderGeometry(0.6, 0.6, 2.2, 4, 1);
  geo2 = new THREE.CylinderGeometry(0.62, 0.62, 2.22, 4, 1);
}} else if (shape === 'ortho') {{
  // Box, unequal sides = orthorhombic
  geo = new THREE.BoxGeometry(1.6, 1.0, 0.7);
  geo2 = new THREE.BoxGeometry(1.62, 1.02, 0.72);
}} else if (shape === 'mono') {{
  // Sheared box = monoclinic
  geo = new THREE.BoxGeometry(1.4, 0.8, 1.1);
  geo2 = new THREE.BoxGeometry(1.42, 0.82, 1.12);
}} else {{
  // Triclinic = irregular box
  geo = new THREE.OctahedronGeometry(1.1, 0);
  geo2 = new THREE.OctahedronGeometry(1.12, 0);
}}

const mat = new THREE.MeshPhongMaterial({{
  color: new THREE.Color(crystalColor),
  emissive: new THREE.Color(crystalColor).multiplyScalar(0.08),
  shininess: 120, specular: new THREE.Color(0xffffff),
  transparent: true, opacity: 0.82,
  side: THREE.DoubleSide,
}});

const mesh = new THREE.Mesh(geo, mat);
const wfMesh = new THREE.Mesh(geo2, wfMat);
scene.add(mesh);
scene.add(wfMesh);

// Particle field (background stars = mineral atoms)
const partGeo = new THREE.BufferGeometry();
const pCount = 280;
const pPos = new Float32Array(pCount * 3);
for(let i=0; i<pCount*3; i++) pPos[i] = (Math.random()-0.5)*14;
partGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
const partMat = new THREE.PointsMaterial({{color:0xc9a84c, size:0.025, transparent:true, opacity:0.5}});
scene.add(new THREE.Points(partGeo, partMat));

// Mouse drag rotation
let isDragging=false, prevX=0, prevY=0, velX=0, velY=0;
renderer.domElement.addEventListener('mousedown', e=>{{isDragging=true;prevX=e.clientX;prevY=e.clientY;}});
renderer.domElement.addEventListener('mouseup', ()=>{{isDragging=false;}});
renderer.domElement.addEventListener('mousemove', e=>{{
  if(!isDragging) return;
  velX=(e.clientX-prevX)*0.012; velY=(e.clientY-prevY)*0.012;
  mesh.rotation.y+=velX; mesh.rotation.x+=velY;
  wfMesh.rotation.y+=velX; wfMesh.rotation.x+=velY;
  prevX=e.clientX; prevY=e.clientY;
}});
renderer.domElement.addEventListener('wheel', e=>{{
  camera.position.z = Math.max(2, Math.min(8, camera.position.z + e.deltaY*0.008));
}});
// Touch support
renderer.domElement.addEventListener('touchstart', e=>{{isDragging=true;prevX=e.touches[0].clientX;prevY=e.touches[0].clientY;}});
renderer.domElement.addEventListener('touchend', ()=>{{isDragging=false;}});
renderer.domElement.addEventListener('touchmove', e=>{{
  if(!isDragging) return;
  velX=(e.touches[0].clientX-prevX)*0.012; velY=(e.touches[0].clientY-prevY)*0.012;
  mesh.rotation.y+=velX; mesh.rotation.x+=velY;
  wfMesh.rotation.y+=velX; wfMesh.rotation.x+=velY;
  prevX=e.touches[0].clientX; prevY=e.touches[0].clientY;
}});

function animate() {{
  requestAnimationFrame(animate);
  if(!isDragging) {{
mesh.rotation.y += 0.006;
mesh.rotation.x += 0.002;
wfMesh.rotation.y += 0.006;
wfMesh.rotation.x += 0.002;
velX*=0.9; velY*=0.9;
  }}
  renderer.render(scene, camera);
}}
animate();
</script>
</body>
</html>
"""
    import streamlit.components.v1 as components
    components.html(crystal_html, height=400, scrolling=False)

    st.markdown(f"""
    <div class='glass-card' style='margin-top:12px;text-align:center;'>
        <div style='color:#c9a84c;font-family:Playfair Display,Georgia,serif;font-size:1rem;font-weight:600;'>{cfg["mineral"]}</div>
        <div style='color:#475569;font-size:0.72rem;margin:4px 0 8px;'>{cfg["formula"]}</div>
        <div style='color:#94a3b8;font-size:0.8rem;line-height:1.7;'>{cfg["desc"]}</div>
        <div style='color:#475569;font-size:0.7rem;margin-top:8px;'>Drag to rotate · Scroll to zoom · Touch supported</div>
    </div>""", unsafe_allow_html=True)

with min_tab1:
    search_m = st.text_input("🔍 Search minerals", placeholder="e.g. Quartz, Calcite, Magnetite...")
    filtered = [m for m in MINERALS if not search_m or
                search_m.lower() in m["name"].lower() or
                search_m.lower() in m["desc"].lower() or
                search_m.lower() in m.get("india","").lower()]

    if not filtered:
        st.warning("No minerals found. Try different terms.")
    else:
        cols = st.columns(3)
        for i, m in enumerate(filtered):
            with cols[i % 3]:
                show_wiki_photo(m["name"], caption=m["name"])
                stars = "⬜" * (10 - int(m["hardness"]*10//10)) + "🟦" * int(m["hardness"])
                st.markdown(f"""
                <div class='mineral-card'>
                    <div style='display:flex;align-items:center;gap:10px;margin-bottom:8px;'>
                        <span style='font-size:1.8rem;'>{m["emoji"]}</span>
                        <div>
                            <div class='mineral-name'>{m["name"]}</div>
                            <div class='mineral-formula'>{m["formula"]}</div>
                        </div>
                    </div>
                    <div style='color:#94a3b8;font-size:0.73rem;line-height:1.8;'>
                    ⚡ <b style='color:#e2e8f0;'>Hardness:</b> {m["hardness"]} (Mohs)<br>
                    ✨ <b style='color:#e2e8f0;'>Lustre:</b> {m["luster"]}<br>
                    🔪 <b style='color:#e2e8f0;'>Cleavage:</b> {m["cleavage"]}<br>
                    🔷 <b style='color:#e2e8f0;'>System:</b> {m["system"]}<br>
                    🎨 <b style='color:#e2e8f0;'>Color:</b> {m["color"]}<br>
                    🇮🇳 <b style='color:#e2e8f0;'>India:</b> {m.get("india","—")}<br>
                    🏭 <b style='color:#e2e8f0;'>Uses:</b> {m["use"]}<br>
                    </div>
                    <div class='mineral-desc' style='margin-top:8px;border-top:1px solid rgba(0,212,255,0.1);padding-top:6px;'>{m["desc"]}</div>
                </div>""", unsafe_allow_html=True)

with min_tab3:
    st.markdown("""
    <div class='glass-card' style='padding:10px 16px;margin-bottom:14px;'>
        <span style='color:#94a3b8;font-size:0.78rem;'>
        🔍 The step-by-step process geology students use in practicals to identify an unknown mineral specimen —
        work through each step in order.
        </span>
    </div>""", unsafe_allow_html=True)

    steps = [
        ("1️⃣","Observe Colour","Note the mineral's colour in fresh light — but be cautious: colour alone is unreliable "
         "since impurities can tint many minerals (e.g. quartz can be clear, purple, pink, or smoky)."),
        ("2️⃣","Check the Streak","Scrape the mineral across an unglazed porcelain streak plate. The colour of the "
         "powder left behind is far more diagnostic than the mineral's outward colour."),
        ("3️⃣","Check Lustre","Is the surface metallic (like a metal) or non-metallic? Non-metallic lustres include "
         "glassy (vitreous), pearly, silky, greasy, resinous, dull/earthy, or adamantine (diamond-like)."),
        ("4️⃣","Scratch Test (Hardness)","Use the Mohs scale — try scratching with a fingernail (2.5), a copper coin "
         "(3.5), a steel knife/file (6.5), or glass (5.5) to bracket the hardness."),
        ("5️⃣","Check Cleavage / Fracture","Does it break along smooth flat planes (cleavage) or irregularly "
         "(fracture — conchoidal, splintery, uneven)? Count the cleavage directions and angles between them."),
        ("6️⃣","Acid Test","A drop of dilute HCl fizzes on calcite (effervesces readily) but not on dolomite unless "
         "powdered — a fast way to tell the two carbonates apart in the field."),
        ("7️⃣","Decision","Combine all observations — colour, streak, lustre, hardness, cleavage, and any special "
         "property (magnetism, taste, fluorescence) — and cross-check against a mineral identification table."),
    ]
    for em, title, detail in steps:
        st.markdown(f"""
        <div class='glass-card' style='padding:12px 16px;margin-bottom:8px;display:flex;gap:14px;align-items:flex-start;'>
            <span style='font-size:1.3rem;'>{em}</span>
            <div>
                <div style='color:#c9a84c;font-weight:600;font-size:0.85rem;margin-bottom:3px;'>{title}</div>
                <div style='color:#94a3b8;font-size:0.78rem;line-height:1.6;'>{detail}</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-heading'>QUICK REFERENCE — SPECIAL PROPERTIES</div>", unsafe_allow_html=True)
    sp_cols = st.columns(4)
    specials = [
        ("🧲","Magnetism","Magnetite attracts a compass needle or paperclip directly"),
        ("👅","Taste","Halite (rock salt) tastes distinctly salty"),
        ("💡","Fluorescence","Fluorite glows under UV light — hence the name"),
        ("🪞","Double Refraction","Calcite (Iceland Spar) doubles images seen through it"),
    ]
    for i, (em, name, note) in enumerate(specials):
        with sp_cols[i]:
            st.markdown(f"""<div class='glass-card' style='padding:10px 12px;text-align:center;'>
                <div style='font-size:1.4rem;'>{em}</div>
                <div style='color:#e2e8f0;font-size:0.75rem;font-weight:600;margin-top:4px;'>{name}</div>
                <div style='color:#94a3b8;font-size:0.68rem;margin-top:3px;line-height:1.4;'>{note}</div>
            </div>""", unsafe_allow_html=True)

# Mohs chart
st.markdown("<div class='section-heading'>MOHS HARDNESS SCALE</div>", unsafe_allow_html=True)
mohs = {"Talc":1,"Gypsum":2,"Calcite":3,"Fluorite":4,"Apatite":5,
        "Orthoclase":6,"Quartz":7,"Topaz":8,"Corundum":9,"Diamond":10}
fig_mh = go.Figure(go.Bar(x=list(mohs.keys()), y=list(mohs.values()),
    marker=dict(color=list(mohs.values()), colorscale=[[0,"#00d4ff"],[0.5,"#7c3aed"],[1,"#f59e0b"]],
                showscale=True, colorbar=dict(tickfont=dict(color="#8a7d65"), title="Hardness")),
    text=list(mohs.values()), textposition="outside", textfont_color="#f0e6d0",
    hovertemplate="<b>%{x}</b><br>Hardness: %{y}<extra></extra>"))
fig_mh.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8a7d65", family="Source Sans 3"), height=280,
    margin=dict(l=5,r=60,t=5,b=5),
    xaxis=dict(color="#8a7d65"), yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
st.plotly_chart(fig_mh, use_container_width=True)

st.markdown("<div class='section-heading'>HOW HARD IS THAT? — EVERYDAY OBJECT COMPARISON</div>", unsafe_allow_html=True)
st.markdown("""
<div class='glass-card' style='padding:10px 16px;margin-bottom:10px;'>
    <span style='color:#94a3b8;font-size:0.78rem;'>
    🖐️ Use everyday objects to estimate hardness in the field — no reference minerals needed.
    </span>
</div>""", unsafe_allow_html=True)
everyday = [
    ("💅","Fingernail","2.5","Scratches talc & gypsum, not calcite"),
    ("🪙","Copper Coin","3.5","Scratches calcite, not fluorite"),
    ("🪟","Glass Plate","5.5","Scratches apatite, not orthoclase"),
    ("🗜️","Steel Knife / File","6.5","Scratches orthoclase, not quartz"),
    ("🏺","Streak Plate (unglazed porcelain)","~6.5","Used for streak test, not hardness"),
]
ec = st.columns(len(everyday))
for i, (em, obj, hd, note) in enumerate(everyday):
    with ec[i]:
        st.markdown(f"""<div class='glass-card' style='padding:10px 8px;text-align:center;'>
            <div style='font-size:1.5rem;'>{em}</div>
            <div style='color:#e2e8f0;font-size:0.72rem;font-weight:600;margin-top:4px;'>{obj}</div>
            <div style='color:#c9a84c;font-family:Orbitron,sans-serif;font-size:0.8rem;margin-top:3px;'>{hd}</div>
            <div style='color:#94a3b8;font-size:0.62rem;margin-top:3px;line-height:1.3;'>{note}</div>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: EARTHQUAKE DASHBOARD
# ═══════════════════════════════════════════════════════════════