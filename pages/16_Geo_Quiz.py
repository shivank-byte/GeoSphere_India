# GeoSphere India — Geo Quiz
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

st.set_page_config(page_title="Geo Quiz — GeoSphere India", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Geologist", "Geo Quiz", "TEST YOUR KNOWLEDGE")

st.markdown("<div class='section-heading'>GEO QUIZ — TIMED · SCORED · RANDOMIZED</div>", unsafe_allow_html=True)

quiz_sections = ["All Sections"] + sorted(set(q.get("section", "General") for q in QUIZ_QUESTIONS))
qf1, qf2 = st.columns(2)
with qf1:
    sel_quiz_section = st.selectbox("Filter by Section", quiz_sections, key="quiz_section_filter")
with qf2:
    sel_difficulty = st.selectbox("Difficulty", ["All Levels", "Basic", "Intermediate", "Advanced"], key="quiz_difficulty_filter")

if sel_quiz_section == "All Sections":
    active_questions = QUIZ_QUESTIONS
else:
    active_questions = [q for q in QUIZ_QUESTIONS if q.get("section", "General") == sel_quiz_section]
if sel_difficulty != "All Levels":
    active_questions = [q for q in active_questions if get_quiz_difficulty(q) == sel_difficulty]
if not active_questions:
    st.warning("No questions match that combination — showing all sections at this difficulty instead.")
    active_questions = [q for q in QUIZ_QUESTIONS if sel_difficulty == "All Levels" or get_quiz_difficulty(q) == sel_difficulty]

total = len(active_questions)
if (st.session_state.quiz_order is None
        or st.session_state.get("quiz_section_used") != sel_quiz_section
        or st.session_state.get("quiz_difficulty_used") != sel_difficulty
        or len(st.session_state.quiz_order) != total):
    st.session_state.quiz_order = random.sample(range(total), total)
    st.session_state.quiz_section_used = sel_quiz_section
    st.session_state.quiz_difficulty_used = sel_difficulty
    st.session_state.quiz_idx = 0
    st.session_state.quiz_score = 0
    st.session_state.quiz_answered = False

idx = st.session_state.quiz_idx
progress = idx / total
st.markdown(f"""
<div style='display:flex;justify-content:space-between;margin-bottom:6px;'>
    <span style='color:#94a3b8;font-size:0.78rem;'>Question {min(idx+1,total)} of {total}</span>
    <span style='color:#00d4ff;font-family:Orbitron;font-size:0.82rem;'>
        Score: {st.session_state.quiz_score}/{total}</span>
</div>
<div style='background:rgba(255,255,255,0.06);border-radius:10px;height:5px;margin-bottom:18px;'>
    <div style='background:linear-gradient(90deg,#00d4ff,#7c3aed);height:5px;border-radius:10px;
        width:{progress*100:.1f}%;'></div>
</div>""", unsafe_allow_html=True)

if idx < total:
    q = active_questions[st.session_state.quiz_order[idx]]
    _diff = get_quiz_difficulty(q)
    _diff_col = {"Basic":"#10b981","Intermediate":"#f59e0b","Advanced":"#dc2626"}[_diff]
    st.markdown(f"""<span style='background:{_diff_col}22;color:{_diff_col};font-size:0.65rem;
        padding:2px 9px;border-radius:10px;'>{_diff}</span>""", unsafe_allow_html=True)
    st.markdown(f"<div class='quiz-question'>{idx+1}. {q['q']}</div>", unsafe_allow_html=True)

    if not st.session_state.quiz_answered:
        opt_cols = st.columns(2)
        for oi, opt in enumerate(q["options"]):
            with opt_cols[oi % 2]:
                if st.button(f"  {opt}", key=f"qopt_{oi}"):
                    st.session_state.quiz_answered = True
                    st.session_state.quiz_chosen   = oi
                    if oi == q["answer"]:
                        st.session_state.quiz_score += 1
                    st.rerun()
    else:
        chosen  = st.session_state.quiz_chosen
        correct = q["answer"]
        for oi, opt in enumerate(q["options"]):
            if oi == correct:
                st.markdown(f"<div class='quiz-correct'>✅ {opt}</div>", unsafe_allow_html=True)
            elif oi == chosen:
                st.markdown(f"<div class='quiz-wrong'>❌ {opt}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='color:#334155;padding:2px 0;'>◻️ {opt}</div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class='glass-card' style='margin-top:12px;border-color:rgba(16,185,129,0.3);'>
            <span style='color:#10b981;font-weight:600;'>💡 Explanation: </span>
            <span style='color:#94a3b8;font-size:0.85rem;'>{q["explain"]}</span>
        </div>""", unsafe_allow_html=True)

        if st.button("Next Question →"):
            st.session_state.quiz_idx += 1
            st.session_state.quiz_answered = False
            st.session_state.quiz_chosen   = None
            st.rerun()
else:
    sc  = st.session_state.quiz_score
    pct = int(sc / total * 100)
    if pct >= 90:   grade, badge_color, badge_icon = "Geology Expert",    "#f59e0b", "🏆"
    elif pct >= 75: grade, badge_color, badge_icon = "Field Geologist",   "#10b981", "⭐"
    elif pct >= 60: grade, badge_color, badge_icon = "Student Geologist", "#00d4ff", "📚"
    elif pct >= 40: grade, badge_color, badge_icon = "Rock Hound",        "#a78bfa", "🔬"
    else:           grade, badge_color, badge_icon = "Earth Apprentice",  "#94a3b8", "🌱"

    st.markdown(f"""
    <div class='hero-banner'>
        <div style='font-family:Orbitron;font-size:2.5rem;color:#f59e0b;'>{sc}/{total}</div>
        <div style='font-size:1rem;color:#e2e8f0;margin:8px 0;'>{pct}% Correct</div>
        <div class='hero-badge' style='background:{badge_color}22;border-color:{badge_color}66;color:{badge_color};font-size:1rem;padding:8px 20px;'>
            {badge_icon} {grade}
        </div>
        <div style='color:#475569;font-size:0.75rem;margin-top:10px;'>
            Section: {sel_quiz_section}
        </div>
    </div>""", unsafe_allow_html=True)

    if pct == 100:
        st.success("🎉 Perfect score! You've mastered this section!")
        st.balloons()
    elif pct >= 90:
        st.balloons()

    if st.button("🔄 Restart Quiz"):
        st.session_state.quiz_idx      = 0
        st.session_state.quiz_score    = 0
        st.session_state.quiz_answered = False
        st.session_state.quiz_chosen   = None
        st.session_state.quiz_order    = random.sample(range(total), total)
        st.rerun()

# ═══════════════════════════════════════════════════════════════
#  PAGE: FLASHCARDS
# ═══════════════════════════════════════════════════════════════

st.markdown("<hr style='border-color:rgba(201,168,76,0.15);margin:20px 0;'>", unsafe_allow_html=True)
st.markdown("<div class='section-heading'>⚡ RAPID FIRE MODE — 10 Questions · 15 Seconds Each</div>", unsafe_allow_html=True)
if "rf_active" not in st.session_state:
    st.session_state.rf_active = False
    st.session_state.rf_idx = 0
    st.session_state.rf_score = 0
    st.session_state.rf_qs = []

if not st.session_state.rf_active:
    st.markdown("<div style='color:#94a3b8;font-size:0.8rem;margin-bottom:10px;'>10 random questions. 15 seconds per question. No explanations. Pure speed.</div>", unsafe_allow_html=True)
    if st.button("⚡ Start Rapid Fire!", key="rf_start"):
        st.session_state.rf_active = True
        st.session_state.rf_idx = 0
        st.session_state.rf_score = 0
        st.session_state.rf_qs = random.sample(QUIZ_QUESTIONS, min(10, len(QUIZ_QUESTIONS)))
        st.session_state.rf_start_time = time.time()
        st.rerun()
else:
    rf_qs = st.session_state.rf_qs
    idx = st.session_state.rf_idx
    if idx < len(rf_qs):
        q = rf_qs[idx]
        elapsed = time.time() - st.session_state.rf_start_time
        remaining = max(0, 15 - int(elapsed))
        prog = remaining / 15
        st.markdown(f"""
        <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
            <span style='color:#94a3b8;'>Q {idx+1}/10</span>
            <span style='color:{"#dc2626" if remaining < 5 else "#f59e0b" if remaining < 10 else "#10b981"};
                font-family:Orbitron;font-size:1.1rem;'>{remaining}s</span>
            <span style='color:#00d4ff;'>Score: {st.session_state.rf_score}</span>
        </div>
        <div style='background:rgba(255,255,255,0.06);border-radius:4px;height:4px;margin-bottom:12px;'>
            <div style='background:{"#dc2626" if remaining<5 else "#10b981"};height:4px;border-radius:4px;width:{prog*100:.0f}%;'></div>
        </div>
        <div style='color:#e2e8f0;font-size:0.9rem;margin-bottom:12px;padding:12px;background:rgba(12,20,45,0.8);border-radius:10px;'>{q["q"]}</div>
        """, unsafe_allow_html=True)
        if remaining == 0:
            st.session_state.rf_idx += 1
            st.session_state.rf_start_time = time.time()
            st.rerun()
        rf_cols = st.columns(2)
        for oi, opt in enumerate(q["options"]):
            with rf_cols[oi%2]:
                if st.button(opt, key=f"rf_{idx}_{oi}", use_container_width=True):
                    if oi == q["answer"]:
                        st.session_state.rf_score += 1
                    st.session_state.rf_idx += 1
                    st.session_state.rf_start_time = time.time()
                    st.rerun()
    else:
        pct = int(st.session_state.rf_score / 10 * 100)
        grade = "🏆 Perfect!" if pct==100 else "⚡ Lightning Fast!" if pct>=80 else "⭐ Good!" if pct>=60 else "📚 Keep Practising"
        st.markdown(f"""
        <div style='text-align:center;padding:24px;'>
            <div style='font-family:Orbitron;font-size:2rem;color:#f59e0b;'>{st.session_state.rf_score}/10</div>
            <div style='color:#e2e8f0;margin:8px 0;'>{grade}</div>
        </div>""", unsafe_allow_html=True)
        if st.button("🔄 Try Again", key="rf_restart"):
            st.session_state.rf_active = False
            st.rerun()
