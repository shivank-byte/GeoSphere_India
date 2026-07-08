# GeoSphere India — Earthquake Dashboard
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

st.set_page_config(page_title="Earthquake Dashboard — GeoSphere India", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Earthquake", "Earthquake Dashboard", "INDIA SEISMIC HISTORY + LIVE USGS")

st.markdown("<div class='section-heading'>EARTHQUAKE DASHBOARD — INDIA SEISMIC HISTORY + LIVE USGS</div>", unsafe_allow_html=True)

# Try live USGS data — rolling 180-day window (cached 2 min), never goes stale
live_data = fetch_usgs_recent_earthquakes(days_back=180, min_magnitude=5.0, limit=20)

if live_data:
    features = live_data["features"]
    eq_list = []
    for f in features:
        p = f["properties"]
        g = f["geometry"]["coordinates"]
        eq_list.append({"Place":p.get("place","Unknown"),"Magnitude":p.get("mag",0),
                         "Depth (km)":round(g[2],1),"Lon":g[0],"Lat":g[1],
                         "Time":pd.to_datetime(p.get("time",0), unit="ms").strftime("%Y-%m-%d %H:%M")})
    eq_df = pd.DataFrame(eq_list)
    st.markdown("""<div class='glass-card' style='padding:10px 14px;margin-bottom:10px;'>
        <span style='color:#10b981;font-size:0.75rem;'>🟢 LIVE — USGS data (M5.0+ globally, last 180 days)</span>
    </div>""", unsafe_allow_html=True)

    fig_live = go.Figure(go.Scattergeo(
        lat=eq_df["Lat"], lon=eq_df["Lon"],
        text=eq_df["Place"],
        mode="markers",
        marker=dict(size=eq_df["Magnitude"] * 3, color=eq_df["Magnitude"],
                    colorscale=[[0,"#10b981"],[0.5,"#f59e0b"],[1,"#dc2626"]],
                    showscale=True, colorbar=dict(title="Magnitude", tickfont=dict(color="#8a7d65")),
                    line=dict(width=1, color="rgba(255,255,255,0.3)"), opacity=0.85),
        hovertemplate="<b>%{text}</b><br>Mag: %{marker.color:.1f}<extra></extra>",
    ))
    fig_live.update_geos(showland=True, landcolor="#0f1e0f", showocean=True, oceancolor="#020817",
        showcountries=True, countrycolor="rgba(255,255,255,0.1)",
        bgcolor="rgba(0,0,0,0)", showframe=False)
    fig_live.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
    st.plotly_chart(fig_live, use_container_width=True)
    import urllib.parse as _urlp
    eq_df["News"] = eq_df["Place"].apply(
        lambda p: f"https://news.google.com/search?q={_urlp.quote(str(p) + ' earthquake')}")
    st.dataframe(
        eq_df[["Place","Magnitude","Depth (km)","Time","News"]].head(10),
        use_container_width=True, hide_index=True,
        column_config={
            "News": st.column_config.LinkColumn("News", display_text="🔗 Read coverage"),
        })
else:
    st.info("Live USGS data unavailable (no internet connection). Showing historic Indian earthquake database.")

# Historical India earthquakes
st.markdown("<div class='section-heading'>HISTORIC INDIAN EARTHQUAKES</div>", unsafe_allow_html=True)
eq_df2 = pd.DataFrame(INDIA_EARTHQUAKES)
fig_h = go.Figure()
fig_h.add_trace(go.Scattergeo(
    lat=eq_df2["lat"], lon=eq_df2["lon"],
    text=eq_df2["name"],
    mode="markers+text", textposition="top center",
    marker=dict(size=eq_df2["mag"] * 3.5, color=eq_df2["mag"],
                colorscale=[[0,"#f59e0b"],[0.5,"#f87171"],[1,"#dc2626"]],
                showscale=True, colorbar=dict(title="Magnitude", tickfont=dict(color="#8a7d65")),
                line=dict(width=1.5, color="rgba(255,255,255,0.4)"), opacity=0.9),
    textfont=dict(color="#f0e6d0", size=9),
    hovertemplate="<b>%{text}</b><br>Mag: %{marker.color:.1f}<br>%{lon:.1f}°E, %{lat:.1f}°N<extra></extra>",
))
fig_h.update_geos(scope="asia", lonaxis_range=[60, 100], lataxis_range=[5, 38],
    showland=True, landcolor="#0f1e0f", showocean=True, oceancolor="#020817",
    showcountries=True, countrycolor="rgba(255,255,255,0.15)",
    showcoastlines=True, coastlinecolor="rgba(0,212,255,0.4)",
    bgcolor="rgba(0,0,0,0)", showframe=False)
fig_h.update_layout(height=440, paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
st.plotly_chart(fig_h, use_container_width=True)

# Magnitude timeline
fig_tl = go.Figure(go.Bar(x=eq_df2["year"], y=eq_df2["mag"],
    text=eq_df2["name"], textposition="outside", textfont=dict(size=8, color="#f0e6d0"),
    marker_color=eq_df2["mag"],
    marker=dict(colorscale=[[0,"#f59e0b"],[1,"#dc2626"]], showscale=False)))
fig_tl.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8a7d65", family="Source Sans 3"), height=280, margin=dict(l=5,r=5,t=5,b=5),
    xaxis=dict(title="Year", color="#8a7d65"),
    yaxis=dict(title="Magnitude", gridcolor="rgba(255,255,255,0.05)", range=[0,10]))
st.plotly_chart(fig_tl, use_container_width=True)

st.markdown("<div class='section-heading'>READ MORE ABOUT EACH HISTORIC EARTHQUAKE</div>", unsafe_allow_html=True)
import urllib.parse as _urlp2
EQ_WIKI_TITLE = {
    "Bhuj, Gujarat": "2001 Gujarat earthquake",
    "Koyna, Maharashtra": "1967 Koynanagar earthquake",
    "Latur, Maharashtra": "1993 Latur earthquake",
    "Uttarkashi, Uttarakhand": "1991 Uttarkashi earthquake",
    "Chamoli, Uttarakhand": "1999 Chamoli earthquake",
    "Andaman Islands": "2004 Indian Ocean earthquake and tsunami",
    "Kashmir": "2005 Kashmir earthquake",
    "Sikkim": "2011 Sikkim earthquake",
    "Nepal–India Border": "April 2015 Nepal earthquake",
    "Delhi NCR": "1956 Bulandshahr earthquake",
}
_hist_cols = st.columns(2)
for i, eq in enumerate(sorted(INDIA_EARTHQUAKES, key=lambda e: -e["year"])):
    with _hist_cols[i % 2]:
        news_url = f"https://news.google.com/search?q={_urlp2.quote(eq['name'] + ' earthquake ' + str(eq['year']))}"
        show_wiki_photo(EQ_WIKI_TITLE.get(eq["name"], eq["name"]), caption=f"{eq['name']} ({eq['year']})")
        st.markdown(f"""
        <div class='glass-card' style='padding:10px 14px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;'>
            <div>
                <span style='color:#e2e8f0;font-size:0.8rem;font-weight:600;'>{eq['name']}</span>
                <span style='color:#94a3b8;font-size:0.72rem;'> · {eq['year']} · M{eq['mag']}</span>
            </div>
            <a href='{news_url}' target='_blank' style='color:#00d4ff;font-size:0.72rem;text-decoration:none;white-space:nowrap;margin-left:8px;'>🔗 News</a>
        </div>""", unsafe_allow_html=True)

st.markdown("<div class='section-heading'>MAGNITUDE → IMPACT SCALE</div>", unsafe_allow_html=True)
_mag_rows = [
    ("M2–3","Rarely felt","#10b981","Detected only by seismographs. ~1 million/year globally."),
    ("M4",  "Felt by many","#84cc16","Windows rattle. No structural damage. ~13,000/year."),
    ("M5",  "Minor damage","#fbbf24","Poorly built structures damaged. ~1,300/year."),
    ("M6",  "Significant", "#f59e0b","Strong shaking. Buildings damaged. ~130/year."),
    ("M7",  "Major",       "#ef4444","Widespread damage. Hundreds to thousands of deaths. ~13/year."),
    ("M8",  "Great",       "#dc2626","Catastrophic. Tens of thousands of deaths. ~1/year."),
    ("M9+", "Extreme",     "#7f1d1d","Country-scale devastation + tsunamis. Once per decade. 2004 Indian Ocean = M9.1"),
]
for mag, label, col, desc in _mag_rows:
    st.markdown(f"""
    <div class='glass-card' style='padding:10px 14px;margin-bottom:6px;border-left:4px solid {col};'>
        <div style='display:flex;justify-content:space-between;'>
            <span style='color:{col};font-family:Orbitron;font-size:0.88rem;font-weight:700;'>{mag}</span>
            <span style='background:{col}22;color:{col};font-size:0.7rem;padding:2px 10px;border-radius:10px;'>{label}</span>
        </div>
        <div style='color:#94a3b8;font-size:0.75rem;margin-top:3px;'>{desc}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div class='section-heading'>GEOLOGIST'S POV — WHAT TO LOOK FOR AFTER AN EARTHQUAKE</div>", unsafe_allow_html=True)
_pov = [
    ("🔍","Surface Rupture","Fault scarp","Fresh scarps, offset roads/fences, ground cracks along fault trace — reveal which fault moved and by how much."),
    ("💧","Liquefaction","Soil liquefaction","Sandy saturated soils behave like liquid — sand boils, foundation failures, lateral spreading near riverbanks."),
    ("🏔️","Landslides","Landslide","Himalayan earthquakes routinely trigger thousands of slides — can dam rivers creating hazardous GLOF lakes."),
    ("🌊","Tsunami Potential","Tsunami","Any M7.5+ submarine quake near Andaman or Makran subduction zone requires immediate coastal hazard assessment."),
    ("📊","Aftershock Pattern","Seismogram","Spatial distribution maps the fault plane — reveals orientation, dimensions, which segments remain stressed."),
    ("🏠","Building Damage","Earthquake engineering","Failure patterns reveal local site amplification — soft soils amplify shaking vs bedrock. Critical for planning."),
]
_pc = st.columns(2)
for i,(em,title,img_topic,desc) in enumerate(_pov):
    with _pc[i%2]:
        show_wiki_photo(img_topic, caption=title)
        st.markdown(f"""
        <div class='glass-card' style='padding:11px;'>
            <div style='display:flex;align-items:center;gap:8px;margin-bottom:5px;'>
                <span style='font-size:1.2rem;'>{em}</span>
                <span style='color:#00d4ff;font-size:0.8rem;font-weight:600;'>{title}</span>
            </div>
            <div style='color:#94a3b8;font-size:0.74rem;line-height:1.55;'>{desc}</div>
        </div>""", unsafe_allow_html=True)
