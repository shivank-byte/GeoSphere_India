import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import random
import math
import time
import datetime
import requests
import re
import os
import base64
try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

# ═══════════════════════════════════════════════════════
#  REAL PHOTO FETCH — Wikipedia REST API, cached, fails silently
# ═══════════════════════════════════════════════════════
@st.cache_data(show_spinner=False, ttl=604800)  # cache 1 week
def fetch_hydrosheds_river(river_name: str, country_code: str = "IN"):
    """
    Fetch river centreline coordinates from OpenStreetMap Overpass API.
    Falls back to our hand-coded RIVERS path if unavailable.
    Returns list of (lat, lon) tuples or None.
    """
    try:
        # Overpass query: fetch waterway relation/way named river_name in India
        query = f"""
        [out:json][timeout:15];
        area["ISO3166-1"="{country_code}"]->.a;
        (
          way["waterway"="river"]["name"~"{river_name}",i](area.a);
          relation["waterway"="river"]["name"~"{river_name}",i](area.a);
        );
        out geom;
        """
        url = "https://overpass-api.de/api/interpreter"
        r = requests.post(url, data={"data": query}, timeout=20,
                          headers={"User-Agent": "GeoSphereIndia/1.0 (https://github.com/geosphere-india; educational Earth-science app for BHU NEP syllabus) Python-requests"})
        if r.status_code != 200:
            return None
        data = r.json()
        # Collect all node coordinates across all elements
        coords = []
        for el in data.get("elements", []):
            if el.get("type") == "way" and "geometry" in el:
                for node in el["geometry"]:
                    coords.append((node["lat"], node["lon"]))
            elif el.get("type") == "node":
                coords.append((el["lat"], el["lon"]))
        if len(coords) < 5:
            return None
        # Downsample to max 40 points for performance
        step = max(1, len(coords) // 40)
        return coords[::step]
    except Exception:
        return None

@st.cache_data(show_spinner=False, ttl=604800)
@st.cache_data(show_spinner=False, ttl=604800)  # cache 1 week — matches fetch_hydrosheds_river
def fetch_osm_mountain_range(range_name: str):
    """
    Fetch mountain range boundary/line from OpenStreetMap.
    Returns list of (lat, lon) or None.
    """
    try:
        query = f"""
        [out:json][timeout:15];
        (
          relation["natural"="mountain_range"]["name"~"{range_name}",i];
          way["natural"="ridge"]["name"~"{range_name}",i];
        );
        out geom;
        """
        url = "https://overpass-api.de/api/interpreter"
        r = requests.post(url, data={"data": query}, timeout=20,
                          headers={"User-Agent": "GeoSphereIndia/1.0 (https://github.com/geosphere-india; educational Earth-science app for BHU NEP syllabus) Python-requests"})
        if r.status_code != 200:
            return None
        data = r.json()
        coords = []
        for el in data.get("elements", []):
            if "geometry" in el:
                for node in el["geometry"]:
                    coords.append((node["lat"], node["lon"]))
        if len(coords) < 3:
            return None
        step = max(1, len(coords) // 50)
        return coords[::step]
    except Exception:
        return None

@st.cache_data(show_spinner=False, ttl=120)  # 2-min cache — still "live" but avoids hammering USGS on every rerun
def fetch_usgs_earthquake_count(days_back: int = 1, min_magnitude: float = 2.5):
    """Live worldwide earthquake count from USGS for the last N days. Returns int or None."""
    try:
        start = (datetime.datetime.utcnow() - datetime.timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%S")
        r = requests.get(
            "https://earthquake.usgs.gov/fdsnws/event/1/count",
            params={"format": "geojson", "starttime": start, "minmagnitude": min_magnitude},
            timeout=5)
        if r.status_code == 200:
            return r.json().get("count")
    except Exception:
        pass
    return None

@st.cache_data(show_spinner=False, ttl=120)  # 2-min cache — still "live" but avoids hammering USGS on every rerun
def fetch_usgs_recent_earthquakes(days_back: int = 180, min_magnitude: float = 5.0, limit: int = 20):
    """Live recent significant earthquakes worldwide from USGS. Returns parsed GeoJSON dict or None.
    Uses a rolling date window (not a hardcoded date) so results never go stale."""
    try:
        start = (datetime.datetime.utcnow() - datetime.timedelta(days=days_back)).strftime("%Y-%m-%d")
        r = requests.get(
            "https://earthquake.usgs.gov/fdsnws/event/1/query",
            params={"format": "geojson", "starttime": start, "minmagnitude": min_magnitude,
                    "orderby": "time", "limit": limit},
            timeout=6)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def _get_unsplash_access_key():
    """Reads a free Unsplash API Access Key from st.secrets["UNSPLASH_ACCESS_KEY"]
    or the UNSPLASH_ACCESS_KEY environment variable. Get a free key at
    https://unsplash.com/oauth/applications — returns None (no error) if
    unset, so the Unsplash fallback silently no-ops on setups without one."""
    try:
        if "UNSPLASH_ACCESS_KEY" in st.secrets:
            return st.secrets["UNSPLASH_ACCESS_KEY"]
    except Exception:
        pass
    return os.environ.get("UNSPLASH_ACCESS_KEY")

@st.cache_data(show_spinner=False, ttl=604800)  # cache 1 week
def fetch_unsplash_image(query: str):
    """Unsplash photo search (api.unsplash.com/search/photos) — requires a
    free Unsplash Access Key (see _get_unsplash_access_key). High-quality,
    professionally shot photos; a good general-purpose fallback alongside
    NASA. Returns an image URL, or None if no key is configured or no
    match is found."""
    access_key = _get_unsplash_access_key()
    if not access_key:
        return None
    try:
        r = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": "5", "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=4)
        if r.status_code == 200:
            for res in r.json().get("results", []):
                urls = res.get("urls", {})
                thumb = urls.get("regular") or urls.get("small") or urls.get("full")
                if thumb:
                    return thumb
    except Exception:
        pass
    return None

@st.cache_data(show_spinner=False, ttl=604800)  # cache 1 week
def fetch_nasa_image(query: str):
    """Free NASA Images & Video Library API (images-api.nasa.gov) — no API
    key required. Great for Earth-observation, space, and planetary-science
    topics (volcanoes, earthquakes, satellite imagery, astronomy). Returns
    an image URL, or None on failure/no match."""
    try:
        r = requests.get(
            "https://images-api.nasa.gov/search",
            params={"q": query, "media_type": "image"},
            timeout=4,
            headers={"User-Agent": "GeoSphereIndia/1.0 (educational Earth-science app)"})
        if r.status_code == 200:
            items = r.json().get("collection", {}).get("items", [])
            for item in items:
                for link in item.get("links", []):
                    if link.get("rel") == "preview" and link.get("href"):
                        return link["href"]
    except Exception:
        pass
    return None

def _get_pexels_api_key():
    """Reads a free Pexels API key from st.secrets["PEXELS_API_KEY"] or the
    PEXELS_API_KEY environment variable. Get a free key at
    https://www.pexels.com/api/ (instant approval, no cost tier ever —
    200 requests/hour, 20,000/month on the free plan) — returns None (no
    error) if unset, so this fallback silently no-ops on setups without one."""
    try:
        if "PEXELS_API_KEY" in st.secrets:
            return st.secrets["PEXELS_API_KEY"]
    except Exception:
        pass
    return os.environ.get("PEXELS_API_KEY")

@st.cache_data(show_spinner=False, ttl=604800)  # cache 1 week
def fetch_pexels_image(query: str):
    """Pexels photo search (api.pexels.com/v1/search) — requires a free
    Pexels API key (see _get_pexels_api_key). Pexels' free tier has no paid
    upgrade requirement — it stays free indefinitely. Returns an image URL,
    or None if no key is configured or no match is found."""
    api_key = _get_pexels_api_key()
    if not api_key:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": "5", "orientation": "landscape"},
            headers={"Authorization": api_key},
            timeout=4)
        if r.status_code == 200:
            for photo in r.json().get("photos", []):
                src = photo.get("src", {})
                thumb = src.get("large") or src.get("medium") or src.get("original")
                if thumb:
                    return thumb
    except Exception:
        pass
    return None

def get_wiki_image(title: str, strict: bool = False):
    """Fetch a representative photo URL for a topic. Returns None on failure
    so the UI can gracefully skip the image. Public wrapper: only successful
    lookups get cached (1 day) — failures are never cached, so a transient
    network hiccup doesn't block a real photo for a whole day.
    Tries, in order: Wikipedia REST summary, MediaWiki pageimages API,
    Wikimedia Commons keyword search, Openverse (api.openverse.org — a free,
    no-key aggregator of Commons/Flickr/museum images), NASA Images API
    (images-api.nasa.gov — free, no key, strong for Earth/space topics),
    Unsplash (needs UNSPLASH_ACCESS_KEY, skipped silently if unset), then
    Pexels (needs PEXELS_API_KEY, also skipped silently if unset — Pexels'
    free tier never expires or requires payment).
    strict=True skips every keyword-search fallback (Commons, Openverse,
    NASA, Unsplash, Pexels) — use this for synthetic/compound queries (e.g.
    "X thin section micrograph") where a loose text match is more likely to
    return an unrelated scanned document than a real photo. A clean
    placeholder is better than a wrong image."""
    try:
        return _wiki_image_attempt(title, strict)
    except Exception:
        return None

@st.cache_data(show_spinner=False, ttl=86400)  # only reached (and cached) on success — see get_wiki_image
def _wiki_image_attempt(title: str, strict: bool = False) -> str:
    import urllib.parse as _up
    safe_title = _up.quote(title.replace(" ", "_"), safe="_():")
    headers = {"User-Agent": "GeoSphereIndia/1.0 (https://github.com/geosphere-india; educational Earth-science app for BHU NEP syllabus) Python-requests"}

    # Attempt 1 — REST summary endpoint (fast, includes disambiguation info)
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe_title}"
        r = requests.get(url, timeout=3.5, headers=headers)
        if r.status_code == 200:
            data = r.json()
            if data.get("type") != "disambiguation":
                thumb = data.get("thumbnail", {}).get("source") or data.get("originalimage", {}).get("source")
                if thumb:
                    return thumb
    except Exception:
        pass

    # Attempt 2 — classic MediaWiki action API with redirects + pageimages,
    # which succeeds for many titles the REST summary endpoint misses.
    try:
        r2 = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "query", "titles": title, "prop": "pageimages",
                    "format": "json", "pithumbsize": "500", "redirects": "1"},
            timeout=3.5, headers=headers)
        if r2.status_code == 200:
            pages = r2.json().get("query", {}).get("pages", {})
            for _pid, pdata in pages.items():
                thumb = pdata.get("thumbnail", {}).get("source")
                if thumb:
                    return thumb
    except Exception:
        pass

    if strict:
        raise LookupError(f"no wiki image found for {title!r} (strict mode — skipped Commons fallback)")

    # Attempt 3 — Wikimedia Commons file search, last resort for topics with
    # no clean Wikipedia article match (e.g. specific place names). Filters
    # out scanned documents/bulletins/journals that sometimes rank highly on
    # text relevance alone but are not photos (this was returning book-page
    # scans instead of real photos for synthetic queries like "X micrograph").
    _DOC_SIGNALS = ("bulletin", "journal", "report", "volume", "page ", "text of",
                    "scan", "manuscript", "proceedings", "gazette", "thesis", "map of",
                    "museum bulletin", "memoir", "circular", "yearbook", "annual ",
                    "transactions", "society", "no.", "vol.", "index of", "catalogue",
                    "titlepage", "title page", "frontispiece")
    try:
        r3 = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": title + " -filetype:pdf -filetype:djvu",
                    "srnamespace": "6", "srlimit": "6", "format": "json"},
            timeout=3.5, headers=headers)
        if r3.status_code == 200:
            results = r3.json().get("query", {}).get("search", [])
            for res in results:
                file_title = res["title"]
                lower_title = file_title.lower()
                if any(sig in lower_title for sig in _DOC_SIGNALS):
                    continue  # skip likely document/scan matches
                if lower_title.endswith((".pdf", ".djvu", ".svg", ".tif", ".tiff")):
                    continue  # skip non-photo file types
                r4 = requests.get(
                    "https://commons.wikimedia.org/w/api.php",
                    params={"action": "query", "titles": file_title, "prop": "imageinfo",
                            "iiprop": "url|size", "iiurlwidth": "500", "format": "json"},
                    timeout=3.5, headers=headers)
                if r4.status_code == 200:
                    pages = r4.json().get("query", {}).get("pages", {})
                    for _pid, pdata in pages.items():
                        info = pdata.get("imageinfo", [{}])
                        w, h = info[0].get("width", 0), info[0].get("height", 0)
                        # Scanned document pages are almost always tall/narrow
                        # (portrait, ~1:1.3–1:1.5 ratio close to A4/letter) —
                        # skip those as an extra guard against document scans.
                        if w and h and (h / w) > 1.25:
                            continue
                        thumb = info[0].get("thumburl") or info[0].get("url")
                        if thumb:
                            return thumb
    except Exception:
        pass

    # Attempt 4 — Openverse (api.openverse.org): free, no API key required,
    # aggregates 800M+ CC-licensed images from Wikimedia Commons, Flickr,
    # museums, and other open sources. Genuinely independent infrastructure
    # from Wikipedia/Wikimedia's own servers, so it's a real backup rather
    # than just hitting the same rate limits again. Same document-scan
    # filtering as the Commons attempt above, since it's the same style of
    # loose keyword search.
    try:
        r5 = requests.get(
            "https://api.openverse.org/v1/images/",
            params={"q": title, "page_size": "6"},
            timeout=3.5, headers=headers)
        if r5.status_code == 200:
            for res in r5.json().get("results", []):
                res_title = (res.get("title") or "").lower()
                if any(sig in res_title for sig in _DOC_SIGNALS):
                    continue
                w, h = res.get("width") or 0, res.get("height") or 0
                if w and h and (h / w) > 1.25:
                    continue  # skip likely document-scan aspect ratios
                thumb = res.get("thumbnail") or res.get("url")
                if thumb:
                    return thumb
    except Exception:
        pass

    # Attempt 5 — NASA Images & Video Library (images-api.nasa.gov): free,
    # no API key required. Independent infrastructure from both Wikimedia
    # and Openverse, and especially strong for Earth-observation, space,
    # and planetary-science subjects that are common in this app.
    nasa_img = fetch_nasa_image(title)
    if nasa_img:
        return nasa_img

    # Attempt 6 — Unsplash (api.unsplash.com). Only runs if a free
    # UNSPLASH_ACCESS_KEY is configured (see _get_unsplash_access_key);
    # otherwise silent no-op.
    unsplash_img = fetch_unsplash_image(title)
    if unsplash_img:
        return unsplash_img

    # Attempt 7 — Pexels (api.pexels.com). Only runs if a free
    # PEXELS_API_KEY is configured (see _get_pexels_api_key); otherwise
    # silent no-op. Pexels' free tier never requires payment or expires.
    pexels_img = fetch_pexels_image(title)
    if pexels_img:
        return pexels_img

    raise LookupError(f"no wiki image found for {title!r}")

def show_wiki_photo(title: str, caption: str = None, width: int = None, strict: bool = False):
    """Render a real photo inline if available, otherwise render a themed SVG placeholder.
    strict=True avoids the Commons keyword-search fallback — see get_wiki_image()."""
    img_url = get_wiki_image(title, strict=strict)
    if img_url:
        try:
            st.image(img_url, caption=caption or title, use_container_width=(width is None))
            return
        except Exception:
            pass
    # SVG placeholder — themed geological swatch card (not a bare "broken image"
    # look) for the cases where no real photo can be found even after retries.
    letter = title[0].upper() if title else "?"
    colors = {"A":"#dc2626","B":"#b45309","C":"#374151","D":"#7c3aed","E":"#059669",
              "F":"#0284c7","G":"#c9a84c","H":"#9333ea","I":"#0891b2","J":"#65a30d",
              "K":"#dc2626","L":"#e5e7eb","M":"#f59e0b","N":"#10b981","O":"#0ea5e9",
              "P":"#a855f7","Q":"#e2e8f0","R":"#ef4444","S":"#94a3b8","T":"#f97316",
              "U":"#06b6d4","V":"#dc2626","W":"#84cc16","X":"#8b5cf6","Y":"#fbbf24","Z":"#6b7280"}
    col = colors.get(letter, "#c9a84c")
    st.markdown(f"""
    <div style='width:100%;aspect-ratio:4/3;background:
        repeating-linear-gradient(135deg, #0c1428, #0c1428 10px, #101d38 10px, #101d38 20px);
        border-radius:8px;display:flex;flex-direction:column;align-items:center;justify-content:center;
        border:1px solid {col}44;margin-bottom:4px;position:relative;overflow:hidden;'>
        <div style='position:absolute;inset:0;background:radial-gradient(circle at 50% 40%,{col}18,transparent 70%);'></div>
        <div style='font-size:2rem;position:relative;'>💎</div>
        <div style='font-size:1.7rem;font-weight:900;color:{col};font-family:Orbitron,sans-serif;
            opacity:0.85;text-shadow:0 0 20px {col};position:relative;margin-top:2px;'>{letter}</div>
        <div style='color:#8695ad;font-size:0.58rem;margin-top:4px;letter-spacing:1px;position:relative;'>Reference not yet available</div>
    </div>
    <div style='color:#8695ad;font-size:0.72rem;text-align:center;margin-bottom:8px;'>{caption or title}</div>
    """, unsafe_allow_html=True)

def render_hero_image(wiki_topic: str, title: str, subtitle: str = ""):
    """Full-width Wikipedia photo banner for the top of a section — sets the
    visual tone before any cards/charts. Falls back to a themed gradient
    banner (still showing the title) if no Wikipedia photo is found.
    During achievement/rare mode, adds the page's poetic Hinglish line
    from RARE_LINES underneath — titles themselves always stay in English."""
    img_url = get_wiki_image(wiki_topic)
    sub_html = f"<div style='color:#c9a84c;font-size:0.8rem;letter-spacing:1.5px;margin-top:4px;'>{subtitle}</div>" if subtitle else ""
    if st.session_state.get("rare_mode") and title in RARE_LINES:
        sub_html += f"<div style='color:#e8c96a;font-size:0.82rem;font-style:italic;margin-top:6px;'>{RARE_LINES[title]}</div>"
    if img_url:
        st.markdown(f"""
        <div style='position:relative;width:100%;height:210px;border-radius:16px;overflow:hidden;
            margin-bottom:18px;background:url("{img_url}") center/cover no-repeat;
            border:1px solid rgba(201,168,76,0.25);'>
            <div style='position:absolute;inset:0;
                background:linear-gradient(180deg,rgba(7,11,24,0.10) 0%,rgba(7,11,24,0.55) 60%,rgba(7,11,24,0.92) 100%);'></div>
            <div style='position:absolute;bottom:16px;left:24px;right:24px;'>
                <div style='font-family:"Playfair Display",Georgia,serif;font-size:1.7rem;color:#f0e6d0;
                    text-shadow:0 2px 10px rgba(0,0,0,0.85);'>{title}</div>
                {sub_html}
            </div>
            <div style='position:absolute;top:10px;right:14px;color:#f0e6d0aa;font-size:0.6rem;
                background:rgba(0,0,0,0.4);padding:2px 8px;border-radius:20px;'>📷 Wikipedia</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='position:relative;width:100%;height:170px;border-radius:16px;overflow:hidden;
            margin-bottom:18px;background:linear-gradient(135deg,#0c1428,#1a2a3a);
            display:flex;align-items:flex-end;border:1px solid rgba(201,168,76,0.25);padding:16px 24px;'>
            <div>
                <div style='font-family:"Playfair Display",Georgia,serif;font-size:1.7rem;color:#f0e6d0;'>{title}</div>
                {sub_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Schematic crustal cross-sections per geological province ──────────────────
# Layers listed bottom-to-top: (label, thickness_km, color, tooltip note)
PROVINCE_CROSS_SECTIONS = {
    "Himalayan Belt": [
        ("Indian Basement", 15, "#4b3621", "Underthrust Indian crystalline crust"),
        ("MCT Zone", 8, "#8b5cf6", "Main Central Thrust — high-grade mylonitic gneiss"),
        ("Lesser Himalaya", 10, "#10b981", "Sedimentary + low-grade metamorphics"),
        ("Tethys Himalaya", 6, "#0ea5e9", "Marine fossiliferous sedimentary sequence"),
        ("High Himalayan Crystallines", 12, "#f59e0b", "Leucogranite + gneiss, exhumed along MCT"),
    ],
    "Indo-Gangetic Plain": [
        ("Indian Shield Basement", 10, "#374151", "Buried continuation of the peninsular craton"),
        ("Siwalik Molasse", 8, "#92400e", "Himalayan-derived sandstone & conglomerate"),
        ("Quaternary Alluvium", 10, "#10b981", "Sand, silt & clay from Ganga–Brahmaputra system"),
    ],
    "Deccan Trap Province": [
        ("Precambrian Basement", 10, "#4b3621", "Underlying Indian shield"),
        ("Lower Basalt Flows", 8, "#7f1d1d", "Earliest flood-basalt eruptions, 66 Ma"),
        ("Middle Flows + Dyke Swarms", 10, "#dc2626", "Feeder dykes, radial swarms"),
        ("Upper Flows (Zeolite-rich)", 6, "#f87171", "Amygdules infilled with zeolite & amethyst"),
    ],
    "Peninsular Shield (Dharwar)": [
        ("Lower Crust", 10, "#1f2937", "Deep Archaean crust, rarely exposed"),
        ("Greenstone Belt", 8, "#8b5cf6", "BIF, gold-bearing schist belts (Kolar, Hutti)"),
        ("Granite–Gneiss Complex", 12, "#a78bfa", "Peninsular Gneissic Complex, 3.3 Ga"),
    ],
    "Eastern Ghats Belt": [
        ("Lower Crustal Granulite", 12, "#0e7490", "High-pressure, high-temperature root zone"),
        ("Charnockite Massif", 8, "#06b6d4", "Named after Job Charnock's Chennai tombstone"),
        ("Khondalite Metasediments", 6, "#67e8f9", "Garnet-sillimanite gneiss, graphite-bearing"),
    ],
    "Aravalli–Delhi Belt": [
        ("Basement Gneiss", 10, "#78350f", "Banded Gneissic Complex"),
        ("Aravalli Metasediments", 8, "#f97316", "Quartzite & schist — Zawar Zn-Pb hosted here"),
        ("Delhi Supergroup", 6, "#fdba74", "Marble (Makrana), phyllite"),
    ],
    "Gondwana Basins": [
        ("Precambrian Basement", 8, "#374151", "Craton floor of the rift basin"),
        ("Lower Gondwana Coal Measures", 10, "#1f2937", "Talchir–Barakar coal seams"),
        ("Upper Gondwana Sandstone/Shale", 6, "#6b7280", "Fluvial redbeds, capped by Deccan basalt in places"),
    ],
    "Andaman–Nicobar Arc": [
        ("Subducting Oceanic Plate", 10, "#0c4a6e", "Indian Plate descending beneath the Sunda Arc"),
        ("Accretionary Wedge", 6, "#0284c7", "Scraped-off forearc sediments (flysch)"),
        ("Ophiolite Sliver", 5, "#38bdf8", "Obducted oceanic crust — chromite host"),
        ("Volcanic Arc", 8, "#dc2626", "Barren Island & Narcondam volcanoes"),
    ],
    "Kutch–Cambay Basin": [
        ("Basement", 8, "#4b3621", "Rifted continental basement"),
        ("Mesozoic Marine Sediments", 8, "#0284c7", "Limestone & shale, passive-margin deposition"),
        ("Cenozoic Evaporites/Limestone", 6, "#93c5fd", "Gypsum, salt — Rann of Kutch"),
    ],
    "Western Ghats": [
        ("Precambrian Gneiss Basement", 10, "#78350f", "Peninsular basement complex"),
        ("Charnockite", 6, "#a78bfa", "Deep crustal granulite exposed by uplift"),
        ("Deccan Basalt Cap", 8, "#dc2626", "Escarpment-forming lava cap in the north"),
    ],
}

def render_province_cross_section(prov_name: str):
    """Schematic (illustrative, not to scale) crustal cross-section for a
    geological province — bottom-to-top stacked layer diagram."""
    layers = PROVINCE_CROSS_SECTIONS.get(prov_name)
    if not layers:
        st.info("Cross-section data not yet available for this province.")
        return
    fig = go.Figure()
    for label, thick, col, note in layers:
        fig.add_trace(go.Bar(
            name=label, x=[thick], y=["Crust"], orientation="h",
            marker_color=col,
            hovertemplate=f"<b>{label}</b><br>~{thick} km<br>{note}<extra></extra>"))
    fig.update_layout(
        barmode="stack", height=270,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0", family="Source Sans 3"),
        legend=dict(orientation="h", y=-0.55, x=0.5, xanchor="center",
                    font=dict(size=9, color="#f0e6d0"), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=5, r=5, t=30, b=90),
        xaxis=dict(title="Relative depth (km, schematic)", gridcolor="rgba(255,255,255,0.05)", color="#8a7d65"),
        yaxis=dict(visible=False),
        title=dict(text="Schematic Crustal Cross-Section (illustrative, not to scale)",
                   font=dict(size=11, color="#c9a84c")))
    st.plotly_chart(fig, use_container_width=True)

# ── State / region centroids for quick "find it on the map" dot markers ──────
STATE_CENTROIDS = {
    "Rajasthan": (26.9, 73.8), "Tamil Nadu": (11.1, 78.6), "Andhra Pradesh": (15.9, 79.7),
    "Maharashtra": (19.6, 75.7), "Karnataka": (15.3, 75.7), "Andaman": (11.7, 92.7),
    "Vindhyan": (24.5, 80.9), "Madhya Pradesh": (23.5, 78.6), "Eastern Ghats": (18.0, 83.5),
    "Himalayan": (30.5, 79.0), "NE India": (26.2, 93.5), "Jharkhand": (23.6, 85.3),
    "Odisha": (20.9, 85.1), "Chhattisgarh": (21.3, 81.9), "WB": (23.0, 87.5),
    "West Bengal": (23.0, 87.5), "Meghalaya": (25.5, 91.4), "Aravalli": (25.0, 73.5),
    "Dharwar": (14.9, 75.5), "Himachal Pradesh": (31.9, 77.2), "Lesser Himalaya": (29.8, 79.5),
    "Chennai": (13.1, 80.2), "Gujarat": (22.5, 71.5), "Kerala": (10.5, 76.3),
    "Telangana": (17.9, 79.3), "Uttarakhand": (30.1, 79.2), "Bihar": (25.6, 85.9),
    "Assam": (26.2, 92.9), "Sikkim": (27.5, 88.5), "Ladakh": (34.2, 77.6), "Kashmir": (34.1, 74.8),
    "Deccan": (19.9, 75.3), "Gondwana": (22.0, 83.0), "Cambay": (22.3, 72.6), "Kutch": (23.7, 69.9),
    "Andaman-Nicobar": (10.5, 92.8), "Nicobar": (7.5, 93.7), "Sunda Arc": (10.0, 95.0),
}

def find_location_for_text(text: str):
    """Scan a free-text location description and return (lat, lon, matched_label)
    for the first recognised Indian state/region, or None."""
    for name, (lat, lon) in STATE_CENTROIDS.items():
        if name.lower() in text.lower():
            return (lat, lon, name)
    return None

def render_location_dot_map(location_text: str, item_name: str, height: int = 220):
    """Small India outline map with a single dot marking where an item
    (rock, mineral, etc.) is primarily found, based on parsing free text."""
    match = find_location_for_text(location_text)
    if not match:
        st.caption(f"📍 Location: {location_text}")
        return
    lat, lon, label = match
    fig = go.Figure(go.Scattergeo(
        lat=[lat], lon=[lon], mode="markers+text",
        marker=dict(size=14, color="#dc2626", line=dict(width=2, color="#f0e6d0")),
        text=[label], textposition="top center",
        textfont=dict(color="#f0e6d0", size=10),
        hovertemplate=f"<b>{item_name}</b><br>{label}<extra></extra>"))
    fig.update_geos(scope="asia", lonaxis_range=[68, 98], lataxis_range=[6, 38],
        showland=True, landcolor="#1a2233", showcountries=True, countrycolor="#3a4358",
        showcoastlines=True, coastlinecolor="#3a4358", bgcolor="rgba(0,0,0,0)")
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def get_quiz_difficulty(q: dict) -> str:
    """Classify a quiz question into Basic / Intermediate / Advanced.
    Deterministic (same question always gets the same difficulty) — combines
    a stable hash with explanation length/technicality as a rough proxy."""
    import hashlib as _hl
    text = q["q"] + q["explain"]
    technical_markers = ["Ma", "Ga", "km/s", "°", "MPa", "atm", "formula", "equation", "±"]
    tech_score = sum(1 for m in technical_markers if m in text)
    h = int(_hl.md5(q["q"].encode()).hexdigest(), 16) % 3
    if tech_score >= 2:
        return "Advanced"
    elif tech_score == 1 or h == 2:
        return "Intermediate"
    else:
        return "Basic" if h == 0 else "Intermediate"

def make_folium_map(center_lat=20.5, center_lon=78.9, zoom=4, height=520):
    """Create a dark-styled Folium map with multi-tile switcher."""
    if not FOLIUM_AVAILABLE:
        return None
    m = folium.Map(
        location=[center_lat, center_lon], zoom_start=zoom,
        tiles=None, control_scale=True,
    )
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="© CartoDB", name="Dark (Default)", max_zoom=19,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="© Esri World Imagery", name="🛰️ Satellite",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="© Esri World Topo", name="🏔️ Terrain",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="© OpenStreetMap", name="🗺️ Street",
    ).add_to(m)
    # NOTE: LayerControl is intentionally NOT added here. It must be added
    # AFTER any FeatureGroup overlays (e.g. add_gsi_layer) are added to the
    # map, otherwise Folium's control never registers those overlays and
    # they silently fail to render. See render_folium(), which adds it last.
    return m

def render_folium(m, height=520):
    """Render Folium map inside Streamlit. Adds the LayerControl here (not in
    make_folium_map) so it's guaranteed to see every overlay/FeatureGroup
    the caller has added in between — otherwise overlays added after an
    early LayerControl never show up (this was the GSI markers bug)."""
    if m is None:
        st.info("🗺️ Folium maps load on Streamlit Cloud. Add `folium` to requirements.txt to enable.")
        return
    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    import streamlit.components.v1 as components
    components.html(m._repr_html_(), height=height, scrolling=False)

# ── GSI Mineral Deposit Locations ──────────────────────────────────────────────
GSI_DEPOSITS = [
    (23.0, 85.3, "Iron Ore",  "Jharkhand",    "Singhbhum Iron Belt",      "High-grade Hematite BIF"),
    (20.8, 84.1, "Iron Ore",  "Odisha",        "Bailadila Range",           "High-grade Hematite"),
    (22.1, 85.8, "Iron Ore",  "Odisha",        "Barbil-Joda Belt",          "Banded Iron Formation"),
    (23.8, 85.3, "Coal",      "Jharkhand",    "Jharia Coalfield",          "Prime Coking Coal"),
    (23.7, 87.5, "Coal",      "West Bengal",  "Raniganj Coalfield",        "Bituminous — Gondwana"),
    (21.8, 83.5, "Coal",      "Chhattisgarh","Korea-Rewa Coalfields",     "Bituminous Coal"),
    (17.5, 79.2, "Coal",      "Telangana",    "Singareni Coalfields",      "Gondwana Bituminous"),
    (24.4, 73.7, "Zinc-Lead", "Rajasthan",    "Zawar Mines, Udaipur",      "World's largest Zn smelter"),
    (25.7, 74.0, "Zinc-Lead", "Rajasthan",    "Rampura-Agucha",            "World's largest Zn mine"),
    (24.9, 74.6, "Copper",    "Rajasthan",    "Khetri Copper Belt",        "Precambrian volcanogenic"),
    (23.8, 86.2, "Copper",    "Jharkhand",    "Singhbhum Copper Belt",     "Archaean greenstone"),
    (12.9, 78.3, "Gold",      "Karnataka",    "Kolar Gold Field",          "Archaean — 3.8 km deep"),
    (15.4, 76.5, "Gold",      "Karnataka",    "Hutti Gold Mine",           "Archaean BIF-hosted"),
    (20.5, 85.5, "Chromite",  "Odisha",        "Sukinda Valley",            ">90% India chromite"),
    (24.6, 80.5, "Diamond",   "Madhya Pradesh","Majhgawan Kimberlite",     "Primary diamond source"),
    (20.3, 85.8, "Bauxite",   "Odisha",        "Panchpatmali",              "India's largest bauxite"),
    (23.5, 85.5, "Bauxite",   "Jharkhand",    "Lohardaga Plateau",         "Laterite-capped bauxite"),
    (9.5,  76.5, "REE/Thorium","Kerala",       "Chavara Beach Placer",      "Monazite, ilmenite"),
    (13.5, 80.3, "REE/Thorium","Tamil Nadu",   "Manavalakurichi Placer",   "Beach heavy minerals"),
    (26.7, 73.0, "Limestone",  "Rajasthan",    "Jodhpur Area",              "Vindhyan limestone"),
]

DEPOSIT_COLORS = {
    "Iron Ore": "#dc2626", "Coal": "#374151", "Zinc-Lead": "#6b7280",
    "Copper": "#b45309", "Gold": "#f59e0b", "Chromite": "#7c3aed",
    "Diamond": "#e0f2fe", "Bauxite": "#92400e", "REE/Thorium": "#10b981",
    "Limestone": "#e5e7eb",
}

def add_gsi_layer(m, selected_minerals=None):
    """Add GSI mineral deposit markers to a Folium map."""
    if not FOLIUM_AVAILABLE or m is None:
        return m
    layer = folium.FeatureGroup(name="💎 GSI Mineral Deposits", show=True)
    for lat, lon, mineral, state, name, grade in GSI_DEPOSITS:
        if selected_minerals and mineral not in selected_minerals:
            continue
        col = DEPOSIT_COLORS.get(mineral, "#f59e0b")
        folium.CircleMarker(
            location=[lat, lon], radius=8, color=col, fill=True,
            fill_color=col, fill_opacity=0.8, weight=2,
            tooltip=f"<b>{name}</b><br>{mineral} · {state}",
            popup=folium.Popup(
                f"<b style='color:{col};'>{name}</b><br>"
                f"<b>Mineral:</b> {mineral}<br>"
                f"<b>State:</b> {state}<br>"
                f"<b>Grade/Notes:</b> {grade}", max_width=220)
        ).add_to(layer)
    layer.add_to(m)
    return m

# ── Gemini Streaming ───────────────────────────────────────────────────────────
def gemini_stream(user_q: str, api_key: str, history=None):
    """Generator yielding Gemini tokens for st.write_stream().
    `history` (optional) is a list of {"role": "user"/"ai", "text": ...} dicts from
    earlier turns in the session — passing it lets follow-up questions like
    "tell me more about that" resolve correctly."""
    import json as _json
    try:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"gemini-3.5-flash:streamGenerateContent?key={api_key}&alt=sse")
        system_instruction = (
            "You are GeoSphere AI, an expert Earth Science assistant specialising in Indian geology "
            "(Himalayas, Deccan Traps, Indian rivers, minerals, soils, seismic zones, BHU NEP syllabus). "
            "Answer clearly in 3-6 sentences with specific facts, mineral names, formation ages, and Indian examples. "
            "If unrelated to geology/Earth science, gently redirect back. Use the prior conversation turns "
            "for context on follow-up questions (e.g. 'tell me more about that')."
        )
        contents = []
        for turn in (history or [])[-8:]:  # last 8 turns is plenty of context
            contents.append({"role": "user" if turn["role"] == "user" else "model",
                              "parts": [{"text": turn["text"]}]})
        contents.append({"role": "user", "parts": [{"text": user_q}]})
        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {"maxOutputTokens": 2048, "thinking_level": "minimal"},
        }
        with requests.post(url, json=payload, timeout=30, stream=True,
                           headers={"Content-Type": "application/json"}) as r:
            if r.status_code != 200:
                if r.status_code in (400, 401, 403):
                    yield f"[Gemini error {r.status_code} — your GEMINI_API_KEY in Streamlit secrets looks missing or invalid. Check it at aistudio.google.com/apikey]"
                elif r.status_code == 404:
                    yield f"[Gemini error 404 — the model name is no longer available. This is a bug on our end, not your API key — please report it.]"
                elif r.status_code == 429:
                    yield f"[Gemini error 429 — rate limit or free-tier daily quota reached. This is not a key problem — wait a bit and try again, or check quota at aistudio.google.com]"
                else:
                    yield f"[Gemini error {r.status_code} — temporary issue on Google's side, please try again shortly]"
                return
            for line in r.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        try:
                            chunk = _json.loads(line[6:])
                            parts = (chunk.get("candidates", [{}])[0]
                                     .get("content", {}).get("parts", []))
                            for p in parts:
                                if "text" in p:
                                    yield p["text"]
                        except Exception:
                            continue
    except Exception as e:
        yield f"[Connection error: {e}]"
# ═══════════════════════════════════════════════════════
URDU_NAV_LABELS = {
    "🌌 Mission Control":      "🌌 Markaz-e-Zameen",
    "🗺️ Geological Map":       "🗺️ Zameen ka Naqsha",
    "🌋 Plate Tectonics":      "🌋 Sarhadon ki Larzish",
    "💎 Mineral Explorer":     "💎 Jawahar ki Talaash",
    "🌍 Earthquake Dashboard": "🌍 Zalzalon ka Hisaab",
    "📅 Geological Time Scale":"📅 Waqt ka Silsila",
    "🧪 Soil Explorer":        "🧪 Khaak ki Kahani",
    "🪙 Economic Geology":     "🪙 Zameen ka Khazana",
    "🪨 Rock Explorer":        "🪨 Pathron ka Jahan",
    "🌋 Volcano Explorer":     "🌋 Aatishfishan ka Raaz",
    "🧭 Structural Tools":     "🧭 Tabdeeli ke Nishaan",
    "🌿 Geography Explorer":   "🌿 Sarzameen ki Sair",
    "🌊 Watershed Explorer":   "🌊 Dariyaon ka Safar",
    "🌊 Oceanography":         "🌊 Samundar ki Baatein",
    "🔬 Thin Section Gallery": "🔬 Baareek Nazar",
    "📚 Semester Notes":       "📚 Ilm ka Safar",
    "🧠 Geo Quiz":             "🧠 Imtihaan-e-Zameen",
    "🃏 Flashcards":           "🃏 Yaadon ke Waraq",
    "🤖 AI Assistant":         "🤖 Hamnava Rehnuma",
    "📓 Field Diary":          "📓 Safar Nama",
    "🥚 About & Archive":      "🥚 Hamari Dastaan",
}

def urdu_label(text: str) -> str:
    """Return the Roman-Urdu-styled label for a nav item when achievement mode
    is active — real Urdu vocabulary, written in the English alphabet
    (Hinglish/Roman-Urdu), never actual Urdu script."""
    if st.session_state.get("rare_mode") and text in URDU_NAV_LABELS:
        return URDU_NAV_LABELS[text]
    return text

# ═══════════════════════════════════════════════════════
#  SESSION STATE INIT
# ═══════════════════════════════════════════════════════
defaults = {
    "loading_done":     False,
    "logo_clicks":      0,
    "about_visited":    False,
    "rare_mode":        False,
    "rare_timer":       0,
    "quiz_idx":         0,
    "quiz_score":       0,
    "quiz_answered":    False,
    "quiz_chosen":      None,
    "quiz_order":       None,
    "fc_idx":           0,
    "fc_show":          False,
    "fc_mastered":      [],
    "chat_history":     [],
    "easter_count":     0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ═══════════════════════════════════════════════════════
#  DATE CHECK — birthday mode
# ═══════════════════════════════════════════════════════
today = datetime.date.today()
IS_BIRTHDAY = (today.month == 9 and today.day == 8)

# ═══════════════════════════════════════════════════════
#  RARE MODE — full screen theme takeover
# ═══════════════════════════════════════════════════════
RARE_LINES = {
    "GeoSphere India":        "Kuch kahaniyan sirf yaad mein rehti hain.",
    "Mission Control":        "Kuch larzishen sirf zameen mein nahi hoti.",
    "Geological Map":         "Har manzil ka pehla nishaan ek naqsha nahi hota.",
    "Plate Tectonics":        "Takkar mein bhi ek nizam hota hai.",
    "Rock Explorer":          "Jo gehra hota hai, wahi tikta hai.",
    "Mineral Explorer":       "Jo gehra hota hai, wahi qeemti hota hai.",
    "Earthquake Dashboard":   "Har toofan ek khamoshi se shuru hota hai.",
    "Geological Time Scale":  "Waqt ka koi gawah nahi hota, phir bhi woh rehta hai.",
    "Volcano Explorer":       "Andar ki aag hamesha bahar nahi aati.",
    "Geography Explorer":     "Har zameen apni kahani khud likhti hai.",
    "Soil Explorer":          "Mitti mein woh raaz hain jo kitabon mein nahi.",
    "Watershed Explorer":     "Dariya bhi apna rasta khud chunte hain.",
    "Economic Geology":       "Jo zameen ke andar hai, wahi duniya chalata hai.",
    "Oceanography":           "Gehra sagar bhi khamosh rehta hai.",
    "Thin Section Gallery":   "Ek chote tukde mein poori duniya hoti hai.",
    "Semester Notes":         "Har kitaab apna raasta khud chunti hai.",
    "Geo Quiz":               "Har sawaal ka jawab ilm se pehle sabr maangta hai.",
    "Flashcards":             "Ek baar jo samajh aaye, woh kabhi nahi bhoolta.",
    "AI Assistant":           "Kuch sawal sirf poochhe jaate hain, jawab nahi maange.",
    "Field Diary":            "Kuch alfaaz likhe nahi jaate, phir bhi padhe jaate hain.",
    "Easter Eggs":            "Jo dhundha woh mil gaya. Baaki sab naqsha tha.",
}

# ═══════════════════════════════════════════════════════
#  GLOBAL CSS
# ═══════════════════════════════════════════════════════
RARE_CSS = """
<style>
/* ── ACHIEVEMENT MODE — full blue takeover ── */
.stApp {
    background: linear-gradient(135deg,#00020f 0%,#000d2e 45%,#000818 75%,#00020f 100%) !important;
}
.hero-title {
    background: linear-gradient(90deg,#3a7bd5,#6ea8fe,#a8c8ff) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 2.4rem !important;
    letter-spacing: 3px !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#00020f 0%,#000d2e 100%) !important;
    border-right: 1px solid rgba(58,123,213,0.35) !important;
}
.glass-card {
    background: rgba(0,15,50,0.8) !important;
    border-color: rgba(58,123,213,0.35) !important;
    box-shadow: 0 0 35px rgba(58,123,213,0.18) !important;
}
.section-heading {
    color: #6ea8fe !important;
    border-left-color: #6ea8fe !important;
    font-family: 'Noto Nastaliq Urdu', 'Playfair Display', Georgia, serif !important;
    font-style: normal !important;
    letter-spacing: 0.5px !important;
}
[data-testid="stSidebar"] [data-baseweb="radio"] label,
[data-testid="stSidebar"] [data-baseweb="radio"] div,
.stButton > button {
    font-family: 'Noto Nastaliq Urdu', 'Source Sans 3', sans-serif !important;
}
.mineral-card { border-color: rgba(58,123,213,0.25) !important; }
.metric-card  { border-color: rgba(58,123,213,0.2) !important; }
.metric-value { color: #6ea8fe !important; }
.metric-label { color: #6a85b8 !important; }
.stApp, .stApp p, .stApp span, .stApp div { color: #c8d8f5; }
.mineral-name, .book-title { color: #6ea8fe !important; }
.mineral-desc, .book-desc, .mineral-formula { color: #8aa3cc !important; }
.float-badge {
    background: rgba(58,123,213,0.12) !important;
    border-color: rgba(58,123,213,0.4) !important;
    color: #6ea8fe !important;
}
.hero-badge {
    background: rgba(58,123,213,0.1) !important;
    border-color: rgba(58,123,213,0.4) !important;
    color: #6ea8fe !important;
}
.hero-sub { color: #6a85b8 !important; }
::-webkit-scrollbar-thumb { background: #3a7bd5 !important; }
::-webkit-scrollbar-track { background: #00020f !important; }
.stButton > button {
    background: linear-gradient(135deg,rgba(58,123,213,0.18),rgba(0,13,46,0.9)) !important;
    color: #6ea8fe !important;
    border-color: rgba(58,123,213,0.45) !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg,rgba(58,123,213,0.32),rgba(0,13,46,0.9)) !important;
    box-shadow: 0 0 18px rgba(58,123,213,0.4) !important;
}
.stTextInput input, .stTextArea textarea {
    background: rgba(0,8,30,0.9) !important;
    border-color: rgba(58,123,213,0.35) !important;
    color: #c8d8f5 !important;
}
div[data-baseweb="select"] > div {
    background: rgba(0,8,30,0.9) !important;
    border-color: rgba(58,123,213,0.35) !important;
    color: #c8d8f5 !important;
}
.stTabs [aria-selected="true"] {
    color: #6ea8fe !important;
    border-bottom-color: #6ea8fe !important;
}
.diary-card, .flashcard-box, .chat-bubble-ai, .chat-bubble-user {
    background: rgba(0,15,50,0.85) !important;
    border-color: rgba(58,123,213,0.3) !important;
}
.chat-label-user, .chat-label-ai { color: #6ea8fe !important; }
.dial-val { color: #6ea8fe !important; }
</style>

<div id="rare-stars"></div>
<div id="emoji-rain-a"></div>
<div id="emoji-rain-b"></div>
<div id="emoji-rain-c"></div>

<style>
/* Starfield */
#rare-stars {
    position:fixed;top:0;left:0;width:100vw;height:100vh;
    pointer-events:none;z-index:1;overflow:hidden;
}
#rare-stars::before {
    content:'';display:block;width:100%;height:100%;
    background-image:
        radial-gradient(1.5px 1.5px at 8%  12%, rgba(180,210,255,0.9) 0%,transparent 100%),
        radial-gradient(1px   1px   at 22%  35%, rgba(140,185,255,0.7) 0%,transparent 100%),
        radial-gradient(2px   2px   at 38%  8%,  rgba(200,225,255,0.8) 0%,transparent 100%),
        radial-gradient(1px   1px   at 51%  52%, rgba(160,200,255,0.6) 0%,transparent 100%),
        radial-gradient(1.5px 1.5px at 67%  28%, rgba(180,210,255,0.9) 0%,transparent 100%),
        radial-gradient(1px   1px   at 79%  71%, rgba(140,185,255,0.7) 0%,transparent 100%),
        radial-gradient(2px   2px   at 91%  15%, rgba(200,225,255,0.85) 0%,transparent 100%),
        radial-gradient(1px   1px   at 14%  68%, rgba(160,200,255,0.6) 0%,transparent 100%),
        radial-gradient(1.5px 1.5px at 33%  82%, rgba(180,210,255,0.8) 0%,transparent 100%),
        radial-gradient(1px   1px   at 58%  91%, rgba(140,185,255,0.7) 0%,transparent 100%),
        radial-gradient(2px   2px   at 72%  44%, rgba(200,225,255,0.75) 0%,transparent 100%),
        radial-gradient(1px   1px   at 85%  60%, rgba(160,200,255,0.65) 0%,transparent 100%),
        radial-gradient(1.5px 1.5px at 4%   88%, rgba(180,210,255,0.8) 0%,transparent 100%),
        radial-gradient(1px   1px   at 46%  22%, rgba(140,185,255,0.6) 0%,transparent 100%),
        radial-gradient(2px   2px   at 96%  78%, rgba(200,225,255,0.7) 0%,transparent 100%);
    animation: twinkle-stars 4s ease-in-out infinite alternate;
}
#rare-stars::after {
    content:'';display:block;position:absolute;top:0;left:0;width:100%;height:100%;
    background-image:
        radial-gradient(1px 1px at 18% 44%, rgba(100,160,255,0.5) 0%,transparent 100%),
        radial-gradient(1px 1px at 42% 77%, rgba(120,175,255,0.4) 0%,transparent 100%),
        radial-gradient(1px 1px at 63% 33%, rgba(100,160,255,0.5) 0%,transparent 100%),
        radial-gradient(1px 1px at 88% 55%, rgba(120,175,255,0.4) 0%,transparent 100%),
        radial-gradient(1px 1px at 27% 91%, rgba(100,160,255,0.45) 0%,transparent 100%);
    animation: twinkle-stars 4s ease-in-out infinite alternate-reverse;
}
@keyframes twinkle-stars { 0%{opacity:0.3} 50%{opacity:0.9} 100%{opacity:0.5} }

/* Emoji rain — independent falling streams spread across the screen */
.emoji-drop {
    position:fixed;top:-40px;
    pointer-events:none !important;z-index:50;
    font-size:1.3rem;opacity:0;
}
.ed1  { left:4%;  animation: fall-drop 4.2s linear 0.0s infinite; }
.ed2  { left:12%; animation: fall-drop 3.6s linear 0.6s infinite; }
.ed3  { left:20%; animation: fall-drop 4.8s linear 1.2s infinite; }
.ed4  { left:29%; animation: fall-drop 3.9s linear 0.3s infinite; }
.ed5  { left:37%; animation: fall-drop 4.4s linear 1.8s infinite; }
.ed6  { left:46%; animation: fall-drop 3.7s linear 0.9s infinite; }
.ed7  { left:55%; animation: fall-drop 4.6s linear 2.4s infinite; }
.ed8  { left:63%; animation: fall-drop 4.0s linear 0.4s infinite; }
.ed9  { left:71%; animation: fall-drop 3.8s linear 1.5s infinite; }
.ed10 { left:80%; animation: fall-drop 4.5s linear 2.1s infinite; }
.ed11 { left:88%; animation: fall-drop 4.1s linear 0.7s infinite; }
.ed12 { left:95%; animation: fall-drop 3.5s linear 1.1s infinite; }

@keyframes fall-drop {
    0%   { opacity:0; transform:translateY(-40px); }
    8%   { opacity:0.7; }
    92%  { opacity:0.7; }
    100% { opacity:0; transform:translateY(105vh); }
}
</style>""" + "".join(
    f'<div class="emoji-drop ed{i+1}">{e}</div>'
    for i, e in enumerate(["✨","⭐","📖","💙","🌌","✨","⭐","🌌","💙","📖","✨","🌌"])
) + """
<style>
"""

NORMAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;0,900;1,400;1,600&family=Source+Sans+3:wght@300;400;500;600;700&family=Orbitron:wght@400;700;900&family=Noto+Nastaliq+Urdu:wght@400;700&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500;1,600&family=Spectral:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

:root {
    --bg-deep:    #070b18;
    --bg-mid:     #0c1428;
    --bg-card:    rgba(12,20,45,0.88);
    --navy:       #0a1232;
    --navy-light: #112050;
    --gold:       #c9a84c;
    --gold-light: #e8c96a;
    --gold-dim:   rgba(201,168,76,0.18);
    --accent1:    #c9a84c;
    --accent2:    #8b6914;
    --accent3:    #e8c96a;
    --accent4:    #a8d5a2;
    --text-main:  #f0e6d0;
    --text-dim:   #8a7d65;
    --glow:       0 0 24px rgba(201,168,76,0.22);
    --serif:      'Playfair Display', Georgia, serif;
    --sans:       'Source Sans 3', system-ui, sans-serif;
    --quote:      'Cormorant Garamond', 'Playfair Display', Georgia, serif;
    --reading:    'Spectral', Georgia, serif;
}

.stApp {
    background: linear-gradient(160deg,#070b18 0%,#0c1428 35%,#0a1232 65%,#060916 100%) !important;
    font-family: var(--sans);
    color: var(--text-main);
    font-size: 16px;
}

footer { visibility: hidden; }
/* Keep the native Streamlit header visible (Share/GitHub/Stop/sidebar-collapse controls)
   but let its background stay transparent so it blends with our theme. */
header[data-testid="stHeader"] { background: transparent !important; visibility: visible !important; }
.block-container { padding-top: 1rem !important; max-width: 1420px; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--gold); border-radius: 3px; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#05091a 0%,#0a1232 100%) !important;
    border-right: 1px solid rgba(201,168,76,0.22);
}
[data-testid="stSidebar"] * { color: var(--text-main) !important; }

.glass-card {
    background: var(--bg-card);
    border: 1px solid rgba(201,168,76,0.2);
    border-radius: 14px;
    padding: 22px;
    backdrop-filter: blur(14px);
    box-shadow: var(--glow), inset 0 1px 0 rgba(201,168,76,0.07);
    margin-bottom: 14px;
    transition: transform 0.22s cubic-bezier(0.34,1.56,0.64,1),
                border-color 0.2s ease,
                box-shadow 0.2s ease;
}
.glass-card:hover {
    transform: translateY(-3px);
    border-color: rgba(201,168,76,0.42);
    box-shadow: 0 8px 32px rgba(201,168,76,0.22),
                inset 0 1px 0 rgba(201,168,76,0.12);
}

/* Mineral + rock card hover lift */
.mineral-card {
    transition: transform 0.2s cubic-bezier(0.34,1.56,0.64,1),
                border-color 0.18s ease, box-shadow 0.18s ease;
}
.mineral-card:hover {
    transform: translateY(-4px) scale(1.012);
    box-shadow: 0 12px 36px rgba(0,212,255,0.18);
    border-color: rgba(0,212,255,0.35) !important;
}

/* Metric card hover */
.metric-card {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(201,168,76,0.18);
}

/* Float badge hover */
.float-badge {
    transition: all 0.18s ease;
}
.float-badge:hover {
    background: rgba(201,168,76,0.22) !important;
    transform: scale(1.08);
    cursor: default;
}

/* Button micro-interactions — more spring */
.stButton > button {
    transition: all 0.2s cubic-bezier(0.34,1.56,0.64,1) !important;
}
.stButton > button:active {
    transform: scale(0.96) !important;
}

/* Section heading reveal animation */
.section-heading {
    animation: section-reveal 0.5s ease both;
}
@keyframes section-reveal {
    from { opacity:0; transform:translateX(-12px); }
    to   { opacity:1; transform:translateX(0); }
}

/* Skeleton loader for heavy sections */
.skeleton {
    background: linear-gradient(90deg,
        rgba(201,168,76,0.04) 0%,
        rgba(201,168,76,0.1) 50%,
        rgba(201,168,76,0.04) 100%);
    background-size: 200% 100%;
    animation: shimmer 1.5s linear infinite;
    border-radius: 8px;
    height: 180px; width: 100%;
}

/* Page content fade-in — smooth, intentional transition */
.stMainBlockContainer > div > div {
    animation: page-fade 0.42s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes page-fade {
    from { opacity:0; transform:translateY(14px); filter:blur(2px); }
    to   { opacity:1; transform:translateY(0);    filter:blur(0); }
}
/* Section headings animate in from left */
.section-heading {
    animation: section-reveal 0.5s cubic-bezier(0.16,1,0.3,1) both !important;
}
/* Stagger child elements for depth */
.stMainBlockContainer > div > div > div:nth-child(1) { animation-delay:0.05s; }
.stMainBlockContainer > div > div > div:nth-child(2) { animation-delay:0.10s; }
.stMainBlockContainer > div > div > div:nth-child(3) { animation-delay:0.15s; }
.stMainBlockContainer > div > div > div:nth-child(4) { animation-delay:0.20s; }

/* Tab hover effects */
.stTabs [role="tab"] {
    transition: color 0.18s ease, border-bottom-color 0.18s ease !important;
}
.stTabs [role="tab"]:hover {
    color: var(--gold) !important;
}

/* Image hover zoom in cards */
.stImage img {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    border-radius: 8px;
}
.stImage img:hover {
    transform: scale(1.03);
    box-shadow: 0 8px 28px rgba(0,0,0,0.4);
}

/* Selectbox/input focus glow */
.stTextInput input:focus,
.stSelectbox [data-baseweb="select"]:focus-within {
    box-shadow: 0 0 0 2px rgba(201,168,76,0.35) !important;
    border-color: rgba(201,168,76,0.5) !important;
}

.hero-banner {
    background: linear-gradient(135deg,rgba(201,168,76,0.06) 0%,rgba(12,20,45,0.9) 50%,rgba(201,168,76,0.04) 100%);
    border: 1px solid rgba(201,168,76,0.3);
    border-radius: 18px;
    padding: 42px 36px;
    text-align: center;
    position: relative;
    overflow: hidden;
    margin-bottom: 22px;
}
.hero-banner::before {
    content:'';position:absolute;inset:0;
    background: radial-gradient(ellipse at 50% -10%,rgba(201,168,76,0.12) 0%,transparent 65%);
    pointer-events:none;
}
.hero-title {
    font-family: var(--serif);
    font-size: 3rem; font-weight: 900;
    background: linear-gradient(90deg,#c9a84c,#f0d878,#c9a84c);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    margin:0; letter-spacing:3px;
}
.hero-sub  {
    color: var(--text-dim); font-size:0.95rem; margin-top:10px;
    letter-spacing:3px; font-family:var(--sans); font-weight:300;
}
.hero-badge {
    display:inline-block;
    background:rgba(201,168,76,0.1); border:1px solid rgba(201,168,76,0.38);
    color:var(--gold); font-size:0.72rem; padding:5px 16px; border-radius:20px;
    letter-spacing:2px; margin-top:14px; font-family:var(--sans); font-weight:500;
}

.section-heading {
    font-family: var(--serif);
    font-size: 1.15rem; font-weight:700; color:var(--gold);
    letter-spacing:1px; font-style:italic;
    border-left:3px solid var(--gold); padding-left:14px; margin:28px 0 16px 0;
}

.metric-card {
    background: linear-gradient(135deg,rgba(201,168,76,0.06),rgba(12,20,45,0.9));
    border: 1px solid rgba(201,168,76,0.18); border-radius:14px;
    padding:20px 16px; text-align:center; transition:all 0.3s; margin-bottom:10px;
}
.metric-card:hover {
    border-color:rgba(201,168,76,0.5); box-shadow:0 0 24px rgba(201,168,76,0.2);
    transform:translateY(-3px);
}
.metric-icon  { font-size:1.9rem; margin-bottom:6px; }
.metric-value {
    font-family:var(--serif); font-size:1.5rem; font-weight:700; color:var(--gold);
}
.metric-label {
    font-size:0.72rem; color:var(--text-dim); letter-spacing:1.5px;
    text-transform:uppercase; margin-top:4px; font-family:var(--sans);
}
.metric-delta { font-size:0.78rem; color:var(--accent4); margin-top:2px; }

.mineral-card {
    background:rgba(10,18,42,0.88); border:1px solid rgba(201,168,76,0.14);
    border-radius:12px; padding:18px; transition:all 0.3s; margin-bottom:10px;
}
.mineral-card:hover { border-color:rgba(201,168,76,0.45); box-shadow:0 0 18px rgba(201,168,76,0.14); }
.mineral-name    { font-family:var(--serif); font-size:1rem; font-weight:700; color:var(--gold); margin-bottom:3px; }
.mineral-formula { font-size:0.85rem; color:var(--gold-light); font-style:italic; margin-bottom:8px; font-family:var(--serif); }
.mineral-desc    { font-size:0.88rem; color:var(--text-dim); line-height:1.65; font-family:var(--sans); }

.book-card {
    background:rgba(10,18,42,0.88); border:1px solid rgba(201,168,76,0.18);
    border-radius:12px; padding:16px; transition:all 0.3s; margin-bottom:10px;
}
.book-card:hover { border-color:rgba(201,168,76,0.45); }
.book-title  { font-weight:700; font-family:var(--serif); color:var(--text-main); font-size:1rem; margin-bottom:4px; }
.book-author { font-size:0.82rem; color:var(--gold); margin-bottom:5px; font-style:italic; }
.book-desc   { font-size:0.82rem; color:var(--text-dim); line-height:1.6; }

.quiz-question { font-size:1.1rem; color:var(--text-main); font-weight:600; margin-bottom:14px; line-height:1.6; font-family:var(--serif); }
.quiz-correct  { color:var(--accent4); font-weight:700; padding:5px 0; font-size:0.95rem; }
.quiz-wrong    { color:#e07070; font-weight:700; padding:5px 0; font-size:0.95rem; }

.float-badge {
    display:inline-block;
    background:rgba(201,168,76,0.12); border:1px solid rgba(201,168,76,0.35);
    border-radius:20px; padding:5px 14px; font-size:0.72rem;
    color:var(--gold); letter-spacing:1.5px; margin:3px;
    animation:pulse-badge 2.5s infinite;
}
@keyframes pulse-badge {
    0%,100%{box-shadow:0 0 0 rgba(201,168,76,0);}
    50%{box-shadow:0 0 10px rgba(201,168,76,0.35);}
}

.dial-wrap   { position:relative;width:130px;height:130px;margin:auto; }
.dial-wrap svg { width:100%;height:100%; }
.dial-center { position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center; }
.dial-val { font-family:var(--serif);font-size:1.25rem;color:var(--gold);font-weight:700; }
.dial-lbl { font-size:0.62rem;color:var(--text-dim);letter-spacing:1px; }

.diary-card {
    background:linear-gradient(135deg,rgba(201,168,76,0.07),rgba(12,20,45,0.9));
    border:1px solid rgba(201,168,76,0.25); border-radius:16px; padding:24px;
    position:relative; overflow:hidden; margin-bottom:14px;
}
.diary-card::after {
    content:'📖'; position:absolute; right:16px; top:50%; transform:translateY(-50%);
    font-size:2.5rem; opacity:0.08;
}
.diary-date { font-family:var(--quote); font-size:0.82rem; color:var(--gold); letter-spacing:1px; font-style:italic; }
.diary-text { color:var(--text-main); font-size:1rem; line-height:1.85; margin-top:10px; font-family:var(--reading); }

.chat-bubble-user {
    background:linear-gradient(135deg,rgba(201,168,76,0.1),rgba(12,20,45,0.8));
    border:1px solid rgba(201,168,76,0.22); border-radius:14px 14px 4px 14px;
    padding:14px 18px; margin:6px 0 14px 40px; color:var(--text-main); font-size:0.95rem; line-height:1.6;
}
.chat-bubble-ai {
    background:rgba(10,18,42,0.9); border:1px solid rgba(201,168,76,0.18);
    border-radius:14px 14px 14px 4px;
    padding:14px 18px; margin:6px 40px 14px 0; color:var(--text-main); font-size:0.95rem; line-height:1.65;
}
.chat-label-user { font-size:0.68rem; color:var(--gold); letter-spacing:2px; text-align:right; margin-right:6px; }
.chat-label-ai   { font-size:0.68rem; color:var(--gold); letter-spacing:2px; margin-left:6px; }

.flashcard-box {
    background:linear-gradient(135deg,rgba(201,168,76,0.07),rgba(12,20,45,0.9));
    border:1px solid rgba(201,168,76,0.22); border-radius:16px;
    padding:32px 24px; text-align:center; min-height:140px;
    display:flex; flex-direction:column; justify-content:center; margin-bottom:12px;
}
.flashcard-q { font-size:1.1rem; color:var(--text-main); font-weight:600; margin-bottom:12px; font-family:var(--serif); }
.flashcard-a { font-size:0.95rem; color:var(--accent4); font-style:italic; font-family:var(--serif); }

.shimmer-bar {
    height:1px;
    background: linear-gradient(90deg,transparent,var(--gold),#f0d878,var(--gold),transparent);
    border-radius:2px; margin-bottom:18px;
    animation:shimmer 3s infinite linear;
    background-size:200% 100%;
}
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

.rare-text {
    font-family:var(--quote); font-size:1.15rem; color:#6ea8fe;
    font-style:italic; text-align:center; margin-top:8px; letter-spacing:0.5px; opacity:0.9;
}

[data-testid="stSidebar"] .stButton:first-of-type > button {
    border-radius: 50% !important;
    width: 56px !important; height: 56px !important;
    min-width: 56px !important; padding: 0 !important;
    font-size: 1.7rem !important;
    background: radial-gradient(circle at 35% 30%, rgba(232,201,106,0.25), rgba(201,168,76,0.08)) !important;
    border: 1.5px solid rgba(201,168,76,0.45) !important;
    box-shadow: 0 0 0 rgba(201,168,76,0) !important;
    transition: all 0.25s ease !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
}
[data-testid="stSidebar"] .stButton:first-of-type > button:hover {
    transform: scale(1.08) !important;
    box-shadow: 0 0 20px rgba(201,168,76,0.45) !important;
    border-color: rgba(232,201,106,0.7) !important;
}
.panda-overlay {
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    display: flex; align-items: center; justify-content: center;
    background: rgba(0,0,0,0.65); z-index: 999998;
    pointer-events: none;
    animation: panda-fade-out 2.6s ease-in-out forwards;
}
.panda-content {
    text-align: center;
    animation: panda-shake-big 0.5s ease-in-out 3;
}
.panda-photo {
    width: 220px; height: 220px; object-fit: cover; border-radius: 50%;
    border: 4px solid #c9a84c; box-shadow: 0 0 40px rgba(201,168,76,0.6);
}
.panda-text {
    margin-top: 16px; font-size: 1.6rem; color: #f0e6d0;
    font-family: 'Playfair Display', Georgia, serif; font-style: italic;
    text-shadow: 0 2px 12px rgba(0,0,0,0.8);
}
@keyframes panda-shake-big {
    0%,100% { transform: rotate(-5deg); }
    25%     { transform: rotate(4deg); }
    50%     { transform: rotate(-3deg); }
    75%     { transform: rotate(5deg); }
}
@keyframes panda-fade-out {
    0%   { opacity: 1; }
    65%  { opacity: 1; }
    100% { opacity: 0; }
}

/* ── Achievement unlock flash overlay ── */
.achievement-overlay {
    position:fixed;top:0;left:0;width:100vw;height:100vh;
    background:rgba(0,5,20,0.95);z-index:99999;
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    animation: fade-in-overlay 1.2s ease forwards;
    pointer-events:none;
}
@keyframes fade-in-overlay { 0%{opacity:0} 100%{opacity:1} }
.achievement-title {
    font-family:var(--serif); font-size:1.6rem; color:#6ea8fe;
    letter-spacing:2px; margin-bottom:12px; text-align:center;
    animation: glow-text 2s ease-in-out infinite alternate;
}
@keyframes glow-text { 0%{text-shadow:0 0 10px rgba(110,168,254,0.5)} 100%{text-shadow:0 0 30px rgba(110,168,254,0.9),0 0 60px rgba(110,168,254,0.4)} }
.achievement-quote {
    font-family:var(--serif); font-size:1.1rem; color:#a8c8ff;
    font-style:italic; text-align:center; max-width:500px; line-height:1.8;
}

/* ── Streamlit overrides ── */
.stButton > button {
    background: linear-gradient(135deg,rgba(201,168,76,0.12),rgba(12,20,45,0.9)) !important;
    color: var(--gold) !important;
    border: 1px solid rgba(201,168,76,0.38) !important;
    border-radius: 8px !important;
    font-family: var(--sans) !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s !important;
    padding: 0.5rem 1.2rem !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg,rgba(201,168,76,0.28),rgba(12,20,45,0.9)) !important;
    box-shadow: 0 0 16px rgba(201,168,76,0.35) !important;
    transform: translateY(-1px) !important;
}
.stSelectbox label,.stRadio label,.stTextInput label,
.stSlider label,.stCheckbox label,.stTextArea label {
    color: var(--text-dim) !important; font-size: 0.88rem !important; font-family:var(--sans) !important;
}
.stTextInput input, .stTextArea textarea {
    background: rgba(7,11,24,0.9) !important; color: var(--text-main) !important;
    border: 1px solid rgba(201,168,76,0.28) !important; border-radius: 8px !important;
    font-size: 0.95rem !important; font-family: var(--sans) !important;
}
div[data-baseweb="select"] > div {
    background: rgba(7,11,24,0.9) !important;
    border-color: rgba(201,168,76,0.28) !important;
    color: var(--text-main) !important;
}
.stDataFrame { border:1px solid rgba(201,168,76,0.15) !important; border-radius:10px; }
.stTabs [data-baseweb="tab-list"] { background:rgba(10,18,42,0.8) !important; border-radius:10px; }
.stTabs [data-baseweb="tab"] { color:var(--text-dim) !important; font-family:var(--sans) !important; }
.stTabs [aria-selected="true"] { color:var(--gold) !important; border-bottom:2px solid var(--gold) !important; }

/* ── Sidebar toggle always visible & clickable — mobile + desktop + achievement mode ── */
/* ── Sidebar toggle — supports multiple Streamlit versions ── */
/* v1.32+ uses data-testid="collapsedControl" */
[data-testid="collapsedControl"],
/* Older versions use stSidebarCollapsedControl */
[data-testid="stSidebarCollapsedControl"],
/* Catch-all for any wrapping element */
button[kind="header"][data-testid*="sidebar"],
div[data-testid*="collapsedControl"] {
    background: rgba(201,168,76,0.22) !important;
    border: 1.5px solid rgba(201,168,76,0.55) !important;
    border-radius: 0 12px 12px 0 !important;
    width: 40px !important;
    min-height: 64px !important;
    opacity: 1 !important;
    visibility: visible !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    position: fixed !important;
    top: 50% !important;
    left: 0 !important;
    transform: translateY(-50%) !important;
    z-index: 2147483647 !important;
    pointer-events: auto !important;
    cursor: pointer !important;
}
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover {
    background: rgba(201,168,76,0.4) !important;
    box-shadow: 4px 0 20px rgba(201,168,76,0.4) !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg {
    fill: #c9a84c !important;
    width: 22px !important; height: 22px !important;
    pointer-events: none !important;
}
/* Ensure the collapsed-sidebar control specifically never hides — scoped tightly
   so this does NOT catch unrelated portal elements like selectbox dropdowns
   (a previous overly-broad `section[data-testid="stSidebar"] ~ div` selector
   here was forcing max z-index onto every sibling div, including dropdown
   popovers, which corrupted their stacking/visibility app-wide). */
section[data-testid="stSidebarCollapsedControl"] {
    opacity: 1 !important;
    visibility: visible !important;
    display: block !important;
    pointer-events: all !important;
    z-index: 999998 !important;
}
/* Native selectbox/multiselect dropdown popover — force a solid, readable,
   correctly-stacked background so options never blend with page content behind them */
div[data-baseweb="popover"] {
    z-index: 999999 !important;
}
div[data-baseweb="popover"] div[data-baseweb="menu"],
ul[role="listbox"] {
    background: #0a1428 !important;
    border: 1px solid rgba(201,168,76,0.35) !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6) !important;
}
li[role="option"], div[data-baseweb="menu"] li {
    background: #0a1428 !important;
    color: #e2e8f0 !important;
}
li[role="option"]:hover, div[data-baseweb="menu"] li:hover {
    background: rgba(201,168,76,0.18) !important;
    color: #f0e6d0 !important;
}
/* Mobile */
@media (max-width: 900px) {
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {
        width: 48px !important;
        min-height: 72px !important;
        background: rgba(201,168,76,0.3) !important;
        border-color: rgba(201,168,76,0.7) !important;
        box-shadow: 2px 0 12px rgba(0,0,0,0.5) !important;
    }
}
</style>
"""

# ═══════════════════════════════════════════════════════
#  SHARED KEYFRAMES + HOVER GLOW (radial dial buttons, etc.)
# ═══════════════════════════════════════════════════════
SHARED_CSS = """
<style>
@keyframes dot-pulse {
    0%,80%,100% { transform:scale(0.6); opacity:0.5; }
    40%          { transform:scale(1.15); opacity:1; }
}
/* Radial dial / section nav buttons — subtle glow on hover, colour-matched per section */
div[data-testid="stButton"] > button {
    transition: box-shadow 0.25s ease, transform 0.15s ease, border-color 0.25s ease !important;
}
div[data-testid="stButton"] > button:hover {
    box-shadow: 0 0 14px rgba(201,168,76,0.55), 0 0 2px rgba(201,168,76,0.8) !important;
    border-color: rgba(201,168,76,0.7) !important;
    transform: translateY(-1px);
}
div[data-testid="stButton"] > button:active {
    transform: translateY(0px) scale(0.98);
}
</style>
"""

RARE_MODE_DURATION_SECONDS = 20  # achievement mode auto-expires after 20s

def init_session_state():
    """Ensure all session-state defaults exist. Safe to call on every page —
    the heavy lifting already happens at module import time, so this is a
    lightweight idempotent guard for pages that import utils differently."""
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    # Achievement/rare mode auto-expires — checked on every page load since
    # this function runs at the top of every page.
    if st.session_state.get("rare_mode") and st.session_state.get("rare_timer"):
        if time.time() - st.session_state.rare_timer > RARE_MODE_DURATION_SECONDS:
            st.session_state.rare_mode = False
            st.session_state.ambient_sound = False  # stop the theme song when the mode ends

def inject_css():
    """Single entry point every page calls to apply GeoSphere's styling.
    Always applies the base (NORMAL_CSS) theme + shared keyframes/hover glow,
    and layers the full-screen Achievement/RARE takeover on top when active."""
    st.markdown(NORMAL_CSS, unsafe_allow_html=True)
    st.markdown(SHARED_CSS, unsafe_allow_html=True)
    if st.session_state.get("rare_mode"):
        st.markdown(RARE_CSS, unsafe_allow_html=True)
        _rare_mode_watchdog()

def _rare_mode_watchdog():
    """While achievement/rare mode is active, arms a JS timer that clicks a
    hidden helper button the instant RARE_MODE_DURATION_SECONDS elapses
    since rare_timer was set. Clicking any Streamlit widget forces a full
    script rerun — that's what actually lets init_session_state() flip
    rare_mode back to False and every page re-render normal (banner, CSS
    takeover, theme song all included). Without this, the 20s expiry check
    in init_session_state only fires on the *next* user-triggered rerun, so
    achievement mode could stay visually "stuck" on indefinitely if nobody
    clicks anything after unlocking it. The helper button itself is hidden
    instantly via a CSS sibling selector (no flash) rather than JS, so only
    the timing/click needs JS."""
    started = st.session_state.get("rare_timer") or time.time()
    remaining_ms = max(0, int((RARE_MODE_DURATION_SECONDS - (time.time() - started)) * 1000)) + 200
    st.markdown('<div id="rare-mode-watchdog-marker"></div>', unsafe_allow_html=True)
    st.button("⏱", key="rare_mode_watchdog_btn")
    st.markdown(f"""
    <style>
    #rare-mode-watchdog-marker + div[data-testid="stButton"] {{
        display: none !important;
    }}
    </style>
    <script>
    (function() {{
        function clickWatchdog() {{
            const marker = document.getElementById('rare-mode-watchdog-marker');
            if (!marker) return false;
            let el = marker.nextElementSibling;
            while (el && !el.querySelector('button')) el = el.nextElementSibling;
            const btn = el ? el.querySelector('button') : null;
            if (btn) {{ btn.click(); return true; }}
            return false;
        }}
        setTimeout(function() {{
            if (!clickWatchdog()) {{
                let tries = 0;
                const iv = setInterval(function() {{
                    tries++;
                    if (clickWatchdog() || tries > 20) clearInterval(iv);
                }}, 200);
            }}
        }}, {remaining_ms});
    }})();
    </script>
    """, unsafe_allow_html=True)

# JavaScript: actively find and style the sidebar toggle regardless of Streamlit version
st.markdown("""
<script>
(function fixSidebarToggle() {
    function applyFix() {
        // Try every known selector across Streamlit versions
        const selectors = [
            '[data-testid="collapsedControl"]',
            '[data-testid="stSidebarCollapsedControl"]',
            'button[aria-label*="sidebar"]',
            'button[aria-label*="Sidebar"]',
        ];
        let found = false;
        for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el) {
                el.style.cssText = `
                    position: fixed !important;
                    top: 50% !important;
                    left: 0 !important;
                    transform: translateY(-50%) !important;
                    z-index: 2147483647 !important;
                    opacity: 1 !important;
                    visibility: visible !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    width: 42px !important;
                    min-height: 66px !important;
                    background: rgba(201,168,76,0.25) !important;
                    border: 1.5px solid rgba(201,168,76,0.6) !important;
                    border-radius: 0 12px 12px 0 !important;
                    pointer-events: auto !important;
                    cursor: pointer !important;
                `;
                found = true;
            }
        }
        return found;
    }
    // Try immediately, then keep retrying for 5 seconds
    if (!applyFix()) {
        let tries = 0;
        const interval = setInterval(() => {
            tries++;
            if (applyFix() || tries > 50) clearInterval(interval);
        }, 100);
    }
    // Also re-apply on any DOM change (Streamlit re-renders frequently)
    const observer = new MutationObserver(() => applyFix());
    observer.observe(document.body, {childList: true, subtree: true});
})();
</script>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
#  DATA LAYER
# ═══════════════════════════════════════════════════════

MINERALS = [
    {"name":"Quartz","formula":"SiO₂","emoji":"💎","hardness":7,"luster":"Vitreous",
     "cleavage":"None","system":"Hexagonal","color":"Colorless/white",
     "india":"Rajasthan, Andhra Pradesh, Telangana",
     "use":"Glass, electronics, sandpaper, concrete",
     "desc":"Most abundant mineral in Earth's crust. Key component of granite and sandstone. Used in semiconductors."},
    {"name":"Feldspar","formula":"KAlSi₃O₈","emoji":"🪨","hardness":6,"luster":"Vitreous-pearly",
     "cleavage":"Two directions","system":"Monoclinic","color":"Pink/white/grey",
     "india":"Rajasthan, Andhra Pradesh",
     "use":"Ceramics, glass, abrasives",
     "desc":"Most common mineral group — 60% of crust. Pink orthoclase in granite, plagioclase in basalt."},
    {"name":"Mica","formula":"K(Mg,Fe)₃AlSi₃O₁₀","emoji":"✨","hardness":2.5,"luster":"Pearly",
     "cleavage":"Perfect basal","system":"Monoclinic","color":"Silver/black/gold",
     "india":"Andhra Pradesh (world's largest), Bihar, Rajasthan",
     "use":"Electronics, insulation, cosmetics, paint",
     "desc":"Sheet silicate. Muscovite (white) and biotite (black) most common. India = world's top mica producer."},
    {"name":"Calcite","formula":"CaCO₃","emoji":"🌊","hardness":3,"luster":"Vitreous",
     "cleavage":"Three directions (rhombohedral)","system":"Trigonal","color":"White/colourless",
     "india":"Rajasthan, Gujarat, MP",
     "use":"Cement, steel flux, agriculture (lime)",
     "desc":"Main component of limestone and marble. Fizzes with dilute HCl — classic field identification test."},
    {"name":"Olivine","formula":"(Mg,Fe)₂SiO₄","emoji":"🍃","hardness":6.5,"luster":"Vitreous",
     "cleavage":"Poor","system":"Orthorhombic","color":"Olive green",
     "india":"Tamil Nadu, Odisha",
     "use":"Refractory (foundry sand), gemstone (peridot)",
     "desc":"Primary mineral of Earth's upper mantle. Gemstone variety = peridot. Weathers rapidly at surface."},
    {"name":"Pyrite","formula":"FeS₂","emoji":"⭐","hardness":6,"luster":"Metallic",
     "cleavage":"Poor","system":"Cubic","color":"Brassy yellow",
     "india":"Rajasthan, Bihar, Karnataka",
     "use":"Sulphuric acid production, formerly pyrotechnics",
     "desc":"Fool's Gold — metallic lustre, cubic crystals. Indicator of reducing conditions in sediments."},
    {"name":"Magnetite","formula":"Fe₃O₄","emoji":"🧲","hardness":5.5,"luster":"Metallic",
     "cleavage":"None","system":"Cubic","color":"Black",
     "india":"Jharkhand, Odisha, Karnataka",
     "use":"Iron ore, pigment, recording media",
     "desc":"Strongly magnetic iron oxide. Records palaeomagnetism. Major iron ore in Indian shield."},
    {"name":"Halite","formula":"NaCl","emoji":"🧂","hardness":2.5,"luster":"Vitreous",
     "cleavage":"Cubic (perfect)","system":"Cubic","color":"Colourless/white/pink",
     "india":"Rajasthan (Sambhar Lake), Gujarat",
     "use":"Food, chemical industry, road de-icing",
     "desc":"Common salt. Forms in evaporite basins. Cubic cleavage and salty taste diagnostic in the field."},
    {"name":"Hornblende","formula":"Ca₂(Mg,Fe)₄Al(Si₇Al)O₂₂(OH)₂","emoji":"🖤","hardness":5.5,"luster":"Vitreous",
     "cleavage":"Two at 60/120°","system":"Monoclinic","color":"Black/dark green",
     "india":"Himalayan metamorphic belts",
     "use":"Minor — construction aggregate",
     "desc":"Common dark amphibole in granites and diorites. 60°/120° cleavage distinguishes it from pyroxene."},
    {"name":"Dolomite","formula":"CaMg(CO₃)₂","emoji":"🔮","hardness":3.5,"luster":"Vitreous-pearly",
     "cleavage":"Three directions","system":"Trigonal","color":"White/grey/pink",
     "india":"Rajasthan, Uttarakhand, Gujarat",
     "use":"Steel flux, cement, refractory, oil reservoir",
     "desc":"Fizzes only in powdered form with HCl. Major reservoir rock for oil and gas globally."},
    {"name":"Gypsum","formula":"CaSO₄·2H₂O","emoji":"🪨","hardness":2,"luster":"Vitreous-silky",
     "cleavage":"Perfect","system":"Monoclinic","color":"White/colourless",
     "india":"Rajasthan (largest), Gujarat, J&K",
     "use":"Plaster of Paris, drywall, fertiliser, cement retarder",
     "desc":"Softest common mineral (Mohs 2). Scratched by fingernail. Enormous industrial use globally."},
    {"name":"Kaolinite","formula":"Al₂Si₂O₅(OH)₄","emoji":"🏺","hardness":1.5,"luster":"Dull-earthy",
     "cleavage":"Perfect","system":"Triclinic","color":"White/cream",
     "india":"Kerala, Karnataka, Rajasthan",
     "use":"Ceramics, porcelain, paper coating, paint filler",
     "desc":"Clay mineral from feldspar weathering. Basis of ceramics. Found in tropical laterite profiles."},
    {"name":"Bauxite","formula":"Al(OH)₃ + AlO(OH)","emoji":"🟤","hardness":1,"luster":"Dull-earthy",
     "cleavage":"None","system":"Amorphous","color":"Red-brown/white",
     "india":"Odisha, Jharkhand, Gujarat, Maharashtra",
     "use":"Primary aluminium ore, refractory, abrasive",
     "desc":"Weathering product of aluminium-rich rocks in tropical climates. India is top-5 world producer."},
    {"name":"Chromite","formula":"FeCr₂O₄","emoji":"⚫","hardness":5.5,"luster":"Metallic-submetallic",
     "cleavage":"None","system":"Cubic","color":"Black",
     "india":"Odisha (90% of India's reserves), Karnataka",
     "use":"Stainless steel, refractory, pigment (chrome green)",
     "desc":"Only ore mineral of chromium. India ranks among top global producers, centred on Sukinda, Odisha."},
    {"name":"Apatite","formula":"Ca₅(PO₄)₃(F,Cl,OH)","emoji":"💚","hardness":5,"luster":"Vitreous-resinous",
     "cleavage":"Poor","system":"Hexagonal","color":"Green/blue/brown/colourless",
     "india":"Rajasthan, Tamil Nadu, Jharkhand",
     "use":"Phosphate fertilisers, phosphoric acid, gemstone",
     "desc":"Primary source of phosphorus for agriculture. Reference mineral at Mohs 5. Occurs in pegmatites and igneous rocks."},
]

ROCKS = {
    "Igneous": [
        {"name":"Granite","emoji":"🏔️","texture":"Coarse-grained (phaneritic)",
         "composition":"Quartz + Feldspar + Mica/Hornblende",
         "formation":"Slow cooling of magma deep in crust (intrusive)",
         "india":"Rajasthan, Tamil Nadu, Andhra Pradesh — Deccan Granite",
         "use":"Construction, monuments, dimension stone"},
        {"name":"Basalt","emoji":"🌋","texture":"Fine-grained (aphanitic) or glassy",
         "composition":"Plagioclase + Pyroxene + Olivine",
         "formation":"Rapid cooling of lava at surface (extrusive)",
         "india":"Deccan Traps (Maharashtra, Karnataka) — world's largest basalt province",
         "use":"Road aggregate, black granite slabs, railway ballast"},
        {"name":"Obsidian","emoji":"⚫","texture":"Glassy (no crystals)",
         "composition":"Felsic silica glass",
         "formation":"Extremely rapid quenching of silica-rich lava",
         "india":"Very rare in India; found in Andaman volcanic arc",
         "use":"Ancient cutting tools, surgical scalpels, jewellery"},
        {"name":"Pumice","emoji":"🧽","texture":"Highly vesicular (frothy)",
         "composition":"Glass + gas bubbles",
         "formation":"Gas-charged silicic magma solidifying rapidly",
         "india":"Barren Island, Andaman (active volcano)",
         "use":"Abrasive (toothpaste, skin care), lightweight concrete"},
        {"name":"Rhyolite","emoji":"🔴","texture":"Fine-grained to glassy",
         "composition":"Quartz + Alkali feldspar + Glass",
         "formation":"Explosive or effusive eruption of silica-rich magma",
         "india":"Rajasthan, Vindhyan belt",
         "use":"Aggregate, silica source"},
        {"name":"Gabbro","emoji":"⬛","texture":"Coarse-grained (phaneritic)",
         "composition":"Plagioclase + Pyroxene ± Olivine",
         "formation":"Slow cooling of basaltic magma at depth",
         "india":"Andaman ophiolite, Eastern Ghats",
         "use":"Dimension stone ('black granite'), aggregate"},
        {"name":"Diorite","emoji":"🔘","texture":"Medium to coarse-grained",
         "composition":"Plagioclase + Hornblende ± Biotite",
         "formation":"Intermediate intrusive igneous rock",
         "india":"Himalayan intrusive complexes, NE India",
         "use":"Decorative stone, sculpture"},
        {"name":"Pegmatite","emoji":"💎","texture":"Very coarse-grained (>1 cm crystals)",
         "composition":"Quartz + Feldspar + Rare minerals",
         "formation":"Last stage of magmatic crystallisation with water-rich melt",
         "india":"Rajasthan, Andhra Pradesh — source of mica, beryl, tourmaline",
         "use":"Source of rare minerals, gemstones, mica"},
    ],
    "Sedimentary": [
        {"name":"Sandstone","emoji":"🟤","texture":"Medium-grained (sand 0.06–2mm)",
         "composition":"Quartz ± Feldspar ± Rock fragments, cemented",
         "formation":"Compaction and cementation of sand in river/beach/desert",
         "india":"Vindhyan (MP, Rajasthan) — Red Fort built from it; Gondwana sandstones",
         "use":"Building stone, aquifer, reservoir rock"},
        {"name":"Limestone","emoji":"⬜","texture":"Fine to coarse (bioclastic to crystalline)",
         "composition":"Calcite (CaCO₃), shell fragments, coral",
         "formation":"Accumulation of marine organisms in shallow warm seas",
         "india":"Rajasthan, MP, AP — India's #1 resource for cement",
         "use":"Cement, steel flux, aggregate, agriculture"},
        {"name":"Shale","emoji":"🟫","texture":"Very fine-grained (clay-silt)",
         "composition":"Clay minerals + quartz + organic matter",
         "formation":"Compaction of mud in lakes, deltas, deep sea",
         "india":"Gondwana coalfields, Vindhyan basin",
         "use":"Brick, tile, oil source rock, shale gas"},
        {"name":"Conglomerate","emoji":"🔘","texture":"Very coarse (>2mm pebbles)",
         "composition":"Rounded clasts in finer matrix",
         "formation":"High-energy rivers, beaches — rapid deposition",
         "india":"Gondwana basal conglomerates, Sub-Himalayan molasse",
         "use":"Aggregate, sometimes decorative"},
        {"name":"Coal","emoji":"⬛","texture":"Massive, conchoidal fracture",
         "composition":"Compressed organic matter (macerals)",
         "formation":"Burial and coalification of peat/plant matter",
         "india":"Jharkhand, Odisha, Chhattisgarh, WB — Gondwana age (Permo-Carboniferous)",
         "use":"Power generation, coking coal for steel"},
        {"name":"Chalk","emoji":"🟡","texture":"Very fine-grained, soft",
         "composition":"Coccolithophore (microalgae) calcite plates",
         "formation":"Deep quiet marine deposition, Cretaceous seas",
         "india":"Not native; Cretaceous limestones in Meghalaya similar",
         "use":"Blackboard chalk (historically), lime"},
        {"name":"Chert","emoji":"🔵","texture":"Cryptocrystalline (very fine silica)",
         "composition":"Microcrystalline SiO₂ (silica)",
         "formation":"Siliceous ooze (marine) or silica replacement",
         "india":"Vindhyan cherts — Precambrian; Aravalli cherts",
         "use":"Ancient tools (flint), road aggregate"},
    ],
    "Metamorphic": [
        {"name":"Marble","emoji":"🏛️","texture":"Coarse crystalline, granoblastic",
         "composition":"Recrystallised calcite/dolomite",
         "formation":"Contact or regional metamorphism of limestone",
         "india":"Rajasthan (Makrana — Taj Mahal marble), Madhya Pradesh",
         "use":"Sculpture, flooring, monuments, acid neutraliser"},
        {"name":"Slate","emoji":"📋","texture":"Very fine-grained, perfect fissility",
         "composition":"Muscovite + chlorite + quartz",
         "formation":"Low-grade metamorphism of shale (T<300°C)",
         "india":"Himachal Pradesh, Rajasthan",
         "use":"Roofing tiles, flooring, writing slates"},
        {"name":"Schist","emoji":"💫","texture":"Medium-grained, schistose foliation",
         "composition":"Mica + quartz + garnet/staurolite",
         "formation":"Medium-grade metamorphism (300–600°C)",
         "india":"Himalayan metamorphic core, Dharwar schist belts",
         "use":"Decorative stone, aggregate"},
        {"name":"Quartzite","emoji":"💎","texture":"Coarse, granoblastic, very hard",
         "composition":"Interlocking quartz grains (>95% SiO₂)",
         "formation":"Metamorphism of sandstone — quartz recrystallises",
         "india":"Aravalli range, Vindhyan hills",
         "use":"Refractory, glass making, road aggregate"},
        {"name":"Gneiss","emoji":"🌀","texture":"Coarse, banded (gneissose)",
         "composition":"Quartz + feldspar + mica/hornblende, banded",
         "formation":"High-grade regional metamorphism (>600°C)",
         "india":"Peninsular gneisses (Dharwar, Charnockites) — 3.3 Ga",
         "use":"Building stone, dimension stone"},
        {"name":"Phyllite","emoji":"🍃","texture":"Fine-grained, silky sheen",
         "composition":"Fine muscovite + chlorite + quartz",
         "formation":"Between slate and schist (medium-low grade)",
         "india":"Lesser Himalaya, Eastern Ghats fringes",
         "use":"Roofing, decorative slabs"},
        {"name":"Charnockite","emoji":"⚫","texture":"Coarse, massive, dark green",
         "composition":"Hypersthene + quartz + feldspar",
         "formation":"Granulite-facies metamorphism — deepest crustal levels",
         "india":"UNIQUE TO INDIA — defined at St. Thomas Mount, Chennai",
         "use":"Monument stone (named after Job Charnock's tombstone!)"},
    ],
}

BOOKS = [
    # Semester 1
    {"title":"Principles of Physical Geology","author":"A. Holmes","subject":"Sem 1 – Elements of Earth Sciences","stars":5,
     "desc":"The classic foundational text — Earth's structure, geological time, volcanoes, earthquakes, weathering. First choice for ESMJ11."},
    {"title":"Understanding Earth","author":"Grotzinger, Jordan, Press & Siever","subject":"Sem 1 – Elements of Earth Sciences","stars":5,
     "desc":"Modern, beautifully illustrated, comprehensive. Excellent for plate tectonics, rock cycle, and Earth systems overview."},
    {"title":"Structural Geology","author":"M.P. Billings","subject":"Sem 1 – Structural Geology","stars":5,
     "desc":"Essential for folds, faults, joints, and field structural problems. Used throughout ESMJ11 and ESMJ32."},
    {"title":"Geological Structures and Maps","author":"R.J. Lisle","subject":"Sem 1 – Structural Geology","stars":4,
     "desc":"Practical guide for geological map reading and structural analysis. Excellent for practicals (ESMJ12, ESMJ34)."},
    # Semester 2
    {"title":"Mineralogy","author":"Berry, Mason & Dietrich","subject":"Sem 2 – Mineralogy","stars":5,
     "desc":"The standard mineralogy text for ESMJ21. Covers physical properties, crystal chemistry, optical properties of all major minerals."},
    {"title":"Optical Mineralogy","author":"W.D. Nesse","subject":"Sem 2 – Optical Mineralogy","stars":5,
     "desc":"Best modern optical mineralogy text. PPL and XPL properties of all rock-forming minerals. Essential for practicals (ESMJ22, ESMJ55)."},
    {"title":"Mineralogy","author":"Dexter Perkins","subject":"Sem 2 – Mineralogy","stars":4,
     "desc":"Clear, well-illustrated modern mineralogy. Good balance of crystal chemistry, physical properties, and petrology links."},
    {"title":"Dana's Textbook of Mineralogy","author":"W.E. Ford","subject":"Sem 2 – Mineralogy","stars":4,
     "desc":"Classic systematic mineralogy reference — comprehensive coverage of all mineral groups and their properties."},
    {"title":"Rutley's Elements of Mineralogy","author":"C.D. Gribble","subject":"Sem 2 – Mineralogy","stars":4,
     "desc":"Concise, field-oriented mineralogy reference. Good for quick identification in hand specimen."},
    # Semester 3
    {"title":"Principles of Physical Geology","author":"A. Holmes","subject":"Sem 3 – Physical Geology","stars":5,
     "desc":"Standard reference for ESMJ31 — geomorphic agents, rock cycle, Earth processes comprehensively covered."},
    {"title":"Geology in the Field","author":"R.A. Compton","subject":"Sem 3 – Field Geology","stars":5,
     "desc":"Essential field geology manual — outcrop description, mapping techniques, compass use, section drawing. Used in ESSE31 and ESMJ711."},
    {"title":"Foundations of Structural Geology","author":"R.G. Park","subject":"Sem 3 – Structural Geology","stars":4,
     "desc":"Modern structural geology with good coverage of ductile deformation and regional examples."},
    # Semester 4
    {"title":"Igneous and Metamorphic Petrology","author":"M.G. Best","subject":"Sem 4 – Petrology","stars":5,
     "desc":"Comprehensive petrology text for ESMJ41. Excellent on igneous textures, Bowen's series, metamorphic facies."},
    {"title":"The Elements of Palaeontology","author":"R.M. Black","subject":"Sem 4 – Palaeontology","stars":4,
     "desc":"Standard palaeontology text for ESMJ42. Covers invertebrate groups, biostratigraphy, fossilisation modes."},
    {"title":"Principles of Sedimentology and Stratigraphy","author":"S. Boggs","subject":"Sem 4 – Stratigraphy","stars":5,
     "desc":"Best modern sedimentology + stratigraphy combination. Covers all sedimentary environments and stratigraphic principles."},
    {"title":"Remote Sensing Geology","author":"R.P. Gupta","subject":"Sem 4 – Remote Sensing","stars":4,
     "desc":"India-focused remote sensing geology text — satellite image interpretation for geological mapping, ESMJ44."},
    {"title":"Introduction to Environmental Geology","author":"E.A. Keller","subject":"Sem 4 – Environmental Geology","stars":4,
     "desc":"Accessible environmental geology text — hazards, land use, water resources. For ESMJ43."},
    {"title":"Groundwater Hydrology","author":"D.K. Todd","subject":"Sem 4 – Hydrogeology","stars":5,
     "desc":"The definitive groundwater text — aquifer types, Darcy's Law, well hydraulics, pumping tests. Essential for ESMJ43."},
    # Semester 5
    {"title":"Petrology: Igneous, Sedimentary and Metamorphic","author":"Blatt & Tracy","subject":"Sem 5 – Petrology","stars":5,
     "desc":"Comprehensive petrology across all three rock types. Excellent for ESMJ51, ESMJ52, ESMJ53."},
    {"title":"Principles of Igneous and Metamorphic Petrology","author":"J.D. Winter","subject":"Sem 5 – Igneous Petrology","stars":5,
     "desc":"Modern, quantitative igneous and metamorphic petrology. Best for Bowen's series, geothermobarometry, phase diagrams."},
    {"title":"Earth Materials: Introduction to Mineralogy and Petrology","author":"Philpotts & Klein","subject":"Sem 5 – Mineralogy","stars":4,
     "desc":"Integrated mineralogy-petrology text. Good coverage of crystal chemistry, physical properties, and rock-forming contexts."},
    # Semester 6
    {"title":"Structural Geology of Rocks and Regions","author":"Davis, Reynolds & Kluth","subject":"Sem 6 – Structural Geology","stars":5,
     "desc":"Best modern structural geology text — kinematic indicators, ductile shear zones, fold-thrust belts, basin analysis."},
    {"title":"Mining Geology","author":"H.M. Ramaiah","subject":"Sem 6 – Economic Geology","stars":4,
     "desc":"India-focused economic geology — ore deposits, exploration, mining methods. Essential for ESMJ62."},
    {"title":"Introduction to Palaeontology","author":"A.K. Dutta","subject":"Sem 6 – Palaeontology","stars":4,
     "desc":"Indian author. Covers invertebrate groups critical for Gondwana stratigraphy of peninsular India. For ESMJ63."},
    {"title":"Geology of India and Burma","author":"M.S. Krishnan","subject":"Sem 6 – Stratigraphy","stars":5,
     "desc":"The foundational Indian geology reference — stratigraphy, structure, mineral deposits from Precambrian to Quaternary."},
    # Semesters 7-8
    {"title":"Remote Sensing and Image Interpretation","author":"Lillesand & Kiefer","subject":"Sem 8 – Remote Sensing","stars":5,
     "desc":"The remote sensing bible — image interpretation, satellite systems, GIS integration. Essential for ESMJ84."},
    {"title":"Geochemistry: An Introduction","author":"Albarède","subject":"Sem 7 – Geochemistry","stars":4,
     "desc":"Modern geochemistry — isotopes, trace elements, geochronology. For ESMJ73."},
    {"title":"Principles of Sedimentology and Stratigraphy","author":"S. Boggs","subject":"Sem 8 – Basin Analysis","stars":5,
     "desc":"Sequence stratigraphy, basin types, and sedimentary systems. Key for ESMJ85."},
    {"title":"Groundwater","author":"H.M. Raghunath","subject":"Sem 8 – Groundwater","stars":4,
     "desc":"Indian-focused groundwater text — aquifers, wells, recharge. For ESMJ83."},
]

QUIZ_QUESTIONS = [
    {"section":"Mineralogy","q":"Which mineral effervesces vigorously with dilute HCl?",
     "options":["Quartz","Calcite","Feldspar","Mica"],"answer":1,
     "explain":"Calcite (CaCO₃) + 2HCl → CaCl₂ + H₂O + CO₂↑. The fizzing is the CO₂ escaping — a classic field test."},
    {"section":"Indian Geology","q":"The Deccan Traps are primarily composed of which rock type?",
     "options":["Granite","Limestone","Basalt","Quartzite"],"answer":2,
     "explain":"Deccan Traps = flood basalts erupted ~66 Ma, covering ~500,000 km² — one of Earth's largest volcanic events."},
    {"section":"Plate Tectonics","q":"Which tectonic event created the Himalayas?",
     "options":["Pacific subduction","India–Eurasia collision","Atlantic spreading","African rift"],"answer":1,
     "explain":"India–Eurasia collision started ~50 Ma ago. India still moves NNE at ~5 cm/yr, continually lifting the Himalayas."},
    {"section":"Geophysics","q":"What does the Mohorovičić discontinuity (Moho) separate?",
     "options":["Inner & outer core","Crust & mantle","Mantle & outer core","Lithosphere & asthenosphere"],"answer":1,
     "explain":"The Moho marks the seismic velocity jump from crust (~6 km/s) to mantle (~8 km/s). Detected by Mohorovičić in 1909."},
    {"section":"Economic Geology","q":"Which Indian state has the largest coal reserves?",
     "options":["Odisha","Jharkhand","Chhattisgarh","West Bengal"],"answer":1,
     "explain":"Jharkhand holds ~26% of India's coal reserves, primarily in the Damodar Valley Gondwana coalfields."},
    {"section":"Indian Geology","q":"The mineral Charnockite is uniquely named after a location in India. Which city?",
     "options":["Mumbai","Kolkata","Chennai","Varanasi"],"answer":2,
     "explain":"Named after Job Charnock's tombstone at St. Thomas Mount, Chennai. The rock is a hypersthene-bearing granulite."},
    {"section":"Plate Tectonics","q":"What type of plate boundary exists between the Indian and Eurasian plates?",
     "options":["Divergent","Transform","Convergent","Passive margin"],"answer":2,
     "explain":"Convergent boundary — the Indian plate subducts/collides with Eurasia, producing the Himalayan fold-thrust belt."},
    {"section":"Geological Time","q":"Which era is known as the 'Age of Reptiles'?",
     "options":["Palaeozoic","Cenozoic","Mesozoic","Precambrian"],"answer":2,
     "explain":"Mesozoic Era (252–66 Ma) — Triassic, Jurassic, Cretaceous — dominated by dinosaurs, marine reptiles, pterosaurs."},
    {"section":"Petrology","q":"Marble is metamorphosed from which sedimentary rock?",
     "options":["Sandstone","Shale","Basalt","Limestone"],"answer":3,
     "explain":"Marble = recrystallised calcite from limestone/dolostone under heat/pressure. Makrana marble built the Taj Mahal."},
    {"section":"Geological Time","q":"What is the Gondwana Supercontinent? When did it begin to break up?",
     "options":["66 Ma","180 Ma","252 Ma","541 Ma"],"answer":1,
     "explain":"Gondwana began breaking up ~180 Ma (Jurassic). India, Africa, Antarctica, Australia, and South America separated."},
    {"section":"Seismology","q":"Which scale measures earthquake magnitude based on seismic moment?",
     "options":["Richter (ML)","Modified Mercalli","Moment Magnitude (Mw)","Rossi-Forel"],"answer":2,
     "explain":"Mw (Moment Magnitude) replaced Richter for large earthquakes. It measures actual energy released in the fault rupture."},
    {"section":"Economic Geology","q":"Which Indian state produces ~90% of India's chromite?",
     "options":["Jharkhand","Karnataka","Odisha","Rajasthan"],"answer":2,
     "explain":"Odisha's Sukinda valley is the world's 2nd largest chromite reserve. India ranks ~4th globally in production."},
    {"section":"Petrology","q":"A rock formed by compaction and cementation of sand grains is called:",
     "options":["Shale","Sandstone","Quartzite","Greywacke"],"answer":1,
     "explain":"Sandstone = lithified sand (0.06–2mm grains). Cemented by silica, calcite, or iron oxide. Common aquifer rock."},
    {"section":"Mineralogy","q":"What is the Mohs hardness of Diamond?",
     "options":["8","9","10","7"],"answer":2,
     "explain":"Diamond = Mohs 10 (hardest natural mineral). Composed of carbon atoms in cubic tetrahedral structure."},
    {"section":"Seismology","q":"The 2004 Indian Ocean tsunami was triggered by an earthquake at which subduction zone?",
     "options":["Makran","Andaman-Sumatra","Zagros","Hindu Kush"],"answer":1,
     "explain":"M9.1 earthquake on 26 Dec 2004 at the Sunda subduction zone near Sumatra generated the devastating Indian Ocean tsunami."},
    {"section":"Mineralogy","q":"Which mineral has perfect cleavage in one direction, splitting into thin flexible sheets?",
     "options":["Quartz","Mica","Calcite","Garnet"],"answer":1,
     "explain":"Mica (biotite/muscovite) has perfect basal cleavage in one plane — its sheet structure makes it useful in electronics and insulation."},
    {"section":"Mineralogy","q":"Kimberlite pipes are primarily mined for which gemstone?",
     "options":["Ruby","Emerald","Diamond","Sapphire"],"answer":2,
     "explain":"Kimberlite is the main host rock for diamonds, rapidly transporting them from 150-200 km mantle depth to the surface."},
    {"section":"Seismology","q":"What does P-wave stand for in seismology?",
     "options":["Pressure wave","Primary wave","Peak wave","Plate wave"],"answer":1,
     "explain":"P-waves (primary waves) are the fastest seismic waves and arrive first after an earthquake, traveling through both solids and liquids."},
    {"section":"Indian Geology","q":"Which Indian river is known as 'Dakshin Ganga'?",
     "options":["Krishna","Narmada","Godavari","Kaveri"],"answer":2,
     "explain":"The Godavari is called Dakshin Ganga ('Ganga of the South') — it's the largest peninsular river, flowing through the Deccan Plateau."},
    {"section":"Soils & Resources","q":"What is the dominant soil type covering the Indo-Gangetic plains?",
     "options":["Black soil","Laterite soil","Alluvial soil","Red soil"],"answer":2,
     "explain":"Alluvial soil, deposited by rivers, covers ~43% of India and is concentrated in the highly fertile Indo-Gangetic plains."},
    {"section":"Plate Tectonics","q":"Which plate boundary type produces transform faults like the San Andreas Fault?",
     "options":["Convergent","Divergent","Transform","Passive"],"answer":2,
     "explain":"Transform boundaries occur where plates slide horizontally past each other, generating powerful but typically shallow earthquakes."},
    {"section":"Economic Geology","q":"What is the primary economic use of bauxite ore?",
     "options":["Steel production","Aluminium production","Cement production","Glass production"],"answer":1,
     "explain":"Bauxite is the principal aluminum ore — about 99% of bauxite mined globally is processed into aluminum via the Bayer process."},
    {"section":"Indian Geology","q":"India's only confirmed active volcano is located on which island?",
     "options":["Lakshadweep","Diu","Barren Island","Elephanta"],"answer":2,
     "explain":"Barren Island in the Andaman Sea is India's only confirmed active volcano, a stratovolcano that has erupted multiple times recently."},
    {"section":"Mineralogy","q":"Which mineral is the principal component of granite along with quartz and mica?",
     "options":["Calcite","Feldspar","Gypsum","Halite"],"answer":1,
     "explain":"Feldspar makes up about 60% of Earth's crust and, along with quartz and mica, forms the bulk of granite's mineral composition."},
    {"section":"Plate Tectonics","q":"What geological feature is created at a divergent plate boundary?",
     "options":["Mountain ranges","Mid-ocean ridges","Ocean trenches","Volcanic arcs"],"answer":1,
     "explain":"At divergent boundaries, plates pull apart and magma rises to fill the gap, building mid-ocean ridges — like the Carlsberg Ridge."},
    {"section":"Indian Geology","q":"The Siwalik Hills, famous for Miocene-Pleistocene mammal fossils, form part of which mountain system?",
     "options":["Aravalli","Western Ghats","Himalayan foothills","Vindhyas"],"answer":2,
     "explain":"The Siwaliks are the outermost, youngest range of the Himalayan foothills, known for rich vertebrate fossil deposits."},
    {"section":"Geomorphology","q":"Which process describes rock breaking down chemically due to oxidation or hydrolysis?",
     "options":["Erosion","Physical weathering","Chemical weathering","Deposition"],"answer":2,
     "explain":"Chemical weathering alters mineral composition (e.g. via oxidation or hydrolysis) — it's the primary process behind India's laterite soils."},
    {"section":"Petrology","q":"What type of rock is formed when sediment is compacted and cemented together?",
     "options":["Igneous","Sedimentary","Metamorphic","Volcanic"],"answer":1,
     "explain":"Sedimentary rocks form through compaction and cementation (lithification) of weathered and eroded material — covering ~75% of Earth's land surface."},
    {"section":"Mineralogy","q":"Which is the most abundant mineral in Earth's crust?",
     "options":["Mica","Feldspar","Quartz","Calcite"],"answer":2,
     "explain":"Quartz (SiO₂) is the single most abundant mineral by volume in Earth's crust, prized for its hardness and use in electronics and glass."},
    # — Stratigraphy (add 4 more to reach 5) —
    {"section":"Stratigraphy","q":"What is an unconformity in geology?",
     "options":["A fault zone","A gap in the rock record (buried erosion surface)","A type of fold","A sedimentary structure"],"answer":1,
     "explain":"An unconformity represents missing time — a buried erosion surface separating rock sequences, indicating a period of non-deposition or removal."},
    {"section":"Stratigraphy","q":"Glossopteris fossils found across India, Africa, Australia, and Antarctica prove what?",
     "options":["Global warming","These continents were once joined (Gondwana)","Marine transgression","Meteor impact"],"answer":1,
     "explain":"Glossopteris (Permian seed fern) is the key biogeographic evidence for Gondwana — the southern supercontinent that broke apart ~180 Ma."},
    {"section":"Stratigraphy","q":"Which Indian rock sequence contains the major coal deposits?",
     "options":["Vindhyan Supergroup","Deccan Traps","Gondwana Supergroup","Aravalli Group"],"answer":2,
     "explain":"The Gondwana Supergroup (Permian–Jurassic) contains India's major coal deposits in basins like Damodar Valley (Jharia, Raniganj) and Mahanadi."},
    {"section":"Stratigraphy","q":"What does the principle of Faunal Succession state?",
     "options":["Older rocks are always below younger","Fossils succeed one another in a definite, recognisable order","Sediments are horizontal at deposition","Strata extend laterally"],"answer":1,
     "explain":"William Smith's Law of Faunal Succession (1799): fossil assemblages change through time in a consistent order, enabling rock correlation across distances."},
    # — Sedimentology (add 4 more) —
    {"section":"Sedimentology","q":"What type of sedimentary structure indicates direction of ancient current flow?",
     "options":["Ripple marks","Cross-bedding foresets","Mud cracks","Load casts"],"answer":1,
     "explain":"Cross-bedding foresets dip downstream — they are one of geology's best palaeocurrent indicators in aeolian and fluvial sandstones."},
    {"section":"Sedimentology","q":"What is a turbidite?",
     "options":["A volcanic deposit","A graded bed deposited by an underwater avalanche (turbidity current)","A tidal flat deposit","A glacial sediment"],"answer":1,
     "explain":"Turbidites are characteristically graded beds (coarse base → fine top) deposited rapidly from turbidity currents moving down continental slopes."},
    {"section":"Sedimentology","q":"Which Indian sedimentary basin is the main offshore oil producer?",
     "options":["Vindhyan Basin","Gondwana Basin","Mumbai High (Bombay High)","Kutch Basin"],"answer":2,
     "explain":"The Mumbai High (Bombay High) offshore basin — Paleocene-Eocene carbonate — is India's largest producing oil field, operated by ONGC."},
    {"section":"Sedimentology","q":"What does BIF stand for and why is it geologically important?",
     "options":["Banded Iron Formation — major Precambrian iron ore","Basic Intrusive Flow — volcanic","British Index Fossil — biostratigraphy","Bottom Infill Formation — sedimentary basin"],"answer":0,
     "explain":"Banded Iron Formation (BIF) — alternating silica and iron-oxide layers deposited in Precambrian oceans. India's major iron ore deposits (Odisha, Jharkhand) are BIFs."},
    # — Geomorphology (add 2 more to balance) —
    {"section":"Geomorphology","q":"What type of drainage pattern develops on uniformly dipping strata following the slope?",
     "options":["Dendritic","Trellis","Consequent (Parallel)","Radial"],"answer":2,
     "explain":"Consequent/parallel drainage follows the initial slope direction of the land surface — common on young fold mountain flanks."},
    {"section":"Geomorphology","q":"What is a peneplain?",
     "options":["A high plateau formed by lava","A near-flat surface produced by long-term erosion close to base level","A coastal terrace","A glacial outwash plain"],"answer":1,
     "explain":"A peneplain (Davis, 1899) is the theoretical end-product of the erosion cycle — a low, gently rolling surface with occasional resistant monadnocks."},
    # — Geological Time (add 3 more) —
    {"section":"Geological Time","q":"When did the Cambrian Explosion occur and why is it significant?",
     "options":["250 Ma — end-Permian extinction","541 Ma — rapid diversification of most animal body plans","66 Ma — K-Pg extinction","3.5 Ga — origin of life"],"answer":1,
     "explain":"The Cambrian Explosion (~541 Ma) saw an extraordinary radiation of multicellular animal life, producing most major animal phyla within ~25 million years."},
    {"section":"Geological Time","q":"What is the age of Earth?",
     "options":["2.5 billion years","4.0 billion years","4.6 billion years","6,000 years"],"answer":2,
     "explain":"Earth formed ~4.6 billion years ago from the solar nebula. The oldest zircon crystals (Jack Hills, Australia) are 4.4 Ga, and moon rocks confirm the ~4.5 Ga age."},
    {"section":"Geological Time","q":"What eon covers the time from Earth's formation to ~541 Ma?",
     "options":["Palaeozoic","Precambrian (Cryptozoic)","Mesozoic","Cenozoic"],"answer":1,
     "explain":"The Precambrian (or Cryptozoic) covers ~88% of Earth's history — from formation (4.6 Ga) to the start of the Cambrian (541 Ma), when hard-shelled fossils first became abundant."},
    # — Geophysics (add 3 more) —
    {"section":"Geophysics","q":"What is isostasy?",
     "options":["Gravity anomaly measurement","Gravitational equilibrium of crust floating on denser mantle","Earthquake wave analysis","Magnetic field polarity"],"answer":1,
     "explain":"Isostasy: crustal blocks float on the denser mantle like icebergs — mountains have deep roots (Airy hypothesis) or thickened crust (Pratt hypothesis). Explains gravity anomalies."},
    {"section":"Geophysics","q":"What is Earth's magnetic field generated by?",
     "options":["Iron in the solid inner core","Convection in the liquid outer core (geodynamo)","Rotation of Earth","Solar wind interaction"],"answer":1,
     "explain":"Earth's magnetic field is generated by convective movement of liquid iron-nickel in the outer core — the geodynamo. Without it, solar wind would strip away the atmosphere."},
    {"section":"Geophysics","q":"Which seismic discontinuity marks the core-mantle boundary?",
     "options":["Mohorovičić discontinuity","Conrad discontinuity","Gutenberg discontinuity","Lehmann discontinuity"],"answer":2,
     "explain":"The Gutenberg discontinuity (~2,890 km depth) marks the core-mantle boundary — detected by the disappearance of P-waves (shadow zone) and absence of S-waves below."},
    # — Structural Geology (add 2 more) —
    {"section":"Structural Geology","q":"In which direction does a reverse fault move the hanging wall?",
     "options":["Down relative to footwall","Up relative to footwall","Horizontally left","Horizontally right"],"answer":1,
     "explain":"In a reverse fault, the hanging wall moves up relative to the footwall under compressional stress — the opposite of a normal fault. Thrusts are low-angle reverse faults."},
    {"section":"Structural Geology","q":"What are S-C fabrics used for in structural geology?",
     "options":["Measuring fold wavelength","Determining shear sense in ductile shear zones","Estimating burial depth","Identifying unconformities"],"answer":1,
     "explain":"S-C fabrics (S = schistosity, C = shear band) in mylonites record the kinematics (shear sense) of ductile deformation — critical for reconstructing tectonic transport direction."},
]

FLASHCARD_SECTION_IMAGE = {
    "Economic Geology": "Ore",
    "Geomorphology": "Landform",
    "Geophysics": "Seismometer",
    "Historical Geology": "Geologic time scale",
    "Igneous Petrology": "Igneous rock",
    "Indian Geology": "Geology of India",
    "Mineralogy": "Mineral",
    "Petrology": "Rock (geology)",
    "Plate Tectonics": "Plate tectonics",
    "Sedimentology": "Sedimentary rock",
    "Soils & Resources": "Soil",
    "Stratigraphy": "Stratum",
    "Structural Geology": "Fault (geology)",
    "Seismology": "Earthquake",
    "Volcanology": "Volcano",
}

FLASHCARDS = [
    {"section":"Structural Geology","q":"What is a batholith?","a":"A large (>100 km²) igneous intrusive body of coarse-grained rock (usually granite) that crystallised deep underground."},
    {"section":"Stratigraphy","q":"Define unconformity in geology.","a":"A buried erosion surface (time gap) between two rock sequences representing missing geologic time."},
    {"section":"Geophysics","q":"What is isostasy?","a":"Gravitational equilibrium of Earth's crust floating on denser mantle — like an iceberg on water; mountains have deep roots."},
    {"section":"Structural Geology","q":"What is a graben?","a":"A down-dropped crustal block between two parallel normal faults — creates rift valleys like the East African Rift."},
    {"section":"Structural Geology","q":"Distinguish strike and dip.","a":"Strike = compass direction of a horizontal line on a tilted surface; Dip = angle and direction of maximum inclination."},
    {"section":"Sedimentology","q":"What are turbidites?","a":"Graded sedimentary beds deposited by underwater avalanches (turbidity currents) down continental slopes."},
    {"section":"Petrology","q":"Define contact metamorphism.","a":"Local thermal metamorphism around a hot igneous intrusion — creates a metamorphic aureole in country rock."},
    {"section":"Petrology","q":"What is metasomatism?","a":"Chemical alteration of rock by hot fluids that change mineralogy without melting — common near igneous intrusions."},
    {"section":"Petrology","q":"What is the rock cycle?","a":"Continuous transformation: magma→igneous→weathering→sediment→sedimentary→burial→metamorphic→melting→magma again."},
    {"section":"Petrology","q":"Define foliation in metamorphic rocks.","a":"Planar fabric in metamorphic rocks from alignment of platy minerals (mica, chlorite) under directed pressure."},
    {"section":"Plate Tectonics","q":"What is an ophiolite?","a":"A slice of ancient oceanic crust emplaced (obducted) onto continental crust — preserves peridotite, gabbro, basalt, sediments."},
    {"section":"Plate Tectonics","q":"What is the Wilson Cycle?","a":"The cycle of opening and closing of ocean basins: continental rifting → ocean formation → subduction → collision → new supercontinent."},
    {"section":"Mineralogy","q":"What does Mohs hardness measure?","a":"A mineral's resistance to scratching, ranked 1 (Talc) to 10 (Diamond) — a quick field identification tool."},
    {"section":"Mineralogy","q":"What is cleavage in a mineral?","a":"A mineral's tendency to break along flat planes defined by weak atomic bonds — mica has perfect cleavage in one direction."},
    {"section":"Mineralogy","q":"What is streak in mineral identification?","a":"The color of a mineral's powder when scratched on an unglazed porcelain plate — more reliable than surface color, since it doesn't vary with impurities."},
    {"section":"Seismology","q":"What is the difference between P-waves and S-waves?","a":"P-waves (primary) are compressional and travel through solids and liquids; S-waves (secondary) are shear waves, slower, and cannot pass through liquids."},
    {"section":"Seismology","q":"What is the focus and epicenter of an earthquake?","a":"The focus (hypocenter) is the point underground where rupture begins; the epicenter is the point on the surface directly above it."},
    {"section":"Geomorphology","q":"What is a dendritic drainage pattern?","a":"A tree-branch-like river network that develops on uniform, gently-sloping rock with no major structural control."},
    {"section":"Geomorphology","q":"What is a peneplain?","a":"A low-relief landscape produced by long-term erosion that has worn mountains down nearly to base level."},
    {"section":"Indian Geology","q":"What are the Deccan Traps?","a":"A massive flood basalt province in western India (~500,000 km²) erupted around 66 Ma, linked to the K-Pg mass extinction."},
    {"section":"Indian Geology","q":"What is the Vindhyan Supergroup?","a":"A thick, largely undeformed Proterozoic sedimentary sequence spanning Madhya Pradesh, UP, and Rajasthan — key for studying ancient stratigraphy."},
    {"section":"Indian Geology","q":"What makes Charnockite significant in Indian geology?","a":"A hypersthene-bearing granulite first described near Chennai (named after Job Charnock's tombstone) — common in the high-grade Eastern Ghats belt."},
    {"section":"Soils & Resources","q":"What distinguishes black (regur) soil from alluvial soil?","a":"Black soil forms from weathered Deccan basalt, rich in clay and moisture-retentive (ideal for cotton); alluvial soil is river-deposited, lighter, and very fertile."},
    {"section":"Soils & Resources","q":"What is laterite and how does it form?","a":"A reddish, iron/aluminum-rich soil/rock formed by intense chemical weathering in hot, wet tropical climates — also a source of bauxite ore."},
    {"section":"Stratigraphy","q":"State the Law of Superposition.","a":"In an undisturbed sequence, younger rock layers lie above older ones — the foundational principle of stratigraphy."},
    {"section":"Structural Geology","q":"What is a Barrovian metamorphic zone?","a":"A sequence of increasing metamorphic grade mapped by index minerals: chlorite → biotite → garnet → staurolite → kyanite → sillimanite (George Barrow, 1893)."},
    {"section":"Igneous Petrology","q":"What is Bowen's Reaction Series?","a":"The sequence in which minerals crystallise from a cooling silicate melt (olivine→pyroxene→amphibole→biotite on the discontinuous branch; Ca-rich→Na-rich plagioclase on the continuous branch)."},
    {"section":"Geophysics","q":"What is the Mohorovičić Discontinuity (Moho)?","a":"The seismic boundary between Earth's crust and mantle, marked by a jump in P-wave velocity at ~35 km depth beneath continents."},
    {"section":"Historical Geology","q":"What is Pangaea?","a":"The supercontinent that existed ~335–175 Ma, containing virtually all of Earth's landmass, before rifting into Laurasia and Gondwana."},
    {"section":"Plate Tectonics","q":"What defines a convergent plate boundary?","a":"Two plates move toward each other — resulting in subduction (oceanic-continental/oceanic-oceanic) or continental collision (e.g. India-Eurasia forming the Himalayas)."},
    {"section":"Mineralogy","q":"What is pleochroism?","a":"The property of some minerals (e.g. biotite, tourmaline) to show different colours when viewed under plane-polarised light at different crystallographic orientations."},
    {"section":"Economic Geology","q":"What is a placer deposit?","a":"A concentration of dense, resistant minerals (gold, ilmenite, monazite) accumulated by gravity sorting in river or beach sediments."},
    {"section":"Volcanology","q":"What is the Volcanic Explosivity Index (VEI)?","a":"A 0–8 logarithmic scale ranking eruption size by ejected volume — VEI 0 is gentle Hawaiian effusion, VEI 8 is a super-eruption."},
    {"section":"Geomorphology","q":"What is a watershed divide?","a":"The topographic boundary separating two adjacent drainage basins, where surface runoff flows to different river systems on either side."},
    {"section":"Indian Geology","q":"What is the significance of the Aravalli Range?","a":"The world's oldest fold mountain range (>2 billion years, deeply eroded), running from Gujarat to Delhi — hosts marble, zinc, and lead deposits."},
]

INDEX_FOSSILS = {
    "Hadean": None,
    "Archaean": "Stromatolite",
    "Siderian": "Ediacaran biota",
    "Cambrian": "Trilobite",
    "Ordovician": "Graptolite",
    "Silurian": "Eurypterid",
    "Devonian": "Dunkleosteus",
    "Carboniferous": "Meganeura",
    "Permian": "Dimetrodon",
    "Triassic": "Ichthyosaur",
    "Jurassic": "Ammonite",
    "Cretaceous": "Triceratops",
    "Paleogene": "Nummulite",
    "Neogene": "Australopithecus",
    "Quaternary": "Woolly mammoth",
}

GEOLOGIC_TIME = [
    {"eon":"Hadean","era":"—","period":"—","start":4600,"color":"#1a1a2e","life":"No life — Earth forming, heavy bombardment, Moon forming"},
    {"eon":"Archaean","era":"—","period":"—","start":4000,"color":"#2d1b69","life":"First prokaryotes (bacteria) — stromatolites appear"},
    {"eon":"Proterozoic","era":"—","period":"Siderian","start":2500,"color":"#7c3aed","life":"First eukaryotes; Snowball Earth episodes; soft-bodied Ediacaran fauna"},
    {"eon":"Phanerozoic","era":"Palaeozoic","period":"Cambrian","start":541,"color":"#1d4ed8","life":"Cambrian Explosion — most animal phyla appear; trilobites dominate"},
    {"eon":"Phanerozoic","era":"Palaeozoic","period":"Ordovician","start":485,"color":"#2563eb","life":"Marine invertebrates flourish; first fish; mass extinction at end"},
    {"eon":"Phanerozoic","era":"Palaeozoic","period":"Silurian","start":444,"color":"#3b82f6","life":"First vascular plants on land; jawed fish evolve"},
    {"eon":"Phanerozoic","era":"Palaeozoic","period":"Devonian","start":419,"color":"#0ea5e9","life":"Age of Fishes; first amphibians; forests appear; Devonian extinction"},
    {"eon":"Phanerozoic","era":"Palaeozoic","period":"Carboniferous","start":359,"color":"#06b6d4","life":"Coal-forming swamp forests; first reptiles; giant insects"},
    {"eon":"Phanerozoic","era":"Palaeozoic","period":"Permian","start":299,"color":"#0891b2","life":"Reptiles diversify; Pangaea assembled; P-T extinction (96% marine species lost)"},
    {"eon":"Phanerozoic","era":"Mesozoic","period":"Triassic","start":252,"color":"#84cc16","life":"First dinosaurs and mammals; recovery after P-T extinction"},
    {"eon":"Phanerozoic","era":"Mesozoic","period":"Jurassic","start":201,"color":"#65a30d","life":"Dinosaurs dominate; first birds; Gondwana breaks up; India separates"},
    {"eon":"Phanerozoic","era":"Mesozoic","period":"Cretaceous","start":145,"color":"#16a34a","life":"Flowering plants; dinosaurs peak; Deccan Traps erupt; K-Pg extinction 66 Ma"},
    {"eon":"Phanerozoic","era":"Cenozoic","period":"Paleogene","start":66,"color":"#f59e0b","life":"Mammals diversify; India collides with Eurasia; Himalayas begin rising"},
    {"eon":"Phanerozoic","era":"Cenozoic","period":"Neogene","start":23,"color":"#f97316","life":"Grasslands spread; hominids evolve; Himalayas reach modern heights"},
    {"eon":"Phanerozoic","era":"Cenozoic","period":"Quaternary","start":2.6,"color":"#ef4444","life":"Ice ages; Homo sapiens evolve and spread; modern world"},
]

INDIA_GEO_PROVINCES = [
    {"name":"Himalayan Belt","lat":30.5,"lon":78.5,"age":"Cenozoic (50 Ma–present)",
     "rock":"Sedimentary, metamorphic, granitic intrusions","tectonic":"Active collisional orogen",
     "minerals":"Gold placer, copper, lead-zinc, coal","sites":"Nanda Devi, Gangotri, Rohtang",
     "color":"#f59e0b","size":18},
    {"name":"Indo-Gangetic Plain","lat":26.5,"lon":82.0,"age":"Quaternary alluvium (2.6 Ma–present)",
     "rock":"Alluvial sediments — sand, silt, clay","tectonic":"Foreland basin, flexural subsidence",
     "minerals":"Groundwater, sand & gravel, kankar lime","sites":"Varanasi, Allahabad, Patna",
     "color":"#10b981","size":16},
    {"name":"Deccan Trap Province","lat":18.5,"lon":75.0,"age":"Late Cretaceous (66 Ma)",
     "rock":"Tholeiitic basalt — 2 km thick lava piles","tectonic":"Continental flood basalt (hotspot?)",
     "minerals":"Zeolites, amethyst, calcite, iron","sites":"Ajanta Caves, Ellora, Lonar Crater",
     "color":"#ef4444","size":20},
    {"name":"Peninsular Shield (Dharwar)","lat":14.0,"lon":76.5,"age":"Archaean–Proterozoic (3.3–0.9 Ga)",
     "rock":"Gneiss, schist, greenstone belts","tectonic":"Ancient stable craton",
     "minerals":"Gold (Kolar), iron, manganese, chromite","sites":"Kolar Gold Field, Bellary",
     "color":"#8b5cf6","size":18},
    {"name":"Eastern Ghats Belt","lat":17.0,"lon":82.0,"age":"Proterozoic (1.6–0.5 Ga)",
     "rock":"Khondalite, charnockite, leptynite","tectonic":"High-grade granulite metamorphic belt",
     "minerals":"Graphite, corundum, chromite, bauxite","sites":"Araku Valley, Simhachalam",
     "color":"#06b6d4","size":14},
    {"name":"Aravalli–Delhi Belt","lat":26.0,"lon":73.5,"age":"Proterozoic (2.5–0.8 Ga)",
     "rock":"Quartzite, schist, phyllite, marble","tectonic":"Ancient orogenic belt (pre-Himalayan)",
     "minerals":"Zinc-lead (Zawar), copper (Khetri), marble (Makrana)","sites":"Udaipur, Pushkar, Jaisalmer",
     "color":"#f97316","size":16},
    {"name":"Gondwana Basins","lat":22.5,"lon":84.0,"age":"Permo-Carboniferous to Jurassic (290–150 Ma)",
     "rock":"Coal-bearing sandstone, shale","tectonic":"Continental rift basins on Indian plate",
     "minerals":"Coal (India's main reserves), oil shale","sites":"Raniganj, Jharia, Singrauli",
     "color":"#374151","size":16},
    {"name":"Andaman–Nicobar Arc","lat":11.5,"lon":92.8,"age":"Cenozoic (50 Ma–present)",
     "rock":"Ophiolite, volcanic arc rocks, flysch","tectonic":"Active subduction zone (Sunda Arc)",
     "minerals":"Chromite (ophiolite), manganese nodules","sites":"Barren Island (active volcano)",
     "color":"#dc2626","size":14},
    {"name":"Kutch–Cambay Basin","lat":22.5,"lon":71.0,"age":"Mesozoic–Cenozoic (150–0 Ma)",
     "rock":"Marine sediments, evaporites, limestone","tectonic":"Rift basin, passive margin",
     "minerals":"Oil & gas (Bombay High), gypsum, salt","sites":"Rann of Kutch, Bhuj",
     "color":"#0284c7","size":14},
    {"name":"Western Ghats","lat":12.0,"lon":75.5,"age":"Precambrian basement + Deccan lava",
     "rock":"Gneiss, charnockite, basalt","tectonic":"Passive margin escarpment",
     "minerals":"Bauxite, iron ore, silica sand","sites":"Agumbe, Kudremukh, Sahyadri",
     "color":"#15803d","size":14},
]

INDIA_EARTHQUAKES = [
    {"name":"Bhuj, Gujarat","year":2001,"mag":7.7,"lat":23.6,"lon":69.8,"depth":16,"deaths":20000},
    {"name":"Koyna, Maharashtra","year":1967,"mag":6.5,"lat":17.4,"lon":73.7,"depth":13,"deaths":177},
    {"name":"Latur, Maharashtra","year":1993,"mag":6.2,"lat":18.0,"lon":76.5,"depth":12,"deaths":9748},
    {"name":"Uttarkashi, Uttarakhand","year":1991,"mag":6.8,"lat":30.8,"lon":78.8,"depth":10,"deaths":768},
    {"name":"Chamoli, Uttarakhand","year":1999,"mag":6.8,"lat":30.5,"lon":79.4,"depth":21,"deaths":103},
    {"name":"Andaman Islands","year":2004,"mag":9.1,"lat":3.3,"lon":95.8,"depth":30,"deaths":227898},
    {"name":"Kashmir","year":2005,"mag":7.6,"lat":34.5,"lon":73.6,"depth":26,"deaths":86000},
    {"name":"Sikkim","year":2011,"mag":6.9,"lat":27.7,"lon":88.2,"depth":50,"deaths":111},
    {"name":"Nepal–India Border","year":2015,"mag":7.8,"lat":28.1,"lon":84.7,"depth":15,"deaths":8964},
    {"name":"Delhi NCR","year":1956,"mag":6.7,"lat":28.6,"lon":77.2,"depth":35,"deaths":0},
]

VOLCANOES = [
    {"name":"Barren Island","lat":12.28,"lon":93.86,"country":"India","status":"Active",
     "last_eruption":"2017","type":"Stratovolcano","wiki_photo":"Barren Island (India)",
     "desc":"India's only active volcano. Part of Andaman arc. Last major eruption 2017."},
    {"name":"Narcondam","lat":13.43,"lon":94.25,"country":"India","status":"Dormant",
     "last_eruption":"Unknown (prehistoric)","type":"Stratovolcano","wiki_photo":"Narcondam Island",
     "desc":"Dormant volcano, Andaman Islands. Dense forest, hornbill sanctuary."},
    {"name":"Mt. Etna","lat":37.75,"lon":15.00,"country":"Italy","status":"Active",
     "last_eruption":"2024","type":"Stratovolcano","wiki_photo":"Mount Etna",
     "desc":"Europe's highest & most active volcano. ~3,300 m. Almost continuously erupting."},
    {"name":"Kilauea","lat":19.42,"lon":-155.29,"country":"USA (Hawaii)","status":"Active",
     "last_eruption":"2023","type":"Shield volcano","wiki_photo":"Kilauea",
     "desc":"One of Earth's most active volcanoes. Lava flows reach ocean. Forms new land."},
    {"name":"Mt. Fuji","lat":35.36,"lon":138.73,"country":"Japan","status":"Dormant",
     "last_eruption":"1707","type":"Stratovolcano","wiki_photo":"Mount Fuji",
     "desc":"Japan's highest peak (3,776 m). Dormant since 1707. UNESCO World Heritage Site."},
    {"name":"Krakatau","lat":-6.10,"lon":105.42,"country":"Indonesia","status":"Active",
     "last_eruption":"2022","type":"Caldera/Stratovolcano","wiki_photo":"Krakatoa",
     "desc":"1883 eruption caused global cooling. Anak Krakatau (child of Krakatau) active today."},
    {"name":"Mt. Pinatubo","lat":15.14,"lon":120.35,"country":"Philippines","status":"Dormant",
     "last_eruption":"1991","type":"Stratovolcano","wiki_photo":"Mount Pinatubo",
     "desc":"1991 eruption (2nd largest 20th century) ejected 10 km³ of material, cooled Earth 0.5°C."},
    {"name":"Eyjafjallajökull","lat":63.63,"lon":-19.62,"country":"Iceland","status":"Dormant",
     "last_eruption":"2010","type":"Stratovolcano","wiki_photo":"Eyjafjallajökull",
     "desc":"2010 eruption disrupted European air travel for weeks. Iceland sits on Mid-Atlantic Ridge."},
    {"name":"Mount Merapi","lat":-7.54,"lon":110.44,"country":"Indonesia","status":"Active",
     "last_eruption":"2023","type":"Stratovolcano","wiki_photo":"Mount Merapi",
     "desc":"Indonesia's most active volcano — frequent pyroclastic flows above the densely populated Yogyakarta region."},
    {"name":"Mount Semeru","lat":-8.11,"lon":112.92,"country":"Indonesia","status":"Active",
     "last_eruption":"2024","type":"Stratovolcano","wiki_photo":"Semeru",
     "desc":"Java's highest peak and one of Indonesia's most persistently active volcanoes on the Sunda Arc."},
    {"name":"Piton de la Fournaise","lat":-21.24,"lon":55.71,"country":"Réunion (France)","status":"Active",
     "last_eruption":"2024","type":"Shield volcano","wiki_photo":"Piton de la Fournaise",
     "desc":"One of the world's most active shield volcanoes — sits over the same hotspot that produced the Deccan Traps ~66 Ma."},
    {"name":"Karthala","lat":-11.75,"lon":43.38,"country":"Comoros","status":"Active",
     "last_eruption":"2007","type":"Shield volcano","wiki_photo":"Karthala",
     "desc":"Largest active volcano in the western Indian Ocean, on Grande Comore island near Madagascar."},
    {"name":"Sinabung","lat":3.17,"lon":98.39,"country":"Indonesia","status":"Active",
     "last_eruption":"2021","type":"Stratovolcano","wiki_photo":"Mount Sinabung",
     "desc":"Sumatra volcano that reawakened in 2010 after centuries of dormancy — part of the same Sunda Arc as Barren Island."},
    {"name":"Taal Volcano","lat":14.00,"lon":120.99,"country":"Philippines","status":"Active",
     "last_eruption":"2022","type":"Caldera","wiki_photo":"Taal Volcano",
     "desc":"One of the world's smallest active volcanoes, sitting inside a lake-filled caldera on Luzon island."},
    {"name":"Damavand","lat":35.95,"lon":52.11,"country":"Iran","status":"Dormant",
     "last_eruption":"Unknown (prehistoric)","type":"Stratovolcano","wiki_photo":"Damavand",
     "desc":"Highest peak in the Middle East (5,610m) — a dormant volcano on the Alborz range near the Arabian-Eurasian collision zone."},
]

SOILS = [
    {"name":"Alluvial Soil","emoji":"🟡","color":"#f59e0b","wiki_term":"Alluvial soil",
     "states":"UP, Bihar, Punjab, Haryana, West Bengal",
     "formation":"Deposition by rivers (Ganga, Indus, Brahmaputra)",
     "crops":"Wheat, rice, sugarcane, cotton",
     "area_pct":43,
     "desc":"Most fertile and widespread soil (43% of India). Rich in potash, lime. Two types: Khadar (new) and Bhangar (old)."},
    {"name":"Black (Regur) Soil","emoji":"🟫","color":"#1f2937","wiki_term":"Regur soil",
     "states":"Maharashtra, MP, Gujarat, Andhra Pradesh",
     "formation":"Weathering of Deccan basaltic lava",
     "crops":"Cotton (hence 'black cotton soil'), soybean, sorghum",
     "area_pct":16,
     "desc":"Highly clayey — expands when wet, cracks when dry. Self-ploughing. Rich in iron, lime, magnesium. Cotton heartland."},
    {"name":"Red & Yellow Soil","emoji":"🔴","color":"#dc2626","wiki_term":"Red soil",
     "states":"Odisha, Chhattisgarh, Jharkhand, parts of AP",
     "formation":"Weathering of crystalline igneous and metamorphic rocks",
     "crops":"Rice, wheat, millets, pulses, groundnut",
     "area_pct":18,
     "desc":"Red color from iron oxide. Less fertile than alluvial. Porous, friable. Needs irrigation and fertiliser."},
    {"name":"Laterite Soil","emoji":"🟤","color":"#92400e","wiki_term":"Laterite",
     "states":"Kerala, Karnataka, Assam, Meghalaya, TN",
     "formation":"Intense leaching in high-rainfall tropical areas",
     "crops":"Tea, coffee, cashew, rubber, coconut",
     "area_pct":8,
     "desc":"Forms in hot wet tropical zones — aluminum and iron hydroxides remain after silica is leached. Used as building brick."},
    {"name":"Mountain Soil","emoji":"🏔️","color":"#4b5563","wiki_term":"Mountain soil",
     "states":"J&K, Himachal Pradesh, Uttarakhand, NE states",
     "formation":"Physical weathering on steep slopes, thin profile",
     "crops":"Apples, pears, potatoes, wheat (terraced)",
     "area_pct":8,
     "desc":"Thin, humus-rich in upper layers. Very variable. Acidic. Requires careful management to prevent erosion."},
    {"name":"Arid (Desert) Soil","emoji":"🏜️","color":"#fbbf24","wiki_term":"Desert soil",
     "states":"Rajasthan, parts of Gujarat, Haryana",
     "formation":"Physical weathering in dry climate, low organic matter",
     "crops":"Bajra, pulses (with irrigation — wheat, cotton)",
     "area_pct":4,
     "desc":"Sandy, low organic, high soluble salts. Irrigation causes waterlogging/salinisation. Caliche (kankar) layers common."},
    {"name":"Saline/Alkaline Soil","emoji":"🧂","color":"#e5e7eb","wiki_term":"Saline soil",
     "states":"Punjab, Haryana, UP, Rajasthan (waterlogged areas)",
     "formation":"High water table, poor drainage, evaporation brings salts",
     "crops":"Salt-tolerant grasses, date palm (with treatment)",
     "area_pct":3,
     "desc":"Usar/Reh soils — excess sodium salts damage plant roots. Can be reclaimed with gypsum application and drainage."},
]

RIVERS = [
    {"name":"Ganga","length_km":2525,"origin":"Gangotri Glacier, Uttarakhand","joins":"Bay of Bengal",
     "basin_km2":861000,"pattern":"Dendritic","tributaries":["Yamuna","Ghaghra","Son","Gandak","Kosi"],
     "states":["Uttarakhand","UP","Bihar","WB"],
     "geo":"Himalayan river — youthful with steep gradient in mountains, mature meandering on plains",
     "path":[(30.9,79.0),(29.9,78.2),(27.6,79.9),(25.6,82.5),(25.3,83.0),(24.8,85.0),(23.5,88.0),(22.0,89.0)]},
    {"name":"Brahmaputra","length_km":2900,"origin":"Angsi Glacier, Tibet (Yarlung Tsangpo)",
     "joins":"Bay of Bengal","basin_km2":651000,"pattern":"Braided",
     "tributaries":["Dibang","Lohit","Subansiri","Teesta"],
     "states":["Arunachal Pradesh","Assam"],
     "geo":"Antecedent river — older than Himalayas, carved gorge 5,500m deep in Eastern Himalayas",
     "path":[(29.5,90.5),(29.0,94.8),(28.1,95.6),(27.2,94.2),(26.2,91.7),(25.0,89.7),(23.5,89.8)]},
    {"name":"Godavari","length_km":1465,"origin":"Trimbakeshwar, Nashik, Maharashtra",
     "joins":"Bay of Bengal","basin_km2":312812,"pattern":"Dendritic-trellis",
     "tributaries":["Indravati","Pranhita","Manjira","Wardha"],
     "states":["Maharashtra","Telangana","AP"],
     "geo":"Largest peninsular river. Flows over Deccan Traps — gorges at Eastern Ghats. 'Dakshin Ganga'.",
     "path":[(20.0,73.8),(19.5,76.5),(18.7,79.5),(17.5,81.0),(16.9,82.2)]},
    {"name":"Krishna","length_km":1400,"origin":"Mahabaleshwar, Maharashtra",
     "joins":"Bay of Bengal","basin_km2":258948,"pattern":"Dendritic",
     "tributaries":["Bhima","Tungabhadra","Musi","Koyna"],
     "states":["Maharashtra","Karnataka","AP","Telangana"],
     "geo":"Flows over Deccan basalt. Nagarjunasagar and Srisailam dams in gorge through Eastern Ghats.",
     "path":[(17.9,73.7),(17.0,76.0),(16.3,79.0),(16.0,80.1),(15.8,80.9)]},
    {"name":"Indus","length_km":3180,"origin":"Sengge Zangbo, Tibet",
     "joins":"Arabian Sea","basin_km2":1165000,"pattern":"Dendritic",
     "tributaries":["Sutlej","Chenab","Ravi","Beas","Jhelum"],
     "states":["J&K","Ladakh (then Pakistan)"],
     "geo":"Ancient river — antecedent to Karakoram and Hindu Kush. Forms alluvial plains of Punjab.",
     "path":[(32.5,80.1),(34.1,77.6),(35.0,74.5),(33.5,73.0),(28.0,69.5),(24.0,67.5)]},
    {"name":"Narmada","length_km":1312,"origin":"Amarkantak, MP",
     "joins":"Arabian Sea","basin_km2":98796,"pattern":"Rectangular (fault-controlled)",
     "tributaries":["Tawa","Burhner","Hiran","Orsang"],
     "states":["MP","Maharashtra","Gujarat"],
     "geo":"Flows W-E along Narmada rift — a graben between Vindhyas and Satpuras. Marble Rocks at Bhedaghat.",
     "path":[(22.7,81.8),(22.8,78.8),(22.3,76.5),(22.0,73.5),(21.7,72.8)]},
    {"name":"Yamuna","length_km":1376,"origin":"Yamunotri Glacier, Uttarakhand","joins":"Ganga at Prayagraj",
     "basin_km2":366223,"pattern":"Dendritic","tributaries":["Chambal","Betwa","Ken","Sindh"],
     "states":["Uttarakhand","Himachal","Haryana","Delhi","UP"],
     "geo":"Major Ganga tributary, flows past Delhi and Agra before joining the Ganga at the Sangam in Prayagraj.",
     "path":[(31.0,78.4),(30.1,77.6),(28.6,77.2),(27.2,77.9),(25.4,81.9)]},
    {"name":"Mahanadi","length_km":858,"origin":"Sihawa, Chhattisgarh","joins":"Bay of Bengal",
     "basin_km2":141600,"pattern":"Dendritic","tributaries":["Seonath","Hasdeo","Ib","Tel"],
     "states":["Chhattisgarh","Odisha"],
     "geo":"Drains the Eastern Ghats and central Indian plateau; the Hirakud Dam forms one of the world's longest earthen dams.",
     "path":[(20.6,81.4),(20.8,82.7),(20.5,84.0),(20.3,85.0),(20.3,86.7)]},
    {"name":"Tapi","length_km":724,"origin":"Multai, Madhya Pradesh","joins":"Arabian Sea",
     "basin_km2":65145,"pattern":"Rectangular (fault-controlled)","tributaries":["Purna","Girna","Panzara"],
     "states":["MP","Maharashtra","Gujarat"],
     "geo":"Flows west through a fault-bounded rift valley parallel to the Narmada, between the Satpura and the Deccan plateau edge.",
     "path":[(21.8,78.3),(21.2,76.0),(21.1,74.0),(21.2,72.8)]},
    {"name":"Sutlej","length_km":1450,"origin":"Lake Rakshastal, Tibet","joins":"Indus (Pakistan)",
     "basin_km2":395000,"pattern":"Dendritic","tributaries":["Beas","Spiti"],
     "states":["Himachal Pradesh","Punjab"],
     "geo":"Longest of the five Punjab rivers; an antecedent river that cuts directly across the rising Himalayan ranges.",
     "path":[(31.4,81.0),(31.7,78.7),(31.6,76.5),(31.0,75.3),(30.0,72.0)]},
    {"name":"Chambal","length_km":960,"origin":"Janapav Hills, Madhya Pradesh","joins":"Yamuna",
     "basin_km2":143219,"pattern":"Dendritic, heavily gullied (badlands)","tributaries":["Banas","Kali Sindh","Parbati"],
     "states":["MP","Rajasthan","UP"],
     "geo":"Famous for the Chambal ravines — deep badland gullies carved into soft alluvium, a unique erosional landscape.",
     "path":[(22.6,75.5),(24.0,75.9),(25.3,76.7),(26.5,79.0),(26.6,79.2)]},
    {"name":"Tungabhadra","length_km":531,"origin":"Western Ghats, Karnataka","joins":"Krishna",
     "basin_km2":71417,"pattern":"Dendritic","tributaries":["Tunga","Bhadra","Varada"],
     "states":["Karnataka","Andhra Pradesh"],
     "geo":"Formed by the union of the Tunga and Bhadra rivers; flows through the historic Hampi (Vijayanagara) region.",
     "path":[(13.4,75.4),(15.0,76.3),(15.8,77.5),(16.0,78.6)]},
]

ECONOMIC_MINERALS = {
    "Coal": {"states":{"Jharkhand":26,"Odisha":25,"Chhattisgarh":17,"WB":11,"MP":9,"Others":12},
             "color":"#374151","emoji":"🪨","use":"Power (80%), coking coal for steel","india_rank":"World #3 producer"},
    "Iron Ore": {"states":{"Odisha":35,"Chhattisgarh":22,"Jharkhand":16,"Karnataka":14,"Others":13},
                  "color":"#b45309","emoji":"🧲","use":"Steel industry, export","india_rank":"World #4 producer"},
    "Bauxite": {"states":{"Odisha":50,"Jharkhand":17,"Gujarat":9,"Maharashtra":8,"Others":16},
                 "color":"#92400e","emoji":"🟤","use":"Aluminium production (99%)","india_rank":"World #5 producer"},
    "Copper": {"states":{"Rajasthan":52,"Jharkhand":34,"MP":8,"Others":6},
                "color":"#b45309","emoji":"🟠","use":"Electrical wiring, plumbing, electronics","india_rank":"Minor producer, imports ~95%"},
    "Zinc-Lead": {"states":{"Rajasthan":90,"Others":10},
                   "color":"#6b7280","emoji":"⚙️","use":"Galvanising steel, batteries, paint","india_rank":"World #1 in zinc (Hindustan Zinc)"},
    "Chromite": {"states":{"Odisha":92,"Karnataka":5,"Others":3},
                  "color":"#1f2937","emoji":"🟫","use":"Stainless steel, refractory bricks","india_rank":"World #4 producer"},
    "Gold": {"states":{"Karnataka":75,"Andhra Pradesh":20,"Others":5},
              "color":"#f59e0b","emoji":"🥇","use":"Jewellery, electronics, reserves","india_rank":"Minor; imports ~800 tonnes/yr"},
    "Limestone": {"states":{"Rajasthan":22,"AP":16,"Karnataka":14,"Gujarat":9,"Others":39},
                   "color":"#e5e7eb","emoji":"🧱","use":"Cement (#1), steel flux, agriculture","india_rank":"World #2 cement producer"},
}

NOTES = {
    "Semester 1": {
        "ESMJ11 — Elements of Earth Sciences": [
            "**Unit I — Earth as a Planet**: Origin by nebular hypothesis; size, shape (oblate spheroid), mass (5.97×10²⁴ kg), density (5.51 g/cc). Internal constitution: Core (inner solid Fe-Ni, outer liquid), Mantle (silicates, peridotite), Crust (continental granitic + oceanic basaltic). Mohorovičić discontinuity separates crust from mantle.",
            "**Unit II — Geological Principles**: Catastrophism vs Uniformitarianism ('The present is the key to the past' — Hutton). Laws of Superposition, Faunal Succession (W. Smith), Original Horizontality. Origin of atmosphere (volcanic outgassing), hydrosphere, biosphere. Weathering: mechanical (frost, thermal) vs chemical (oxidation, hydrolysis, carbonation). Mass wasting: rockfall, landslide, creep.",
            "**Unit III — Earthquakes & Volcanoes**: Earthquake belts — Circum-Pacific ('Ring of Fire'), Alpine-Himalayan, Mid-oceanic ridges. Volcano types: Shield (Hawaii, basaltic, gentle), Stratovolcano (composite, explosive, e.g. Vesuvius), Caldera (post-eruption collapse). Volcanic belts mirror plate boundaries. Geological Time Scale — Eons, Eras, Periods, Epochs; radiometric dating (U-Pb, K-Ar, Rb-Sr, C-14).",
            "**Unit IV — Structural Geology Intro**: Primary structures (bedding, graded bedding, cross-bedding, ripple marks) vs secondary (folds, faults, joints). Strike = compass direction of a bedding trace on horizontal surface; Dip = angle + direction of maximum inclination. Clinometer compass usage. Plunge of folds. Fold types: anticline, syncline, isoclinal, recumbent. Fault types: normal, reverse, thrust, strike-slip.",
        ],
        "ESMD11 — Evolving Earth (Multi-disciplinary)": [
            "**Scope of Earth Sciences**: Geology, geophysics, geochemistry, oceanography, atmospheric science — all linked. Sub-disciplines: petrology, mineralogy, structural geology, stratigraphy, palaeontology, hydrogeology, economic geology, engineering geology, remote sensing.",
            "**Plate Tectonics Overview**: Wegener's Continental Drift (1912) → Seafloor spreading (Hess, 1960) → Plate Tectonics. Evidence: palaeomagnetism, fit of continents, matching fossils/rock types across oceans, GPS measurements today.",
            "**Mass Extinctions & Ice Ages**: Five major extinctions: End-Ordovician (glaciation), Late Devonian, End-Permian (96% species lost — Siberian Traps volcanism), End-Triassic, K-Pg (asteroid + Deccan Traps). Milankovitch cycles drive ice ages: eccentricity (100 ka), obliquity (41 ka), precession (23 ka).",
            "**Solar System & Earth Structure**: Solar system 4.6 Ga old — solar nebula collapse. Terrestrial vs Jovian planets. Earth's layers detected via seismic wave behaviour. P-wave shadow zone → liquid outer core. S-wave shadow zone → confirms liquid outer core. Inner core boundary detected at ~5,150 km depth.",
        ],
        "ESSE11 — Smartphone Geosciences (SEC)": [
            "**Geology Apps**: Rockd, iRocks, GeoMapApp, FieldMove Clino (strike/dip measurement), Mineral Identifier, Earthquake by USGS, BHUVAN (ISRO India maps), Google Earth — all useful in field.",
            "**Digital Compass & GPS**: NAVIC (India's regional satellite navigation system), GPS Apps for geotagging samples. Digital compass for bearing (fore + back bearings). FieldMove Clino measures dip/strike using phone accelerometer + gyroscope.",
            "**Remote Data Tools**: Google Earth — distance, elevation, geology overlays. BHUVAN (bhuvan.nrsc.gov.in) — ISRO's India-specific satellite viewer, free high-resolution imagery. NASA Worldview — real-time satellite data.",
        ],
    },
    "Semester 2": {
        "ESMJ21 — Minerals and Earth Material": [
            "**Fundamentals of Mineralogy**: Mineral = naturally occurring, inorganic, definite chemical composition, crystalline atomic structure. ~4,000 known minerals; ~30 are rock-forming. Mineral-forming processes: igneous (crystallisation from melt), sedimentary (precipitation, evaporation), metamorphic (recrystallisation under P-T).",
            "**Physical Properties**: Colour (unreliable), streak (reliable — scratch on porcelain plate), lustre (metallic, vitreous, resinous, pearly, silky, earthy), hardness (Mohs 1–10), cleavage (perfect/good/poor — defined by atomic structure), fracture (conchoidal, hackly, uneven), specific gravity (ratio to water density), special: magnetism (magnetite), fluorescence, taste (halite), smell (sulphur).",
            "**Key Rock-forming Minerals**: Silicates — Olivine (Mg,Fe)₂SiO₄, Pyroxene (augite, hypersthene), Quartz SiO₂, Feldspar (orthoclase KAlSi₃O₈, albite NaAlSi₃O₈, labradorite), Mica (muscovite, biotite), Amphibole (hornblende), Clay minerals (serpentine, talc, kaolinite). Carbonates: Calcite CaCO₃ (fizzes in HCl), Dolomite CaMg(CO₃)₂. Sulphates: Gypsum. Phosphates: Apatite.",
            "**Optical Mineralogy**: Light behaviour: reflection, refraction, polarisation. Nicol prism (calcite crystal) polarises light. Polarising microscope: PPL (one polariser) + XPL (crossed polars). Isotropic minerals (cubic) → dark under XPL. Anisotropic → interference colours (Michel-Lévy chart). Key properties: relief, colour, pleochroism, cleavage, extinction angle, twinning, birefringence.",
            "**Crystallography**: 7 crystal systems defined by axial lengths + angles: Cubic (a=b=c, 90°), Tetragonal, Orthorhombic, Hexagonal, Trigonal, Monoclinic, Triclinic. Crystal forms: cube, octahedron, rhombohedron, prism, pyramid, pinacoid, dome. Miller indices (hkl) define crystal faces.",
        ],
        "ESMD21 — Earth, Environment and Society": [
            "**Physical Divisions of India**: (1) Himalayas — Trans-Himalaya, Greater Himalaya (Himadri), Lesser Himalaya (Himachal), Siwaliks. (2) Northern Plains — alluvial, Ganga-Indus-Brahmaputra. (3) Peninsular Plateau — Deccan, Chota Nagpur, Malwa. (4) Coastal Plains — Eastern (wide, deltaic) and Western (narrow, backed by Ghats). (5) Islands — Andaman & Nicobar (volcanic arc) and Lakshadweep (coral atolls).",
            "**Geological Hazards**: Earthquakes — seismic zones I–V (India). Floods — annually in Brahmaputra, Ganga plains. Landslides — Himalayan and Western Ghats regions. Tsunamis — 2004 Indian Ocean (M9.1, ~230,000 deaths). Volcanoes — Barren Island (active). Droughts — cyclical in Rajasthan, Deccan.",
            "**Atmosphere & Hydrosphere**: Atmospheric layers: troposphere (weather), stratosphere (ozone), mesosphere, thermosphere, exosphere. Hydrological cycle: evaporation → condensation → precipitation → runoff → infiltration → groundwater → back to ocean. Groundwater: aquifers, water table, recharge zones.",
            "**Geo-heritage Sites of India**: Lonar Crater (Maharashtra) — meteorite impact; Dinosaur Fossil Park (Balasinor, Gujarat); Marble Rocks, Bhedaghat (Jabalpur); Columnar basalt at St. Mary's Island, Karnataka; Cretaceous-Paleogene boundary sections in Deccan.",
        ],
        "ESSE21 — Gemology (SEC)": [
            "**Gem Properties**: Hardness (>7 Mohs for most gems — resistance to scratching), refractive index (determines brilliance and fire), specific gravity, colour, clarity, fluorescence. The 4 Cs: Cut, Clarity, Colour, Carat weight.",
            "**Indian Gems**: Diamonds (Panna, MP — from Vindhyan kimberlite pipes), Emeralds (Rajasthan — Ajmer, Bubani), Rubies & Sapphires (Kashmir — finest blue sapphires; Tamil Nadu), Garnets (Rajasthan, Odisha), Alexandrite (Andhra Pradesh).",
            "**Synthetic vs Natural**: Synthetic gems have identical chemistry but formed in lab (hydrothermal or flame-fusion). Detection: inclusions, growth patterns, UV fluorescence, spectroscopy. Simulants are different materials that look similar (e.g., cubic zirconia simulating diamond).",
        ],
    },
    "Semester 3": {
        "ESMJ31 — Physical Geology": [
            "**Geomorphic Agents & Processes**: Running water — most powerful agent. Erosion → transportation → deposition. River stages: youth (V-valley, waterfalls, rapids), maturity (meandering, floodplain), old age (oxbow lakes, wide valley). Glaciers: U-valley, cirque, arête, horn (e.g. Matterhorn), drumlin, esker, moraine. Wind: deflation, abrasion → yardang, ventifact, barchan dune. Waves: wave-cut notch/platform, sea arch, stack, cave.",
            "**Weathering in India**: Chemical weathering dominates in humid tropics (Western Ghats, NE India) — laterisation, kaolinisation. Mechanical weathering dominates in deserts (Rajasthan — salt crystallisation, insolation) and cold mountains (Himalayas — frost action). Spheroidal weathering in granites (Karnataka, Rajasthan).",
            "**Drainage Basins of India**: Himalayan rivers (perennial, antecedent, e.g. Indus, Ganga, Brahmaputra) vs Peninsular rivers (seasonal, consequent, shorter, e.g. Godavari, Krishna, Narmada, Tapi). Drainage patterns: dendritic (homogeneous rock), trellis (folded strata), rectangular (joints), radial (volcanic dome/hill). Divide = watershed boundary.",
            "**Geological Work of Ice & Wind**: Glacial erosion: plucking (quarrying) and abrasion → roches moutonnées, striations. Glacial deposits: till (unsorted), outwash (sorted by water). Aeolian erosion: deflation hollows, desert pavement. Coastal processes: longshore drift, constructive vs destructive waves.",
        ],
        "ESMJ32 — Elementary Structural Geology": [
            "**Stress & Strain**: Normal stress (perpendicular to surface), shear stress (parallel). Principal stresses σ₁ > σ₂ > σ₃. Strain = change in shape/volume. Elastic (recoverable), plastic (permanent), brittle (fracture) behaviour depends on temperature, pressure, confining pressure, strain rate, rock type.",
            "**Folds**: Parts — hinge (line of max curvature), limbs, axial plane, fold axis. Types: anticline (core = older), syncline (core = younger), isoclinal (parallel limbs), recumbent (axial plane horizontal), overturned (one limb inverted), box fold, chevron fold. Plunge = inclination of fold axis.",
            "**Faults**: Normal (extensional — hanging wall moves down), Reverse (compressional — hanging wall moves up), Thrust (reverse at <45° — e.g. MCT, MBT, MFT in Himalayas), Strike-slip (horizontal — left-lateral vs right-lateral). Fault rocks: fault breccia, fault gouge, cataclasite, mylonite.",
            "**Joints**: Systematic joints (parallel sets) vs non-systematic. Columnar joints (cooling basalt — Deccan, St. Mary's Island). Tension gashes, pressure solution seams. Joints control groundwater flow, quarrying, engineering works.",
            "**Primary Sedimentary Structures**: Bedding/stratification, graded bedding, cross-bedding (aeolian or fluvial), ripple marks (current vs wave), mud cracks, sole marks, flute casts — all indicate palaeoenvironment and way-up.",
        ],
    },
    "Semester 4": {
        "ESMJ41 — Petrology and Economic Geology": [
            "**Igneous Petrology**: Bowen's Reaction Series — continuous branch: Ca-plagioclase → Na-plagioclase; discontinuous: olivine → pyroxene → amphibole → biotite. Magma types by SiO₂: ultramafic (<45%), mafic (45–52%), intermediate (52–63%), felsic (>63%). CIPW normative mineralogy from whole-rock chemistry. Igneous textures: phaneritic, aphanitic, porphyritic, glassy, vesicular, amygdaloidal, pyroclastic.",
            "**Metamorphic Petrology**: Facies concept (Eskola, 1920): zeolite, prehnite-pumpellyite, greenschist, amphibolite, granulite, blueschist (high P, low T — subduction), eclogite. Barrovian zones (Barrow, 1893): chlorite→biotite→garnet→staurolite→kyanite→sillimanite. Index minerals track isograds (lines of equal metamorphic grade).",
            "**Economic Geology Intro**: Ore deposit types — magmatic (chromite, PGE in dunite/peridotite), hydrothermal (gold, Cu, Pb-Zn — from hot water), skarn (W, Mo at igneous-carbonate contacts), sedimentary/exhalative (SEDEX — Pb-Zn), residual (bauxite, laterite), placer (gold, ilmenite, monazite on beaches).",
            "**Indian Ore Deposits**: Iron BIF in Odisha–Jharkhand (Bailadila, Barbil). Kolar Gold Field (KGF) — greenstone belt, 3.8 km deep, Archaean. Zawar Mines (Rajasthan) — Zn-Pb, world's largest integrated zinc producer. Chromite — Sukinda Valley, Odisha (>90% India's chromite). Bauxite — Panchpatmali, Odisha. Coal — Jharkhand, Odisha, Chhattisgarh (Gondwana age).",
        ],
        "ESMJ42 — Palaeontology and Stratigraphy": [
            "**Fossilisation**: Conditions: rapid burial, hard parts, absence of scavengers/O₂. Types: actual remains (permafrost mammoths), replacement (silicified wood), mould (external impression), cast (internal fill), trace fossils/ichnofossils (burrows, tracks, coprolites), compression, amber preservation.",
            "**Index Fossils**: Short stratigraphic range, wide geographic distribution, easily identifiable. Examples: Ammonites (Mesozoic), Graptolites (Ordovician–Silurian), Fusulinids (Carboniferous–Permian), Trilobites (Cambrian–Permian), Foraminifera (Mesozoic–Recent — used in oil exploration).",
            "**Gondwana Biostratigraphy (India)**: Glossopteris flora (seed fern) — Permian, found across India, Africa, Australia, Antarctica, S. America → proof of Gondwana supercontinent. Gangamopteris, Vertebraria (root system of Glossopteris). Rajmahal Traps flora (Mesozoic). Siwalik fauna (Miocene-Pleistocene mammals).",
            "**Stratigraphic Principles**: Superposition, Original Horizontality, Lateral Continuity, Cross-cutting Relationships, Faunal Succession. Unconformity types: angular unconformity, disconformity, nonconformity, paraconformity. Lithostratigraphy (rock type), Biostratigraphy (fossils), Chronostratigraphy (time), Magnetostratigraphy (polarity reversals).",
            "**Indian Stratigraphy**: Archaean (Dharwar Craton >2.5 Ga) → Proterozoic (Aravalli, Vindhyan 1.7–0.6 Ga) → Gondwana (Permian–Jurassic, coal-bearing) → Deccan Traps (66 Ma) → Siwalik molasse (Miocene–Pleistocene) → Quaternary alluvium.",
        ],
        "ESMJ43 — Environmental Geology & Hydrogeology": [
            "**Environmental Geology**: Study of interaction between humans and the geological environment. Topics: geohazards (earthquakes, floods, landslides, tsunamis, volcanoes), land use planning, waste disposal, contamination, climate change, sea-level rise. India's vulnerability: flood plains, coastal zones, seismic zones IV–V.",
            "**Hydrogeology**: Aquifer = water-bearing permeable rock/sediment. Types: Unconfined (water table aquifer, recharged directly), Confined (artesian — pressurised, piezometric surface above top of aquifer), Perched (isolated above main water table), Leaky (aquitard allows slow leakage). Darcy's Law: Q = KiA (K = hydraulic conductivity, i = hydraulic gradient, A = cross-sectional area).",
            "**Indian Groundwater**: Alluvial aquifers (Indo-Gangetic plains — most productive). Hard rock aquifers (fractured granite/basalt in Peninsular India — limited storage). India extracts ~25% of world's groundwater. GRACE satellite shows alarming depletion in NW India (Punjab, Haryana). Chennai's 2019 water crisis — aquifer over-extraction.",
            "**Remote Sensing Basics**: Electromagnetic spectrum: gamma, X-ray, UV, visible (0.4–0.7 μm), NIR, SWIR, TIR, microwave. Satellites: Landsat-9 (30m), Sentinel-2 (10m), Resourcesat-2 (5.8m), Cartosat-3 (0.25m). NDVI = (NIR-Red)/(NIR+Red) — vegetation index. Geological applications: lithological mapping, lineament detection, soil moisture, flood monitoring.",
        ],
    },
    "Semester 5": {
        "ESMJ51 — Metamorphic Petrology": [
            "**Metamorphic Agents**: Heat (contact around intrusions), pressure (lithostatic from burial + directed tectonic stress), chemically active fluids (hydrothermal — metasomatism). Types: contact/thermal (hornfels, skarn), regional/dynamo-thermal (schist, gneiss, eclogite), dynamic/cataclastic (mylonite along faults), burial metamorphism (zeolite facies).",
            "**Metamorphic Facies**: Zeolite (T<200°C, low P) → Prehnite-Pumpellyite → Greenschist (chlorite, epidote, actinolite, albite) → Amphibolite (hornblende, plagioclase — migmatite boundary) → Granulite (high T, low H₂O — pyroxene stable) → Blueschist (high P, low T — glaucophane — subduction zones) → Eclogite (garnet+omphacite — very high P).",
            "**Barrovian Zones**: Mapped by George Barrow in Scottish Highlands (1893): Chlorite zone → Biotite zone → Garnet zone → Staurolite zone → Kyanite zone → Sillimanite zone. Each zone records increasing P-T metamorphic conditions. Isograds = surfaces (lines on map) connecting first appearance of index mineral.",
            "**Indian Metamorphic Terrains**: Eastern Ghats Mobile Belt (granulite facies, 1.0–0.5 Ga — part of former Gondwana suture). Himalayan metamorphics — MCT zone shows inverted metamorphism (higher grade rocks above lower grade). Aravalli-Delhi fold belt (amphibolite–greenschist). Southern Granulite Terrain (SGT), Tamil Nadu — charnockites.",
        ],
        "ESMJ52 — Sedimentary Petrology": [
            "**Sedimentary Processes**: Weathering → erosion → transport (traction, saltation, suspension, solution) → deposition → burial → diagenesis → lithification. Diagenesis: compaction, cementation (silica, calcite, iron oxide), dissolution, recrystallisation, dolomitisation.",
            "**Clastic vs Non-Clastic**: Clastic — fragments of pre-existing rocks: conglomerate, breccia, sandstone, siltstone, shale (size grades by Wentworth scale). Non-clastic (chemical/biochemical): limestone (CaCO₃ — reef, chalk, oolitic), chert, rock salt/gypsum (evaporites), coal (organic), BIF (banded iron formation — Precambrian).",
            "**Sedimentary Structures**: Cross-bedding (flow direction indicator — foresets dip downstream), graded bedding (turbidites — coarse at base to fine at top), ripple marks (current vs oscillation), mud cracks (subaerial exposure), flute casts and groove casts (palaeocurrent), bioturbation (organism mixing).",
            "**Indian Sedimentary Basins**: Gondwana basins (Damodar, Mahanadi — Permian–Jurassic coal). Vindhyan basin (MP, UP, Rajasthan — Proterozoic). Kutch basin (Jurassic marine — ammonites). Jaisalmer basin (Jurassic). Krishna-Godavari offshore basin (oil/gas). Mumbai High (Paleocene-Eocene carbonate — largest oil field).",
        ],
        "ESMJ53 — Igneous Petrology": [
            "**Magma Genesis**: Partial melting of mantle (peridotite) → basaltic magma. Mechanisms: decompression melting (mid-ocean ridges, hotspots — pressure drop), flux melting (subduction zones — water from slab lowers solidus), heat transfer (crustal melting → granites). Primary magma → differentiation by fractional crystallisation, assimilation, magma mixing.",
            "**Volcanic vs Plutonic**: Plutonic (intrusive) — slow cooling → coarse-grained (phaneritic). Volcanic (extrusive) — rapid cooling → fine-grained (aphanitic) or glassy. Hypabyssal — intermediate (dykes, sills) → porphyritic. Intrusive bodies: batholith (>100 km²), stock, laccolith, lopolith, phacolith, dyke (discordant), sill (concordant).",
            "**Deccan Traps (India)**: Continental flood basalts erupted 66–60 Ma at NW Deccan (moved SE with India's drift). Volume: ~500,000 km², thickness up to 3 km. Tholeiitic basalts in multiple flows with red boles (palaeosols) between flows. Western Ghats escarpment formed by differential erosion of flows. CO₂ release contributed to K-Pg environmental crisis.",
            "**Alkaline Rocks & Kimberlites**: Alkaline rocks (nephelinite, phonolite, carbonatite) at rifts and hotspots — Sung Valley carbonatite (Meghalaya). Kimberlites — ultramafic, K-rich, gas-charged pipes from >150 km depth, carrying mantle xenoliths and diamonds. Majhgawan pipe, Panna (MP) — India's primary diamond source.",
        ],
        "ESMJ54 — Mineralogy and Crystallography": [
            "**Crystal Symmetry Elements**: Centre of symmetry, planes of symmetry, axes of symmetry (2-fold/diad, 3-fold/triad, 4-fold/tetrad, 6-fold/hexad). Point groups (32 crystal classes) and space groups (230). Crystal habit: prismatic, tabular, acicular, bladed, equant, platy, fibrous.",
            "**Systematic Mineralogy**: Native elements (gold, diamond, sulphur, graphite), Sulphides (galena, sphalerite, chalcopyrite, pyrite — metallic lustre, high SG), Oxides (magnetite, haematite, corundum, rutile), Halides (halite, fluorite), Carbonates (calcite, dolomite — rhombic cleavage), Sulphates (gypsum, barite), Phosphates (apatite — in bones/teeth), Silicates (largest group — SiO₄ tetrahedra framework).",
            "**Silicate Classification**: Nesosilicates (isolated SiO₄ — olivine, garnet, zircon), Sorosilicates (two tetrahedra — epidote), Cyclosilicates (rings — tourmaline, beryl), Inosilicates (chains — single chain = pyroxenes, double chain = amphiboles), Phyllosilicates (sheets — mica, clay, talc, chlorite), Tectosilicates (3D framework — quartz, feldspar, zeolite).",
            "**X-Ray Diffraction (XRD)**: Bragg's Law: nλ = 2d sinθ. Each mineral has unique d-spacing fingerprint. XRD identifies minerals in fine-grained rocks, clays, and mixtures — essential for research and industry (cement, ceramics, pharma).",
        ],
    },
    "Semester 6": {
        "ESMJ61 — Structural Geology (Advanced)": [
            "**Deformation Analysis**: Finite strain — stretching (S) and rotation. Strain ellipsoid (XYZ axes). Flinn diagram (k-values): k>1 = constriction (cigar shape), k<1 = flattening (pancake), k=1 = plane strain. Kinematic indicators: sigma and delta porphyroclasts, S-C fabrics, shear bands, asymmetric boudins — all record shear sense.",
            "**Ductile Shear Zones**: Mylonite, ultramylonite, protomylonite. Fabric oblique to shear zone = kinematics. Vorticity analysis. Crustal-scale ductile shear zones mark sutures, terrane boundaries, MCT-type structures in Himalayas.",
            "**Thrust Systems**: Fold-thrust belts (thin-skinned vs thick-skinned). Piggyback thrusting (youngest fault in foreland) vs break-back (hinterland). Duplexes, triangle zones, pop-up structures. Himalayan foreland: MFT (Main Frontal Thrust — active, ~5 mm/yr of shortening) → MBT → MCT → STDS (South Tibetan Detachment System).",
            "**Basin Analysis Intro**: Sedimentary basins classified by tectonic setting: rift basins (East Africa, Cambay), passive margin (Krishna-Godavari offshore), foreland basin (Ganga basin — flexural subsidence from Himalayan load), strike-slip basin, backarc basin. Sequence stratigraphy: systems tracts, transgressive-regressive cycles, eustasy.",
        ],
        "ESMJ62 — Economic Geology (Advanced)": [
            "**Hydrothermal Ore Deposits**: Formed by hot aqueous fluids (100–500°C). Epithermal (shallow, low T — Au, Ag, Hg), Mesothermal (medium depth — Au-quartz veins), Hypothermal (deep, high T — Sn, W, Mo). Fluid sources: magmatic, meteoric, metamorphic, seawater. Indian examples: Hutti Gold Mine (Karnataka), Sindesar Khurd (Rajasthan — Zn-Pb).",
            "**Sedimentary Ore Deposits**: BIF (Banded Iron Formation) — Precambrian, alternate silica-iron bands (hematite, magnetite), origin debated (ocean chemistry change). Coal — Gondwana (Permian, best coking coal) and Tertiary (lignite, Tamil Nadu). Phosphorite — Rajasthan, Mussoorie syncline. Evaporites — salt, gypsum (Rajasthan, Gujarat).",
            "**Placer Deposits**: Heavy minerals concentrated by running water or waves on beaches. Gold placers (Himalayan rivers), beach placers of India (Kerala, Tamil Nadu, Odisha): ilmenite (Ti), rutile (Ti), zircon (Zr, Hf), monazite (REE, Th), garnet. IREL (Indian Rare Earths Limited) operates these deposits.",
            "**Mineral Policy & GSI**: Geological Survey of India (GSI, est. 1851) — geological mapping, mineral exploration, seismic monitoring. MECL (Mineral Exploration Corporation Ltd.) — detailed exploration. NMDC, SAIL, Hindustan Zinc, Coal India — major PSUs. National Mineral Policy 2019: auction-based allocation, transparency, sustainable mining.",
        ],
        "ESMJ63 — Palaeontology (Advanced)": [
            "**Invertebrate Palaeontology**: Porifera (sponges — siliceous/calcareous spicules), Coelenterata (corals — rugose Palaeozoic, scleractinian Mesozoic-Recent), Brachiopoda (lamp shells — lophophore feeding; Ordovician index fossils), Mollusca (bivalves, gastropods, cephalopods — ammonites, belemnites), Echinodermata (echinoids, crinoids), Graptolita (colonial, Ordovician-Silurian index fossils).",
            "**Vertebrate Palaeontology**: Pisces → Amphibia → Reptilia (Age of Reptiles = Mesozoic) → Mammalia (Cenozoic explosion after K-Pg). Indian Siwalik sequence (Miocene-Pleistocene): abundant mammal fossils — Sivapithecus (great ape), Stegodon (elephant ancestor), Equus (horse), Bos (cattle). Rajasaurus narmadensis — Indian dinosaur from Late Cretaceous (Narmada valley, Gujarat).",
            "**Microfossils**: Foraminifera (calcareous shells, key in oil exploration for biostratigraphy and palaeo-water depth). Ostracoda (bivalved crustaceans — fresh and marine). Conodonts (phosphatic teeth elements — Palaeozoic–Triassic index fossils). Palynology (pollen and spores — palaeoclimate, coal stratigraphy).",
        ],
        "ESMJ64 — Stratigraphy (Advanced)": [
            "**Stratigraphic Codes**: International Stratigraphic Guide (ISG). Lithostratigraphic units: Group > Formation > Member > Bed. Type section (stratotype) — reference section where formation is defined. Chronostratigraphic units: Eonothem, Erathem, System, Series, Stage — time-rock units parallel to Eon, Era, Period, Epoch, Age.",
            "**Indian Stratigraphic Column**: Pre-Cambrian Shields (Dharwar, Singhbhum, Aravalli — mineral-rich cratons) → Vindhyan Supergroup (Proterozoic — sandstone, limestone, shale) → Gondwana Supergroup (Permian–Jurassic — coal, Glossopteris) → Cretaceous Deccan Traps → Tertiary marine (Kutch, Assam) → Quaternary (alluvium, glacial).",
            "**Sequence Stratigraphy**: Vail et al. (1977) — sea-level cycles control stratigraphy. Systems tracts: Lowstand (LST), Transgressive (TST), Highstand (HST). Sequence boundaries (SB), Maximum Flooding Surface (MFS). Applications: petroleum exploration, carbonate platform analysis.",
            "**Gondwana Stratigraphy of India**: Talchir Formation (diamictite — glacial, base of Gondwana), Barakar Formation (coal-bearing — major coal), Raniganj Formation (top Permian coal). Triassic–Jurassic Gondwana: Panchet, Mahadeva. Found in Damodar, Son, Mahanadi, Pranhita-Godavari basins.",
        ],
    },
    "Semester 7 (Electives)": {
        "ESMJ71 — Geomorphology & Geotectonics": [
            "**Geomorphic Processes**: Endogenic (tectonics, volcanism) vs Exogenic (weathering, erosion, deposition). Davis Cycle of Erosion: Youth → Maturity → Old age → Rejuvenation. Peneplain = erosion surface approaching base level. Monadnock = isolated resistant hill on peneplain. Inselberg (bornhardt) = granite dome in tropical weathering landscape.",
            "**Geotectonics**: Study of large-scale deformation and its driving mechanisms. Wilson Cycle: continental rifting → ocean opening → subduction → collision → new supercontinent. Hotspots: fixed mantle plumes (Hawaii, Reunion — responsible for Deccan Traps). LIPs (Large Igneous Provinces): Deccan, Siberian Traps, Kerguelen Plateau.",
            "**Himalayan Geomorphology**: Young mountains still rising (~5 mm/yr). Deep river gorges (antecedent rivers predate uplift). High denudation rates. Proglacial lakes — GLOF hazard (Glacial Lake Outburst Flood). Debris flows, rockfalls, landslides common in Lesser Himalayas and Siwaliks.",
        ],
        "ESMJ73 — Geochemistry & Instrumentation": [
            "**Geochemical Principles**: Goldschmidt's classification: lithophile (Si, Al, Ca, Na, K — silicate/oxide affinity), siderophile (Fe, Ni, Co, PGE — metal affinity), chalcophile (Cu, Pb, Zn, S — sulphide affinity), atmophile (N, O, H, noble gases). Goldschmidt rules for ionic substitution: similar ionic radius and charge → substitute in crystal lattice.",
            "**Isotope Geochemistry**: Stable isotopes (δ¹⁸O, δ¹³C, δD) — track past climate, fluid sources, biological processes. Radiogenic isotopes — geochronology: U-Pb (zircon — very robust, >4 Ga), Rb-Sr, Sm-Nd (mantle reservoirs), K-Ar/Ar-Ar (volcanic rocks, thermal history), Lu-Hf. Cosmogenic isotopes (¹⁰Be, ²⁶Al) — surface exposure dating, erosion rates.",
            "**Analytical Instruments**: XRF (X-ray fluorescence) — major element chemistry of whole rocks. ICP-MS (Inductively Coupled Plasma Mass Spectrometry) — trace elements and isotopes, ppb sensitivity. EPMA (Electron Probe Micro-Analyser) — spot chemical analysis of minerals in thin section. SEM-EDS — imaging + chemistry. SIMS (Secondary Ion Mass Spectrometry) — in-situ U-Pb dating of zircon.",
        ],
        "ESMJ75 — Fuel Geology": [
            "**Petroleum System**: Source rock (organic-rich shale, e.g. Eocene shale in Mumbai High), maturation (burial → catagenesis → oil window 60-120°C → gas window >150°C), migration (primary through microfractures, secondary through faults/carrier beds), trap (structural: anticline, fault; stratigraphic: pinch-out, unconformity; hydrodynamic), reservoir (porous sandstone or carbonate), seal (shale, evaporite cap rock).",
            "**Indian Petroleum Basins**: Mumbai High (Offshore, Paleocene-Eocene — India's largest oil field, ~450 million tonnes). Assam-Arakan basin (oldest producing, since 1890s). Krishna-Godavari offshore (gas — ONGC + Reliance). Rajasthan basin (Barmer — Cairn India/Vedanta). Kutch basin (gas, exploration phase). NELP (New Exploration Licensing Policy) and HELP (Hydrocarbon Exploration Licensing Policy) govern exploration.",
            "**Coal in India**: Formation: peat → lignite → sub-bituminous → bituminous → anthracite (increasing rank with burial/temperature). Gondwana coals (Permian, Damodar Valley — Jharia, Raniganj) = high-rank bituminous/coking coal. Tertiary coals (Assam, Meghalaya, Tamil Nadu) = lower rank lignite. India has world's 4th largest coal reserves (~319 billion tonnes).",
        ],
    },
    "Semester 8 (Electives)": {
        "ESMJ81 — Marine Geology, Oceanography & Climate": [
            "**Ocean Floor Morphology**: Continental shelf (0–200 m, gently sloping), Continental slope (200–3000 m, steep), Continental rise (turbidite fans), Abyssal plain (flat, deepest — 3000–6000 m), Mid-ocean ridge (divergent boundary, spreading centre), Ocean trenches (subduction zones, deepest — Challenger Deep ~11 km). Indian Ocean: Carlsberg Ridge, 90° East Ridge, Ninetyeast Ridge.",
            "**Marine Sediments**: Terrigenous (land-derived, thick near continents), Pelagic (open ocean): calcareous ooze (foraminifera, coccoliths, CaCO₃ — above CCD), siliceous ooze (diatoms, radiolaria — below CCD or high productivity zones), red clay (slowest accumulation, abyssal). CCD (Carbonate Compensation Depth) ~4,500 m in Indian Ocean.",
            "**Indian Ocean Circulation**: North Indian Ocean unique — monsoon-reversal current. NE monsoon (winter) → NE current; SW monsoon (summer) → SW monsoon current. Somali Current (western boundary current — reverses seasonally). Agulhas Current (SW of Madagascar). Thermohaline circulation (deep ocean conveyor belt) driven by density differences (T + salinity).",
            "**Paleoclimate**: Marine isotope stages from δ¹⁸O in foraminifera records ice volume + temperature. PETM (Palaeocene-Eocene Thermal Maximum) — rapid warming 56 Ma. K-Pg cooling from impact winter. Glacial-interglacial cycles from ice cores (EPICA, VOSTOK): CO₂ closely tracks temperature over 800,000 years.",
        ],
        "ESMJ83 — Groundwater Hydrology & Soil Geology": [
            "**Groundwater Flow Systems**: Darcy's Law: Q = -KA(dh/dl). Hydraulic conductivity (K) varies: gravel (10⁻² m/s), sand (10⁻⁴), silt (10⁻⁶), clay (10⁻⁹), granite (10⁻⁹–10⁻¹¹). Dupuit-Forchheimer assumptions for unconfined aquifer. Theis equation — transient (non-steady) groundwater flow to a pumping well.",
            "**Well Hydraulics**: Cone of depression around pumping well. Specific yield (unconfined) vs specific storage (confined). Aquifer tests (pumping tests): plot drawdown vs time on log scale → Theis curve matching → derive T (transmissivity) and S (storage coefficient). Step-drawdown tests for well efficiency.",
            "**Soil Pedology**: Soil profile: O (organic), A (topsoil, leached), B (subsoil, illuviation), C (weathered parent material), R (bedrock). USDA soil classification. Indian soils: Alluvial (Indo-Gangetic plains), Red (Deccan), Black/Regur (Deccan basalt, cotton), Laterite (humid tropics), Desert (Rajasthan), Mountain (Himalayas).",
        ],
        "ESMJ84 — Remote Sensing & GIS": [
            "**Satellite Image Interpretation**: Tone (brightness), texture (smoothness/roughness), pattern (spatial arrangement), shape, size, shadow, association — all used to interpret geology. False-colour composites: Band 4-3-2 (standard FCC, vegetation red), Band 7-4-2 (Landsat SWIR — geological mapping, exposes bare rock clearly).",
            "**GIS Analysis**: Vector data (points, lines, polygons) vs Raster data (grids, images). Overlay analysis, buffer, interpolation (IDW, kriging for geochemical data), DEM analysis (slope, aspect, hillshade, watershed delineation). ArcGIS, QGIS (free/open-source), Google Earth Engine (cloud-based Python/JS).",
            "**Applications in Indian Geology**: GSI National Geological Mapping Programme using Resourcesat-2. Landslide hazard mapping (Uttarakhand, Himachal). Flood mapping (Brahmaputra, Ganga). Land use/land cover change. Mineral exploration (iron oxide mapping using ASTER TIR). Coastal erosion monitoring (Karnataka, Odisha).",
        ],
    },
}

THIN_SECTIONS = [
    {"name":"Quartz (PPL)","emoji":"💎","desc":"Colourless, low relief, conchoidal fracture. Undulatory extinction under XPL. No cleavage.",
     "color":"rgba(200,230,255,0.3)","border":"#a0d8ef"},
    {"name":"Quartz (XPL)","emoji":"🌈","desc":"White-grey-yellow interference colours (1st order). Undulatory (wavy) extinction is diagnostic.",
     "color":"rgba(255,220,100,0.3)","border":"#ffd700"},
    {"name":"Biotite (PPL)","emoji":"🟫","desc":"Strong pleochroism: yellow→brown→dark brown. Perfect cleavage. Bird's eye extinction.",
     "color":"rgba(150,80,20,0.3)","border":"#8B4513"},
    {"name":"Biotite (XPL)","emoji":"⭐","desc":"High birefringence — 2nd–3rd order interference colours. Cleavage traces prominent.",
     "color":"rgba(255,160,80,0.3)","border":"#FF8C00"},
    {"name":"Plagioclase (XPL)","emoji":"🔲","desc":"Polysynthetic twinning (multiple parallel bands) is diagnostic. Low birefringence, grey colours.",
     "color":"rgba(200,200,200,0.3)","border":"#aaa"},
    {"name":"Orthoclase/K-spar","emoji":"🟪","desc":"Carlsbad twinning (2 sectors). Turbid/cloudy appearance. Perthitic unmixing texture often visible.",
     "color":"rgba(200,100,200,0.3)","border":"#DA70D6"},
    {"name":"Hornblende (PPL)","emoji":"🖤","desc":"Two cleavages at 60°/120° — diagnostic. Green-brown pleochroism. Elongated crystals.",
     "color":"rgba(30,60,30,0.4)","border":"#2f4f2f"},
    {"name":"Calcite (XPL)","emoji":"🌀","desc":"Very high birefringence — creamy/pearl interference colours. Rhombic cleavage. Twinkling in PPL.",
     "color":"rgba(240,220,200,0.3)","border":"#DEB887"},
    {"name":"Olivine (PPL)","emoji":"🍃","desc":"Colourless to pale green, high relief, fractures. Altered to serpentine/iddingsite around margins.",
     "color":"rgba(100,200,100,0.3)","border":"#90EE90"},
    {"name":"Garnet (PPL)","emoji":"🔴","desc":"High relief, isotropic (dark under XPL) — cubic mineral. Euhedral dodecahedra. Red/pink in hand specimen.",
     "color":"rgba(200,50,50,0.3)","border":"#DC143C"},
    {"name":"Pyroxene (Augite, XPL)","emoji":"🟢","desc":"Two cleavages at ~90° (distinguishes from hornblende's 60°/120°). 2nd order interference colours.",
     "color":"rgba(50,150,50,0.3)","border":"#228B22"},
    {"name":"Magnetite (PPL)","emoji":"⬛","desc":"Opaque — completely black under both PPL and XPL. Cubic, often octahedral shapes. Strongly magnetic.",
     "color":"rgba(20,20,20,0.5)","border":"#333"},
]

AI_KNOWLEDGE = {
    "geology": "Geology is the scientific study of Earth — its materials (rocks, minerals), structures, processes, and 4.6-billion-year history. It tells us where resources are, predicts hazards, and reads the story of life on Earth. The word comes from Greek: geo (Earth) + logos (reason/word).",
    "deccan traps": "The Deccan Traps are a massive flood basalt province in western India — ~500,000 km² of tholeiitic basalt, erupted 66 Ma ago. The lava piles reach 2 km thick in places. Their CO₂ emissions contributed to global warming before the K-Pg extinction event.",
    "himalaya": "The Himalayas formed from India–Eurasia collision starting ~50 Ma ago. They contain 10 of Earth's 14 peaks above 8,000 m (including Everest at 8,849 m). India still moves NNE at ~5 cm/yr, pushing the Himalayas upward ~5 mm/year.",
    "mohs": "Mohs hardness scale (1–10): Talc(1), Gypsum(2), Calcite(3), Fluorite(4), Apatite(5), Orthoclase(6), Quartz(7), Topaz(8), Corundum(9), Diamond(10). Each mineral scratches all those below it.",
    "plate tectonics": "Plate tectonics: Earth's lithosphere (~100 km thick) is divided into ~15 major plates that move on the viscous asthenosphere at 1–10 cm/year. Boundaries: divergent (spreading ridges), convergent (subduction or collision), transform (sliding). Explains earthquakes, volcanoes, mountains.",
    "metamorphism": "Metamorphism transforms rocks via heat, pressure, and chemically active fluids without melting. Types: contact (near intrusions — produces hornfels), regional (deep burial — produces schist, gneiss), dynamic (along faults). Barrow's zones track increasing grade: chlorite→biotite→garnet→kyanite→sillimanite.",
    "earthquake": "Earthquakes = sudden release of elastic energy stored along faults. P-waves (compressional, fastest) arrive first; S-waves (shear) second; surface waves cause most damage. Mw (moment magnitude) measures energy released. India's seismic zone V (most hazardous) covers the Himalayas, NE India, Andaman.",
    "rock cycle": "The rock cycle: Magma (from mantle/melting) cools → igneous rocks. Weathering + erosion → sediments. Burial + lithification → sedimentary rocks. Heat + pressure → metamorphic rocks. Continued heating → melting → magma again. Nothing is permanent on geologic timescales.",
    "bhu": "BHU (Banaras Hindu University), Varanasi — founded 1916 by Pandit Madan Mohan Malaviya. Its Department of Geology (now Earth & Planetary Sciences) is one of India's finest, known for Vindhyan stratigraphy, Gondwana studies, and mineral exploration research.",
    "gondwana": "Gondwana was a supercontinent comprising India, Africa, Antarctica, Australia, South America, and Arabia. It began breaking up ~180 Ma (Jurassic). India rifted away ~130 Ma and drifted north rapidly. Glossopteris fossil flora proves all these continents were once joined.",
    "stratigraphy": "Stratigraphy = study of rock layers (strata). Key principles: superposition (older below younger), original horizontality, lateral continuity, faunal succession, cross-cutting relationships. Used to correlate rocks across India and reconstruct Earth history.",
    "soil": "Indian soils: Alluvial (43%, most fertile, Gangetic plains), Black/Regur (16%, Deccan basalt, cotton), Red/Yellow (18%, crystalline rocks, less fertile), Laterite (8%, tropical leaching), Mountain, Arid/Desert, Saline. Soil formation depends on parent rock, climate, topography, organisms, time.",
    "varanasi": "Varanasi (Kashi/Benares) sits on the Gangetic alluvial plain, one of the oldest continuously inhabited cities (~3000 years). The city stands on old terraces of the Ganga. Sarnath nearby has been a Buddhist site since 5th century BCE.",
    "igneous": "Igneous rocks form from cooling magma/lava. Intrusive (plutonic) rocks like granite cool slowly underground = coarse grains. Extrusive (volcanic) rocks like basalt cool fast at the surface = fine grains or glass. Classified by silica content: felsic (high silica, light) to mafic/ultramafic (low silica, dark, dense).",
    "sedimentary": "Sedimentary rocks form from weathered/eroded material that's deposited, compacted, and cemented (lithified). Types: clastic (sandstone, shale — from fragments), chemical (limestone — from precipitation), organic (coal — from organic matter). Cover ~75% of Earth's land surface, despite being a small % of crust volume.",
    "volcano": "A volcano is a vent where magma, ash, and gases escape Earth's interior. Types: shield (gentle, basaltic — like Hawaii), composite/stratovolcano (explosive, layered — like Fuji), cinder cone (small, steep). India's only active volcano is Barren Island in the Andamans.",
    "quartz": "Quartz (SiO₂) is the most abundant mineral in Earth's crust. Hardness 7 on Mohs scale, vitreous luster, no cleavage, hexagonal crystal system. Found in granite, sandstone; used in glass, electronics, and as a gemstone (amethyst, citrine are quartz varieties).",
    "feldspar": "Feldspar is the most common mineral group, making up ~60% of Earth's crust. Comes in two main types: orthoclase (potassium-rich, pink) and plagioclase (sodium/calcium-rich, white-grey). Key component of granite and basalt.",
    "mica": "Mica minerals have perfect basal cleavage, splitting into thin, flexible sheets. Biotite (black/dark) and muscovite (silvery, transparent) are common types. India — especially Andhra Pradesh — holds the world's largest mica deposits, used in electronics and insulation.",
    "calcite": "Calcite (CaCO₃) is the main mineral in limestone and marble. Hardness 3 on Mohs scale, effervesces (fizzes) with dilute acid — a quick field test geologists use to identify it.",
    "fold": "A fold is a bend in rock layers caused by compressive stress, without breaking. Anticlines arch upward (older rocks in the core), synclines bend downward (younger rocks in the core). The Himalayas are full of large-scale folds from the India-Asia collision.",
    "fault": "A fault is a fracture in rock where blocks have moved relative to each other. Normal faults (extension), reverse/thrust faults (compression), and strike-slip faults (lateral, like California's San Andreas) are the three main types. The Himalayan Frontal Thrust is a major active fault system.",
    "weathering": "Weathering breaks down rock in place. Physical/mechanical weathering (frost wedging, thermal expansion) creates fragments without changing chemistry. Chemical weathering (oxidation, hydrolysis, carbonation) alters mineral composition — it's why laterite soils form in India's wet tropical regions.",
    "erosion": "Erosion is the removal and transport of weathered material by water, wind, ice, or gravity. The Ganga–Brahmaputra system carries one of the world's largest sediment loads, eroded from the rapidly uplifting Himalayas.",
    "monsoon": "The Indian monsoon is driven by differential heating between land and ocean, creating seasonal wind reversal. The Himalayas act as a barrier, forcing monsoon clouds to rise and dump rainfall, directly shaping Indian river systems, soil fertility, and agriculture.",
    "tsunami": "Tsunamis are series of long-wavelength ocean waves usually triggered by undersea earthquakes (especially subduction zone megathrusts), volcanic eruptions, or landslides. The 2004 Indian Ocean tsunami originated from a Mw 9.1 earthquake off Sumatra and devastated India's Andaman & Nicobar and Tamil Nadu coasts.",
    "richter": "The Richter scale measures earthquake magnitude logarithmically — each whole number increase means ~32x more energy released. Modern seismology mostly uses moment magnitude (Mw) instead, which is more accurate for large earthquakes.",
    "wegener": "Alfred Wegener proposed Continental Drift in 1912 — that continents were once joined as Pangaea and drifted apart. He lacked a mechanism (mantle convection wasn't understood yet), so it was rejected for decades until plate tectonics confirmed it in the 1960s.",
    "fossil": "Fossils are preserved remains or traces of past life. India's Siwalik Hills (Himalayan foothills) are famous for Miocene-Pleistocene mammal fossils; the Gondwana coal beds preserve Glossopteris flora that link India to Antarctica, Africa, and Australia.",
    "coal": "Coal is an organic sedimentary rock formed from compressed, buried plant material over millions of years (peat → lignite → bituminous → anthracite). India's coal — mostly Gondwana-age — is concentrated in Jharkhand, Odisha, Chhattisgarh, and West Bengal.",
    "petroleum": "Petroleum forms from marine organic matter buried in sedimentary basins, subjected to heat and pressure (the 'oil window', roughly 60–150°C) over millions of years. India's major basins include Bombay High (offshore Mumbai), Assam, and the Krishna-Godavari basin.",
    "ocean": "Oceans cover ~71% of Earth's surface and drive climate via currents, heat storage, and the water cycle. The ocean floor is geologically young (entirely recycled every ~200 Ma) compared to continents, due to seafloor spreading and subduction.",
    "current": "Ocean currents are driven by wind, Earth's rotation (Coriolis effect), and density differences from temperature/salinity. The Indian Ocean is unique for reversing currents seasonally with the monsoon — unlike the Atlantic or Pacific.",
    "glacier": "Glaciers are large, slow-moving ice masses formed by accumulated snow compaction. The Himalayan glaciers (like Gangotri, source of the Ganga) feed major South Asian rivers and are retreating due to climate change.",
    "mountain": "Mountains form mainly through tectonic processes: collision (Himalayas — fold mountains), volcanism (block/volcanic mountains), or faulting (block mountains, like horsts). Erosion continuously works against uplift, balancing mountain height over geologic time.",
    "gsi": "The Geological Survey of India (GSI), established 1851, is one of the oldest geological survey organisations in the world. It conducts geological mapping, mineral exploration, and natural hazard assessment across India.",
    "diamond": "Diamond is pure carbon crystallized under extreme pressure 150–200 km deep in the mantle, then transported rapidly to the surface via kimberlite pipes — among the fastest-rising magmas known. India's diamonds occur in Madhya Pradesh (Panna) and historically in Andhra Pradesh (Golconda).",
    "limestone": "Limestone is a sedimentary rock made mostly of calcium carbonate (calcite), formed from marine shells, coral, and chemical precipitation. India's major limestone belts are in Madhya Pradesh, Rajasthan, Andhra Pradesh, and Meghalaya — used in cement production.",
    "marble": "Marble is metamorphosed limestone, recrystallized under heat and pressure. Pure marble is white; impurities create veining and color. Rajasthan's Makrana marble was used to build the Taj Mahal.",
    "sandstone": "Sandstone is a clastic sedimentary rock made of sand-sized quartz/feldspar grains cemented together. India's Vindhyan sandstones (Madhya Pradesh, Uttar Pradesh) are world-famous for preserving 600-million-year-old cross-bedding and ripple marks.",
    "shale": "Shale is a fine-grained sedimentary rock formed from compacted clay and silt, splitting easily along thin layers (fissility). It's the source rock for much of the world's petroleum and natural gas.",
    "schist": "Schist is a medium-to-high grade metamorphic rock with visible, aligned platy minerals (mica, chlorite) giving it a foliated, almost glittery texture. Common in the Himalayan metamorphic belt.",
    "gneiss": "Gneiss is a high-grade metamorphic rock showing banded foliation — alternating light (quartz/feldspar) and dark (biotite/hornblende) layers. India's Peninsular Gneissic Complex is among the oldest rock units on Earth (over 3 billion years old).",
    "magma": "Magma is molten rock beneath Earth's surface, a mix of melted minerals, dissolved gases, and crystals. Its silica content controls viscosity and eruption style — felsic magma is thick and explosive, mafic magma is runny and flows easily.",
    "lava": "Lava is magma that has reached the surface. Pahoehoe lava is smooth and ropey; aa lava is rough and blocky. The Deccan Traps were built from enormous, repeated basaltic lava flows.",
    "subduction": "Subduction occurs when one tectonic plate (usually oceanic, denser) sinks beneath another at a convergent boundary. It generates deep earthquakes, volcanic arcs, and ocean trenches — the Andaman-Sumatra trench is a classic example near India.",
    "convergent": "A convergent plate boundary is where two plates move toward each other — producing subduction zones (oceanic-continental) or collision zones (continental-continental, like India-Eurasia forming the Himalayas).",
    "divergent": "A divergent plate boundary is where plates pull apart, allowing magma to rise and form new crust — mid-ocean ridges are the classic example, like the Carlsberg Ridge in the Indian Ocean.",
    "transform": "A transform plate boundary is where plates slide past each other horizontally, neither creating nor destroying crust. These produce powerful, shallow earthquakes — California's San Andreas Fault is the textbook example.",
    "asthenosphere": "The asthenosphere is the partially molten, ductile layer of the upper mantle (roughly 100–700 km deep) on which the rigid lithospheric plates slide, driven by convection currents.",
    "lithosphere": "The lithosphere is Earth's rigid outer shell — the crust plus the uppermost mantle — broken into tectonic plates roughly 100 km thick that move atop the asthenosphere.",
    "mantle": "Earth's mantle extends from ~35 km to 2,890 km depth, making up about 84% of Earth's volume. It's solid rock that flows slowly over geologic time, driving plate tectonics through convection.",
    "core": "Earth's core has two parts: a liquid outer core (iron-nickel, generates the magnetic field via convection) and a solid inner core, under immense pressure despite temperatures around 5,500°C — as hot as the Sun's surface.",
    "crust": "Earth's crust is the thin, rigid outermost layer — oceanic crust (5-10 km thick, basaltic, dense) and continental crust (30-70 km thick, granitic, lighter). It makes up less than 1% of Earth's volume.",
    "ganga": "The Ganga (Ganges) originates at Gangotri glacier in the Himalayas, flows 2,525 km through the Indo-Gangetic plain, and drains into the Bay of Bengal. It carries one of the largest sediment loads of any river on Earth, built from rapid Himalayan erosion.",
    "brahmaputra": "The Brahmaputra originates in Tibet (as the Yarlung Tsangpo), cuts through the eastern Himalayan syntaxis, and flows through Assam before joining the Ganga delta — known for dramatic seasonal flooding and channel shifting.",
    "vindhyan": "The Vindhyan Supergroup is a thick (over 4 km), largely undeformed sequence of Proterozoic sedimentary rocks (sandstone, shale, limestone) spanning Madhya Pradesh, Uttar Pradesh, and Rajasthan — one of India's best natural laboratories for ancient stratigraphy.",
    "aravalli": "The Aravalli Range, running through Rajasthan, is among the oldest fold mountain systems on Earth (over 2 billion years old, now deeply eroded to low hills) — far older than the still-young, jagged Himalayas.",
    "western ghats": "The Western Ghats are a mountain range along India's west coast, formed by faulting and volcanic activity related to the breakup of Gondwana and the Deccan eruptions. A UNESCO World Heritage biodiversity hotspot with ancient laterite-capped plateaus.",
    "kimberlite": "Kimberlite is an ultramafic igneous rock that forms deep-source volcanic pipes — the primary source rock for diamonds, rapidly transporting them from mantle depths (150-200 km) to the surface in violent eruptions.",
    "ophiolite": "An ophiolite is a slice of oceanic crust and upper mantle thrust onto continental crust during collision — a rare window into ocean-floor rocks on land. India's Andaman ophiolite records ancient subduction.",
    "laterite": "Laterite is a reddish, iron- and aluminum-rich soil/rock formed by intense chemical weathering in hot, wet tropical climates — common across India's Western Ghats, Odisha, and Kerala, and an important source of bauxite (aluminum ore) and iron ore.",
    "alluvial": "Alluvial soil is deposited by rivers — fine, fertile, and renewed by floods. It covers ~43% of India, especially the Indo-Gangetic plains, and supports the bulk of the country's agriculture.",
    "black soil": "Black soil (regur) forms from weathered Deccan basalt, rich in clay, iron, and lime, retaining moisture well. It's ideal for cotton cultivation and dominates Maharashtra, Madhya Pradesh, and Gujarat.",
    "bauxite": "Bauxite is the principal ore of aluminum, formed by intense tropical weathering (laterization) of aluminum-rich rocks. India's major deposits are in Odisha, Jharkhand, Chhattisgarh, and Gujarat.",
    "iron ore": "India holds major iron ore reserves (hematite and magnetite) concentrated in Odisha, Jharkhand, Chhattisgarh, and Karnataka — among the world's largest, feeding the domestic steel industry and exports.",
    "magnitude": "Earthquake magnitude measures the energy released at the source. Moment magnitude (Mw) is most accurate for large quakes; each whole-number increase represents roughly 32 times more energy released.",
    "seismic": "Seismic zones in India are classified I (least hazardous) to V (most hazardous) by the Bureau of Indian Standards based on historical earthquake activity, fault density, and tectonic setting — the Himalayas, NE India, Kutch, and the Andamans fall in Zone V.",
    "p wave": "P-waves (primary/compressional waves) are the fastest seismic waves, traveling through solids and liquids by compressing and expanding rock in the direction of travel — they're the first waves detected after an earthquake.",
    "s wave": "S-waves (secondary/shear waves) move rock perpendicular to their direction of travel, are slower than P-waves, and cannot pass through liquids — this property helped scientists discover Earth's liquid outer core.",
    "metamorphic": "Metamorphic rocks form when existing rock is transformed by heat, pressure, or fluids without fully melting. Foliated types (schist, gneiss) show aligned mineral bands; non-foliated types (marble, quartzite) don't.",
    "hardness": "Mineral hardness is measured by resistance to scratching, using the Mohs scale (1-10): Talc to Diamond. It's a quick field-identification test — a fingernail scratches up to hardness 2.5, a steel knife up to about 5.5.",
    "cleavage": "Cleavage is a mineral's tendency to break along flat planes defined by weak atomic bonds — mica has perfect cleavage in one direction (peels into sheets), while quartz has none (fractures irregularly).",
    "luster": "Luster describes how a mineral's surface reflects light — metallic (like pyrite), vitreous/glassy (quartz), pearly (mica), earthy (kaolinite), or silky (asbestos) — a key identification clue alongside hardness and color.",
    "pangaea": "Pangaea was the supercontinent that existed roughly 335 to 175 million years ago, containing nearly all of Earth's landmass before splitting first into Laurasia and Gondwana, then further into today's continents.",
    "extinction": "Mass extinctions are rapid, global losses of biodiversity. The K-Pg extinction (66 Ma) wiped out non-avian dinosaurs, likely from an asteroid impact combined with Deccan Traps volcanism and its climate effects — both events occurred almost simultaneously.",
    "dinosaur": "Dinosaurs dominated land ecosystems for about 165 million years (Triassic to Cretaceous). India, then part of a drifting subcontinent, has yielded dinosaur fossils (including titanosaur eggs) in Gujarat's Deccan volcanic sediments.",
    "geological time scale": "The geological time scale divides Earth's 4.6-billion-year history into Eons, Eras, Periods, and Epochs based on rock strata and major biological/geological events — from the Hadean through today's Holocene/Anthropocene.",
    "precambrian": "The Precambrian spans from Earth's formation (4.6 Ga) to about 541 Ma — over 85% of Earth's history — including the origin of life, the first oxygen in the atmosphere, and the assembly/breakup of early supercontinents.",
    "jurassic": "The Jurassic Period (201-145 Ma) saw Pangaea splitting apart, dinosaurs flourishing, and the first birds appearing. Marine sediments from this period are found in Kutch, Gujarat, rich in ammonite fossils.",
    "cretaceous": "The Cretaceous Period (145-66 Ma) ended with a mass extinction. India, isolated as a drifting island continent for much of this period, experienced the massive Deccan Traps eruptions near its close.",
    "volcanic eruption": "Volcanic eruptions range from gentle effusive lava flows (low-silica magma) to violent explosive eruptions (high-silica, gas-rich magma). Eruption style depends on magma viscosity, gas content, and the speed of gas escape.",
    "barren island": "Barren Island, in the Andaman Sea, is India's only confirmed active volcano — a stratovolcano that has erupted multiple times in recent decades, most recently in the 2020s.",
    "groundwater": "Groundwater is water stored in soil pores and rock fractures below the water table. India relies heavily on groundwater for irrigation and drinking water, with serious depletion concerns in Punjab, Haryana, and parts of southern India.",
    "watershed": "A watershed (or drainage basin) is the land area where all surface water drains to a common outlet, like a river or lake. India's major watersheds include the Ganga, Indus, Brahmaputra, Godavari, Krishna, and Narmada basins.",
    "drainage pattern": "Drainage patterns reflect underlying geology: dendritic (tree-like, on uniform rock), trellis (parallel, on folded rock like the Himalayan foothills), radial (from a central peak), and rectangular (controlled by faults/joints).",
    "delta": "A river delta forms where a river deposits sediment as it slows entering a sea or lake. The Ganga-Brahmaputra delta (Sundarbans) is the world's largest, spanning India and Bangladesh.",
    "ocean trench": "Ocean trenches are the deepest parts of the ocean, formed at subduction zones where one plate bends and sinks beneath another. The Sunda/Java Trench near the Andaman Islands is linked to India's regional seismic hazard.",
    "coral reef": "Coral reefs are built by colonial marine organisms (corals) depositing calcium carbonate skeletons. India's reefs are found in the Gulf of Kutch, Gulf of Mannar, Lakshadweep, and Andaman & Nicobar Islands.",
    "monazite": "Monazite is a phosphate mineral and an important source of rare earth elements and thorium in India, found in beach placer sand deposits along Kerala, Tamil Nadu, and Odisha's coasts.",
    "petrology": "Petrology is the branch of geology studying rocks — their composition, texture, structure, and origin — divided into igneous, sedimentary, and metamorphic petrology.",
    "mineralogy": "Mineralogy is the study of minerals — their crystal structure, chemistry, physical properties, and formation conditions — foundational to identifying rocks and ores in the field and lab.",
    "geomorphology": "Geomorphology studies landforms and the processes (weathering, erosion, tectonics, deposition) that shape Earth's surface over time — explaining why the Himalayas are jagged while the Aravallis are worn smooth.",
    "hydrology": "Hydrology is the study of water's movement, distribution, and quality on and below Earth's surface — covering rivers, groundwater, the water cycle, and water resource management.",
    "paleontology": "Paleontology is the study of fossils and ancient life, using preserved remains to reconstruct past organisms, environments, and evolutionary history — closely tied to stratigraphy for dating rock layers.",
    "thin section": "A thin section is a 0.03 mm-thick slice of rock mounted on glass, ground thin enough for light to pass through, examined under a polarizing microscope to identify minerals by their optical properties.",
}

# Sort knowledge keys longest-first so multi-word/specific keywords are checked before short generic ones.
AI_KNOWLEDGE_KEYS_SORTED = sorted(AI_KNOWLEDGE.keys(), key=len, reverse=True)

DIARY_ENTRIES = [
    {"date":"Day 1 — First Day at BHU Geology","location":"Banaras Hindu University","text":"First day in the corridors of the BHU Geology department. The walls are lined with rock specimens, old survey maps, and faded photographs of field expeditions. Picked up a piece of basalt from the lab counter — this rock type covers 500,000 km² of India. The Deccan Traps. Everything starts to feel connected. This place has been producing geologists since 1917."},
    {"date":"Day 12 — Ganga Ghat at Dusk","location":"Assi Ghat","text":"After the first mineralogy lecture, walked down to Assi Ghat. The Ganga carries sediment from the Himalayas — olivine grains from glacial erosion, feldspar from granite weathering, mica flakes catching the last light. Every river is a moving geological record. BHU is one of the few places where you can study geology and then walk to one of its greatest classrooms in fifteen minutes."},
    {"date":"Day 47 — Vindhyan Field Practical","location":"Mirzapur","text":"Vindhyan sandstone in the afternoon sun, Mirzapur district. Ran fingers along cross-bedding that formed 600 million years ago. Time stops making human sense out here. Professor Sharma said: 'You're not looking at rock. You're reading a letter from the Proterozoic.' The Vindhyan Supergroup outcrops are practically in BHU's backyard — a privilege most geology departments would envy."},
    {"date":"Day 89 — The Thin Section Lab","location":"Petrographic microscope","text":"First polarising microscope session in the BHU petrography lab. Quartz glowing pale grey in PPL, erupting into whites and yellows under XPL. Biotite deep amber, pleochroic. Feldspar twinned like a fingerprint. A whole world in a 0.03mm slice. The professor said the microscope is a geologist's most honest instrument — it doesn't let you guess."},
    {"date":"Day 124 — Structural Geology Begins","location":"Ramnagar, Varanasi","text":"Strike and dip. Clinometer compass. Brunton compass. The professor demonstrated on a roadcut between BHU and Ramnagar — sandstone beds tilted 35° NE. I recorded the wrong dip direction twice. He didn't say anything, just handed me the compass again. The most important geology lessons come without lectures."},
    {"date":"Day 156 — Semester End, Exam Season","location":"Banaras Hindu University","text":"Structural geology diagrams at 2am in the BHU hostel. Folds, faults, foliations. The Himalayan orogeny plays on repeat in the mind — India crashing into Eurasia at 5 cm/yr. Too slow to feel, too powerful to stop. Still happening right now as I write this. The Himalayas are still rising. That thought makes everything feel less urgent and more vast."},
    {"date":"Day 178 — Sarnath & Deep Time","location":"Sarnath","text":"A group of us cycled to Sarnath on a Sunday. Stood on ground where 2,500 years of human history is buried in alluvium deposited by floods of the Varuna river. The geologist brain doesn't switch off — while everyone admired the Dhamek Stupa, I was counting flood layers in the riverbank. Geology makes you unable to see anything as permanent."},
    {"date":"Day 203 — Monsoon, Lab, and Pyrite","location":"Pyrite","text":"Rain hammering the BHU geology building roof. Thin sections on every table. Someone found pyrite in a Vindhyan sample and the whole lab leaned in. Fool's Gold — but only a fool would dismiss it. Pyrite tells you about oxygen levels, reducing conditions, hydrothermal fluid pathways, deep-time ocean chemistry. One mineral, a dozen stories."},
    {"date":"Day 241 — First Real Geological Map","location":"Chunar","text":"Drew my first proper geological map today from the Chunar area field data — contacts, strike and dip symbols, a fault line I almost missed until the outcrop pattern gave it away. Professor's red pen found three errors. Each correction taught me to look slower, think spatially, trust the rock over the assumption. The Chunar sandstone (Vindhyan) under the fort walls is a geological monument hiding in plain sight."},
    {"date":"Day 267 — The Reference Library","location":"Banaras Hindu University Library","text":"Spent an evening in the BHU geology library reading Krishnan's 'Geology of India and Burma' — the old edition, before the maps were updated. He described outcrops that still exist exactly as he wrote them in 1949. Geology is one of the few fields where a 70-year-old textbook is still perfectly valid in places. The rocks don't update themselves."},
    {"date":"Day 298 — Mineral Identification Practical","location":"Gypsum","text":"Hardness kits, streak plates, dilute HCl. Magnetite pulling at the magnet with quiet certainty. Calcite fizzing right on cue. Gypsum scratching with a fingernail (hardness 2). Realized geology is half memory, half detective work — every physical property is a clue the mineral can't conceal. The trick is learning to ask the right questions."},
    {"date":"Day 334 — The Quiet Outcrop Nobody Talks About","location":"Phyllite","text":"Found a roadcut between BHU's back gate and Lanka — tight little folds in phyllite, easy to walk past without noticing. Sat there for twenty minutes just looking. Calculated the fold axis plunge. Took sketches. Some of the best geology in this city isn't behind glass in a museum — it's in a roadcut that ten thousand people pass every day without stopping."},
    {"date":"Day 372 — Glossopteris","location":"Glossopteris","text":"A cast of Glossopteris in a shale sample, passed around the BHU lab like it was treasure. A leaf that once grew across Gondwana — India, Africa, Antarctica, Australia, South America, all one supercontinent. Held proof of a vanished world in one hand. Wegener was right, and the fossil in my palm was part of the evidence."},
    {"date":"Day 410 — Night Before the Deccan Traps Field Trip","location":"Pune","text":"Boots packed. Hand lens cleaned. Notebook still mostly empty. Tomorrow: Deccan basalt country — Pune region. Real outcrops, real weather, and real mistakes. Somewhere between nervous and impatient. The professor said to touch every rock we see. 'The information lives in the texture, not the colour.' This is the part they don't warn you you'll miss most once you leave."},
    {"date":"Day 445 — Deccan Traps, Western Ghats Escarpment","location":"Western Ghats","text":"Standing on a flow contact between two basalt eruptions, separated by a red bole — a palaeosol, a fossil soil formed between eruptions. Two flows, separated by decades or centuries, now compressed into 30 cm of red iron-rich clay. The Deccan erupted for nearly 5 million years. This red line is a pause between catastrophes. I photographed it seventeen times."},
    {"date":"Day 489 — Varanasi Monsoon Flood, Geological Eyes","location":"Ganges", "text":"The Ganga in full flood — brown, carrying everything. Sand banks drowned. Ghats half-submerged. Every geology student at BHU should see this at least once. This flood is building the alluvial plain that feeds half of India. The sediment settling here today will be sandstone in 10 million years, if the conditions are right. Nothing is wasted in geology."},
]

# ═══════════════════════════════════════════════════════
#  LOADING ANIMATION (first visit only)
# ═══════════════════════════════════════════════════════
if not st.session_state.loading_done:
    ph = st.empty()
    with ph.container():
        st.markdown("""
        <style>
        @keyframes pulse-ring {
            0%   { transform:scale(0.8); opacity:0.8; }
            50%  { transform:scale(1.1); opacity:0.4; }
            100% { transform:scale(0.8); opacity:0.8; }
        }
        @keyframes text-reveal {
            0%   { opacity:0; transform:translateY(18px); }
            100% { opacity:1; transform:translateY(0); }
        }
        @keyframes bar-fill {
            0%   { width:0%; }
            100% { width:100%; }
        }
        @keyframes dot-pulse {
            0%,80%,100% { transform:scale(0); opacity:0; }
            40%          { transform:scale(1); opacity:1; }
        }
        .splash-wrap {
            position:fixed;top:0;left:0;width:100vw;height:100vh;
            background:radial-gradient(ellipse at 30% 40%, #0c1428 0%, #070b18 60%, #030510 100%);
            display:flex;flex-direction:column;align-items:center;justify-content:center;
            z-index:9999999;
        }
        .splash-globe {
            font-size:5rem;margin-bottom:24px;
            animation:pulse-ring 2.4s ease-in-out infinite;
            filter:drop-shadow(0 0 32px rgba(201,168,76,0.6));
        }
        .splash-title {
            font-family:'Playfair Display',Georgia,serif;font-size:2.6rem;font-weight:900;
            background:linear-gradient(90deg,#c9a84c,#f0d878,#e8c96a,#c9a84c);
            background-size:200%;
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            background-clip:text;letter-spacing:5px;
            animation:text-reveal 0.8s ease forwards, shimmer 3s linear infinite;
        }
        .splash-sub {
            color:#a89968;font-size:0.72rem;letter-spacing:4px;
            font-family:'Source Sans 3',sans-serif;margin:8px 0 32px;
            animation:text-reveal 1s ease 0.3s both;
        }
        .splash-bar-wrap {
            width:260px;height:3px;background:rgba(201,168,76,0.12);
            border-radius:3px;overflow:hidden;margin-bottom:20px;
        }
        .splash-bar {
            height:3px;background:linear-gradient(90deg,#c9a84c,#f0d878,#c9a84c);
            border-radius:3px;animation:bar-fill 1.4s ease-out 0.5s both;
        }
        .splash-status {
            color:#a89968;font-size:0.65rem;letter-spacing:2px;
            font-family:'Source Sans 3',sans-serif;
            animation:text-reveal 0.6s ease 1s both;
        }
        .splash-status span { color:#c9a84c; }
        </style>
        <div class='splash-wrap'>
            <div class='splash-globe'>🌍</div>
            <div class='splash-title'>GeoSphere India</div>
            <div class='splash-sub'>EARTH SCIENCE INTELLIGENCE PLATFORM</div>
            <div class='splash-bar-wrap'><div class='splash-bar'></div></div>
            <div class='splash-status'>
                Initialising geological systems &nbsp;·&nbsp;
                Loading mineral database &nbsp;·&nbsp;
                <span>Ready</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(1.8)
    ph.empty()
    st.session_state.loading_done = True

# ═══════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════
#  SIDEBAR RENDER FUNCTION
# ═══════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════
#  MULTIPAGE SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════
PAGE_MAP = {
    "🌌 Mission Control":      "app.py",
    "🗺️ Geological Map":       "pages/1_Geological_Map.py",
    "🌋 Plate Tectonics":      "pages/2_Plate_Tectonics.py",
    "🪨 Rock Explorer":        "pages/3_Rock_Explorer.py",
    "💎 Mineral Explorer":     "pages/4_Mineral_Explorer.py",
    "🌍 Earthquake Dashboard": "pages/5_Earthquake_Dashboard.py",
    "🌋 Volcano Explorer":     "pages/6_Volcano_Explorer.py",
    "📅 Geological Time Scale":"pages/7_Geological_Time_Scale.py",
    "🧭 Structural Tools":     "pages/8_Structural_Tools.py",
    "🌿 Geography Explorer":   "pages/9_Geography_Explorer.py",
    "🌊 Watershed Explorer":   "pages/10_Watershed_Explorer.py",
    "🧪 Soil Explorer":        "pages/11_Soil_Explorer.py",
    "🪙 Economic Geology":     "pages/12_Economic_Geology.py",
    "🌊 Oceanography":         "pages/13_Oceanography.py",
    "🔬 Thin Section Gallery": "pages/14_Thin_Section_Gallery.py",
    "📚 Semester Notes":       "pages/15_Semester_Notes.py",
    "🧠 Geo Quiz":             "pages/16_Geo_Quiz.py",
    "🃏 Flashcards":           "pages/17_Flashcards.py",
    "🤖 AI Assistant":         "pages/18_AI_Assistant.py",
    "📓 Field Diary":          "pages/19_Field_Diary.py",
    "🥚 About & Archive":      "pages/20_About.py",
}

def render_sidebar():
    """Render the GeoSphere sidebar with multipage navigation."""
    with st.sidebar:
        # Logo click easter egg
        clicks = st.session_state.logo_clicks
        click_hint = "▸ Hadd ho." if clicks >= 10 else "▸ SYSTEM ONLINE" if clicks >= 5 else "· · ·"
        st.markdown(f"<div style='text-align:center;font-size:0.55rem;color:#a89968;letter-spacing:2px;min-height:10px;'>{click_hint}</div>", unsafe_allow_html=True)
        col_logo, _ = st.columns([1, 3])
        with col_logo:
            if st.button("🌍", key="logo_click", help="Click me..."):
                st.session_state.logo_clicks += 1
                if st.session_state.logo_clicks >= 10:
                    panda_img = get_wiki_image("Giant panda")
                    panda_html = f'<img src="{panda_img}" class="panda-photo">' if panda_img else '<div style="font-size:4rem;">🐼</div>'
                    st.markdown(f"""
                    <div class="panda-overlay">
                        <div class="panda-content">{panda_html}
                        <div class="panda-text">Hadd ho.</div></div>
                    </div>""", unsafe_allow_html=True)
                st.rerun()

        if st.session_state.logo_clicks >= 5:
            st.markdown("""
            <div style='background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.2);
                border-radius:10px;padding:8px;margin-bottom:8px;'>
                <div style='color:#a89968;font-size:0.55rem;letter-spacing:2px;'>SYSTEM</div>
                <div style='color:#c9a84c;font-size:0.7rem;margin-top:4px;line-height:2;'>
                    Alias : COMPUTER<br>Status : Online
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:rgba(201,168,76,0.15);margin:8px 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='color:#a89968;font-size:0.58rem;letter-spacing:3px;padding:0 4px 6px;'>NAVIGATION</div>", unsafe_allow_html=True)

        # Navigation using page_link for multipage — during achievement mode,
        # labels switch to Roman-Urdu (Urdu vocabulary, English alphabet).
        for label, page_file in PAGE_MAP.items():
            st.page_link(page_file, label=urdu_label(label), use_container_width=True)

        st.markdown("<hr style='border-color:rgba(201,168,76,0.1);margin:10px 0;'>", unsafe_allow_html=True)

        # Live seismic index — cached 2 min (this sidebar renders on every single page)
        _eq_count = fetch_usgs_earthquake_count(days_back=1, min_magnitude=4.5)

        if _eq_count is not None:
            sv = min(100, int(_eq_count / 30 * 100))
            level = "HIGH" if sv > 66 else "MODERATE" if sv > 33 else "LOW"
            level_col = "#dc2626" if sv > 66 else "#f59e0b" if sv > 33 else "#10b981"
            r_circ, circ = 35, 2 * math.pi * 35
            dash = circ * sv / 100
            st.markdown(f"""
            <div style='text-align:center;padding:6px 0;'>
                <div style='font-size:0.52rem;color:#8a7d65;letter-spacing:2px;margin-bottom:6px;'>SEISMIC INDEX</div>
                <div style='position:relative;width:80px;height:80px;margin:0 auto;'>
                    <svg width='80' height='80' viewBox='0 0 80 80'>
                        <circle cx='40' cy='40' r='{r_circ}' fill='none' stroke='rgba(201,168,76,0.1)' stroke-width='7'/>
                        <circle cx='40' cy='40' r='{r_circ}' fill='none' stroke='{level_col}' stroke-width='7'
                            stroke-dasharray='{dash:.1f} {circ:.1f}' stroke-dashoffset='{circ/4:.1f}' stroke-linecap='round'/>
                    </svg>
                    <div style='position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;'>
                        <div style='font-family:Orbitron,sans-serif;font-size:0.85rem;color:{level_col};'>{sv}</div>
                    </div>
                </div>
                <div style='color:{level_col};font-size:0.56rem;letter-spacing:1.5px;margin-top:3px;'>{level}</div>
                <div style='color:#a89968;font-size:0.52rem;margin-top:2px;'>{_eq_count} M4.5+ / 24h</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style='text-align:center;margin:8px 0;'>
            <span class='float-badge'>🌋 Live</span>
            <span class='float-badge'>🌍 Earth Science</span>
        </div>""", unsafe_allow_html=True)

        # Achievement-mode theme song — plays ONLY while rare_mode is active
        # (auto-triggered on unlock, auto-stops when it expires). No manual
        # toggle — this isn't general ambient audio, it's part of the easter egg.
        if st.session_state.get("rare_mode") and st.session_state.get("ambient_sound"):
            _audio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio.mp3")
            if os.path.exists(_audio_path):
                st.audio(_audio_path, format="audio/mp3", loop=True, autoplay=True)

        st.markdown("""
        <div style='font-size:0.57rem;color:#a89968;text-align:center;padding:6px 0;line-height:2;'>
            <span style='color:#c9a84c;opacity:0.5;'>Made for Earth Science</span><br>
            <span>Dedicated to Curiosity.</span>
        </div>""", unsafe_allow_html=True)
