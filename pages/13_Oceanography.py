# GeoSphere India — Oceanography
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

st.set_page_config(page_title="Oceanography — GeoSphere India", page_icon="🌊", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Indian Ocean", "Oceanography", "INDIAN OCEAN SYSTEMS")

st.markdown("<div class='section-heading'>OCEANOGRAPHY — INDIAN OCEAN SYSTEMS</div>", unsafe_allow_html=True)

oc_tab1, oc_tab2, oc_tab3 = st.tabs(["🌊 Current Map", "🌍 Ocean Zones", "📊 Data & Facts"])

with oc_tab1:
    st.markdown("<div style='color:#94a3b8;font-size:0.78rem;margin-bottom:8px;'>Animated ocean currents — Indian Ocean circulatory system. Arrows show flow direction.</div>", unsafe_allow_html=True)

    monsoon_season = st.radio("🔄 Monsoon switch", ["☀️ Summer (SW Monsoon, Jun–Sep)", "❄️ Winter (NE Monsoon, Dec–Feb)"],
        horizontal=True, key="monsoon_toggle")
    _is_summer = monsoon_season.startswith("☀️")
    st.caption("The Indian Ocean is the only ocean on Earth where surface currents completely reverse "
               "direction with the seasons — driven by the monsoon winds rather than fixed by Coriolis alone.")

    fig_oc = go.Figure()

    # India EEZ
    fig_oc.add_trace(go.Scattergeo(
        lat=[8,8,22,30,23,8], lon=[68,82,90,78,68,68],
        fill="toself", fillcolor="rgba(0,212,255,0.06)",
        line=dict(color="rgba(0,212,255,0.4)", width=1.2),
        name="India EEZ", mode="lines", hoverinfo="name"))

    def curve(lat0, lon0, lat1, lon1, bend, n=16):
        pts = []
        dlat, dlon = lat1-lat0, lon1-lon0
        plat, plon = -dlon, dlat
        norm = (plat**2+plon**2)**0.5 or 1
        plat, plon = plat/norm, plon/norm
        for i in range(n+1):
            t = i/n
            ca = bend * math.sin(math.pi*t)
            pts.append((lat0+dlat*t+plat*ca, lon0+dlon*t+plon*ca))
        return pts

    if _is_summer:
        currents = [
            # lat0,lon0,lat1,lon1,bend,name,color,description
            (14,78,8,45,4.0,    "Southwest Monsoon Current","#00d4ff", "SW monsoon drives water east→west then curves north — reversed from winter"),
            (5,80,10,100,-3.5,  "South Equatorial Current","#c084fc",  "Steady westward drift below equator year-round"),
            (5,48,20,60,-2.5,   "Somali Current (Summer)","#f59e0b",   "One of the fastest currents on Earth in summer — flows NE at up to 3.5 m/s, reversing completely from winter"),
            (8,68,4,90,-3.0,    "Equatorial Counter Current","#34d399","Eastward counter-flow between the two equatorial currents"),
            (-10,80,-25,58,5.0, "Agulhas Current","#f87171",           "Strong western boundary current off SE Africa coast"),
            (5,60,2,85,-2.0,    "Indian Monsoon Current (SW)","#fbbf24","Flows east — strongest seasonal reversal current on Earth"),
            (-5,100,-15,82,3.5, "South Indian Ocean Gyre","#a78bfa",   "Clockwise subtropical gyre linking currents in the south"),
        ]
    else:
        currents = [
            (8,45,14,78,4.0,    "Northeast Monsoon Current","#00d4ff", "NE monsoon drives water west→east reversal of the summer pattern"),
            (5,80,10,100,-3.5,  "South Equatorial Current","#c084fc",  "Steady westward drift below equator year-round"),
            (20,60,5,48,2.5,    "Somali Current (Winter)","#f59e0b",   "Weaker, flows SW in winter — the reverse of its powerful summer jet"),
            (4,90,8,68,3.0,     "Equatorial Counter Current","#34d399","Westward counter-flow reverses direction from the summer season"),
            (-10,80,-25,58,5.0, "Agulhas Current","#f87171",           "Strong western boundary current off SE Africa coast — largely season-independent"),
            (2,85,5,60,2.0,     "Indian Monsoon Current (NE)","#fbbf24","Flows west — the winter half of the great seasonal reversal"),
            (-5,100,-15,82,3.5, "South Indian Ocean Gyre","#a78bfa",   "Clockwise subtropical gyre linking currents in the south"),
        ]

    for lat0,lon0,lat1,lon1,bend,name_c,color_c,desc_c in currents:
        path = curve(lat0,lon0,lat1,lon1,bend)
        lats_c = [p[0] for p in path]
        lons_c = [p[1] for p in path]
        fig_oc.add_trace(go.Scattergeo(
            lat=lats_c, lon=lons_c, mode="lines",
            line=dict(color=color_c, width=3),
            name=name_c,
            hovertemplate=f"<b>{name_c}</b><br>{desc_c}<extra></extra>"))
        # Mid-path arrow
        mid = len(lats_c)//2
        angle = math.degrees(math.atan2(
            lons_c[mid]-lons_c[mid-1],
            lats_c[mid]-lats_c[mid-1]))
        fig_oc.add_trace(go.Scattergeo(
            lat=[lats_c[mid]], lon=[lons_c[mid]], mode="markers",
            marker=dict(symbol="triangle-up", size=12, color=color_c,
                        angle=angle, line=dict(width=1, color="#0c1428")),
            showlegend=False, hoverinfo="skip"))
        # End arrow
        angle2 = math.degrees(math.atan2(
            lons_c[-1]-lons_c[-2], lats_c[-1]-lats_c[-2]))
        fig_oc.add_trace(go.Scattergeo(
            lat=[lats_c[-1]], lon=[lons_c[-1]], mode="markers",
            marker=dict(symbol="triangle-up", size=10, color=color_c,
                        angle=angle2, line=dict(width=1, color="#0c1428")),
            showlegend=False, hoverinfo="skip"))

    # Major shipping routes
    routes = [
        ([12,8,1,-5,-25],[52,55,65,75,80],"Hormuz→Suez Route","rgba(255,255,255,0.25)"),
        ([12,8,-5,-30,-35],[52,72,80,90,95],"Hormuz→Malacca Route","rgba(255,200,100,0.25)"),
    ]
    for rlat,rlon,rname,rcol in routes:
        fig_oc.add_trace(go.Scattergeo(
            lat=rlat, lon=rlon, mode="lines",
            line=dict(color=rcol, width=1.5, dash="dot"),
            name=rname, hovertemplate=f"<b>{rname}</b><extra></extra>"))

    # Key ports — with approximate annual cargo traffic (million tonnes/year)
    ports = [("Mumbai (JNPT)",18.9,72.8,74), ("Chennai",13.1,80.3,52), ("Visakhapatnam",17.7,83.3,73),
             ("Kochi",9.9,76.3,38), ("Paradip",20.3,86.6,145), ("Aden",12.8,45.0,4),
             ("Colombo",6.9,79.9,7), ("Singapore",1.3,103.8,626)]
    for pname,plat,plon,traffic in ports:
        fig_oc.add_trace(go.Scattergeo(
            lat=[plat], lon=[plon], text=[pname], mode="markers+text",
            textposition="top right",
            marker=dict(size=6 + min(traffic, 200)/25, color="#e2e8f0", symbol="square"),
            textfont=dict(color="#94a3b8", size=8),
            showlegend=False,
            hovertemplate=f"<b>Port: {pname}</b><br>~{traffic} million tonnes/year<extra></extra>"))

    fig_oc.update_geos(lonaxis_range=[40,115], lataxis_range=[-40,32],
        showland=True, landcolor="#1a2a1a", showocean=True, oceancolor="#010d1f",
        showcountries=True, countrycolor="rgba(255,255,255,0.15)",
        showcoastlines=True, coastlinecolor="rgba(0,212,255,0.35)",
        bgcolor="rgba(0,0,0,0)", showframe=False)
    fig_oc.update_layout(height=500, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
        legend=dict(bgcolor="rgba(10,22,40,0.88)", font=dict(size=9, color="#f0e6d0"),
                    bordercolor="rgba(0,212,255,0.3)", borderwidth=1))
    st.plotly_chart(fig_oc, use_container_width=True)

    st.markdown("""
    <div class='glass-card' style='padding:10px 16px;'>
    <span style='color:#94a3b8;font-size:0.76rem;'>
    🚢 <b style='color:#00d4ff;'>Dotted lines</b> = major shipping lanes.
    <b style='color:#f59e0b;'>Somali Current</b> reverses completely each monsoon season — one of the
    most dramatic oceanographic events on Earth. The Indian Ocean is the only ocean with this
    seasonal circulatory reversal, driven by the differential heating of Asia.
    </span></div>""", unsafe_allow_html=True)

    st.markdown("<div style='color:#c9a84c;font-size:0.8rem;margin:14px 0 6px;'>⚓ Port Traffic (approx. cargo throughput)</div>", unsafe_allow_html=True)
    port_df = pd.DataFrame([{"Port": p, "Country": "India" if p not in ("Aden","Colombo","Singapore") else {"Aden":"Yemen","Colombo":"Sri Lanka","Singapore":"Singapore"}[p],
                              "Annual traffic (Mt/yr)": t} for p, _, _, t in ports]).sort_values("Annual traffic (Mt/yr)", ascending=False)
    st.dataframe(port_df, use_container_width=True, hide_index=True)

    st.markdown("<div class='section-heading'>THE MONSOON REVERSAL — WHY THIS OCEAN IS UNIQUE</div>", unsafe_allow_html=True)
    _mon_img_col, _mon_txt_col = st.columns([1, 2])
    with _mon_img_col:
        show_wiki_photo("Somali Current" if _is_summer else "Monsoon of South Asia",
                         caption="Somali Current jet" if _is_summer else "Northeast monsoon")
    with _mon_txt_col:
        st.markdown(f"""
        <div class='glass-card' style='padding:14px;border-color:{"rgba(0,212,255,0.3)" if _is_summer else "rgba(99,102,241,0.3)"};'>
            <div style='color:{"#00d4ff" if _is_summer else "#6366f1"};font-size:0.85rem;font-weight:600;margin-bottom:8px;'>
                {"☀️ SW Monsoon Current — The Reversal" if _is_summer else "❄️ NE Monsoon Current — Winter Pattern"}
            </div>
            <div style='color:#94a3b8;font-size:0.8rem;line-height:1.8;'>
            {"🌊 <b style='color:#e2e8f0;'>Somali Current</b>: Flows NE at up to 3.5 m/s — one of the world's fastest ocean currents. Completely reverses from its winter direction.<br>🌊 <b style='color:#e2e8f0;'>SW Monsoon Current</b>: Drives water east across the Indian Ocean, replacing the winter NE current.<br>🌡️ <b style='color:#e2e8f0;'>Upwelling</b>: Cold, nutrient-rich water rises along Somalia and Oman coasts — creating productive fisheries.<br>🐠 <b style='color:#e2e8f0;'>Marine life</b>: Phytoplankton blooms follow the upwelling — entire food chains shift with the monsoon."
            if _is_summer else
            "🌊 <b style='color:#e2e8f0;'>NE Monsoon Current</b>: Flows SW across Bay of Bengal toward Sri Lanka and SE coast of India.<br>🌊 <b style='color:#e2e8f0;'>Somali Current</b>: Reverses to flow SW — cold, less energetic than its summer counterpart.<br>🌡️ <b style='color:#e2e8f0;'>Temperature</b>: Arabian Sea slightly cooler. Bay of Bengal stays warm — fuels cyclone season.<br>🐠 <b style='color:#e2e8f0;'>Fisheries</b>: Good conditions along India's east coast as nutrient mixing improves."}
            </div>
            <div style='color:#475569;font-size:0.72rem;margin-top:8px;'>
            The Indian Ocean is the <b>only ocean</b> on Earth with a complete seasonal reversal of surface currents — driven by Asia's thermal contrast with the ocean.
            </div>
        </div>""", unsafe_allow_html=True)

with oc_tab2:
    st.markdown("<div class='section-heading'>OCEAN ZONES & DEPTH PROFILES</div>", unsafe_allow_html=True)

    # Ocean depth zone chart
    zones = [
        ("Epipelagic (Sunlight Zone)","0–200m","#0ea5e9",
         "Light penetrates fully. Photosynthesis occurs. Phytoplankton, zooplankton, fish, coral reefs. "
         "Indian Ocean coral reefs: Lakshadweep, Gulf of Mannar, Andaman & Nicobar."),
        ("Mesopelagic (Twilight Zone)","200–1,000m","#0369a1",
         "Faint light, no photosynthesis. Bioluminescent organisms. Daily vertical migration — "
         "animals feed at surface at night, retreat to depth by day. Temperature drops sharply (thermocline)."),
        ("Bathypelagic (Midnight Zone)","1,000–4,000m","#1e3a5f",
         "Complete darkness. Pressure 100–400 atm. Temperature 2–4°C. Anglerfish, giant squid. "
         "Below the carbonate compensation depth (CCD, ~4,500m) — no calcareous shells preserved."),
        ("Abyssopelagic (Abyssal Zone)","4,000–6,000m","#0f172a",
         "Abyssal plains — Earth's largest ecosystem by area. Red clay and siliceous ooze sediments. "
         "Foraminifera tests dissolve above CCD. Polymetallic nodules (Mn, Ni, Cu, Co) on the seafloor."),
        ("Hadopelagic (Hadal Zone)",">6,000m","#030712",
         "Ocean trenches — subduction zones. Sunda Trench (near Andaman) reaches ~7,725m. "
         "Extreme pressure (600+ atm). Specialised hadal fauna only. Very few expeditions have reached here."),
    ]

    show_wiki_photo("Indian Ocean", caption="Indian Ocean — satellite view (Wikipedia)")

    _zone_bounds = [0, 200, 1000, 4000, 6000, 8000]
    fig_depth = go.Figure()
    for i, (name, depth, col, desc) in enumerate(zones):
        fig_depth.add_trace(go.Bar(
            x=["Ocean depth"], y=[_zone_bounds[i+1]-_zone_bounds[i]], base=_zone_bounds[i],
            marker_color=col, name=name, orientation="v",
            hovertemplate=f"<b>{name}</b><br>{depth}<extra></extra>"))
    fig_depth.update_layout(
        barmode="stack", height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0", family="Source Sans 3"),
        margin=dict(l=5,r=5,t=25,b=5), showlegend=True,
        legend=dict(orientation="h", y=-0.15, font=dict(size=8, color="#f0e6d0"), bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(title="Depth (m)", autorange="reversed", gridcolor="rgba(255,255,255,0.05)", color="#8a7d65"),
        xaxis=dict(visible=False),
        title=dict(text="Depth-scale visual — Indian Ocean pelagic zones", font=dict(size=10, color="#94a3b8")))
    st.plotly_chart(fig_depth, use_container_width=True)

    zone_images = {
        "Epipelagic (Sunlight Zone)": "Coral reef",
        "Mesopelagic (Twilight Zone)": "Bioluminescence",
        "Bathypelagic (Midnight Zone)": "Anglerfish",
        "Abyssopelagic (Abyssal Zone)": "Abyssal plain",
        "Hadopelagic (Hadal Zone)": "Oceanic trench",
    }
    for name, depth, col, desc in zones:
        zimg_col, ztxt_col = st.columns([1, 3])
        with zimg_col:
            show_wiki_photo(zone_images.get(name, "Ocean"), caption=name.split(" (")[0])
        with ztxt_col:
            st.markdown(f"""
            <div class='glass-card' style='border-left:4px solid {col};padding:12px 16px;margin-bottom:8px;'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div style='color:#e2e8f0;font-size:0.85rem;font-weight:600;'>{name}</div>
                    <span style='background:{col};color:white;font-size:0.72rem;padding:2px 10px;
                        border-radius:20px;font-family:Source Sans 3,sans-serif;'>{depth}</span>
                </div>
                <div style='color:#94a3b8;font-size:0.78rem;line-height:1.6;margin-top:6px;'>{desc}</div>
            </div>""", unsafe_allow_html=True)

    # Indian Ocean key ridges and basins
    st.markdown("<div class='section-heading'>KEY FEATURES OF THE INDIAN OCEAN FLOOR</div>", unsafe_allow_html=True)
    features = [
        ("Carlsberg Ridge","A NW-SE spreading ridge connecting the Red Sea rift to the Central Indian Ridge. "
         "Divergent boundary — Arabia and India separating at ~2.5 cm/yr. Creates new oceanic crust."),
        ("90° East Ridge","One of Earth's longest linear volcanic features (5,000 km) — formed by the "
         "Kerguelen hotspot as India drifted northward. Near-vertical, aseismic ridge."),
        ("Sunda Trench (Java Trench)","The deepest part of the Indian Ocean (7,725m). Active subduction — "
         "Australian plate under Eurasian plate. Generated the 2004 M9.1 earthquake and tsunami."),
        ("Mid-Indian Ocean Ridge","A triple junction (Rodrigues Triple Junction) where the African, "
         "Indian, and Antarctic plates meet — one of only a few triple junctions on Earth."),
        ("Deccan Plateau Submarine Extension","The Laxmi Ridge and Laxmi Basin off India's west coast "
         "preserve the record of India's separation from the Seychelles microcontinent ~65 Ma."),
    ]
    for fname, fdesc in features:
        st.markdown(f"""
        <div class='glass-card' style='padding:12px 16px;margin-bottom:8px;'>
            <div style='color:#00d4ff;font-size:0.85rem;font-weight:600;margin-bottom:4px;'>{fname}</div>
            <div style='color:#94a3b8;font-size:0.78rem;line-height:1.6;'>{fdesc}</div>
        </div>""", unsafe_allow_html=True)

with oc_tab3:
    st.markdown("<div class='section-heading'>OCEANOGRAPHIC DATA & INDIA'S MARITIME SIGNIFICANCE</div>", unsafe_allow_html=True)

    facts_oc = [
        ("🌊","Area","70.56 million km² — 3rd largest ocean. Only ocean bounded on 3 sides by land: Asia, Africa, Australia."),
        ("📏","Average Depth","3,741m average. Max depth: Sunda Trench ~7,725m (Java Trench)."),
        ("🇮🇳","India's EEZ","2.37 million km² — larger than India's land area. Rich in fish, oil, gas, and polymetallic nodules."),
        ("🌡️","Sea Surface Temperature","25–29°C in equatorial Indian Ocean. Fuels intense Bay of Bengal cyclones."),
        ("🌀","Monsoon Driver","The Indian Ocean is the only ocean with a complete seasonal circulatory reversal — driven by the Asian monsoon heat low."),
        ("⚓","Shipping","~80% of world's seaborne oil trade passes through the Indian Ocean. Straits of Hormuz and Malacca are global chokepoints."),
        ("🐋","Marine Life","Whale sharks (world's largest fish), blue whales, dugongs, manta rays, and the world's largest coral reef system after the Pacific."),
        ("💧","Salinity","Indian Ocean has the highest salinity of all oceans (~35–36 ppt) partly due to low freshwater input relative to evaporation in the Arabian Sea."),
        ("🛢️","Petroleum","Mumbai High (Bombay High) — India's largest offshore field, 160 km from Mumbai. ~8 million tonnes oil/year. Also major gas fields in KG Basin."),
        ("🧪","Marine Geology","Siliceous ooze (radiolaria, diatoms) south of 55°S. Calcareous ooze (foraminifera, coccoliths) in shallower water above CCD. Red clay in deep basins."),
        ("🌊","Tides","Semidiurnal tides (two high, two low per day) along India's coasts. Tidal range up to 8m in Gulf of Khambhat — one of the world's highest."),
        ("📡","Monitoring","INCOIS (Indian National Centre for Ocean Information Services, Hyderabad) provides real-time ocean data, tsunami alerts, and fishery forecasts."),
    ]
    fc_cols = st.columns(2)
    for i, (em, nm, ds) in enumerate(facts_oc):
        with fc_cols[i % 2]:
            st.markdown(f"""
            <div class='glass-card' style='padding:12px 14px;margin-bottom:8px;'>
                <div style='display:flex;align-items:center;gap:10px;margin-bottom:4px;'>
                    <span style='font-size:1.3rem;'>{em}</span>
                    <span style='color:#00d4ff;font-size:0.82rem;font-weight:600;'>{nm}</span>
                </div>
                <div style='color:#94a3b8;font-size:0.75rem;line-height:1.55;'>{ds}</div>
            </div>""", unsafe_allow_html=True)
