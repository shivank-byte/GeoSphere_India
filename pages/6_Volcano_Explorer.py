# GeoSphere India — Volcano Explorer
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

st.set_page_config(page_title="Volcano Explorer — GeoSphere India", page_icon="🌋", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Volcano", "Volcano Explorer", "BARREN ISLAND · NARCONDAM · GLOBAL")

st.markdown("<div class='section-heading'>VOLCANO EXPLORER — BARREN ISLAND · NARCONDAM · GLOBAL</div>", unsafe_allow_html=True)

# ── Lava animation ──────────────────────────────────────────────────────────
import streamlit.components.v1 as _vc
_vc.html("""
<!DOCTYPE html>
<html>
<head>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#070b18; display:flex; align-items:center; justify-content:center; height:220px; overflow:hidden; }
.scene { position:relative; width:320px; height:200px; }
/* Volcano mountain shape */
.volcano-body {
position:absolute; bottom:0; left:50%; transform:translateX(-50%);
width:0; height:0;
border-left:110px solid transparent;
border-right:110px solid transparent;
border-bottom:160px solid #2d1a0a;
filter:drop-shadow(0 0 20px rgba(220,38,38,0.4));
}
.volcano-inner {
position:absolute; bottom:0; left:50%; transform:translateX(-50%);
width:0; height:0;
border-left:70px solid transparent;
border-right:70px solid transparent;
border-bottom:140px solid #1a0f05;
}
/* Crater glow */
.crater {
position:absolute; bottom:155px; left:50%; transform:translateX(-50%);
width:44px; height:14px;
background:radial-gradient(ellipse,#ff6600,#dc2626,#7f1d1d);
border-radius:50%;
box-shadow: 0 0 20px 8px rgba(255,100,0,0.6), 0 0 40px 15px rgba(220,38,38,0.4);
animation: crater-pulse 1.8s ease-in-out infinite;
}
@keyframes crater-pulse {
0%,100% { box-shadow: 0 0 20px 8px rgba(255,100,0,0.6), 0 0 40px 15px rgba(220,38,38,0.4); }
50%      { box-shadow: 0 0 30px 14px rgba(255,140,0,0.8), 0 0 60px 25px rgba(220,38,38,0.6); }
}
/* Lava flows down the sides */
.lava-flow {
position:absolute; bottom:0; width:14px;
background:linear-gradient(to bottom, #ff6600, #dc2626, #7f1d1d, transparent);
border-radius:0 0 6px 6px;
transform-origin:top center;
animation: flow-down 2.5s ease-in infinite;
opacity:0;
}
.lava-flow.l1 { left:calc(50% - 38px); bottom:60px; height:80px; animation-delay:0s; }
.lava-flow.l2 { left:calc(50% + 20px); bottom:55px; height:75px; animation-delay:0.7s; }
.lava-flow.l3 { left:calc(50% - 12px); bottom:65px; height:90px; animation-delay:1.3s; }
.lava-flow.l4 { left:calc(50% - 54px); bottom:40px; height:65px; animation-delay:1.8s; }
.lava-flow.l5 { left:calc(50% + 36px); bottom:38px; height:60px; animation-delay:0.4s; }

@keyframes flow-down {
0%  { opacity:0; transform:scaleY(0); }
15% { opacity:0.9; transform:scaleY(0.3); }
60% { opacity:0.7; transform:scaleY(1); }
100%{ opacity:0; transform:scaleY(1) translateY(20px); }
}
/* Lava blobs erupting upward */
.blob {
position:absolute; border-radius:50%;
background:radial-gradient(circle,#ffaa00,#ff4400);
animation: erupt 2s ease-out infinite;
opacity:0;
}
.blob.b1 { width:8px;  height:8px;  left:calc(50% - 4px);  bottom:162px; animation-delay:0s;   }
.blob.b2 { width:6px;  height:6px;  left:calc(50% + 8px);  bottom:162px; animation-delay:0.5s; }
.blob.b3 { width:10px; height:10px; left:calc(50% - 10px); bottom:162px; animation-delay:1.0s; }
.blob.b4 { width:5px;  height:5px;  left:calc(50% + 4px);  bottom:162px; animation-delay:1.5s; }
.blob.b5 { width:7px;  height:7px;  left:calc(50% - 6px);  bottom:162px; animation-delay:0.3s; }

@keyframes erupt {
0%   { opacity:0;   transform:translate(0,0) scale(1); }
10%  { opacity:1; }
60%  { opacity:0.6; transform:translate(var(--tx,5px), var(--ty,-55px)) scale(0.5); }
100% { opacity:0;   transform:translate(var(--tx,8px), var(--ty,-80px)) scale(0); }
}
.b1 { --tx:-8px;  --ty:-70px; }
.b2 { --tx:14px;  --ty:-55px; }
.b3 { --tx:-14px; --ty:-65px; }
.b4 { --tx:18px;  --ty:-75px; }
.b5 { --tx:6px;   --ty:-85px; }

/* Smoke clouds */
.smoke {
position:absolute; border-radius:50%;
background:rgba(120,80,40,0.35);
animation: rise-smoke 3s ease-out infinite;
opacity:0;
}
.smoke.s1 { width:30px; height:30px; left:calc(50% - 15px); bottom:170px; animation-delay:0s; }
.smoke.s2 { width:22px; height:22px; left:calc(50% + 5px);  bottom:170px; animation-delay:1s; }
.smoke.s3 { width:26px; height:26px; left:calc(50% - 22px); bottom:170px; animation-delay:2s; }

@keyframes rise-smoke {
0%   { opacity:0;   transform:translate(0,0) scale(0.3); }
20%  { opacity:0.6; transform:translate(0,-15px) scale(0.7); }
100% { opacity:0;   transform:translate(10px,-70px) scale(1.8); }
}
/* Glow halo at base */
.base-glow {
position:absolute; bottom:0; left:50%; transform:translateX(-50%);
width:220px; height:30px;
background:radial-gradient(ellipse,rgba(255,80,0,0.3),transparent 70%);
animation:base-flicker 1.2s ease-in-out infinite alternate;
}
@keyframes base-flicker { from{opacity:0.5} to{opacity:1} }
/* Label */
.label {
position:absolute; bottom:6px; left:50%; transform:translateX(-50%);
color:#c9a84c; font-family:'Orbitron',monospace; font-size:9px;
letter-spacing:2px; white-space:nowrap; opacity:0.7;
text-shadow:0 0 8px rgba(201,168,76,0.5);
}
</style>
</head>
<body>
<div class='scene'>
  <div class='volcano-body'></div>
  <div class='volcano-inner'></div>
  <div class='base-glow'></div>
  <div class='lava-flow l1'></div>
  <div class='lava-flow l2'></div>
  <div class='lava-flow l3'></div>
  <div class='lava-flow l4'></div>
  <div class='lava-flow l5'></div>
  <div class='smoke s1'></div>
  <div class='smoke s2'></div>
  <div class='smoke s3'></div>
  <div class='crater'></div>
  <div class='blob b1'></div>
  <div class='blob b2'></div>
  <div class='blob b3'></div>
  <div class='blob b4'></div>
  <div class='blob b5'></div>
  <div class='label'>BARREN ISLAND — INDIA'S ACTIVE VOLCANO</div>
</div>
</body>
</html>
""", height=220, scrolling=False)

fig_v = go.Figure()
for v in VOLCANOES:
    color = "#dc2626" if v["status"] == "Active" else "#f59e0b"
    size  = 17 if v["country"] == "India" else 12
    fig_v.add_trace(go.Scattergeo(
        lat=[v["lat"]], lon=[v["lon"]],
        mode="markers+text", text=[v["name"]],
        textposition="top center",
        marker=dict(size=size, color=color, symbol="triangle-up",
                    line=dict(width=2, color="rgba(255,255,255,0.6)")),
        textfont=dict(color="#ffffff", size=12 if v["country"]=="India" else 10, family="Arial Black"),
        name=v["name"],
        hovertemplate=f"<b>{v['name']}</b><br>Country: {v['country']}<br>Status: {v['status']}<br>Type: {v['type']}<br>Last eruption: {v['last_eruption']}<extra></extra>",
    ))

fig_v.update_geos(showland=True, landcolor="#0f1e0f", showocean=True, oceancolor="#020817",
    showcountries=True, countrycolor="rgba(255,255,255,0.1)",
    showcoastlines=True, coastlinecolor="rgba(0,212,255,0.3)",
    bgcolor="rgba(0,0,0,0)", showframe=False)
fig_v.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
st.plotly_chart(fig_v, use_container_width=True)

st.markdown("<div class='section-heading'>VOLCANO PROFILES</div>", unsafe_allow_html=True)
v_cols = st.columns(2)
for i, v in enumerate(VOLCANOES):
    with v_cols[i % 2]:
        status_color = "#dc2626" if v["status"] == "Active" else "#f59e0b"
        india_badge = "🇮🇳" if v["country"] == "India" else "🌍"
        show_wiki_photo(v.get("wiki_photo", v["name"]), caption=v["name"])
        st.markdown(f"""
        <div class='mineral-card' style='border-color:{status_color}33;'>
            <div style='display:flex;justify-content:space-between;align-items:start;'>
                <div style='color:{status_color};font-family:Orbitron;font-size:0.82rem;'>
                🌋 {v["name"]} {india_badge}
                </div>
                <span style='font-size:0.65rem;background:{status_color}22;padding:2px 8px;
                border-radius:10px;color:{status_color};'>{v["status"]}</span>
            </div>
            <div style='color:#94a3b8;font-size:0.75rem;line-height:1.8;margin-top:8px;'>
            🏔️ Type: {v["type"]}<br>
            🌏 Location: {v["country"]}<br>
            🔥 Last Eruption: {v["last_eruption"]}<br>
            📋 {v["desc"]}
            </div>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: GEOLOGICAL TIME SCALE
# ═══════════════════════════════════════════════════════════════

st.markdown("<div class='section-heading'>VEI — VOLCANIC EXPLOSIVITY INDEX</div>", unsafe_allow_html=True)
_vei = [
    (0,"Hawaiian","Barren Island","#ef4444","Continuous gentle effusion. Lava flows, no explosion."),
    (1,"Hawaiian/Strombolian","Stromboli","#f97316","Gentle. Small ash clouds. Very frequent."),
    (2,"Strombolian","Sakurajima","#f59e0b","Explosive bursts. Ash to 1 km. Eruptions every few weeks."),
    (3,"Vulcanian","Soufrière Hills","#eab308","Moderate. Ash to 3-15 km. Once per year globally."),
    (4,"Sub-Plinian","Eyjafjallajökull 2010","#84cc16","Large eruption. 10-25 km ash column. Disrupts air travel."),
    (5,"Plinian","Mt. St. Helens 1980","#10b981","Very large. 25 km column. Once per 10 years."),
    (6,"Ultra-Plinian","Pinatubo 1991","#0ea5e9","Massive. Cooled global climate 0.5°C. Once per century."),
    (7,"Ultra-Plinian","Tambora 1815","#6366f1","Catastrophic. Year Without Summer. Once per 1,000 yrs."),
    (8,"Mega-colossal","Yellowstone (prehistoric)","#8b5cf6","Supervolcano. Civilisation-scale event. Once per 10,000+ yrs."),
]
_vei_cols = st.columns([1,3,2,3])
_vei_cols[0].markdown("<div style='color:#c9a84c;font-size:0.72rem;font-weight:600;'>VEI</div>", unsafe_allow_html=True)
_vei_cols[1].markdown("<div style='color:#c9a84c;font-size:0.72rem;font-weight:600;'>Type</div>", unsafe_allow_html=True)
_vei_cols[2].markdown("<div style='color:#c9a84c;font-size:0.72rem;font-weight:600;'>Example</div>", unsafe_allow_html=True)
_vei_cols[3].markdown("<div style='color:#c9a84c;font-size:0.72rem;font-weight:600;'>Description</div>", unsafe_allow_html=True)
for vei, vtype, example, col, desc in _vei:
    c1,c2,c3,c4 = st.columns([1,3,2,3])
    c1.markdown(f"<div style='color:{col};font-family:Orbitron;font-size:0.9rem;font-weight:700;padding:4px 0;'>{vei}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='color:#e2e8f0;font-size:0.78rem;padding:4px 0;'>{vtype}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='color:#94a3b8;font-size:0.75rem;padding:4px 0;'>{example}</div>", unsafe_allow_html=True)
    c4.markdown(f"<div style='color:#94a3b8;font-size:0.75rem;padding:4px 0;'>{desc}</div>", unsafe_allow_html=True)

st.markdown("<div class='section-heading'>BARREN ISLAND — INDIA'S ONLY ACTIVE VOLCANO</div>", unsafe_allow_html=True)
show_wiki_photo("Barren Island volcano", caption="Barren Island — India's only active volcano")
st.markdown("""
<div class='glass-card'>
    <div style='display:grid;grid-template-columns:1fr 1fr;gap:14px;'>
        <div style='color:#94a3b8;font-size:0.8rem;line-height:2;'>
            📍 <b style='color:#e2e8f0;'>Location:</b> Andaman Sea, 135 km NE of Port Blair<br>
            🌋 <b style='color:#e2e8f0;'>Type:</b> Stratovolcano (composite cone)<br>
            📏 <b style='color:#e2e8f0;'>Height:</b> 354 m above sea level<br>
            ⚗️ <b style='color:#e2e8f0;'>Magma type:</b> Basaltic-andesitic (subduction zone)<br>
            🧭 <b style='color:#e2e8f0;'>Setting:</b> Andaman-Sumatra subduction arc<br>
            🏝️ <b style='color:#e2e8f0;'>Access:</b> Day trips from Port Blair with permit
        </div>
        <div style='color:#94a3b8;font-size:0.8rem;line-height:2;'>
            📅 <b style='color:#e2e8f0;'>Eruption History:</b><br>
            1787 — First recorded eruption<br>
            1991 — Major eruption after 200-year dormancy<br>
            1994–95 — Continued activity<br>
            2005 — Activity after 2004 tsunami (M9.1)<br>
            2008–09 — Extended eruption period<br>
            2017 — Most recent confirmed activity<br>
        </div>
    </div>
    <div style='color:#94a3b8;font-size:0.78rem;margin-top:10px;border-top:1px solid rgba(255,255,255,0.07);padding-top:8px;line-height:1.7;'>
        <b style='color:#dc2626;'>Geological significance:</b> Barren Island sits on the Andaman arc, 
        formed by subduction of the Indian Plate beneath the Burma Plate. It is the only confirmed 
        active volcano in India and the broader South Asian region. The 2004 M9.1 earthquake 
        (same subduction zone) may have reactivated its magmatic system.
    </div>
</div>""", unsafe_allow_html=True)
