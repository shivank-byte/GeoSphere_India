# GeoSphere India — Structural Tools
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

st.set_page_config(page_title="Structural Tools — GeoSphere India", page_icon="🧭", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Fault (geology)", "Structural Tools", "COMPASS · STRIKE/DIP VISUALIZER")

st.markdown("<div class='section-heading'>STRUCTURAL GEOLOGY TOOLS — COMPASS · STRIKE/DIP VISUALIZER</div>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown("<div class='section-heading'>COMPASS ROSE</div>", unsafe_allow_html=True)
    bearing = st.slider("Strike / Bearing (°)", 0, 359, 45, 1)
    dip_ang = st.slider("Dip Angle (°)", 0, 90, 30, 1)
    dip_dir_offset = 90  # dip direction is 90° from strike

    # Compass SVG
    r_outer = 120
    cx, cy  = 150, 150
    rad     = math.radians(bearing - 90)  # rotate for compass convention
    dip_rad = math.radians((bearing + dip_dir_offset) - 90)
    x2 = cx + r_outer * math.cos(rad)
    y2 = cy + r_outer * math.sin(rad)
    x3 = cx - r_outer * math.cos(rad)
    y3 = cy - r_outer * math.sin(rad)
    dip_x = cx + (r_outer * 0.6) * math.cos(dip_rad)
    dip_y = cy + (r_outer * 0.6) * math.sin(dip_rad)

    compass_svg = f"""
    <svg viewBox='0 0 300 300' width='100%'>
      <circle cx='{cx}' cy='{cy}' r='145' fill='rgba(8,18,38,0.9)' stroke='rgba(0,212,255,0.25)' stroke-width='2'/>
      <circle cx='{cx}' cy='{cy}' r='120' fill='none' stroke='rgba(0,212,255,0.12)' stroke-width='1'/>
      <circle cx='{cx}' cy='{cy}' r='80'  fill='none' stroke='rgba(0,212,255,0.08)' stroke-width='1'/>
      {''.join([f"<text x='{cx + 130*math.cos(math.radians(a-90)):.1f}' y='{cy + 130*math.sin(math.radians(a-90)):.1f}' fill='#94a3b8' font-size='11' text-anchor='middle' dominant-baseline='middle' font-family='Exo 2'>{a}</text>" for a in range(0,360,30)])}
      <text x='{cx}' y='12' fill='#00d4ff' font-size='16' text-anchor='middle' font-family='Orbitron' font-weight='700'>N</text>
      <text x='{cx}' y='296' fill='#94a3b8' font-size='14' text-anchor='middle' font-family='Orbitron'>S</text>
      <text x='12' y='{cy+5}' fill='#94a3b8' font-size='14' text-anchor='middle' font-family='Orbitron'>W</text>
      <text x='292' y='{cy+5}' fill='#94a3b8' font-size='14' text-anchor='middle' font-family='Orbitron'>E</text>
      <line x1='{x3:.1f}' y1='{y3:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='#00d4ff' stroke-width='3' stroke-linecap='round'/>
      <circle cx='{cx}' cy='{cy}' r='6' fill='#00d4ff'/>
      <line x1='{cx}' y1='{cy}' x2='{dip_x:.1f}' y2='{dip_y:.1f}' stroke='#f59e0b' stroke-width='2.5' stroke-dasharray='6,3'/>
      <circle cx='{dip_x:.1f}' cy='{dip_y:.1f}' r='5' fill='#f59e0b'/>
      <text x='155' y='268' fill='#00d4ff' font-size='10' font-family='Exo 2'>— Strike</text>
      <text x='155' y='282' fill='#f59e0b' font-size='10' font-family='Exo 2'>- - Dip direction</text>
    </svg>"""
    st.markdown(f"<div style='background:rgba(8,18,38,0.6);border:1px solid rgba(0,212,255,0.15);border-radius:12px;padding:10px;'>{compass_svg}</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='section-heading'>MEASUREMENT SUMMARY</div>", unsafe_allow_html=True)
    dip_direction = (bearing + 90) % 360
    notation = f"N{bearing:03d}°E / {dip_ang}°"
    st.markdown(f"""
    <div class='glass-card'>
        <div style='color:#00d4ff;font-family:Orbitron;font-size:0.8rem;margin-bottom:14px;'>FIELD MEASUREMENT</div>
        <div style='color:#94a3b8;font-size:0.82rem;line-height:2.4;'>
        🧭 <b style='color:#e2e8f0;'>Strike:</b> {bearing}° (from North)<br>
        📐 <b style='color:#e2e8f0;'>Dip Angle:</b> {dip_ang}°<br>
        ➡️ <b style='color:#e2e8f0;'>Dip Direction:</b> {dip_direction}°<br>
        📝 <b style='color:#e2e8f0;'>Notation:</b> {notation}<br>
        </div>
    </div>
    <div class='glass-card' style='margin-top:8px;'>
        <div style='color:#f59e0b;font-family:Orbitron;font-size:0.8rem;margin-bottom:12px;'>FOLD / FAULT REFERENCE</div>
        <div style='color:#94a3b8;font-size:0.78rem;line-height:2;'>
        • Anticline = upward arch (older rocks in core)<br>
        • Syncline = downward trough (younger rocks in core)<br>
        • Normal fault = hanging wall moves DOWN<br>
        • Reverse fault = hanging wall moves UP<br>
        • Thrust = low-angle reverse (< 30°)<br>
        • Strike-slip = lateral movement along fault
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-heading'>STEREOGRAPHIC PROJECTION (EQUAL AREA)</div>", unsafe_allow_html=True)
    theta  = math.radians(bearing)
    r_proj = math.sin(math.radians(dip_ang))
    px = 0.5 + 0.45 * r_proj * math.sin(theta)
    py = 0.5 - 0.45 * r_proj * math.cos(theta)

    fig_stereo = go.Figure()
    fig_stereo.add_shape(type="circle", xref="paper", yref="paper",
        x0=0.05, y0=0.05, x1=0.95, y1=0.95,
        line=dict(color="rgba(0,212,255,0.4)", width=2))
    fig_stereo.add_trace(go.Scatter(x=[px], y=[py], mode="markers",
        marker=dict(size=14, color="#00d4ff", symbol="x",
                    line=dict(width=3, color="#00d4ff")),
        hovertemplate=f"Strike: {bearing}°<br>Dip: {dip_ang}°<extra></extra>"))
    for label, lx, ly in [("N",0.5,0.98),("S",0.5,0.01),("E",0.99,0.5),("W",0.01,0.5)]:
        fig_stereo.add_annotation(x=lx, y=ly, text=label, showarrow=False,
            font=dict(color="#8a7d65", size=12, family="Orbitron"), xref="paper", yref="paper")
    fig_stereo.update_layout(height=220,
        paper_bgcolor="rgba(8,18,38,0.6)", plot_bgcolor="rgba(8,18,38,0)",
        xaxis=dict(visible=False, range=[0,1]), yaxis=dict(visible=False, range=[0,1]),
        margin=dict(l=5,r=5,t=5,b=5), font=dict(color="#f0e6d0"))
    st.plotly_chart(fig_stereo, use_container_width=True)


st.markdown("<div class='section-heading'>FAULT vs FOLD — STRESS RESPONSE VISUALISER</div>", unsafe_allow_html=True)
import streamlit.components.v1 as _fvc
_fvc.html("""
<style>
html,body{background:#070b18;margin:0;padding:0;font-family:Arial,sans-serif;color:#f0e6d0;}
.row{display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:16px;padding:16px;}
.box{background:rgba(12,20,45,0.9);border:1px solid rgba(201,168,76,0.25);border-radius:12px;
     padding:16px;text-align:center;}
.title{color:#c9a84c;font-size:11px;letter-spacing:1.5px;margin-bottom:10px;line-height:1.4;}
svg{width:100%;max-width:200px;height:80px;}
.desc{color:#94a3b8;font-size:11px;line-height:1.5;margin-top:8px;}
</style>
<div class='row'>
<div class='box'>
  <div class='title'>COMPRESSIONAL STRESS → FOLD</div>
  <svg viewBox='0 0 200 80'>
    <path d='M10,50 Q50,10 100,50 Q150,90 190,50' stroke='#c9a84c' stroke-width='3' fill='none'/>
    <path d='M10,60 Q50,20 100,60 Q150,100 190,60' stroke='#f59e0b' stroke-width='2' fill='none'/>
    <path d='M10,40 Q50,0 100,40 Q150,80 190,40' stroke='#e8c96a' stroke-width='2' fill='none'/>
    <text x='20' y='75' font-size='9' fill='#475569'>anticline →</text>
    <text x='110' y='75' font-size='9' fill='#475569'>← syncline</text>
  </svg>
  <div class='desc'>Rock bends plastically under compression (deep crust, high T). Forms anticlines (arch up) and synclines (bowl down).</div>
</div>
<div class='box'>
  <div class='title'>COMPRESSIONAL STRESS → THRUST FAULT</div>
  <svg viewBox='0 0 200 80'>
    <line x1='10' y1='60' x2='90' y2='60' stroke='#94a3b8' stroke-width='2'/>
    <line x1='110' y1='40' x2='190' y2='40' stroke='#94a3b8' stroke-width='2'/>
    <path d='M90,60 L110,40' stroke='#dc2626' stroke-width='3'/>
    <polygon points='95,48 110,40 100,55' fill='#dc2626'/>
    <text x='10' y='75' font-size='9' fill='#475569'>footwall</text>
    <text x='110' y='35' font-size='9' fill='#f0e6d0'>hanging wall (up)</text>
  </svg>
  <div class='desc'>Rock fractures brittlely (shallow crust, low T). Thrust = hanging wall moves UP. MFT, MBT, MCT in Himalayas are all thrust faults.</div>
</div>
<div class='box'>
  <div class='title'>EXTENSIONAL STRESS → NORMAL FAULT</div>
  <svg viewBox='0 0 200 80'>
    <line x1='10' y1='40' x2='90' y2='40' stroke='#94a3b8' stroke-width='2'/>
    <line x1='110' y1='60' x2='190' y2='60' stroke='#94a3b8' stroke-width='2'/>
    <path d='M90,40 L110,60' stroke='#0ea5e9' stroke-width='3'/>
    <polygon points='95,52 110,60 100,45' fill='#0ea5e9'/>
    <text x='10' y='35' font-size='9' fill='#f0e6d0'>hanging wall (down)</text>
    <text x='110' y='75' font-size='9' fill='#475569'>footwall</text>
  </svg>
  <div class='desc'>Hanging wall moves DOWN under extension (rifting). Creates grabens like the Narmada rift valley.</div>
</div>
</div>
""", height=340, scrolling=True)

st.markdown("<div class='section-heading'>HIMALAYAN CROSS-SECTION — NAMED THRUST SYSTEM</div>", unsafe_allow_html=True)
st.markdown("""
<div class='glass-card' style='padding:12px 16px;margin-bottom:10px;'>
    <span style='color:#94a3b8;font-size:0.8rem;line-height:1.6;'>
    <b style='color:#c9a84c;'>What to take away:</b> all three thrusts (MCT, MBT, MFT) are the same fault —
    the <b>Main Himalayan Thrust (MHT)</b> — splaying up to the surface at different points. Rock above each
    thrust was pushed <b>up and over</b> younger rock in front of it. Moving south to north you cross them in
    age order: <b>MFT</b> (youngest, active today) → <b>MBT</b> → <b>MCT</b> (oldest, deepest-rooted). The
    <b>STDS</b> is different — it's an extensional detachment riding on <i>top</i> of the stack, unrelated in
    sense of motion to the thrusts below it.
    </span>
</div>""", unsafe_allow_html=True)
import streamlit.components.v1 as _svc
_svc.html("""
<style>
html,body{background:#070b18;margin:0;padding:0;font-family:Arial,sans-serif;}
svg{width:100%;height:auto;display:block;}
</style>
<svg viewBox='0 0 700 380' preserveAspectRatio='xMidYMid meet'>
  <rect width='700' height='380' fill='#070b18'/>

  <!-- Terrain zone divider ticks + labels (south=right, north=left) -->
  <line x1='560' y1='40' x2='560' y2='300' stroke='rgba(255,255,255,0.08)' stroke-width='1'/>
  <line x1='400' y1='40' x2='400' y2='300' stroke='rgba(255,255,255,0.08)' stroke-width='1'/>
  <line x1='230' y1='40' x2='230' y2='300' stroke='rgba(255,255,255,0.08)' stroke-width='1'/>
  <text x='605' y='55' fill='#94a3b8' font-size='13'>Indo-Gangetic</text>
  <text x='605' y='70' fill='#94a3b8' font-size='13'>Plain</text>
  <text x='420' y='55' fill='#94a3b8' font-size='13'>Sub-Himalaya</text>
  <text x='420' y='70' fill='#94a3b8' font-size='13'>(Siwaliks)</text>
  <text x='260' y='55' fill='#94a3b8' font-size='13'>Lesser</text>
  <text x='260' y='70' fill='#94a3b8' font-size='13'>Himalaya</text>
  <text x='70' y='55' fill='#f0e6d0' font-size='13' font-weight='bold'>Greater</text>
  <text x='70' y='70' fill='#f0e6d0' font-size='13' font-weight='bold'>Himalaya</text>
  <text x='10' y='95' fill='#6366f1' font-size='12'>Tibetan Plateau →</text>

  <!-- Topography skyline (south flat plain rising to north high peaks) -->
  <path d='M700,260 L560,255 L500,220 L400,190 L340,140 L230,100 L150,85 L60,90 L0,95'
        stroke='#c9a84c' stroke-width='2.5' fill='none'/>

  <!-- Main Himalayan Thrust (MHT) — the single basal detachment all thrusts sole into -->
  <path d='M700,330 Q450,345 230,300 Q100,270 20,220'
        stroke='#94a3b8' stroke-width='2' fill='none' stroke-dasharray='2,4'/>
  <text x='430' y='362' fill='#94a3b8' font-size='12'>Main Himalayan Thrust (MHT) — all three thrusts below sole into this one basal fault</text>

  <!-- MFT — youngest, southernmost, shallowest ramp -->
  <path d='M560,330 Q580,290 620,260 L660,255' stroke='#dc2626' stroke-width='4' fill='none'/>
  <text x='600' y='300' fill='#dc2626' font-size='15' font-weight='bold'>MFT</text>

  <!-- MBT — middle -->
  <path d='M400,330 Q430,260 470,215 L520,205' stroke='#f59e0b' stroke-width='4' fill='none'/>
  <text x='420' y='250' fill='#f59e0b' font-size='15' font-weight='bold'>MBT</text>

  <!-- MCT — oldest, northernmost, steepest, deepest exhumation -->
  <path d='M230,300 Q260,190 300,130 L340,110' stroke='#10b981' stroke-width='4' fill='none'/>
  <text x='250' y='170' fill='#10b981' font-size='15' font-weight='bold'>MCT</text>

  <!-- STDS — extensional detachment at the top of the high Himalaya, opposite sense -->
  <path d='M60,95 Q120,80 200,72' stroke='#6366f1' stroke-width='3' fill='none' stroke-dasharray='7,4'/>
  <text x='90' y='60' fill='#6366f1' font-size='14' font-weight='bold'>STDS</text>

  <!-- India plate motion arrow -->
  <path d='M695,355 L610,355' stroke='#c9a84c' stroke-width='2' marker-end='url(#arr)'/>
  <defs><marker id='arr' markerWidth='7' markerHeight='7' refX='3.5' refY='3.5' orient='auto'>
    <path d='M0,0 L7,3.5 L0,7 Z' fill='#c9a84c'/></marker></defs>
  <text x='615' y='372' fill='#c9a84c' font-size='12'>Indian Plate underthrusting → ~5 cm/yr</text>

  <!-- Legend -->
  <rect x='8' y='240' width='210' height='92' rx='6' fill='rgba(7,11,24,0.92)' stroke='rgba(201,168,76,0.25)'/>
  <text x='16' y='258' fill='#dc2626' font-size='12' font-weight='bold'>MFT</text>
  <text x='55' y='258' fill='#cbd5e1' font-size='11'>Main Frontal Thrust (active)</text>
  <text x='16' y='276' fill='#f59e0b' font-size='12' font-weight='bold'>MBT</text>
  <text x='55' y='276' fill='#cbd5e1' font-size='11'>Main Boundary Thrust</text>
  <text x='16' y='294' fill='#10b981' font-size='12' font-weight='bold'>MCT</text>
  <text x='55' y='294' fill='#cbd5e1' font-size='11'>Main Central Thrust</text>
  <text x='16' y='312' fill='#6366f1' font-size='12' font-weight='bold'>STDS</text>
  <text x='55' y='312' fill='#cbd5e1' font-size='11'>S. Tibetan Detachment (extensional)</text>
  <text x='16' y='328' fill='#94a3b8' font-size='11'>— — MHT: basal thrust all others join</text>
</svg>
""", height=400)
