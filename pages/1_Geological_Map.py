# GeoSphere India — Geological Map
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

st.set_page_config(page_title="Geological Map — GeoSphere India", page_icon="🗺️", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Geology of India", "Geological Map", "PROVINCES, CRATONS & MINERAL BELTS")

st.markdown("<div class='section-heading'>INTERACTIVE GEOLOGICAL MAP OF INDIA</div>", unsafe_allow_html=True)

gmap_tab1, gmap_tab2, gmap_tab3 = st.tabs(["🗺️ Geological Provinces", "💎 GSI Mineral Deposits", "🏞️ Famous Sites"])

with gmap_tab1:
    st.markdown("""
    <div class='glass-card' style='padding:10px 16px;margin-bottom:10px;'>
        <span style='color:#94a3b8;font-size:0.78rem;'>
        🗺️ Hover markers for quick info · Select province below for full detail
        </span>
    </div>""", unsafe_allow_html=True)

    map_view = st.radio("Map style", ["🗺️ Geological Overview", "🛰️ Satellite"], horizontal=True, key="gmap_view_toggle")

    if map_view == "🛰️ Satellite" and FOLIUM_AVAILABLE:
        m_prov = make_folium_map(center_lat=22, center_lon=82, zoom=5)
        for p in INDIA_GEO_PROVINCES:
            folium.CircleMarker(
                location=[p["lat"], p["lon"]], radius=9, color=p["color"], fill=True,
                fill_color=p["color"], fill_opacity=0.85, weight=2,
                tooltip=f"<b>{p['name']}</b><br>{p['age']}",
                popup=folium.Popup(f"<b style='color:{p['color']};'>{p['name']}</b><br>"
                                    f"<b>Age:</b> {p['age']}<br><b>Tectonic:</b> {p['tectonic']}", max_width=240)
            ).add_to(m_prov)
        render_folium(m_prov, height=520)
        st.caption("🛰️ Use the layer switcher (top-right of the map) to toggle Satellite / Terrain / Street tiles.")
    else:
        if map_view == "🛰️ Satellite" and not FOLIUM_AVAILABLE:
            st.info("Satellite view needs `folium` — showing the geological overview instead.")
        lats   = [p["lat"]   for p in INDIA_GEO_PROVINCES]
        lons   = [p["lon"]   for p in INDIA_GEO_PROVINCES]
        names  = [p["name"]  for p in INDIA_GEO_PROVINCES]
        colors = [p["color"] for p in INDIA_GEO_PROVINCES]
        sizes  = [p["size"]  for p in INDIA_GEO_PROVINCES]
        hover  = [f"<b>{p['name']}</b><br>Age: {p['age']}<br>Rock: {p['rock'][:40]}..." for p in INDIA_GEO_PROVINCES]

        fig_map = go.Figure()
        fig_map.add_trace(go.Scattergeo(
            lat=lats, lon=lons, text=names, customdata=hover,
            mode="markers+text", textposition="top center",
            marker=dict(size=sizes, color=colors, line=dict(width=1.5, color="rgba(255,255,255,0.4)"),
                        opacity=0.9),
            textfont=dict(color="#f0e6d0", size=9, family="Source Sans 3"),
            hovertemplate="%{customdata}<extra></extra>",
        ))
        fig_map.update_geos(
            scope="asia", lonaxis_range=[68, 98], lataxis_range=[6, 38],
            showland=True, landcolor="#0f1e0f", showocean=True, oceancolor="#020817",
            showlakes=True, lakecolor="#0a1628",
            showcountries=True, countrycolor="rgba(255,255,255,0.15)",
            showcoastlines=True, coastlinecolor="rgba(0,212,255,0.5)",
            showrivers=True, rivercolor="rgba(0,180,255,0.3)",
            bgcolor="rgba(0,0,0,0)", showframe=False,
            showsubunits=True, subunitcolor="rgba(255,255,255,0.08)",
        )
        fig_map.update_layout(height=520, paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
        st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("<div class='section-heading'>GEOLOGICAL PROVINCES — DETAIL CARDS</div>", unsafe_allow_html=True)
    sel = st.selectbox("Select Province", [p["name"] for p in INDIA_GEO_PROVINCES])
    prov = next(p for p in INDIA_GEO_PROVINCES if p["name"] == sel)
    _prov_photo_topic = prov["sites"].split(",")[0].strip()
    c0, c1, c2 = st.columns([1, 1, 1])
    with c0:
        show_wiki_photo(_prov_photo_topic, caption=_prov_photo_topic)
    with c1:
        st.markdown(f"""
        <div class='glass-card' style='border-color:{prov["color"]}44;'>
            <div style='color:{prov["color"]};font-family:Orbitron,sans-serif;font-size:0.9rem;margin-bottom:12px;'>{prov["name"]}</div>
            <div style='color:#94a3b8;font-size:0.8rem;line-height:2;'>
            🕐 <b style='color:#e2e8f0;'>Age:</b> {prov["age"]}<br>
            🪨 <b style='color:#e2e8f0;'>Rock Types:</b> {prov["rock"]}<br>
            🔩 <b style='color:#e2e8f0;'>Tectonic Setting:</b> {prov["tectonic"]}
            </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='glass-card' style='border-color:{prov["color"]}44;'>
            <div style='color:#94a3b8;font-size:0.8rem;line-height:2;'>
            💎 <b style='color:#e2e8f0;'>Key Minerals:</b> {prov["minerals"]}<br>
            📍 <b style='color:#e2e8f0;'>Famous Sites:</b> {prov["sites"]}
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-heading'>CROSS-SECTION THROUGH THIS PROVINCE</div>", unsafe_allow_html=True)
    render_province_cross_section(prov["name"])

with gmap_tab2:
    st.markdown("""
    <div class='glass-card' style='padding:10px 16px;margin-bottom:10px;'>
        <span style='color:#94a3b8;font-size:0.78rem;'>
        💎 GSI mineral deposit locations across India — click any marker for deposit details.
        Use satellite tile layer for terrain context.
        </span>
    </div>""", unsafe_allow_html=True)

    min_filter = st.multiselect("Filter by Mineral",
        sorted(set(d[2] for d in GSI_DEPOSITS)),
        default=sorted(set(d[2] for d in GSI_DEPOSITS)),
        key="gsi_filter")

    if min_filter:
        _mp_cols = st.columns(min(len(min_filter), 6))
        for i, m_name in enumerate(min_filter[:6]):
            with _mp_cols[i % 6]:
                show_wiki_photo(m_name, caption=m_name)

    if FOLIUM_AVAILABLE:
        m_gsi = make_folium_map(center_lat=22, center_lon=80, zoom=5)
        m_gsi = add_gsi_layer(m_gsi, selected_minerals=min_filter if min_filter else None)
        render_folium(m_gsi, height=520)
    else:
        # Fallback Plotly map when Folium not installed
        fig_gsi = go.Figure()
        for lat, lon, mineral, state, name, grade in GSI_DEPOSITS:
            if min_filter and mineral not in min_filter:
                continue
            col = DEPOSIT_COLORS.get(mineral, "#f59e0b")
            fig_gsi.add_trace(go.Scattergeo(
                lat=[lat], lon=[lon], mode="markers",
                marker=dict(size=12, color=col, opacity=0.85,
                            line=dict(width=1.5, color="rgba(255,255,255,0.5)")),
                name=mineral,
                hovertemplate=f"<b>{name}</b><br>{mineral} · {state}<br>{grade}<extra></extra>"))
        fig_gsi.update_geos(scope="asia", lonaxis_range=[68,98], lataxis_range=[6,38],
            showland=True, landcolor="#0f1e0f", showocean=True, oceancolor="#020817",
            showcountries=True, countrycolor="rgba(255,255,255,0.15)",
            showcoastlines=True, coastlinecolor="rgba(0,212,255,0.4)",
            bgcolor="rgba(0,0,0,0)", showframe=False)
        fig_gsi.update_layout(height=520, paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
            legend=dict(bgcolor="rgba(10,22,40,0.88)", font=dict(size=9, color="#f0e6d0"),
                        bordercolor="rgba(201,168,76,0.3)", borderwidth=1))
        st.plotly_chart(fig_gsi, use_container_width=True)
        st.info("Add `folium` to requirements.txt for satellite tile layers.")

    # Deposit summary table
    st.markdown("<div class='section-heading'>DEPOSIT SUMMARY</div>", unsafe_allow_html=True)
    dcols = st.columns(4)
    shown = [d for d in GSI_DEPOSITS if not min_filter or d[2] in min_filter]
    for i, (lat, lon, mineral, state, name, grade) in enumerate(shown):
        with dcols[i % 4]:
            col = DEPOSIT_COLORS.get(mineral, "#f59e0b")
            st.markdown(f"""
            <div class='glass-card' style='padding:10px 12px;border-color:{col}44;'>
                <div style='color:{col};font-size:0.75rem;font-weight:600;margin-bottom:3px;'>{mineral}</div>
                <div style='color:#e2e8f0;font-size:0.72rem;font-weight:600;'>{name}</div>
                <div style='color:#94a3b8;font-size:0.68rem;line-height:1.5;margin-top:3px;'>
                📍 {state}<br>⚗️ {grade}
                </div>
            </div>""", unsafe_allow_html=True)

with gmap_tab3:
    st.markdown("""
    <div class='glass-card' style='padding:10px 16px;margin-bottom:12px;'>
        <span style='color:#94a3b8;font-size:0.78rem;'>
        🏞️ Iconic locations where you can see India's geology up close — each shaped by the provinces above.
        </span>
    </div>""", unsafe_allow_html=True)
    FAMOUS_SITES = [
        ("Ajanta Caves", "Deccan basalt carved into 2nd-century BCE Buddhist rock-cut caves — 30 caves cut directly into a horseshoe-shaped lava cliff.", "Ajanta Caves"),
        ("Lonar crater", "1.8 km wide impact crater blasted into Deccan basalt ~50,000 years ago — one of the few impact craters in basaltic rock on Earth.", "Lonar crater"),
        ("Marble Rocks, Bhedaghat", "Narmada river gorge cut through brilliant white Precambrian marble cliffs up to 30m high, near Jabalpur.", "Bhedaghat"),
        ("Zawar Mines", "One of the world's oldest zinc-smelting sites (Aravalli belt, Rajasthan) — mined continuously for over 2,000 years.", "Zawar"),
        ("Siachen Glacier", "World's highest battlefield sits atop a glacier carved by the ongoing Himalayan uplift — Karakoram range.", "Siachen Glacier"),
        ("Great Rann of Kutch", "World's largest salt desert — a seasonally flooded rift basin that turns brilliant white in the dry season.", "Rann of Kutch"),
    ]
    fs_cols = st.columns(3)
    for i, (name, desc, wiki_topic) in enumerate(FAMOUS_SITES):
        with fs_cols[i % 3]:
            show_wiki_photo(wiki_topic, caption=name)
            st.markdown(f"""
            <div class='glass-card' style='padding:10px 12px;'>
                <div style='color:#c9a84c;font-size:0.78rem;font-weight:600;margin-bottom:4px;'>{name}</div>
                <div style='color:#94a3b8;font-size:0.72rem;line-height:1.5;'>{desc}</div>
            </div>""", unsafe_allow_html=True)

st.markdown("<div class='section-heading'>INDIA'S GEOLOGICAL DIVERSITY, IN ONE STRIP</div>", unsafe_allow_html=True)
_strip = ["Himalayas", "Deccan Traps", "Thar Desert", "Rann of Kutch", "Western Ghats", "Andaman Islands"]
_strip_cols = st.columns(len(_strip))
for i, topic in enumerate(_strip):
    with _strip_cols[i]:
        show_wiki_photo(topic, caption=topic)
