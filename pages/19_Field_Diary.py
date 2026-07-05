# GeoSphere India — Field Diary
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

st.set_page_config(page_title="Field Diary — GeoSphere India", page_icon="📓", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Geologist", "Field Diary", "A GEOLOGIST'S JOURNEY")

st.markdown("<div class='section-heading'>FIELD DIARY — A GEOLOGIST'S JOURNEY</div>", unsafe_allow_html=True)
for entry in DIARY_ENTRIES:
    dcol1, dcol2 = st.columns([1, 3])
    with dcol1:
        show_wiki_photo(entry.get("location", entry["date"]), caption=entry.get("location", ""))
    with dcol2:
        st.markdown(f"""
        <div class='diary-card'>
            <div class='diary-date'>{entry["date"]}</div>
            <div class='diary-text'>{entry["text"]}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("""
<div class='glass-card' style='text-align:center;border-color:rgba(124,58,237,0.3);'>
    <div style='color:#7c3aed;font-family:Orbitron;font-size:0.75rem;letter-spacing:2px;'>
    ARCHIVE STATISTICS
    </div>
    <div style='color:#475569;font-size:0.78rem;margin-top:12px;line-height:2.4;font-family:Exo 2;'>
    Years Active ............ 11<br>
    Integrity ............... 100%<br>
    Memories Lost ........... 0
    </div>
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: ABOUT & ARCHIVE (Easter Egg trigger here)
# ═══════════════════════════════════════════════════════════════

st.markdown("<div class='section-heading'>✍️ WRITE YOUR OWN FIELD ENTRY</div>", unsafe_allow_html=True)
if "user_diary" not in st.session_state:
    st.session_state.user_diary = []
_dc1, _dc2 = st.columns([1,2])
with _dc1:
    _entry_date = st.text_input("Date/Title", placeholder="Day 15 — First Outcrop", key="diary_date")
with _dc2:
    _entry_text = st.text_area("Your observation", placeholder="Describe what you saw, touched, or understood today...", key="diary_text", height=100)
if st.button("📝 Save Entry", key="save_diary"):
    if _entry_date and _entry_text:
        st.session_state.user_diary.append({"date":_entry_date,"text":_entry_text})
        st.success("Entry saved!")
        st.rerun()
if st.session_state.user_diary:
    st.markdown("<div class='section-heading'>YOUR ENTRIES</div>", unsafe_allow_html=True)
    for entry in reversed(st.session_state.user_diary):
        st.markdown(f"""
        <div class='diary-card'>
            <div class='diary-date'>{entry["date"]}</div>
            <div class='diary-text'>{entry["text"]}</div>
        </div>""", unsafe_allow_html=True)
