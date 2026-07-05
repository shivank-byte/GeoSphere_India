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

# ═══════════════════════════════════════════════════════════════
#  PAGE: GEOGRAPHY EXPLORER
# ═══════════════════════════════════════════════════════════════

st.markdown("<div class='section-heading'>FAULT vs FOLD — STRESS RESPONSE VISUALISER</div>", unsafe_allow_html=True)
import streamlit.components.v1 as _fvc
_fvc.html("""
<style>
body{background:#070b18;margin:0;padding:16px;font-family:Arial,sans-serif;color:#f0e6d0;}
.row{display:flex;gap:20px;justify-content:center;flex-wrap:wrap;}
.box{background:rgba(12,20,45,0.9);border:1px solid rgba(201,168,76,0.25);border-radius:12px;
     padding:16px;width:220px;text-align:center;}
.title{color:#c9a84c;font-size:11px;letter-spacing:2px;margin-bottom:10px;}
svg{width:200px;height:80px;}
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
""", height=280)

st.markdown("<div class='section-heading'>HIMALAYAN CROSS-SECTION — NAMED THRUST SYSTEM</div>", unsafe_allow_html=True)
import streamlit.components.v1 as _svc
_svc.html("""
<style>
body{background:#070b18;margin:0;padding:12px;font-family:Arial,sans-serif;}
svg{width:100%;height:260px;}
</style>
<svg viewBox='0 0 700 260'>
  <!-- Background -->
  <rect width='700' height='260' fill='#070b18'/>
  <!-- Tethyan Himalaya -->
  <path d='M0,180 L100,80 L200,100 L300,120 L400,140 L500,160 L600,180 L700,190' 
        stroke='#c9a84c' stroke-width='1.5' fill='rgba(201,168,76,0.08)' stroke-dasharray='5,3'/>
  <!-- MFT -->
  <path d='M500,220 L580,160 L700,150' stroke='#dc2626' stroke-width='2.5' fill='none'/>
  <text x='510' y='215' fill='#dc2626' font-size='10' font-weight='bold'>MFT</text>
  <!-- MBT -->
  <path d='M360,220 L440,140 L580,120' stroke='#f59e0b' stroke-width='2.5' fill='none'/>
  <text x='365' y='215' fill='#f59e0b' font-size='10' font-weight='bold'>MBT</text>
  <!-- MCT -->
  <path d='M180,220 L280,120 L440,80' stroke='#10b981' stroke-width='2.5' fill='none'/>
  <text x='185' y='215' fill='#10b981' font-size='10' font-weight='bold'>MCT</text>
  <!-- STDS -->
  <path d='M80,200 L160,120 L300,60' stroke='#6366f1' stroke-width='2' fill='none' stroke-dasharray='6,3'/>
  <text x='60' y='195' fill='#6366f1' font-size='9'>STDS</text>
  <!-- Terrain labels -->
  <text x='610' y='145' fill='#f0e6d0' font-size='9'>Indo-Gangetic Plain</text>
  <text x='440' y='130' fill='#f0e6d0' font-size='9'>Sub-Himalaya (Siwaliks)</text>
  <text x='270' y='105' fill='#f0e6d0' font-size='9'>Lesser Himalaya</text>
  <text x='120' y='80' fill='#f0e6d0' font-size='9'>Greater Himalaya</text>
  <text x='20' y='60' fill='#94a3b8' font-size='9'>Tethyan / Tibet</text>
  <!-- India plate arrow -->
  <path d='M650,240 L580,240' stroke='#c9a84c' stroke-width='1.5' marker-end='url(#arr)'/>
  <defs><marker id='arr' markerWidth='6' markerHeight='6' refX='3' refY='3' orient='auto'>
    <path d='M0,0 L6,3 L0,6 Z' fill='#c9a84c'/></marker></defs>
  <text x='585' y='255' fill='#c9a84c' font-size='9'>India Plate → 5cm/yr</text>
  <!-- Legend -->
  <rect x='10' y='220' width='180' height='35' rx='5' fill='rgba(12,20,45,0.8)' stroke='rgba(201,168,76,0.2)'/>
  <text x='16' y='232' fill='#c9a84c' font-size='8'>MFT=Main Frontal Thrust (active)</text>
  <text x='16' y='243' fill='#f59e0b' font-size='8'>MBT=Main Boundary Thrust</text>
  <text x='16' y='254' fill='#10b981' font-size='8'>MCT=Main Central Thrust  STDS=South Tibetan Detachment</text>
</svg>
""", height=280)
