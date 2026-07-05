# GeoSphere India — Flashcards
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

st.set_page_config(page_title="Flashcards — GeoSphere India", page_icon="🃏", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Geology", "Flashcards", "TERMS & CONCEPTS")

st.markdown("<div class='section-heading'>FLASHCARDS — GEOLOGY TERMS & CONCEPTS</div>", unsafe_allow_html=True)

fc_sections = ["All Sections"] + sorted(set(c.get("section", "General") for c in FLASHCARDS))
sel_section = st.selectbox("Filter by Section", fc_sections, key="fc_section_filter")

if sel_section == "All Sections":
    active_cards = FLASHCARDS
else:
    active_cards = [c for c in FLASHCARDS if c.get("section", "General") == sel_section]

# Clamp index if filter shrinks the deck
if st.session_state.fc_idx >= len(active_cards):
    st.session_state.fc_idx = 0

total_fc = len(active_cards)
fc = active_cards[st.session_state.fc_idx]
mastered = len(st.session_state.fc_mastered)

st.markdown(f"""
<div style='display:flex;justify-content:space-between;margin-bottom:12px;'>
    <span style='color:#94a3b8;font-size:0.78rem;'>Card {st.session_state.fc_idx+1} of {total_fc}
        <span style='color:#00d4ff;'>· {fc.get("section","General")}</span></span>
    <span style='color:#10b981;font-size:0.78rem;'>✅ Mastered: {mastered}/{len(FLASHCARDS)}</span>
</div>""", unsafe_allow_html=True)

st.markdown(f"""
<div class='flashcard-box'>
    <div class='flashcard-q'>Q: {fc["q"]}</div>
    {"<div class='flashcard-a'>A: " + fc["a"] + "</div>" if st.session_state.fc_show else ""}
</div>""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("👁️ Reveal"):
        st.session_state.fc_show = True
        st.rerun()
with c2:
    if st.button("⬅️ Previous") and st.session_state.fc_idx > 0:
        st.session_state.fc_idx  -= 1
        st.session_state.fc_show  = False
        st.rerun()
with c3:
    if st.button("➡️ Next") and st.session_state.fc_idx < total_fc - 1:
        st.session_state.fc_idx  += 1
        st.session_state.fc_show  = False
        st.rerun()
with c4:
    if st.button("✅ Mastered"):
        global_idx = FLASHCARDS.index(fc)
        if global_idx not in st.session_state.fc_mastered:
            st.session_state.fc_mastered.append(global_idx)
        st.session_state.fc_idx  = (st.session_state.fc_idx + 1) % total_fc
        st.session_state.fc_show = False
        st.rerun()

prog_fc = mastered / len(FLASHCARDS)
st.markdown(f"""
<div style='background:rgba(255,255,255,0.06);border-radius:8px;height:6px;margin-top:14px;'>
    <div style='background:linear-gradient(90deg,#10b981,#00d4ff);height:6px;border-radius:8px;
        width:{prog_fc*100:.1f}%;'></div>
</div>
<div style='color:#94a3b8;font-size:0.72rem;margin-top:4px;'>{int(prog_fc*100)}% mastered overall</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: AI ASSISTANT
# ═══════════════════════════════════════════════════════════════

st.markdown("<hr style='border-color:rgba(201,168,76,0.15);margin:20px 0;'>", unsafe_allow_html=True)
st.markdown("<div class='section-heading'>🔁 SPACED REPETITION — Cards You Miss Come Back Sooner</div>", unsafe_allow_html=True)
if "sr_deck" not in st.session_state:
    st.session_state.sr_deck = list(range(len(FLASHCARDS)))
    st.session_state.sr_missed = []
    st.session_state.sr_idx = 0
    st.session_state.sr_show = False
    st.session_state.sr_round = 1

if st.session_state.sr_deck:
    sr_fc = FLASHCARDS[st.session_state.sr_deck[st.session_state.sr_idx]]
    st.markdown(f"""
    <div style='display:flex;justify-content:space-between;margin-bottom:10px;'>
        <span style='color:#94a3b8;font-size:0.76rem;'>Round {st.session_state.sr_round} · Card {st.session_state.sr_idx+1}/{len(st.session_state.sr_deck)}</span>
        <span style='color:#f59e0b;font-size:0.76rem;'>Missed: {len(st.session_state.sr_missed)}</span>
    </div>
    <div class='flashcard-box'>
        <div class='flashcard-q'>Q: {sr_fc["q"]}</div>
        {"<div class='flashcard-a'>A: " + sr_fc["a"] + "</div>" if st.session_state.sr_show else ""}
    </div>""", unsafe_allow_html=True)
    _sr1,_sr2,_sr3 = st.columns(3)
    with _sr1:
        if st.button("👁️ Show Answer", key="sr_show"):
            st.session_state.sr_show = True
            st.rerun()
    if st.session_state.sr_show:
        with _sr2:
            if st.button("✅ Got it!", key="sr_got"):
                st.session_state.sr_idx += 1
                st.session_state.sr_show = False
                if st.session_state.sr_idx >= len(st.session_state.sr_deck):
                    if st.session_state.sr_missed:
                        st.session_state.sr_deck = st.session_state.sr_missed[:]
                        st.session_state.sr_missed = []
                        st.session_state.sr_idx = 0
                        st.session_state.sr_round += 1
                    else:
                        st.session_state.sr_deck = []
                st.rerun()
        with _sr3:
            if st.button("❌ Missed", key="sr_miss"):
                st.session_state.sr_missed.append(st.session_state.sr_deck[st.session_state.sr_idx])
                st.session_state.sr_idx += 1
                st.session_state.sr_show = False
                if st.session_state.sr_idx >= len(st.session_state.sr_deck):
                    st.session_state.sr_deck = st.session_state.sr_missed[:]
                    st.session_state.sr_missed = []
                    st.session_state.sr_idx = 0
                    st.session_state.sr_round += 1
                st.rerun()
else:
    st.success("🎉 All cards mastered! No more missed cards.")
    if st.button("🔄 Restart Spaced Repetition"):
        st.session_state.sr_deck = list(range(len(FLASHCARDS)))
        st.session_state.sr_missed = []
        st.session_state.sr_idx = 0
        st.session_state.sr_show = False
        st.session_state.sr_round = 1
        st.rerun()
