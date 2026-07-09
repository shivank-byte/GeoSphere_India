# GeoSphere India — Geography Explorer
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

st.set_page_config(page_title="Geography Explorer — GeoSphere India", page_icon="🌿", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Geography of India", "Geography Explorer", "TERRAIN & DRAINAGE")

st.markdown("<div class='section-heading'>GEOGRAPHY EXPLORER — INDIA TERRAIN & DRAINAGE</div>", unsafe_allow_html=True)

geo_tab1, geo_tab2, geo_tab3, geo_tab4, geo_tab5 = st.tabs(
    ["🌊 Rivers Map", "⛰️ Mountains Map", "🏛️ Capitals, Plates & Seismic", "🏜️ Deserts & Islands", "🧭 Physiographic Divisions"])

# ── RIVERS TAB ──────────────────────────────────────────────────
with geo_tab1:
    st.markdown("<div style='color:#94a3b8;font-size:0.8rem;margin-bottom:8px;'>Major Indian river systems — hover for details. OSM live data where available, curated paths otherwise.</div>", unsafe_allow_html=True)
    fig_riv = go.Figure()
    river_colors = ["#00d4ff","#38bdf8","#7dd3fc","#a5f3fc","#34d399","#6ee7b7",
                    "#86efac","#fcd34d","#fb923c","#f87171","#c084fc","#a78bfa"]
    for idx, r in enumerate(RIVERS):
        col = river_colors[idx % len(river_colors)]
        # Try OSM live path first, fall back to curated path
        osm_path = fetch_hydrosheds_river(r["name"])
        path = osm_path if osm_path and len(osm_path) > 5 else r.get("path", [])
        if not path:
            continue
        plats = [p[0] for p in path]
        plons = [p[1] for p in path]
        fig_riv.add_trace(go.Scattergeo(
            lat=plats, lon=plons, mode="lines",
            line=dict(color=col, width=2.5),
            name=r["name"],
            hovertemplate=f"<b>{r['name']}</b><br>Length: {r['length_km']} km<br>Origin: {r['origin']}<br>Joins: {r['joins']}<extra></extra>"))
        # Source marker
        fig_riv.add_trace(go.Scattergeo(
            lat=[plats[0]], lon=[plons[0]], mode="markers",
            marker=dict(size=7, color=col, symbol="circle"),
            showlegend=False,
            hovertemplate=f"<b>{r['name']} — Source</b><br>{r['origin']}<extra></extra>"))
        # Mouth marker
        fig_riv.add_trace(go.Scattergeo(
            lat=[plats[-1]], lon=[plons[-1]], mode="markers",
            marker=dict(size=9, color=col, symbol="diamond"),
            showlegend=False,
            hovertemplate=f"<b>{r['name']} — Mouth</b><br>Joins: {r['joins']}<extra></extra>"))

    fig_riv.update_geos(scope="asia", lonaxis_range=[66, 98], lataxis_range=[6, 37],
        showland=True, landcolor="#0f1f0f", showocean=True, oceancolor="#020817",
        showcountries=True, countrycolor="rgba(255,255,255,0.2)",
        showcoastlines=True, coastlinecolor="rgba(0,212,255,0.4)",
        showrivers=True, rivercolor="rgba(0,160,255,0.3)",
        bgcolor="rgba(0,0,0,0)", showframe=False)
    fig_riv.update_layout(height=520, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
        legend=dict(
            bgcolor="rgba(10,22,40,0.88)", font=dict(size=8, color="#f0e6d0"),
            bordercolor="rgba(0,212,255,0.25)", borderwidth=1,
            orientation="v", x=1.01, y=1, xanchor="left",
            tracegroupgap=2,
        ))
    st.plotly_chart(fig_riv, use_container_width=True)

    # River summary cards below map
    # A few rivers need their exact Wikipedia title (English exonym or disambiguated form);
    # everything else uses the bare name directly, which matches Wikipedia's article title.
    RIVER_WIKI_TITLE = {"Ganga": "Ganges", "Tapi": "Tapti River", "Chambal": "Chambal River", "Krishna": "Krishna River"}
    rcols = st.columns(4)
    for i, r in enumerate(RIVERS):
        with rcols[i % 4]:
            show_wiki_photo(RIVER_WIKI_TITLE.get(r["name"], r["name"]), caption=r["name"])
            st.markdown(f"""
            <div class='glass-card' style='padding:10px;text-align:center;'>
                <div style='color:#00d4ff;font-size:0.8rem;font-weight:600;'>{r["name"]}</div>
                <div style='color:#94a3b8;font-size:0.68rem;line-height:1.6;margin-top:4px;'>
                📏 {r["length_km"]} km<br>
                🌊 {r["joins"]}<br>
                🗺️ {", ".join(r["states"][:2])}
                </div>
            </div>""", unsafe_allow_html=True)

# ── MOUNTAINS TAB ────────────────────────────────────────────────
with geo_tab2:
    st.markdown("<div style='color:#94a3b8;font-size:0.8rem;margin-bottom:8px;'>Major mountain ranges, hills, and plateaus of India.</div>", unsafe_allow_html=True)
    mountains_data = [
        ("Himalayas",       32.0, 78.5, "The world's highest range. Active orogeny — still rising ~5mm/yr. Contains all 8000m+ peaks."),
        ("Karakoram",       35.5, 76.5, "Home to K2 (8,611m — world's 2nd highest). Trans-Himalayan range. Heavy glaciation."),
        ("Aravalli Range",  25.5, 73.5, "World's oldest fold mountains (>2 Ga, deeply eroded). Rajasthan to Delhi. Rich in marble, zinc, lead."),
        ("Vindhya Range",   23.5, 78.0, "Proterozoic sandstone scarps. Divides Ganga plains from Deccan. Vindhyan Supergroup outcrops."),
        ("Satpura Range",   21.5, 76.5, "Block mountain (horst). Parallel to Narmada rift. Max elevation ~1,350m (Dhupgarh)."),
        ("Western Ghats",   15.0, 74.5, "UNESCO World Heritage. Escarpment from Deccan lava/Gondwana rifting. Highest: Anamudi 2,695m."),
        ("Eastern Ghats",   17.5, 82.0, "Discontinuous range. Granulite-grade metamorphic rocks. Connects to Eastern Ghats Mobile Belt."),
        ("Nilgiri Hills",   11.5, 76.5, "Junction of Western + Eastern Ghats. High-altitude shola grasslands. Highest: Doddabetta 2,637m."),
        ("Shillong Plateau",25.5, 91.5, "Meghalaya plateau — a detached fragment of the Peninsular craton. Wettest place on Earth nearby."),
        ("Chota Nagpur",    23.5, 85.5, "Ancient craton. Coal, iron ore, mica, bauxite — India's mineral heartland. Jharkhand plateau."),
    ]
    fig_mtn = go.Figure()
    mtn_colors_map = {
        "Himalayas": "#f59e0b", "Karakoram": "#fbbf24",
        "Aravalli Range": "#34d399", "Vindhya Range": "#6ee7b7",
        "Satpura Range": "#a78bfa", "Western Ghats": "#10b981",
        "Eastern Ghats": "#84cc16", "Nilgiri Hills": "#4ade80",
        "Shillong Plateau": "#fb923c", "Chota Nagpur": "#f87171",
    }
    for name, lat, lon, desc in mountains_data:
        col = mtn_colors_map.get(name, "#f59e0b")
        fig_mtn.add_trace(go.Scattergeo(
            lat=[lat], lon=[lon], text=[name],
            mode="markers+text", textposition="top right",
            marker=dict(size=13, color=col, symbol="triangle-up",
                        line=dict(width=1.5, color="rgba(255,255,255,0.4)")),
            textfont=dict(color=col, size=10, family="Arial Black"),
            name=name,
            hovertemplate=f"<b>{name}</b><br>{desc}<extra></extra>"))

    fig_mtn.update_geos(scope="asia", lonaxis_range=[66, 98], lataxis_range=[6, 37],
        showland=True, landcolor="#1a150a", showocean=True, oceancolor="#020817",
        showcountries=True, countrycolor="rgba(255,255,255,0.2)",
        showcoastlines=True, coastlinecolor="rgba(255,200,100,0.4)",
        bgcolor="rgba(0,0,0,0)", showframe=False)
    fig_mtn.update_layout(height=520, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
        showlegend=False)
    st.plotly_chart(fig_mtn, use_container_width=True)

    # Mountain cards with Wikipedia photos
    MOUNTAIN_WIKI_TITLE = {"Chota Nagpur": "Chota Nagpur Plateau"}
    mc = st.columns(3)
    for i, (name, lat, lon, desc) in enumerate(mountains_data[:6]):
        with mc[i % 3]:
            show_wiki_photo(MOUNTAIN_WIKI_TITLE.get(name, name), caption=name)
            st.markdown(f"""
            <div class='glass-card' style='padding:10px;'>
                <div style='color:#f59e0b;font-size:0.82rem;font-weight:600;margin-bottom:4px;'>{name}</div>
                <div style='color:#94a3b8;font-size:0.71rem;line-height:1.5;'>{desc}</div>
            </div>""", unsafe_allow_html=True)

DESERT_REGIONS = [
    ("Thar Desert", 27.0, 71.0, "Great Indian Desert — ~200,000 km² across Rajasthan, Gujarat, Haryana, Punjab. Aeolian sand dunes over Precambrian basement; one of the world's most densely populated deserts."),
    ("Rann of Kutch", 23.7, 69.9, "Salt marsh / seasonal desert — the Great & Little Rann of Kutch. Tectonically active rift basin; site of the 2001 Bhuj earthquake."),
]
ISLAND_CHAINS = [
    ("Andaman Islands", 12.0, 92.9, "Volcanic-arc islands above the Andaman–Sunda subduction zone. Barren Island — India's only active volcano — sits at the arc front."),
    ("Nicobar Islands", 7.5, 93.7, "Southern continuation of the Andaman arc, closer to the Sunda Trench; struck hardest by the 2004 Indian Ocean tsunami."),
    ("Lakshadweep", 10.6, 72.6, "Coral atolls capping submerged volcanic seamounts on the Chagos-Laccadive Ridge — geologically unrelated to the Andaman volcanic arc."),
]

# ── COMBINED TAB ────────────────────────────────────────────────
with geo_tab3:
    map_choice = st.radio("Map", ["🏛️ State & UT Capitals", "🌍 Plate Boundaries", "🎯 Seismic Zones", "🌆 Major Metro Cities"],
        horizontal=True, key="geo3_map_choice")

    if map_choice == "🏛️ State & UT Capitals":
        st.caption("All 28 state capitals and 8 Union Territory capitals/headquarters.")
        STATE_CAPITALS = [
            ("Andhra Pradesh","Amaravati",16.51,80.52,"State"), ("Arunachal Pradesh","Itanagar",27.10,93.62,"State"),
            ("Assam","Dispur (Guwahati)",26.14,91.79,"State"), ("Bihar","Patna",25.61,85.14,"State"),
            ("Chhattisgarh","Raipur",21.25,81.63,"State"), ("Goa","Panaji",15.49,73.83,"State"),
            ("Gujarat","Gandhinagar",23.22,72.68,"State"), ("Haryana","Chandigarh",30.74,76.79,"State"),
            ("Himachal Pradesh","Shimla",31.10,77.17,"State"), ("Jharkhand","Ranchi",23.36,85.33,"State"),
            ("Karnataka","Bengaluru",12.97,77.59,"State"), ("Kerala","Thiruvananthapuram",8.52,76.94,"State"),
            ("Madhya Pradesh","Bhopal",23.26,77.41,"State"), ("Maharashtra","Mumbai",19.08,72.88,"State"),
            ("Manipur","Imphal",24.82,93.94,"State"), ("Meghalaya","Shillong",25.57,91.88,"State"),
            ("Mizoram","Aizawl",23.73,92.72,"State"), ("Nagaland","Kohima",25.67,94.11,"State"),
            ("Odisha","Bhubaneswar",20.30,85.82,"State"), ("Punjab","Chandigarh",30.74,76.79,"State"),
            ("Rajasthan","Jaipur",26.91,75.79,"State"), ("Sikkim","Gangtok",27.33,88.61,"State"),
            ("Tamil Nadu","Chennai",13.08,80.27,"State"), ("Telangana","Hyderabad",17.39,78.49,"State"),
            ("Tripura","Agartala",23.83,91.28,"State"), ("Uttar Pradesh","Lucknow",26.85,80.95,"State"),
            ("Uttarakhand","Dehradun",30.32,78.03,"State"), ("West Bengal","Kolkata",22.57,88.36,"State"),
            ("Andaman & Nicobar Islands","Port Blair",11.62,92.73,"UT"), ("Chandigarh (UT)","Chandigarh",30.74,76.79,"UT"),
            ("Dadra & Nagar Haveli and Daman & Diu","Daman",20.42,72.83,"UT"), ("Delhi (NCT)","New Delhi",28.61,77.21,"UT"),
            ("Jammu & Kashmir","Srinagar",34.08,74.80,"UT"), ("Ladakh","Leh",34.15,77.58,"UT"),
            ("Lakshadweep","Kavaratti",10.57,72.64,"UT"), ("Puducherry","Puducherry",11.94,79.83,"UT"),
        ]
        fig_cap = go.Figure()
        for group, color, sym in [("State","#00d4ff","circle"), ("UT","#f59e0b","diamond")]:
            pts = [s for s in STATE_CAPITALS if s[4] == group]
            fig_cap.add_trace(go.Scattergeo(
                lat=[p[2] for p in pts], lon=[p[3] for p in pts],
                text=[p[1] for p in pts], mode="markers+text", textposition="top center",
                marker=dict(size=7, color=color, symbol=sym, line=dict(width=1, color="white")),
                textfont=dict(color=color, size=7), name=f"{group} Capital",
                customdata=[p[0] for p in pts],
                hovertemplate="<b>%{text}</b><br>%{customdata}<extra></extra>"))
        fig_cap.update_geos(scope="asia", lonaxis_range=[66, 98], lataxis_range=[6, 37],
            showland=True, landcolor="#1a2a1a", showocean=True, oceancolor="#020817",
            showcountries=True, countrycolor="rgba(255,255,255,0.2)",
            showcoastlines=True, coastlinecolor="rgba(0,212,255,0.5)",
            bgcolor="rgba(0,0,0,0)", showframe=False)
        fig_cap.update_layout(height=560, paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
            legend=dict(bgcolor="rgba(10,22,40,0.85)", font=dict(size=10, color="#f0e6d0"),
                        orientation="h", y=-0.05))
        st.plotly_chart(fig_cap, use_container_width=True)

    elif map_choice == "🌍 Plate Boundaries":
        st.caption("Simplified plate boundaries around the Indian Plate — where India collides, subducts, or grinds past its neighbours.")
        PLATE_BOUNDARIES = [
            ("Himalayan Front (India–Eurasia, convergent)", "#dc2626",
             [(35.2,74.6),(33.5,76.0),(30.7,79.0),(28.2,84.0),(27.8,88.5),(27.9,91.5),(29.0,95.2)]),
            ("Andaman–Sunda Arc (India–Burma, subduction)", "#f59e0b",
             [(15.0,93.5),(12.3,93.9),(9.0,93.0),(5.5,95.5),(2.0,97.0)]),
            ("Owen Fracture Zone (India–Arabia, transform)", "#8b5cf6",
             [(24.0,60.0),(20.0,59.5),(15.0,58.5),(10.5,57.5)]),
            ("Carlsberg Ridge (India–Africa, divergent)", "#10b981",
             [(10.0,57.0),(5.0,62.0),(0.0,66.0),(-5.0,68.0)]),
        ]
        fig_pb = go.Figure()
        for name, color, pts in PLATE_BOUNDARIES:
            fig_pb.add_trace(go.Scattergeo(
                lat=[p[0] for p in pts], lon=[p[1] for p in pts],
                mode="lines", line=dict(color=color, width=4, dash="dash"),
                name=name, hovertemplate=f"<b>{name}</b><extra></extra>"))
        fig_pb.add_trace(go.Scattergeo(lat=[22], lon=[79], text=["INDIAN PLATE"],
            mode="text", textfont=dict(color="#c9a84c", size=13), showlegend=False, hoverinfo="skip"))
        fig_pb.update_geos(scope="asia", lonaxis_range=[52, 100], lataxis_range=[-8, 38],
            showland=True, landcolor="#1a2a1a", showocean=True, oceancolor="#020817",
            showcountries=True, countrycolor="rgba(255,255,255,0.2)",
            showcoastlines=True, coastlinecolor="rgba(0,212,255,0.5)",
            bgcolor="rgba(0,0,0,0)", showframe=False)
        fig_pb.update_layout(height=520, paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
            legend=dict(bgcolor="rgba(10,22,40,0.85)", font=dict(size=9, color="#f0e6d0"),
                        orientation="h", y=-0.1))
        st.plotly_chart(fig_pb, use_container_width=True)
        st.caption("Schematic — boundary traces are simplified for illustration, not survey-grade.")

    elif map_choice == "🎯 Seismic Zones":
        st.caption("India's 4-tier seismic hazard zonation (Bureau of Indian Standards, IS 1893).")
        fig_sz = go.Figure()
        zones = [(33,76,"Zone V — Very High","#dc2626"),(27,88,"Zone V — Very High","#dc2626"),
                 (23,93,"Zone V — Very High","#dc2626"),(25,85,"Zone IV — High","#f59e0b"),
                 (19,73,"Zone IV — High","#f59e0b"),(22,78,"Zone III — Moderate","#fbbf24"),
                 (17,80,"Zone III — Moderate","#fbbf24"),(20,74,"Zone II — Low","#34d399"),
                 (13,78,"Zone II — Low","#34d399")]
        for lat,lon,label,col in zones:
            fig_sz.add_trace(go.Scattergeo(lat=[lat], lon=[lon], text=[label.split(" — ")[0]],
                mode="markers+text", textposition="top right",
                marker=dict(size=16, color=col, opacity=0.65),
                textfont=dict(color=col, size=9),
                name=label, hovertemplate=f"<b>{label}</b><extra></extra>"))
        fig_sz.update_geos(scope="asia", lonaxis_range=[66, 98], lataxis_range=[6, 37],
            showland=True, landcolor="#1a2a1a", showocean=True, oceancolor="#020817",
            showcountries=True, countrycolor="rgba(255,255,255,0.2)",
            showcoastlines=True, coastlinecolor="rgba(0,212,255,0.5)",
            bgcolor="rgba(0,0,0,0)", showframe=False)
        fig_sz.update_layout(height=520, paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
        st.plotly_chart(fig_sz, use_container_width=True)
        _zc = st.columns(4)
        for i, (lbl, col, note) in enumerate([("Zone II","#34d399","Low — stable peninsula"),
                ("Zone III","#fbbf24","Moderate — most of the plateau"),
                ("Zone IV","#f59e0b","High — near-Himalaya & Kutch"),
                ("Zone V","#dc2626","Very High — Himalaya, NE, Andaman")]):
            with _zc[i]:
                st.markdown(f"<div style='text-align:center;padding:8px;background:{col}22;border-radius:8px;'>"
                            f"<div style='color:{col};font-weight:600;'>{lbl}</div>"
                            f"<div style='color:#94a3b8;font-size:0.68rem;'>{note}</div></div>", unsafe_allow_html=True)

    else:  # Major Metro Cities
        st.caption("India's largest cities by population — distinct from the state capitals above (many aren't capitals at all).")
        METROS = [
            ("Mumbai", 19.08, 72.88, "~20.4M", "Maharashtra"), ("Delhi", 28.70, 77.10, "~32.9M", "Delhi NCT"),
            ("Bengaluru", 12.97, 77.59, "~13.6M", "Karnataka"), ("Hyderabad", 17.39, 78.49, "~10.5M", "Telangana"),
            ("Ahmedabad", 23.03, 72.58, "~8.4M", "Gujarat"), ("Chennai", 13.08, 80.27, "~11.5M", "Tamil Nadu"),
            ("Kolkata", 22.57, 88.36, "~15.1M", "West Bengal"), ("Surat", 21.17, 72.83, "~7.5M", "Gujarat"),
            ("Pune", 18.52, 73.86, "~7.4M", "Maharashtra"), ("Jaipur", 26.91, 75.79, "~4.1M", "Rajasthan"),
        ]
        fig_metro = go.Figure(go.Scattergeo(
            lat=[m[1] for m in METROS], lon=[m[2] for m in METROS],
            text=[m[0] for m in METROS], mode="markers+text", textposition="top center",
            marker=dict(size=[14+i*0.5 for i in range(len(METROS))][::-1], color="#22d3ee", opacity=0.8,
                        line=dict(width=1, color="white")),
            textfont=dict(color="#22d3ee", size=9),
            customdata=[[m[3], m[4]] for m in METROS],
            hovertemplate="<b>%{text}</b><br>Population: %{customdata[0]}<br>%{customdata[1]}<extra></extra>"))
        fig_metro.update_geos(scope="asia", lonaxis_range=[66, 98], lataxis_range=[6, 37],
            showland=True, landcolor="#1a2a1a", showocean=True, oceancolor="#020817",
            showcountries=True, countrycolor="rgba(255,255,255,0.2)",
            showcoastlines=True, coastlinecolor="rgba(0,212,255,0.5)",
            bgcolor="rgba(0,0,0,0)", showframe=False)
        fig_metro.update_layout(height=520, paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
        st.plotly_chart(fig_metro, use_container_width=True)

with geo_tab4:
    st.markdown("<div style='color:#94a3b8;font-size:0.8rem;margin-bottom:8px;'>India's desert regions and island chains — geologically distinct from the mainland.</div>", unsafe_allow_html=True)
    fig_di = go.Figure()
    for name, lat, lon, desc in DESERT_REGIONS:
        fig_di.add_trace(go.Scattergeo(lat=[lat], lon=[lon], text=[name],
            mode="markers+text", textposition="top right",
            marker=dict(size=15, color="#eab308", symbol="square", opacity=0.9),
            textfont=dict(color="#eab308", size=10), name=name,
            hovertemplate=f"<b>{name}</b><br>{desc}<extra></extra>"))
    for name, lat, lon, desc in ISLAND_CHAINS:
        fig_di.add_trace(go.Scattergeo(lat=[lat], lon=[lon], text=[name],
            mode="markers+text", textposition="top right",
            marker=dict(size=13, color="#22d3ee", symbol="star", opacity=0.9),
            textfont=dict(color="#22d3ee", size=10), name=name,
            hovertemplate=f"<b>{name}</b><br>{desc}<extra></extra>"))
    fig_di.update_geos(scope="asia", lonaxis_range=[66, 98], lataxis_range=[6, 37],
        showland=True, landcolor="#1a2a1a", showocean=True, oceancolor="#020817",
        showcountries=True, countrycolor="rgba(255,255,255,0.2)",
        showcoastlines=True, coastlinecolor="rgba(0,212,255,0.5)",
        bgcolor="rgba(0,0,0,0)", showframe=False)
    fig_di.update_layout(height=440, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
        legend=dict(bgcolor="rgba(10,22,40,0.85)", font=dict(size=9, color="#f0e6d0"),
                    bordercolor="rgba(0,212,255,0.3)", borderwidth=1))
    st.plotly_chart(fig_di, use_container_width=True)

    st.markdown("<div class='section-heading'>🏜️ DESERT REGIONS</div>", unsafe_allow_html=True)
    d_cols = st.columns(len(DESERT_REGIONS))
    for i, (name, lat, lon, desc) in enumerate(DESERT_REGIONS):
        with d_cols[i]:
            show_wiki_photo(name, caption=name)
            st.markdown(f"""
            <div class='glass-card' style='padding:12px;'>
                <div style='color:#eab308;font-size:0.82rem;font-weight:600;margin-bottom:4px;'>{name}</div>
                <div style='color:#94a3b8;font-size:0.75rem;line-height:1.55;'>{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-heading'>🏝️ ISLAND CHAINS</div>", unsafe_allow_html=True)
    i_cols = st.columns(len(ISLAND_CHAINS))
    for i, (name, lat, lon, desc) in enumerate(ISLAND_CHAINS):
        with i_cols[i]:
            show_wiki_photo(name, caption=name)
            st.markdown(f"""
            <div class='glass-card' style='padding:12px;'>
                <div style='color:#22d3ee;font-size:0.82rem;font-weight:600;margin-bottom:4px;'>{name}</div>
                <div style='color:#94a3b8;font-size:0.75rem;line-height:1.55;'>{desc}</div>
            </div>""", unsafe_allow_html=True)

with geo_tab5:
    st.markdown("<div class='section-heading'>INDIA PHYSIOGRAPHIC DIVISIONS</div>", unsafe_allow_html=True)
    physio = [
        ("🏔️","Himalayan Mountains","Himalayas","2,500 km range. 3 parallel zones: Himadri (Greater Himalaya, >7000m), Himachal (Lesser Himalaya, 1000-4500m), and Siwaliks (outer foothills). Formed by ongoing India-Eurasia collision since ~50 Ma."),
        ("🌾","Northern Plains","Indo-Gangetic Plain","700,000 km². Built from Ganga-Indus-Brahmaputra alluvium. Sub-divided into Bhabar, Terai, Bhangar and Khadar. India's most fertile, densely populated region."),
        ("⛰️","Peninsular Plateau","Deccan Plateau","Oldest part of India — stable Precambrian craton >3 Ga. Average 600-900m elevation. Includes Deccan Plateau (basalt), Chota Nagpur (minerals), and Malwa Plateau."),
        ("🌊","Coastal Plains","Konkan","Western (narrow, steep, Konkan + Malabar) and Eastern (broad, deltaic, Coromandel + Northern Circars)."),
        ("🏝️","Islands","Andaman Islands","Andaman & Nicobar (volcanic arc — India's only active volcano). Lakshadweep (coral atolls — geologically unrelated to the Andamans)."),
    ]
    pc = st.columns(5)
    for i, (em, name, wiki_topic, desc) in enumerate(physio):
        with pc[i]:
            show_wiki_photo(wiki_topic, caption=name)
            st.markdown(f"""
            <div class='glass-card' style='padding:12px;text-align:center;'>
                <div style='font-size:1.5rem;margin-bottom:5px;'>{em}</div>
                <div style='color:#00d4ff;font-size:0.75rem;font-weight:600;margin-bottom:5px;'>{name}</div>
                <div style='color:#94a3b8;font-size:0.67rem;line-height:1.5;'>{desc}</div>
            </div>""", unsafe_allow_html=True)
