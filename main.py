import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import random
import math
import time
import datetime
import requests

# ═══════════════════════════════════════════════════════
#  PAGE CONFIG  — must be first Streamlit call
# ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="GeoSphere India",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    "Human Diary":            "Kuch alfaaz likhe nahi jaate, phir bhi padhe jaate hain.",
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
    font-family: 'Playfair Display', Georgia, serif !important;
    font-style: italic !important;
    letter-spacing: 1px !important;
}
.mineral-card { border-color: rgba(58,123,213,0.25) !important; }
.metric-card  { border-color: rgba(58,123,213,0.2) !important; }
.metric-value { color: #6ea8fe !important; }
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

/* Emoji rain — 3 staggered streams */
#emoji-rain-a,#emoji-rain-b,#emoji-rain-c {
    position:fixed;top:0;left:0;width:100vw;height:0;
    pointer-events:none;z-index:9998;overflow:visible;
    font-size:1.3rem;white-space:nowrap;opacity:0;
}
#emoji-rain-a { animation: fall-a 7s linear 0.5s infinite; }
#emoji-rain-b { animation: fall-b 7s linear 2.5s infinite; }
#emoji-rain-c { animation: fall-c 7s linear 4.5s infinite; }

#emoji-rain-a::before { content:"✨    ⭐    📖    💙    🌌    ✨    ⭐    🌌"; position:absolute;top:0;left:5%; }
#emoji-rain-b::before { content:"📖    💙    ✨    🌌    ⭐    📖    💙    ✨"; position:absolute;top:0;left:30%; }
#emoji-rain-c::before { content:"🌌    ✨    💙    ⭐    📖    🌌    ✨    💙"; position:absolute;top:0;left:58%; }

@keyframes fall-a { 0%{opacity:0;transform:translateY(-40px)} 8%{opacity:0.65} 92%{opacity:0.65} 100%{opacity:0;transform:translateY(105vh)} }
@keyframes fall-b { 0%{opacity:0;transform:translateY(-40px)} 8%{opacity:0.5}  92%{opacity:0.5}  100%{opacity:0;transform:translateY(105vh)} }
@keyframes fall-c { 0%{opacity:0;transform:translateY(-40px)} 8%{opacity:0.55} 92%{opacity:0.55} 100%{opacity:0;transform:translateY(105vh)} }
</style>
"""

NORMAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;0,900;1,400;1,600&family=Source+Sans+3:wght@300;400;500;600;700&family=Orbitron:wght@400;700;900&display=swap');

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
}

.stApp {
    background: linear-gradient(160deg,#070b18 0%,#0c1428 35%,#0a1232 65%,#060916 100%) !important;
    font-family: var(--sans);
    color: var(--text-main);
    font-size: 16px;
}

#MainMenu, footer, header { visibility: hidden; }
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
.diary-date { font-family:var(--serif); font-size:0.78rem; color:var(--gold); letter-spacing:1px; font-style:italic; }
.diary-text { color:var(--text-main); font-size:0.95rem; line-height:1.8; margin-top:10px; font-family:var(--sans); }

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
    font-family:var(--serif); font-size:1rem; color:#6ea8fe;
    font-style:italic; text-align:center; margin-top:8px; letter-spacing:0.5px; opacity:0.85;
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

/* ── Sidebar toggle always visible — mobile + desktop ── */
[data-testid="collapsedControl"] {
    background: rgba(201,168,76,0.18) !important;
    border: 1px solid rgba(201,168,76,0.5) !important;
    border-radius: 0 10px 10px 0 !important;
    width: 36px !important;
    min-height: 60px !important;
    opacity: 1 !important;
    visibility: visible !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
[data-testid="collapsedControl"]:hover {
    background: rgba(201,168,76,0.35) !important;
    box-shadow: 3px 0 16px rgba(201,168,76,0.35) !important;
}
[data-testid="collapsedControl"] svg { 
    fill: #c9a84c !important;
    width: 20px !important;
    height: 20px !important;
}
section[data-testid="stSidebarCollapsedControl"] { 
    opacity: 1 !important; 
    visibility: visible !important;
    display: block !important;
    pointer-events: all !important;
}
/* Mobile specific */
@media (max-width: 768px) {
    [data-testid="collapsedControl"] {
        width: 44px !important;
        min-height: 70px !important;
        background: rgba(201,168,76,0.25) !important;
    }
}
</style>
"""

# Inject CSS
if st.session_state.rare_mode:
    st.markdown(RARE_CSS, unsafe_allow_html=True)
st.markdown(NORMAL_CSS, unsafe_allow_html=True)

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
    {"title":"Physical Geology","author":"Plummer, Carlson & Hammersley","subject":"Sem 1 – Physical Geology","stars":5,
     "desc":"BHU standard reference. Covers Earth processes from minerals to plate tectonics. Excellent figures."},
    {"title":"Earth Materials","author":"Hefferan & O'Brien","subject":"Sem 1 – Earth Materials","stars":4,
     "desc":"Modern mineralogy and petrology reference. Good coverage of optical properties and Indian examples."},
    {"title":"Principles of Geomorphology","author":"W.D. Thornbury","subject":"Sem 2 – Geomorphology","stars":5,
     "desc":"Landmark work on landform evolution. Essential for Indian physiographic divisions and drainage patterns."},
    {"title":"Optical Mineralogy","author":"W.A. Deer, Howie & Zussman","subject":"Sem 2 – Mineralogy","stars":5,
     "desc":"The definitive petrography reference. Optical properties of all rock-forming minerals under polarised light."},
    {"title":"Petrology of Igneous & Metamorphic Rocks","author":"Hyndman","subject":"Sem 3 – Petrology","stars":4,
     "desc":"Detailed igneous and metamorphic petrography. Good companion to Deccan Traps and Himalayan studies."},
    {"title":"Structural Geology","author":"M.P. Billings","subject":"Sem 3 – Structural Geology","stars":5,
     "desc":"Rigorous treatment of folds, faults, and foliations. Used extensively in BHU practical classes."},
    {"title":"An Introduction to Palaeontology","author":"A.K. Dutta","subject":"Sem 4 – Palaeontology","stars":4,
     "desc":"Indian author. Covers invertebrate fossil groups critical for Gondwana stratigraphy of peninsular India."},
    {"title":"Stratigraphy & Sedimentation","author":"Krumbein & Sloss","subject":"Sem 4 – Stratigraphy","stars":5,
     "desc":"Classic on sedimentary environments and stratigraphic correlation — vital for Indian basin analysis."},
    {"title":"Mining Geology","author":"H.M. Ramaiah","subject":"Sem 5 – Economic Geology","stars":4,
     "desc":"Indian text covering ore deposits, economic minerals, and exploration geology relevant to GSI work."},
    {"title":"Groundwater Hydrology","author":"D.K. Todd","subject":"Sem 5 – Hydrogeology","stars":4,
     "desc":"Standard hydrogeology text covering aquifer types, well hydraulics, groundwater flow — all relevant to India."},
    {"title":"Remote Sensing & Image Interpretation","author":"Lillesand & Kiefer","subject":"Sem 6 – Remote Sensing","stars":5,
     "desc":"The remote sensing bible. Essential for satellite-based geological mapping and GIS integration."},
    {"title":"Geochemistry","author":"Krauskopf & Bird","subject":"Sem 7 – Geochemistry","stars":4,
     "desc":"Covers elemental distribution, isotopes, thermodynamics — foundation for petrology and ore studies."},
    {"title":"Principles of Oceanography","author":"Davis","subject":"Sem 8 – Oceanography","stars":3,
     "desc":"Covers ocean dynamics, Indian Ocean currents, tides, marine geology — relevant to Indian coast."},
]

QUIZ_QUESTIONS = [
    {"q":"Which mineral effervesces vigorously with dilute HCl?",
     "options":["Quartz","Calcite","Feldspar","Mica"],"answer":1,
     "explain":"Calcite (CaCO₃) + 2HCl → CaCl₂ + H₂O + CO₂↑. The fizzing is the CO₂ escaping — a classic field test."},
    {"q":"The Deccan Traps are primarily composed of which rock type?",
     "options":["Granite","Limestone","Basalt","Quartzite"],"answer":2,
     "explain":"Deccan Traps = flood basalts erupted ~66 Ma, covering ~500,000 km² — one of Earth's largest volcanic events."},
    {"q":"Which tectonic event created the Himalayas?",
     "options":["Pacific subduction","India–Eurasia collision","Atlantic spreading","African rift"],"answer":1,
     "explain":"India–Eurasia collision started ~50 Ma ago. India still moves NNE at ~5 cm/yr, continually lifting the Himalayas."},
    {"q":"What does the Mohorovičić discontinuity (Moho) separate?",
     "options":["Inner & outer core","Crust & mantle","Mantle & outer core","Lithosphere & asthenosphere"],"answer":1,
     "explain":"The Moho marks the seismic velocity jump from crust (~6 km/s) to mantle (~8 km/s). Detected by Mohorovičić in 1909."},
    {"q":"Which Indian state has the largest coal reserves?",
     "options":["Odisha","Jharkhand","Chhattisgarh","West Bengal"],"answer":1,
     "explain":"Jharkhand holds ~26% of India's coal reserves, primarily in the Damodar Valley Gondwana coalfields."},
    {"q":"The mineral Charnockite is uniquely named after a location in India. Which city?",
     "options":["Mumbai","Kolkata","Chennai","Varanasi"],"answer":2,
     "explain":"Named after Job Charnock's tombstone at St. Thomas Mount, Chennai. The rock is a hypersthene-bearing granulite."},
    {"q":"What type of plate boundary exists between the Indian and Eurasian plates?",
     "options":["Divergent","Transform","Convergent","Passive margin"],"answer":2,
     "explain":"Convergent boundary — the Indian plate subducts/collides with Eurasia, producing the Himalayan fold-thrust belt."},
    {"q":"Which era is known as the 'Age of Reptiles'?",
     "options":["Palaeozoic","Cenozoic","Mesozoic","Precambrian"],"answer":2,
     "explain":"Mesozoic Era (252–66 Ma) — Triassic, Jurassic, Cretaceous — dominated by dinosaurs, marine reptiles, pterosaurs."},
    {"q":"Marble is metamorphosed from which sedimentary rock?",
     "options":["Sandstone","Shale","Basalt","Limestone"],"answer":3,
     "explain":"Marble = recrystallised calcite from limestone/dolostone under heat/pressure. Makrana marble built the Taj Mahal."},
    {"q":"What is the Gondwana Supercontinent? When did it begin to break up?",
     "options":["66 Ma","180 Ma","252 Ma","541 Ma"],"answer":1,
     "explain":"Gondwana began breaking up ~180 Ma (Jurassic). India, Africa, Antarctica, Australia, and South America separated."},
    {"q":"Which scale measures earthquake magnitude based on seismic moment?",
     "options":["Richter (ML)","Modified Mercalli","Moment Magnitude (Mw)","Rossi-Forel"],"answer":2,
     "explain":"Mw (Moment Magnitude) replaced Richter for large earthquakes. It measures actual energy released in the fault rupture."},
    {"q":"Which Indian state produces ~90% of India's chromite?",
     "options":["Jharkhand","Karnataka","Odisha","Rajasthan"],"answer":2,
     "explain":"Odisha's Sukinda valley is the world's 2nd largest chromite reserve. India ranks ~4th globally in production."},
    {"q":"A rock formed by compaction and cementation of sand grains is called:",
     "options":["Shale","Sandstone","Quartzite","Greywacke"],"answer":1,
     "explain":"Sandstone = lithified sand (0.06–2mm grains). Cemented by silica, calcite, or iron oxide. Common aquifer rock."},
    {"q":"What is the Mohs hardness of Diamond?",
     "options":["8","9","10","7"],"answer":2,
     "explain":"Diamond = Mohs 10 (hardest natural mineral). Composed of carbon atoms in cubic tetrahedral structure."},
    {"q":"The 2004 Indian Ocean tsunami was triggered by an earthquake at which subduction zone?",
     "options":["Makran","Andaman-Sumatra","Zagros","Hindu Kush"],"answer":1,
     "explain":"M9.1 earthquake on 26 Dec 2004 at the Sunda subduction zone near Sumatra generated the devastating Indian Ocean tsunami."},
]

FLASHCARDS = [
    {"q":"What is a batholith?","a":"A large (>100 km²) igneous intrusive body of coarse-grained rock (usually granite) that crystallised deep underground."},
    {"q":"Define unconformity in geology.","a":"A buried erosion surface (time gap) between two rock sequences representing missing geologic time."},
    {"q":"What is isostasy?","a":"Gravitational equilibrium of Earth's crust floating on denser mantle — like an iceberg on water; mountains have deep roots."},
    {"q":"What is a graben?","a":"A down-dropped crustal block between two parallel normal faults — creates rift valleys like the East African Rift."},
    {"q":"Distinguish strike and dip.","a":"Strike = compass direction of a horizontal line on a tilted surface; Dip = angle and direction of maximum inclination."},
    {"q":"What are turbidites?","a":"Graded sedimentary beds deposited by underwater avalanches (turbidity currents) down continental slopes."},
    {"q":"Define contact metamorphism.","a":"Local thermal metamorphism around a hot igneous intrusion — creates a metamorphic aureole in country rock."},
    {"q":"What is metasomatism?","a":"Chemical alteration of rock by hot fluids that change mineralogy without melting — common near igneous intrusions."},
    {"q":"What is the rock cycle?","a":"Continuous transformation: magma→igneous→weathering→sediment→sedimentary→burial→metamorphic→melting→magma again."},
    {"q":"Define foliation in metamorphic rocks.","a":"Planar fabric in metamorphic rocks from alignment of platy minerals (mica, chlorite) under directed pressure."},
    {"q":"What is an ophiolite?","a":"A slice of ancient oceanic crust emplaced (obducted) onto continental crust — preserves peridotite, gabbro, basalt, sediments."},
    {"q":"What is the Wilson Cycle?","a":"The cycle of opening and closing of ocean basins: continental rifting → ocean formation → subduction → collision → new supercontinent."},
]

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
     "last_eruption":"2017","type":"Stratovolcano","desc":"India's only active volcano. Part of Andaman arc. Last major eruption 2017."},
    {"name":"Narcondam","lat":13.43,"lon":94.25,"country":"India","status":"Dormant",
     "last_eruption":"Unknown (prehistoric)","type":"Stratovolcano","desc":"Dormant volcano, Andaman Islands. Dense forest, hornbill sanctuary."},
    {"name":"Mt. Etna","lat":37.75,"lon":15.00,"country":"Italy","status":"Active",
     "last_eruption":"2024","type":"Stratovolcano","desc":"Europe's highest & most active volcano. ~3,300 m. Almost continuously erupting."},
    {"name":"Kilauea","lat":19.42,"lon":-155.29,"country":"USA (Hawaii)","status":"Active",
     "last_eruption":"2023","type":"Shield volcano","desc":"One of Earth's most active volcanoes. Lava flows reach ocean. Forms new land."},
    {"name":"Mt. Fuji","lat":35.36,"lon":138.73,"country":"Japan","status":"Dormant",
     "last_eruption":"1707","type":"Stratovolcano","desc":"Japan's highest peak (3,776 m). Dormant since 1707. UNESCO World Heritage Site."},
    {"name":"Krakatau","lat":-6.10,"lon":105.42,"country":"Indonesia","status":"Active",
     "last_eruption":"2022","type":"Caldera/Stratovolcano","desc":"1883 eruption caused global cooling. Anak Krakatau (child of Krakatau) active today."},
    {"name":"Mt. Pinatubo","lat":15.14,"lon":120.35,"country":"Philippines","status":"Dormant",
     "last_eruption":"1991","type":"Stratovolcano","desc":"1991 eruption (2nd largest 20th century) ejected 10 km³ of material, cooled Earth 0.5°C."},
    {"name":"Eyjafjallajökull","lat":63.63,"lon":-19.62,"country":"Iceland","status":"Dormant",
     "last_eruption":"2010","type":"Stratovolcano","desc":"2010 eruption disrupted European air travel for weeks. Iceland sits on Mid-Atlantic Ridge."},
]

SOILS = [
    {"name":"Alluvial Soil","emoji":"🟡","color":"#f59e0b",
     "states":"UP, Bihar, Punjab, Haryana, West Bengal",
     "formation":"Deposition by rivers (Ganga, Indus, Brahmaputra)",
     "crops":"Wheat, rice, sugarcane, cotton",
     "area_pct":43,
     "desc":"Most fertile and widespread soil (43% of India). Rich in potash, lime. Two types: Khadar (new) and Bhangar (old)."},
    {"name":"Black (Regur) Soil","emoji":"⬛","color":"#1f2937",
     "states":"Maharashtra, MP, Gujarat, Andhra Pradesh",
     "formation":"Weathering of Deccan basaltic lava",
     "crops":"Cotton (hence 'black cotton soil'), soybean, sorghum",
     "area_pct":16,
     "desc":"Highly clayey — expands when wet, cracks when dry. Self-ploughing. Rich in iron, lime, magnesium. Cotton heartland."},
    {"name":"Red & Yellow Soil","emoji":"🔴","color":"#dc2626",
     "states":"Odisha, Chhattisgarh, Jharkhand, parts of AP",
     "formation":"Weathering of crystalline igneous and metamorphic rocks",
     "crops":"Rice, wheat, millets, pulses, groundnut",
     "area_pct":18,
     "desc":"Red color from iron oxide. Less fertile than alluvial. Porous, friable. Needs irrigation and fertiliser."},
    {"name":"Laterite Soil","emoji":"🟤","color":"#92400e",
     "states":"Kerala, Karnataka, Assam, Meghalaya, TN",
     "formation":"Intense leaching in high-rainfall tropical areas",
     "crops":"Tea, coffee, cashew, rubber, coconut",
     "area_pct":8,
     "desc":"Forms in hot wet tropical zones — aluminum and iron hydroxides remain after silica is leached. Used as building brick."},
    {"name":"Mountain Soil","emoji":"🏔️","color":"#4b5563",
     "states":"J&K, Himachal Pradesh, Uttarakhand, NE states",
     "formation":"Physical weathering on steep slopes, thin profile",
     "crops":"Apples, pears, potatoes, wheat (terraced)",
     "area_pct":8,
     "desc":"Thin, humus-rich in upper layers. Very variable. Acidic. Requires careful management to prevent erosion."},
    {"name":"Arid (Desert) Soil","emoji":"🏜️","color":"#fbbf24",
     "states":"Rajasthan, parts of Gujarat, Haryana",
     "formation":"Physical weathering in dry climate, low organic matter",
     "crops":"Bajra, pulses (with irrigation — wheat, cotton)",
     "area_pct":4,
     "desc":"Sandy, low organic, high soluble salts. Irrigation causes waterlogging/salinisation. Caliche (kankar) layers common."},
    {"name":"Saline/Alkaline Soil","emoji":"🧂","color":"#e5e7eb",
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
     "geo":"Himalayan river — youthful with steep gradient in mountains, mature meandering on plains"},
    {"name":"Brahmaputra","length_km":2900,"origin":"Angsi Glacier, Tibet (Yarlung Tsangpo)",
     "joins":"Bay of Bengal","basin_km2":651000,"pattern":"Braided",
     "tributaries":["Dibang","Lohit","Subansiri","Teesta"],
     "states":["Arunachal Pradesh","Assam"],
     "geo":"Antecedent river — older than Himalayas, carved gorge 5,500m deep in Eastern Himalayas"},
    {"name":"Godavari","length_km":1465,"origin":"Trimbakeshwar, Nashik, Maharashtra",
     "joins":"Bay of Bengal","basin_km2":312812,"pattern":"Dendritic-trellis",
     "tributaries":["Indravati","Pranhita","Manjira","Wardha"],
     "states":["Maharashtra","Telangana","AP"],
     "geo":"Largest peninsular river. Flows over Deccan Traps — gorges at Eastern Ghats. 'Dakshin Ganga'."},
    {"name":"Krishna","length_km":1400,"origin":"Mahabaleshwar, Maharashtra",
     "joins":"Bay of Bengal","basin_km2":258948,"pattern":"Dendritic",
     "tributaries":["Bhima","Tungabhadra","Musi","Koyna"],
     "states":["Maharashtra","Karnataka","AP","Telangana"],
     "geo":"Flows over Deccan basalt. Nagarjunasagar and Srisailam dams in gorge through Eastern Ghats."},
    {"name":"Indus","length_km":3180,"origin":"Sengge Zangbo, Tibet",
     "joins":"Arabian Sea","basin_km2":1165000,"pattern":"Dendritic",
     "tributaries":["Sutlej","Chenab","Ravi","Beas","Jhelum"],
     "states":["J&K","Ladakh (then Pakistan)"],
     "geo":"Ancient river — antecedent to Karakoram and Hindu Kush. Forms alluvial plains of Punjab."},
    {"name":"Narmada","length_km":1312,"origin":"Amarkantak, MP",
     "joins":"Arabian Sea","basin_km2":98796,"pattern":"Rectangular (fault-controlled)",
     "tributaries":["Tawa","Burhner","Hiran","Orsang"],
     "states":["MP","Maharashtra","Gujarat"],
     "geo":"Flows W-E along Narmada rift — a graben between Vindhyas and Satpuras. Marble Rocks at Bhedaghat."},
]

ECONOMIC_MINERALS = {
    "Coal": {"states":{"Jharkhand":26,"Odisha":25,"Chhattisgarh":17,"WB":11,"MP":9,"Others":12},
             "color":"#374151","emoji":"⬛","use":"Power (80%), coking coal for steel","india_rank":"World #3 producer"},
    "Iron Ore": {"states":{"Odisha":35,"Chhattisgarh":22,"Jharkhand":16,"Karnataka":14,"Others":13},
                  "color":"#b45309","emoji":"🔴","use":"Steel industry, export","india_rank":"World #4 producer"},
    "Bauxite": {"states":{"Odisha":50,"Jharkhand":17,"Gujarat":9,"Maharashtra":8,"Others":16},
                 "color":"#92400e","emoji":"🟤","use":"Aluminium production (99%)","india_rank":"World #5 producer"},
    "Copper": {"states":{"Rajasthan":52,"Jharkhand":34,"MP":8,"Others":6},
                "color":"#b45309","emoji":"🟠","use":"Electrical wiring, plumbing, electronics","india_rank":"Minor producer, imports ~95%"},
    "Zinc-Lead": {"states":{"Rajasthan":90,"Others":10},
                   "color":"#6b7280","emoji":"⚫","use":"Galvanising steel, batteries, paint","india_rank":"World #1 in zinc (Hindustan Zinc)"},
    "Chromite": {"states":{"Odisha":92,"Karnataka":5,"Others":3},
                  "color":"#1f2937","emoji":"🟫","use":"Stainless steel, refractory bricks","india_rank":"World #4 producer"},
    "Gold": {"states":{"Karnataka":75,"Andhra Pradesh":20,"Others":5},
              "color":"#f59e0b","emoji":"🥇","use":"Jewellery, electronics, reserves","india_rank":"Minor; imports ~800 tonnes/yr"},
    "Limestone": {"states":{"Rajasthan":22,"AP":16,"Karnataka":14,"Gujarat":9,"Others":39},
                   "color":"#e5e7eb","emoji":"⬜","use":"Cement (#1), steel flux, agriculture","india_rank":"World #2 cement producer"},
}

NOTES = {
    "Semester 1": {
        "Physical Geology": [
            "**Earth's Origin**: Nebular hypothesis — solar nebula collapsed 4.6 Ga ago; differentiation → core + mantle + crust.",
            "**Plate Tectonics**: Lithosphere (~100 km thick) moves on viscous asthenosphere. 3 boundary types: divergent, convergent, transform.",
            "**Earthquakes**: Stress release on faults → seismic waves (P, S, Love, Rayleigh). Focus vs Epicentre. Mw scale.",
            "**Volcanoes**: Magma reaches surface → lava. Types: shield, stratovolcano, caldera. Related to hot spots + plate boundaries.",
            "**Rock Cycle**: Igneous → weathering → sediment → sedimentary → metamorphism → metamorphic → melting → igneous.",
            "**Geologic Time**: Relative (superposition, cross-cutting) vs absolute (radiometric dating, C-14, U-Pb, K-Ar).",
            "**Geomorphic Agents**: Running water, glaciers, wind, waves, groundwater — all shape landforms.",
        ],
        "Earth Materials": [
            "**Minerals**: Naturally occurring, inorganic, definite composition, crystalline structure. ~4000 known minerals.",
            "**Crystal Systems**: Cubic, tetragonal, orthorhombic, hexagonal, trigonal, monoclinic, triclinic — 7 systems.",
            "**Physical Properties**: Colour, streak, lustre, hardness (Mohs), cleavage, fracture, specific gravity, magnetism.",
            "**Silicate Structure**: SiO₄ tetrahedra — nesosilicates, sorosilicates, cyclosilicates, inosilicates, phyllosilicates, tectosilicates.",
            "**Non-silicate minerals**: Oxides, sulphides, carbonates, sulphates, halides, native elements — many are ore minerals.",
        ],
    },
    "Semester 2": {
        "Mineralogy": [
            "**Optical Properties**: Refractive index, birefringence, extinction angle, pleochroism — studied in polarising microscope.",
            "**Thin Section**: Rock ground to 0.03mm. Minerals transparent. Crossed polars → interference colours (Michel-Lévy chart).",
            "**Isotropic vs Anisotropic**: Cubic minerals → isotropic (dark under XPL); others → anisotropic (coloured interference).",
            "**Uniaxial vs Biaxial**: Tetragonal/hexagonal → uniaxial (one optic axis). Orthorhombic/monoclinic/triclinic → biaxial (two optic axes).",
            "**Common minerals under microscope**: Quartz (undulatory extinction, no colour), feldspar (twinning), biotite (strong pleochroism).",
        ],
        "Geomorphology": [
            "**Drainage Patterns**: Dendritic (homogeneous rock), trellis (folded/faulted), rectangular (joints), radial (dome/cone).",
            "**River Stages**: Youth (V-valley, waterfalls), Mature (meandering, floodplain), Old age (oxbow lakes, braided).",
            "**Glacial Landforms**: U-valley, cirque, arête, horn, drumlin, esker, moraine, fjord.",
            "**Coastal Landforms**: Wave-cut platform, sea arch, stack, spit, tombolo, beach ridge.",
            "**India Physiography**: 5 regions — Himalayas, Northern Plains, Peninsular Plateau, Coastal Plains, Islands.",
            "**Himalayan Divisions**: Trans-Himalaya, Greater Himalaya (Himadri), Lesser Himalaya (Himachal), Sub-Himalaya (Siwaliks).",
        ],
    },
    "Semester 3": {
        "Petrology": [
            "**Igneous Textures**: Phaneritic (coarse, intrusive), aphanitic (fine, extrusive), porphyritic (mixed), glassy, vesicular, pyroclastic.",
            "**Bowen's Reaction Series**: Crystallisation order of minerals from magma — discontinuous (olivine→pyroxene→amphibole→biotite) and continuous (Ca-rich→Na-rich plagioclase).",
            "**CIPW Norm**: Standard calculation to express rock composition as normative minerals from chemical analysis.",
            "**Metamorphic Facies**: P-T conditions → zeolite, prehnite-pumpellyite, greenschist, amphibolite, granulite, blueschist, eclogite.",
            "**Index Minerals**: Barrow's zones (Scotland) — chlorite→biotite→garnet→staurolite→kyanite→sillimanite = increasing metamorphic grade.",
            "**Deccan Petrology**: Tholeiitic basalts with low-K, high-Ti chemistry. Three chemically distinct formations.",
        ],
        "Structural Geology": [
            "**Stress & Strain**: Compressive, tensile, shear stress → elastic, plastic, brittle deformation depending on T, P, strain rate.",
            "**Fold Geometry**: Hinge, limbs, axial plane, plunge. Types: anticline/syncline, isoclinal, recumbent, box fold, chevron.",
            "**Fault Types**: Normal (extensional), reverse (compressional), thrust (low-angle reverse), strike-slip (transcurrent).",
            "**Foliation Types**: Slaty cleavage, phyllitic cleavage, schistosity, gneissosity — progressively higher grade.",
            "**Lineation**: Mineral lineation, intersection lineation, boudinage — record direction of tectonic transport.",
            "**Himalayan Structure**: Main Central Thrust (MCT), Main Boundary Thrust (MBT), Main Frontal Thrust (MFT) — piggyback thrust sequence.",
        ],
    },
    "Semester 4": {
        "Palaeontology": [
            "**Fossilisation**: Preservation as actual remains, replacement, mould/cast, impression, trace fossils (ichnofossils).",
            "**Index Fossils**: Short-lived, wide-spread organisms used for biostratigraphic correlation — ammonites, graptolites, fusulinids.",
            "**Cambrian Fauna**: Trilobites, brachiopods, archaeocyathids — Cambrian Explosion = rapid diversification.",
            "**Gondwana Fossils (India)**: Glossopteris (seed fern), Gangamopteris — prove India was part of Gondwana.",
            "**Cephalopods**: Ammonites (coiled) and belemnites — excellent zone fossils for Mesozoic stratigraphy.",
            "**Mass Extinctions**: End-Ordovician, Late Devonian, End-Permian (worst — 96% marine), End-Triassic, End-Cretaceous (K-Pg).",
        ],
        "Stratigraphy": [
            "**Principles**: Superposition, Original Horizontality, Lateral Continuity, Cross-cutting Relationships, Faunal Succession.",
            "**Indian Stratigraphy**: Archaean (Dharwar, Singhbhum) → Proterozoic (Vindhyan, Aravalli) → Gondwana → Deccan Traps → Quaternary.",
            "**Vindhyan Supergroup**: Unmetamorphosed sediments 1.7–0.6 Ga. Sandstone (Red Fort), limestone, shale. In MP, Rajasthan, UP.",
            "**Gondwana Supergroup**: Permian–Jurassic continental sediments with coal. Key coal-bearing unit of India.",
            "**Biostratigraphy**: Zonation using fossils. Concurrent range zones, total range zones, assemblage zones.",
            "**Seismic Stratigraphy**: Reflectors on seismic sections represent stratal surfaces — key tool in basin analysis.",
        ],
    },
    "Semester 5": {
        "Economic Geology": [
            "**Ore Deposits**: Magmatic (chromite in dunite), hydrothermal (gold, copper), sedimentary (BIF iron), residual (bauxite), placer (gold).",
            "**Indian Iron Ore**: BIF (Banded Iron Formation) in Odisha–Jharkhand–Karnataka — Precambrian. India = World's #4 iron ore producer.",
            "**Kolar Gold Field (KGF)**: Archaean greenstone belt, Karnataka. ~3.8 km deep mines. Produced >900 tonnes gold. Closed 2001.",
            "**Hindustan Zinc (Zawar, Rajasthan)**: World's largest integrated zinc producer. Proterozoic MVT-type deposit.",
            "**GSI**: Geological Survey of India (est. 1851) — responsible for geological mapping, mineral exploration, seismic monitoring.",
            "**Resource Classification**: Proved, Probable, Possible (for mining); McKelvey box — reserves vs resources.",
        ],
        "Hydrogeology": [
            "**Aquifer Types**: Confined (artesian), unconfined (water table), leaky, perched.",
            "**Darcy's Law**: Q = KiA where K = hydraulic conductivity, i = hydraulic gradient, A = area.",
            "**Indian Groundwater**: Hard rock aquifers (fractured gneiss, basalt) in Peninsular India; alluvial aquifers in plains.",
            "**Groundwater Crisis**: India extracts 25% of world's groundwater. North India plains depleting rapidly (GRACE satellite data).",
            "**Geothermal**: India has geothermal provinces — Puga (J&K), Tattapani (CG), Manikaran (HP). Low-enthalpy mostly.",
        ],
    },
    "Semester 6": {
        "Remote Sensing & GIS": [
            "**Electromagnetic Spectrum**: Visible (0.4–0.7 μm), Near-IR, SWIR, TIR, Microwave — different geological applications.",
            "**Satellites used in India**: Landsat (30m), Sentinel-2 (10m), Resourcesat (5.8m), Cartosat (0.25m), MODIS (250m).",
            "**Band Combinations**: 4-3-2 (RGB) = true colour; 7-4-2 = geology/minerals; 5-4-3 = vegetation; 12-11-4 = SWIR for minerals.",
            "**GIS Layers**: Topography (DEM), geology, soil, drainage, vegetation, land use — stacked for analysis.",
            "**DGPS**: Differential GPS for precise field coordinates. Essential for geotagging samples and mapping outcrops.",
            "**Google Earth Engine**: Cloud-based satellite analysis. Python/JS API. NDVI, change detection, time series — free for researchers.",
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
}

DIARY_ENTRIES = [
    {"date":"Day 1 — The Beginning","text":"First day at BHU Geology. The department corridors smelled of minerals and old maps. Picked up a piece of basalt from the lab counter and thought — this rock type covers 500,000 km² of India. The Deccan Traps. Everything starts to feel connected."},
    {"date":"Day 47 — Field Practical","text":"Vindhyan sandstone in the afternoon sun. Ran fingers along cross-bedding that formed 600 million years ago. Time stops making human sense out here. The professor said: 'You're not looking at rock. You're reading a letter from the Proterozoic.'"},
    {"date":"Day 89 — The Thin Section","text":"First polarising microscope session. Quartz glowing blue, feldspar in grey, biotite exploding in amber under crossed polars. A whole world in a 0.03mm slice. Started to understand why geologists obsess over microscopes."},
    {"date":"Day 156 — Exam Season","text":"Structural geology diagrams at 2am. Folds, faults, foliations. The Himalayan orogeny plays on repeat in the mind. India crashing into Eurasia at 5 cm/yr — too slow to feel, too powerful to stop. Still going."},
    {"date":"Day 203 — Monsoon Lab","text":"Rain outside, thin sections inside. Someone found pyrite in a Vindhyan sample and the whole lab leaned in. Fool's Gold — but only a fool would dismiss it. Tells you about oxygen levels, fluid pathways, deep-time chemistry."},
]

# ═══════════════════════════════════════════════════════
#  LOADING ANIMATION (first visit only)
# ═══════════════════════════════════════════════════════
if not st.session_state.loading_done:
    ph = st.empty()
    with ph.container():
        st.markdown("""
        <div style='text-align:center;padding:100px 20px;background:linear-gradient(160deg,#070b18,#0c1428);min-height:100vh;'>
            <div style='font-family:Playfair Display,Georgia,serif;font-size:3rem;font-weight:900;
                background:linear-gradient(90deg,#c9a84c,#f0d878,#c9a84c);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                background-clip:text;letter-spacing:4px;margin-bottom:16px;'>
                GeoSphere India
            </div>
            <div style='color:#4a4230;font-size:0.82rem;letter-spacing:4px;margin-bottom:36px;
                font-family:Source Sans 3,sans-serif;font-style:italic;'>
                EARTH SCIENCE INTELLIGENCE PLATFORM
            </div>
            <div style='color:#2a2416;font-size:0.76rem;letter-spacing:2px;line-height:2.8;font-family:Source Sans 3,sans-serif;'>
                Initializing GeoSphere Core...<br>
                Loading Geological Database...<br>
                Calibrating Tectonic Systems...<br>
                Restoring Memory Cache...<br>
                <span style='color:#c9a84c;'>Ready.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(1.5)
    ph.empty()
    st.session_state.loading_done = True

# ═══════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════
with st.sidebar:
    # Logo with click counter (hidden easter egg mechanism)
    st.markdown("""
    <div style='text-align:center;padding:18px 0 10px;'>
        <div style='font-family:Playfair Display,Georgia,serif;font-size:1.4rem;font-weight:900;
            background:linear-gradient(90deg,#c9a84c,#f0d878);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            background-clip:text;letter-spacing:2px;'>
            🌍 GeoSphere
        </div>
        <div style='font-size:0.6rem;color:#4a4230;letter-spacing:3px;margin-top:4px;
            font-family:Source Sans 3,sans-serif;'>
            INDIA · EARTH SCIENCE
        </div>
        <hr style='border-color:rgba(201,168,76,0.2);margin:14px 0 10px;'>
    </div>
    """, unsafe_allow_html=True)

    # ── Easter egg logo click area ──
    # Shows click count as tiny dots so user knows it's working
    clicks = st.session_state.logo_clicks
    dot_display = "·" * min(clicks, 25)
    click_hint  = ""
    if   clicks == 0:  click_hint = "· · ·"
    elif clicks < 8:   click_hint = dot_display
    elif clicks < 14:  click_hint = "▸ SYSTEM ONLINE"
    elif clicks < 20:  click_hint = "▸ Still clicking?"
    else:              click_hint = "▸ Hadd ho."

    st.markdown(f"""
    <div style='text-align:center;margin-bottom:6px;'>
        <div style='font-size:0.58rem;color:#2a2416;letter-spacing:2px;min-height:12px;'>{click_hint}</div>
    </div>""", unsafe_allow_html=True)

    col_logo, col_gap = st.columns([1, 3])
    with col_logo:
        if st.button("🌍", key="logo_click", help="Click me..."):
            st.session_state.logo_clicks += 1
            st.rerun()

    if st.session_state.logo_clicks >= 8:
        st.markdown("""
        <div style='background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.2);
            border-radius:10px;padding:10px;margin-bottom:8px;'>
            <div style='color:#4a4230;font-size:0.6rem;letter-spacing:2px;'>SYSTEM</div>
            <div style='color:#c9a84c;font-family:Source Sans 3,sans-serif;font-size:0.72rem;margin-top:5px;line-height:2;'>
                Alias : COMPUTER<br>Status : Online<br>Build : Stable
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.session_state.logo_clicks >= 20:
            st.markdown("""
            <div style='color:#3a3020;font-size:0.75rem;text-align:center;
                padding:6px;font-style:italic;font-family:Source Sans 3,sans-serif;'>...Hadd ho.</div>""",
                unsafe_allow_html=True)
        elif st.session_state.logo_clicks >= 14:
            st.markdown("""
            <div style='color:#3a3020;font-size:0.75rem;text-align:center;
                padding:6px;font-family:Source Sans 3,sans-serif;'>...Still?</div>""",
                unsafe_allow_html=True)

    # 8 sidebar pages — Mission Control first so globe is default
    SIDEBAR_PAGES = [
        "🌌 Mission Control",
        "🗺️ Geological Map",
        "🌋 Plate Tectonics",
        "💎 Mineral Explorer",
        "🌍 Earthquake Dashboard",
        "📅 Geological Time Scale",
        "🧪 Soil Explorer",
        "🪙 Economic Geology",
    ]

    st.markdown("""
    <div style='font-size:0.68rem;color:#8a7d65;letter-spacing:2px;
        text-transform:uppercase;padding:4px 0 8px 4px;font-family:Source Sans 3,sans-serif;'>
        Navigate
    </div>""", unsafe_allow_html=True)

    page = st.radio("", SIDEBAR_PAGES, label_visibility="collapsed")

    # Session state for sub-page from Mission Control radial dial
    if "sub_page" not in st.session_state:
        st.session_state.sub_page = None

    # Seismic radial dial
    sv = random.randint(18, 92)
    r, circ = 52, 2 * math.pi * 52
    dash = circ * sv / 100
    st.markdown("""<hr style='border-color:rgba(201,168,76,0.12);margin:14px 0;'>""", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align:center;padding:6px 0;'>
        <div style='font-size:0.58rem;color:#8a7d65;letter-spacing:2px;margin-bottom:8px;
            font-family:Source Sans 3,sans-serif;'>SEISMIC INDEX</div>
        <div class='dial-wrap'>
            <svg viewBox='0 0 130 130'>
                <circle cx='65' cy='65' r='{r}' fill='none' stroke='rgba(201,168,76,0.08)' stroke-width='8'/>
                <circle cx='65' cy='65' r='{r}' fill='none' stroke='#c9a84c' stroke-width='8'
                    stroke-dasharray='{dash:.1f} {circ:.1f}'
                    stroke-dashoffset='{circ/4:.1f}' stroke-linecap='round'/>
            </svg>
            <div class='dial-center'>
                <div class='dial-val'>{sv}</div>
                <div class='dial-lbl'>/ 100</div>
            </div>
        </div>
    </div>
    <div style='text-align:center;margin:6px 0 12px;'>
        <span class='float-badge'>🌋 Live</span>
        <span class='float-badge'>🛰️ v2.0</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size:0.6rem;color:#2a2416;text-align:center;padding:6px 0;line-height:2;
        font-family:Source Sans 3,sans-serif;'>
        GeoSphere v08.09.08.11<br>
        <span style='color:#c9a84c;opacity:0.5;'>Made for Earth Science</span><br>
        <span style='color:#1e1a12;'>Lat: 25.2677°N · Lon: 82.9913°E</span><br>
        <span style='color:#1e1a12;'>Dedicated to Curiosity.</span>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
#  ACHIEVEMENT MODE — auto reset after 20s
# ═══════════════════════════════════════════════════════
if st.session_state.rare_mode:
    elapsed = time.time() - st.session_state.rare_timer
    if elapsed > 20:
        st.session_state.rare_mode  = False
        st.session_state.rare_timer = 0
        st.rerun()

# ═══════════════════════════════════════════════════════
#  AUDIO — plays when achievement mode active
# ═══════════════════════════════════════════════════════
import os, base64

def play_audio():
    audio_path = os.path.join(os.path.dirname(__file__), "audio.mp3")
    if os.path.exists(audio_path):
        with open(audio_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <audio id="rare-audio" autoplay loop style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
            var a = document.getElementById('rare-audio');
            if(a){{ a.volume = 0.45; a.play().catch(()=>{{}}); }}
        </script>""", unsafe_allow_html=True)

if st.session_state.rare_mode:
    play_audio()

# ═══════════════════════════════════════════════════════
#  HERO BANNER
# ═══════════════════════════════════════════════════════
st.markdown("<div class='shimmer-bar'></div>", unsafe_allow_html=True)

page_label = page.split(" ", 1)[1] if " " in page else page
rare_quote = RARE_LINES.get(page_label, "")

if st.session_state.rare_mode:
    # ── Achievement mode hero ──
    st.markdown(f"""
    <div class='hero-banner' style='border-color:rgba(58,123,213,0.45);
        background:linear-gradient(135deg,rgba(0,15,50,0.95),rgba(0,8,35,0.98));'>
        <p class='hero-title' style='
            background:linear-gradient(90deg,#3a7bd5,#6ea8fe,#a8c8ff);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            background-clip:text;font-size:2.4rem;font-family:Playfair Display,Georgia,serif;
            letter-spacing:3px;font-style:italic;'>
            The Story Between The Lines
        </p>
        <p class='rare-text' style='font-size:1.05rem;'>"{rare_quote}"</p>
        <span class='hero-badge' style='border-color:rgba(58,123,213,0.5);color:#6ea8fe;
            background:rgba(58,123,213,0.1);'>
            ✨ RARE EVENT · {datetime.datetime.now().strftime("%d %b %Y")} ✨
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Final quote card
    st.markdown("""
    <div style='
        background:linear-gradient(135deg,rgba(0,12,40,0.95),rgba(0,5,25,0.98));
        border:1px solid rgba(58,123,213,0.3);border-radius:16px;
        padding:32px 36px;text-align:center;margin:0 auto 20px;max-width:640px;
        box-shadow:0 0 40px rgba(58,123,213,0.12);'>
        <div style='font-family:Playfair Display,Georgia,serif;font-size:1.15rem;
            color:#a8c8ff;font-style:italic;line-height:2;letter-spacing:0.3px;'>
            "Some stories never ask to be remembered.<br>
            Yet somehow&hellip; they always are."
        </div>
        <div style='color:#1a2a4a;font-size:0.68rem;margin-top:16px;letter-spacing:2px;'>
            — Achievement Unlocked · The Surprise Was Worth It
        </div>
    </div>""", unsafe_allow_html=True)

elif IS_BIRTHDAY:
    st.markdown(f"""
    <div class='hero-banner'>
        <p class='hero-title'>A Rare Sky</p>
        <p class='hero-sub'>FOR A RARE DAY · EARTH SCIENCE · EXPLORATION</p>
        <span class='hero-badge'>BHU EARTH SCIENCE · {datetime.datetime.now().strftime("%d %b %Y")}</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class='hero-banner'>
        <p class='hero-title'>GeoSphere India</p>
        <p class='hero-sub'>EARTH SCIENCE INTELLIGENCE PLATFORM · BHU · v2.0</p>
        <span class='hero-badge'>BHU EARTH SCIENCE · {datetime.datetime.now().strftime("%d %b %Y")}</span>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE ROUTING — sidebar pages + sub_page from radial dial
# ═══════════════════════════════════════════════════════════════
# Sub-page overrides sidebar selection when set from radial dial
effective_page = st.session_state.get("sub_page") or page

# ═══════════════════════════════════════════════════════════════
#  PAGE: MISSION CONTROL  (default / home)
# ═══════════════════════════════════════════════════════════════
if effective_page not in [
    "🗺️ Geological Map","🌋 Plate Tectonics","💎 Mineral Explorer",
    "🌍 Earthquake Dashboard","📅 Geological Time Scale","🧪 Soil Explorer",
    "🪙 Economic Geology","🪨 Rock Explorer","🌋 Volcano Explorer",
    "🧭 Structural Tools","🌿 Geography Explorer","🌊 Watershed Explorer",
    "🌊 Oceanography","🔬 Thin Section Gallery","📚 Semester Notes",
    "🧠 Geo Quiz","🃏 Flashcards","🤖 AI Assistant","📓 Human Diary",
    "🥚 About & Archive"
] or effective_page == "🌌 Mission Control":
    # Clear sub_page so sidebar works normally after
    if st.session_state.get("sub_page") == "🌌 Mission Control":
        st.session_state.sub_page = None

    st.markdown("<div class='section-heading'>Mission Control — Earth at a Glance</div>", unsafe_allow_html=True)

    # ── Rotating 3D Earth globe ──
    st.markdown("<div class='section-heading'>Rotating Earth — Tectonic Plates</div>", unsafe_allow_html=True)
    plate_centers = {
        "Pacific":(-10,-170),"North American":(50,-100),"South American":(-15,-60),
        "Eurasian":(50,60),"African":(5,25),"Australian":(-25,130),
        "Antarctic":(-75,0),"Indian":(20,75),"Arabian":(25,45),
        "Caribbean":(15,-75),"Nazca":(-15,-85),"Philippine":(15,130),
    }
    lats_g = [v[0] for v in plate_centers.values()]
    lons_g = [v[1] for v in plate_centers.values()]
    names_g = list(plate_centers.keys())
    fig_globe = go.Figure()
    fig_globe.add_trace(go.Scattergeo(
        lat=lats_g, lon=lons_g, text=names_g,
        mode="markers+text", textposition="top center",
        marker=dict(size=10, color="#c9a84c",
                    line=dict(width=1.5, color="rgba(240,216,120,0.6)")),
        textfont=dict(color="#f0e6d0", size=9, family="Source Sans 3"),
        hovertemplate="<b>%{text}</b> Plate<extra></extra>",
        name="Plates"
    ))
    fig_globe.add_trace(go.Scattergeo(
        lat=[20.5937], lon=[78.9629], text=["India"],
        mode="markers+text",
        marker=dict(size=14, color="#e8c96a", symbol="star"),
        textfont=dict(color="#e8c96a", size=12, family="Playfair Display"),
        hovertemplate="<b>India</b> — Indian Plate — Moving NNE ~5 cm/yr<extra></extra>",
        name="India"
    ))
    fig_globe.update_geos(
        projection_type="orthographic",
        showland=True,  landcolor="#1a2a18",
        showocean=True, oceancolor="#070b18",
        showlakes=True, lakecolor="#0c1428",
        showcountries=True, countrycolor="rgba(201,168,76,0.15)",
        showcoastlines=True, coastlinecolor="rgba(201,168,76,0.4)",
        bgcolor="rgba(0,0,0,0)", showframe=False,
        projection_rotation=dict(lon=78, lat=20, roll=0),
    )
    fig_globe.update_layout(
        height=460, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0"),
        margin=dict(l=0,r=0,t=0,b=0), showlegend=False,
        updatemenus=[dict(
            type="buttons", showactive=False,
            buttons=[dict(
                label="▶ Rotate",
                method="animate",
                args=[None, dict(frame=dict(duration=80,redraw=True),fromcurrent=True,loop=True)]
            )],
            x=0.05, y=0.05, bgcolor="rgba(201,168,76,0.15)",
            font=dict(color="#c9a84c", size=11),
            bordercolor="rgba(201,168,76,0.3)", borderwidth=1,
        )]
    )
    # Add animation frames for rotation
    frames = []
    for lon_r in range(0, 360, 4):
        frames.append(go.Frame(
            layout=dict(geo=dict(projection_rotation=dict(lon=lon_r, lat=20, roll=0)))
        ))
    fig_globe.frames = frames
    st.plotly_chart(fig_globe, use_container_width=True)

    # ── Radial dial menu for remaining pages ──
    st.markdown("<div class='section-heading'>Explore — All Sections</div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='color:#8a7d65;font-size:0.85rem;margin-bottom:16px;font-family:Source Sans 3,sans-serif;'>
    Click any section below to open it directly from Mission Control.
    </div>""", unsafe_allow_html=True)

    EXTRA_PAGES = [
        ("🪨","Rock Explorer"),
        ("🌋","Volcano Explorer"),
        ("🧭","Structural Tools"),
        ("🌿","Geography Explorer"),
        ("🌊","Watershed Explorer"),
        ("🌊","Oceanography"),
        ("🔬","Thin Section Gallery"),
        ("📚","Semester Notes"),
        ("🧠","Geo Quiz"),
        ("🃏","Flashcards"),
        ("🤖","AI Assistant"),
        ("📓","Human Diary"),
        ("🥚","About & Archive"),
    ]
    dial_cols = st.columns(4)
    for i, (em, name) in enumerate(EXTRA_PAGES):
        with dial_cols[i % 4]:
            if st.button(f"{em} {name}", key=f"dial_{i}", use_container_width=True):
                st.session_state.sub_page = f"{em} {name}"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    metrics = [
        ("🌍","6,371 km","Earth Radius","Mean"),
        ("🏔️","8,849 m","Everest","World's highest"),
        ("🌊","11,034 m","Mariana Trench","Ocean floor"),
        ("⛰️","4.56 Ga","Earth Age","Billion years"),
        ("🌡️","5,500°C","Inner Core","Estimated temp"),
        ("🔢","15","Major Plates","Tectonic"),
        ("🌋","1,350+","Active Volcanoes","On Earth"),
        ("🇮🇳","3.287M km²","India Area","7th largest"),
    ]
    cols = st.columns(4)
    for i, (ico, val, lbl, sub) in enumerate(metrics):
        with cols[i % 4]:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-icon'>{ico}</div>
                <div class='metric-value'>{val}</div>
                <div class='metric-label'>{lbl}</div>
                <div class='metric-delta'>{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("<div class='section-heading'>EARTH'S INTERIOR STRUCTURE</div>", unsafe_allow_html=True)
        layers     = ["Inner Core","Outer Core","Lower Mantle","Upper Mantle","Crust"]
        thick      = [1221, 2259, 2200, 640, 30]
        col_e      = ["#ff4444","#ff8800","#cc6600","#886622","#336633"]
        temps      = ["~5,500°C","~4,000–5,000°C","~1,000–3,700°C","~500–900°C","~0–200°C"]
        fig_e = go.Figure()
        for lay, th, cl, te in zip(layers, thick, col_e, temps):
            fig_e.add_trace(go.Bar(name=lay, x=[th], y=["Interior"], orientation="h",
                marker_color=cl, hovertemplate=f"<b>{lay}</b><br>Thickness: {th} km<br>Temp: {te}<extra></extra>"))
        fig_e.update_layout(barmode="stack", height=150,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0e6d0", family="Source Sans 3"),
            legend=dict(orientation="h", y=-1.1, font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=5, r=5, t=5, b=90),
            xaxis=dict(title="Depth (km)", gridcolor="rgba(255,255,255,0.05)", color="#8a7d65"),
            yaxis=dict(visible=False))
        st.plotly_chart(fig_e, use_container_width=True)

        st.markdown("<div class='section-heading'>INDIA TECTONIC HIGHLIGHTS — click any card to expand</div>", unsafe_allow_html=True)
        facts_detail = [
            ("🏔️","Himalayas",
             "India–Eurasia collision ~50 Ma. Still rising 5mm/yr.",
             "Age","~50 Ma to present (Cenozoic)",
             "Rock Types","Sedimentary (Tethys shelf), Metamorphic (MCT zone), Granitic intrusions",
             "Key Structures","Main Central Thrust (MCT), Main Boundary Thrust (MBT), Main Frontal Thrust (MFT)",
             "Minerals","Gold placers, copper, lead-zinc, tourmaline, beryl in pegmatites",
             "Did you know?","The crustal root under the Himalayas is ~100 km thick — like an iceberg, most of the mountain is underground."),
            ("🌋","Deccan Traps",
             "500,000 km² flood basalt erupted 66 Ma, linked to K-Pg extinction.",
             "Age","66–60 Ma (Late Cretaceous to Early Paleogene)",
             "Rock Types","Tholeiitic basalt — individual lava flows 10–50 m thick, stacked up to 2 km",
             "Key Structures","Dyke swarms, sills, columnar jointing, vesicles filled with zeolites & amethyst",
             "Minerals","Zeolites, amethyst (geode capital: Pune region), calcite, iron ore",
             "Did you know?","Ajanta and Ellora caves are carved entirely into Deccan basalt. The Lonar crater (Maharashtra) was created by a meteorite impact into Deccan Traps."),
            ("🪨","Indian Shield",
             "Precambrian craton — some rocks 3.3 Ga old. India's stable geological core.",
             "Age","3.3 Ga (Archaean) to 600 Ma (Late Proterozoic)",
             "Rock Types","Gneiss, greenstone belts, granites, schists — Dharwar & Singhbhum cratons",
             "Key Structures","Greenstone belts (BIF iron ore), shear zones, charnockite massifs",
             "Minerals","Iron ore (BIF), gold (Kolar), manganese, chromite, copper",
             "Did you know?","The Dharwar craton contains some of India's oldest exposed rocks (~3.3 Ga) near the Karnataka–Andhra Pradesh border. Jack Hills, Australia has older zircons (4.4 Ga) but no exposed rock that old."),
            ("💎","Eastern Ghats",
             "High-grade granulite belt — charnockites, khondalites. Rich in industrial minerals.",
             "Age","Proterozoic (1.6–0.5 Ga)",
             "Rock Types","Charnockite, khondalite, leptynite, quartzofeldspathic gneiss — granulite facies",
             "Key Structures","Banded gneisses, migmatites, shear zones parallel to coast",
             "Minerals","Graphite, corundum, chromite, bauxite, sillimanite, garnet",
             "Did you know?","Charnockite is unique to India — named after Job Charnock's tombstone in Chennai (St. Thomas Mount). It's the deepest crustal rock exposed at the surface anywhere."),
            ("🌊","Andaman Arc",
             "Active subduction zone. Barren Island volcano. 2004 M9.1 tsunami epicentre.",
             "Age","Cenozoic (50 Ma to present)",
             "Rock Types","Ophiolite (peridotite, gabbro, basalt), volcanic arc andesites, flysch sediments",
             "Key Structures","Trench, forearc basin, volcanic arc, backarc basin — classic subduction geometry",
             "Minerals","Chromite in ophiolite, manganese nodules on seafloor",
             "Did you know?","The 2004 Indian Ocean tsunami (M9.1) ruptured ~1,300 km of the Andaman-Sumatra subduction zone. The seafloor moved up to 15 m horizontally and 5 m vertically in minutes."),
            ("🔥","Koyna Seismic Zone",
             "Reservoir-triggered seismicity (RTS). India's deadliest intraplate quake M6.5 in 1967.",
             "Age","Active — post-dam construction (1962 onward)",
             "Rock Types","Deccan basalt (hard, brittle) — stress concentrates along pre-existing fault lines",
             "Key Structures","NE-trending faults reactivated by water load of Koyna reservoir",
             "Minerals","Not applicable — significance is seismic hazard, not mineral resources",
             "Did you know?","Before Koyna (1967), scientists didn't think filling a reservoir could trigger a large earthquake. It changed seismic hazard assessment worldwide — now all large dams are monitored for RTS."),
        ]

        if "selected_fact" not in st.session_state:
            st.session_state.selected_fact = None

        fc_cols = st.columns(3)
        for i, fd in enumerate(facts_detail):
            em, nm, short = fd[0], fd[1], fd[2]
            with fc_cols[i % 3]:
                is_selected = st.session_state.selected_fact == nm
                border_col  = "#00d4ff" if is_selected else "rgba(0,212,255,0.18)"
                bg_col      = "rgba(0,212,255,0.08)" if is_selected else "rgba(15,30,60,0.75)"
                st.markdown(f"""
                <div style='background:{bg_col};border:1px solid {border_col};border-radius:14px;
                    padding:12px 14px;margin-bottom:8px;cursor:pointer;transition:all 0.2s;'>
                    <div style='font-size:1.3rem;margin-bottom:5px;'>{em}</div>
                    <div style='color:#00d4ff;font-weight:600;font-size:0.82rem;margin-bottom:3px;'>{nm}</div>
                    <div style='color:#94a3b8;font-size:0.74rem;line-height:1.5;'>{short}</div>
                    <div style='color:#00d4ff;font-size:0.65rem;margin-top:6px;letter-spacing:1px;'>
                    {"▼ EXPANDED" if is_selected else "▶ CLICK TO EXPAND"}
                    </div>
                </div>""", unsafe_allow_html=True)
                if st.button(f"{'▼' if is_selected else '▶'} {nm}", key=f"fact_btn_{i}"):
                    st.session_state.selected_fact = None if is_selected else nm
                    st.rerun()

        # Detail panel
        if st.session_state.selected_fact:
            fd = next(f for f in facts_detail if f[1] == st.session_state.selected_fact)
            em         = fd[0]
            nm         = fd[1]
            age_lbl    = fd[3]
            age_val    = fd[4]
            rock_lbl   = fd[5]
            rock_val   = fd[6]
            struct_lbl = fd[7]
            struct_val = fd[8]
            min_lbl    = fd[9]
            min_val    = fd[10]
            did_lbl    = fd[11]
            did_val    = fd[12]
            st.markdown(f"""
            <div class='glass-card' style='border-color:rgba(0,212,255,0.35);margin-top:4px;'>
                <div style='display:flex;align-items:center;gap:10px;margin-bottom:14px;'>
                    <span style='font-size:2rem;'>{em}</span>
                    <span style='color:#00d4ff;font-family:Orbitron,sans-serif;font-size:0.95rem;'>{nm}</span>
                </div>
                <div style='display:grid;grid-template-columns:1fr 1fr;gap:14px;'>
                    <div style='color:#94a3b8;font-size:0.78rem;line-height:2;'>
                    🕐 <b style='color:#e2e8f0;'>{age_lbl}:</b> {age_val}<br>
                    🪨 <b style='color:#e2e8f0;'>{rock_lbl}:</b> {rock_val}<br>
                    🔩 <b style='color:#e2e8f0;'>{struct_lbl}:</b> {struct_val}
                    </div>
                    <div style='color:#94a3b8;font-size:0.78rem;line-height:2;'>
                    💎 <b style='color:#e2e8f0;'>{min_lbl}:</b> {min_val}<br>
                    <br>
                    <b style='color:#f59e0b;'>💡 {did_lbl}:</b><br>
                    <span style='font-style:italic;line-height:1.6;'>{did_val}</span>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='section-heading'>MINERAL RESERVES</div>", unsafe_allow_html=True)
        m_in = {"Iron Ore":28,"Coal":22,"Bauxite":12,"Limestone":11,"Copper":9,"Manganese":8,"Zinc-Lead":6,"Others":4}
        fig_p = go.Figure(go.Pie(labels=list(m_in.keys()), values=list(m_in.values()), hole=0.42,
            marker=dict(colors=["#ef4444","#374151","#92400e","#e5e7eb","#f97316","#7c3aed","#6b7280","#10b981"])))
        fig_p.update_traces(textfont_color="#f0e6d0",
            hovertemplate="<b>%{label}</b><br>Share: %{percent}<extra></extra>")
        fig_p.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#f0e6d0", family="Source Sans 3"),
            legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=5,r=5,t=5,b=5), height=270,
            annotations=[dict(text="India", x=0.5, y=0.5, showarrow=False,
                font=dict(color="#8a7d65", size=11))])
        st.plotly_chart(fig_p, use_container_width=True)

        st.markdown("<div class='section-heading'>SEISMIC ZONES</div>", unsafe_allow_html=True)
        sz = {"Zone II\n(Low)":10,"Zone III\n(Moderate)":30,"Zone IV\n(High)":25,"Zone V\n(Very High)":35}
        fig_sz = go.Figure(go.Bar(x=list(sz.keys()), y=list(sz.values()),
            marker_color=["#10b981","#f59e0b","#f87171","#dc2626"],
            text=[f"{v}%" for v in sz.values()], textposition="outside", textfont_color="#f0e6d0"))
        fig_sz.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8a7d65", family="Source Sans 3"), height=230,
            margin=dict(l=5,r=5,t=5,b=5),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            xaxis=dict(tickfont=dict(size=9)))
        st.plotly_chart(fig_sz, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: GEOLOGICAL MAP
# ═══════════════════════════════════════════════════════════════
elif "Geological Map" in effective_page:
    st.markdown("<div class='section-heading'>INTERACTIVE GEOLOGICAL MAP OF INDIA</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='glass-card' style='padding:12px 16px;margin-bottom:12px;'>
        <span style='color:#94a3b8;font-size:0.8rem;'>
        🗺️ Click any geological province marker to see details below · Hover for quick info
        </span>
    </div>""", unsafe_allow_html=True)

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
        scope="asia",
        lonaxis_range=[68, 98], lataxis_range=[6, 38],
        showland=True,   landcolor="#0f1e0f",
        showocean=True,  oceancolor="#020817",
        showlakes=True,  lakecolor="#0a1628",
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
    c1, c2 = st.columns(2)
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

# ═══════════════════════════════════════════════════════════════
#  PAGE: PLATE TECTONICS SIMULATOR
# ═══════════════════════════════════════════════════════════════
elif "Plate Tectonics" in effective_page:
    st.markdown("<div class='section-heading'>PLATE TECTONICS SIMULATOR — INDIA'S TECTONIC JOURNEY</div>", unsafe_allow_html=True)

    ma = st.slider("⏱️ Time (Million Years Ago → Present)", min_value=0, max_value=100, value=50, step=5,
                   format="%d Ma")

    # Interpolate India plate position
    india_lat_start = -10  # 100 Ma — southern hemisphere
    india_lat_end   =  20  # 0 Ma — present
    india_lat = india_lat_start + (india_lat_end - india_lat_start) * (1 - ma / 100)

    eurasia_lat = 45

    stage = "Moving northward through the Tethys Ocean"
    if ma <= 10:   stage = "Active collision — Himalayas rising rapidly"
    elif ma <= 50: stage = "Continental collision phase — suture forming"
    elif ma <= 80: stage = "Rapid northward drift — 15–20 cm/yr!"

    fig_tec = go.Figure()
    # Eurasian plate
    fig_tec.add_trace(go.Scattergeo(
        lat=[eurasia_lat, eurasia_lat, eurasia_lat+12, eurasia_lat+12, eurasia_lat],
        lon=[60, 110, 110, 60, 60],
        fill="toself", fillcolor="rgba(245,158,11,0.2)",
        line=dict(color="#f59e0b", width=2), name="Eurasian Plate", mode="lines",
        hoverinfo="name"
    ))
    # Indian plate
    fig_tec.add_trace(go.Scattergeo(
        lat=[india_lat, india_lat, india_lat+16, india_lat+16, india_lat],
        lon=[68, 98, 98, 68, 68],
        fill="toself", fillcolor="rgba(0,212,255,0.2)",
        line=dict(color="#00d4ff", width=2), name="Indian Plate", mode="lines",
        hoverinfo="name"
    ))
    # Movement arrow
    if ma > 0:
        fig_tec.add_trace(go.Scattergeo(
            lat=[india_lat + 8, india_lat + 14],
            lon=[83, 83],
            mode="lines+markers",
            line=dict(color="#10b981", width=3),
            marker=dict(size=[0, 14], symbol=["circle", "arrow-up"], color="#10b981"),
            name="Movement Direction", hoverinfo="skip"
        ))
    # Himalaya label
    if ma <= 50:
        fig_tec.add_trace(go.Scattergeo(
            lat=[32], lon=[78],
            mode="markers+text",
            marker=dict(size=12, color="#f59e0b", symbol="triangle-up"),
            text=["🏔️ Himalayas"], textfont=dict(color="#f59e0b", size=11),
            textposition="top right", name="Himalayas", hoverinfo="skip"
        ))

    fig_tec.update_geos(
        lonaxis_range=[50, 120], lataxis_range=[-20, 65],
        showland=True, landcolor="#1a2a1a",
        showocean=True, oceancolor="#020817",
        showcountries=True, countrycolor="rgba(255,255,255,0.1)",
        showcoastlines=True, coastlinecolor="rgba(0,212,255,0.3)",
        bgcolor="rgba(0,0,0,0)", showframe=False,
    )
    fig_tec.update_layout(
        height=450, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0"),
        margin=dict(l=0,r=0,t=0,b=0),
        legend=dict(bgcolor="rgba(10,22,40,0.8)", font=dict(size=11))
    )
    st.plotly_chart(fig_tec, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-icon'>⏱️</div>
            <div class='metric-value'>{ma} Ma</div>
            <div class='metric-label'>Time</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        drift = round(5 + (ma / 100) * 15, 1)
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-icon'>🚀</div>
            <div class='metric-value'>{drift} cm/yr</div>
            <div class='metric-label'>Drift Speed</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-icon'>🌋</div>
            <div class='metric-value'>{round(india_lat, 1)}°</div>
            <div class='metric-label'>India Latitude</div>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class='glass-card' style='text-align:center;margin-top:8px;'>
        <span style='color:#00d4ff;font-family:Orbitron,sans-serif;font-size:0.75rem;letter-spacing:2px;'>
        TECTONIC STAGE:</span><br>
        <span style='color:#e2e8f0;font-size:0.9rem;margin-top:6px;display:block;'>{stage}</span>
    </div>""", unsafe_allow_html=True)

    # Key events timeline
    st.markdown("<div class='section-heading'>KEY TECTONIC EVENTS</div>", unsafe_allow_html=True)
    events = [
        (180,"Gondwana Breakup","India begins separating from Antarctica/Africa"),
        (130,"India Rift","India + Madagascar separate from main Gondwana"),
        (90,"Rapid Drift","India alone — moves 15–20 cm/yr northward"),
        (66,"Deccan Traps","Hotspot volcanism as India passes over Réunion hotspot"),
        (50,"First Contact","India touches Eurasia — Tethys Sea closes"),
        (40,"Suture Formed","Indus-Tsangpo suture zone — ocean completely closed"),
        (20,"Himalayas Rise","Thrust faults active — mountains rapidly gaining height"),
        (0,"Present","India still moving 5 cm/yr NNE; Himalayas still growing"),
    ]
    ev_df = pd.DataFrame(events, columns=["Ma","Event","Detail"])
    st.dataframe(ev_df.style.set_properties(**{
        "background-color":"rgba(8,18,38,0.85)","color":"#e2e8f0",
        "border":"1px solid rgba(0,212,255,0.1)","font-size":"0.8rem"}),
        use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: ROCK EXPLORER
# ═══════════════════════════════════════════════════════════════
elif "Rock Explorer" in effective_page:
    st.markdown("<div class='section-heading'>ROCK EXPLORER — IGNEOUS · SEDIMENTARY · METAMORPHIC</div>", unsafe_allow_html=True)

    c_map = {"Igneous":"#f87171","Sedimentary":"#fbbf24","Metamorphic":"#a78bfa"}
    tabs  = st.tabs(["🌋 Igneous", "🏜️ Sedimentary", "💫 Metamorphic", "🔍 Search"])

    for tab, rtype in zip(tabs[:3], ["Igneous","Sedimentary","Metamorphic"]):
        with tab:
            cols = st.columns(3)
            for i, r in enumerate(ROCKS[rtype]):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class='mineral-card' style='border-color:{c_map[rtype]}33;'>
                        <div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>
                            <span style='font-size:1.5rem;'>{r["emoji"]}</span>
                            <span class='mineral-name' style='color:{c_map[rtype]};'>{r["name"]}</span>
                        </div>
                        <div style='color:#94a3b8;font-size:0.73rem;line-height:1.5;'>
                        <b style='color:#e2e8f0;'>Texture:</b> {r["texture"]}<br>
                        <b style='color:#e2e8f0;'>Composition:</b> {r["composition"]}<br>
                        <b style='color:#e2e8f0;'>Formation:</b> {r["formation"]}<br>
                        <b style='color:#e2e8f0;'>India:</b> {r["india"]}<br>
                        <b style='color:#e2e8f0;'>Uses:</b> {r["use"]}
                        </div>
                    </div>""", unsafe_allow_html=True)

    with tabs[3]:
        search_r = st.text_input("🔍 Search any rock", placeholder="e.g. Granite, Basalt, Marble...")
        all_rocks = [(rtype, r) for rtype, rs in ROCKS.items() for r in rs]
        if search_r:
            res = [(rt, r) for rt, r in all_rocks if search_r.lower() in r["name"].lower() or
                   search_r.lower() in r["desc"].lower() or search_r.lower() in r["formation"].lower()]
            if not res:
                st.warning("No rocks found. Try different keywords.")
            else:
                for rt, r in res:
                    st.markdown(f"""
                    <div class='glass-card'>
                        <div style='display:flex;justify-content:space-between;align-items:start;'>
                            <div style='font-size:1.5rem;'>{r["emoji"]}</div>
                            <span style='font-size:0.68rem;background:{c_map[rt]}22;padding:2px 8px;
                                border-radius:10px;color:{c_map[rt]};'>{rt}</span>
                        </div>
                        <div style='color:{c_map[rt]};font-family:Orbitron,sans-serif;font-size:0.9rem;margin:6px 0;'>{r["name"]}</div>
                        <div style='color:#94a3b8;font-size:0.8rem;line-height:1.7;'>
                        🔬 <b style='color:#e2e8f0;'>Texture:</b> {r["texture"]}<br>
                        🧱 <b style='color:#e2e8f0;'>Composition:</b> {r["composition"]}<br>
                        🌋 <b style='color:#e2e8f0;'>Formation:</b> {r["formation"]}<br>
                        🇮🇳 <b style='color:#e2e8f0;'>India:</b> {r["india"]}<br>
                        🏗️ <b style='color:#e2e8f0;'>Uses:</b> {r["use"]}
                        </div>
                    </div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#475569;text-align:center;padding:30px;'>Type a rock name to search</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: MINERAL EXPLORER
# ═══════════════════════════════════════════════════════════════
elif "Mineral Explorer" in effective_page:
    st.markdown("<div class='section-heading'>MINERAL EXPLORER — 15 KEY MINERALS</div>", unsafe_allow_html=True)

    search_m = st.text_input("🔍 Search minerals", placeholder="e.g. Quartz, Calcite, Magnetite...")
    filtered = [m for m in MINERALS if not search_m or
                search_m.lower() in m["name"].lower() or
                search_m.lower() in m["desc"].lower() or
                search_m.lower() in m.get("india","").lower()]

    if not filtered:
        st.warning("No minerals found. Try different terms.")
    else:
        cols = st.columns(3)
        for i, m in enumerate(filtered):
            with cols[i % 3]:
                stars = "⬜" * (10 - int(m["hardness"]*10//10)) + "🟦" * int(m["hardness"])
                st.markdown(f"""
                <div class='mineral-card'>
                    <div style='display:flex;align-items:center;gap:10px;margin-bottom:8px;'>
                        <span style='font-size:1.8rem;'>{m["emoji"]}</span>
                        <div>
                            <div class='mineral-name'>{m["name"]}</div>
                            <div class='mineral-formula'>{m["formula"]}</div>
                        </div>
                    </div>
                    <div style='color:#94a3b8;font-size:0.73rem;line-height:1.8;'>
                    ⚡ <b style='color:#e2e8f0;'>Hardness:</b> {m["hardness"]} (Mohs)<br>
                    ✨ <b style='color:#e2e8f0;'>Lustre:</b> {m["luster"]}<br>
                    🔪 <b style='color:#e2e8f0;'>Cleavage:</b> {m["cleavage"]}<br>
                    🔷 <b style='color:#e2e8f0;'>System:</b> {m["system"]}<br>
                    🎨 <b style='color:#e2e8f0;'>Color:</b> {m["color"]}<br>
                    🇮🇳 <b style='color:#e2e8f0;'>India:</b> {m.get("india","—")}<br>
                    🏭 <b style='color:#e2e8f0;'>Uses:</b> {m["use"]}<br>
                    </div>
                    <div class='mineral-desc' style='margin-top:8px;border-top:1px solid rgba(0,212,255,0.1);padding-top:6px;'>{m["desc"]}</div>
                </div>""", unsafe_allow_html=True)

    # Mohs chart
    st.markdown("<div class='section-heading'>MOHS HARDNESS SCALE</div>", unsafe_allow_html=True)
    mohs = {"Talc":1,"Gypsum":2,"Calcite":3,"Fluorite":4,"Apatite":5,
            "Orthoclase":6,"Quartz":7,"Topaz":8,"Corundum":9,"Diamond":10}
    fig_mh = go.Figure(go.Bar(x=list(mohs.keys()), y=list(mohs.values()),
        marker=dict(color=list(mohs.values()), colorscale=[[0,"#00d4ff"],[0.5,"#7c3aed"],[1,"#f59e0b"]],
                    showscale=True, colorbar=dict(tickfont=dict(color="#8a7d65"), title="Hardness")),
        text=list(mohs.values()), textposition="outside", textfont_color="#f0e6d0",
        hovertemplate="<b>%{x}</b><br>Hardness: %{y}<extra></extra>"))
    fig_mh.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a7d65", family="Source Sans 3"), height=280,
        margin=dict(l=5,r=60,t=5,b=5),
        xaxis=dict(color="#8a7d65"), yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
    st.plotly_chart(fig_mh, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: EARTHQUAKE DASHBOARD
# ═══════════════════════════════════════════════════════════════
elif "Earthquake" in effective_page:
    st.markdown("<div class='section-heading'>EARTHQUAKE DASHBOARD — INDIA SEISMIC HISTORY + LIVE USGS</div>", unsafe_allow_html=True)

    # Try live USGS data
    live_data = None
    try:
        resp = requests.get(
            "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2025-01-01&minmagnitude=5.0&orderby=time&limit=20",
            timeout=5)
        if resp.status_code == 200:
            live_data = resp.json()
    except Exception:
        pass

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
            <span style='color:#10b981;font-size:0.75rem;'>🟢 LIVE — USGS data (M5.0+ globally, 2025)</span>
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
        st.dataframe(eq_df[["Place","Magnitude","Depth (km)","Time"]].head(10).style.set_properties(**{
            "background-color":"rgba(8,18,38,0.85)","color":"#e2e8f0","font-size":"0.78rem"}),
            use_container_width=True, hide_index=True)
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

# ═══════════════════════════════════════════════════════════════
#  PAGE: VOLCANO EXPLORER
# ═══════════════════════════════════════════════════════════════
elif "Volcano" in effective_page:
    st.markdown("<div class='section-heading'>VOLCANO EXPLORER — BARREN ISLAND · NARCONDAM · GLOBAL</div>", unsafe_allow_html=True)

    fig_v = go.Figure()
    for v in VOLCANOES:
        color = "#dc2626" if v["status"] == "Active" else "#f59e0b"
        size  = 16 if v["country"] == "India" else 10
        fig_v.add_trace(go.Scattergeo(
            lat=[v["lat"]], lon=[v["lon"]],
            mode="markers+text", text=[v["name"]],
            textposition="top center",
            marker=dict(size=size, color=color, symbol="triangle-up",
                        line=dict(width=2, color="rgba(255,255,255,0.5)")),
            textfont=dict(color="#f0e6d0", size=10 if v["country"]=="India" else 8),
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
elif "Time Scale" in effective_page:
    st.markdown("<div class='section-heading'>GEOLOGICAL TIME SCALE — 4.6 BILLION YEARS</div>", unsafe_allow_html=True)

    fig_ts = go.Figure()
    for i, period in enumerate(GEOLOGIC_TIME):
        end   = GEOLOGIC_TIME[i-1]["start"] if i > 0 else 0
        start = period["start"]
        width = start - end
        fig_ts.add_trace(go.Bar(
            name=period["period"] if period["period"] != "—" else period["era"],
            x=[width], y=[f'{period["era"] if period["era"]!="—" else period["eon"]}'],
            orientation="h",
            marker_color=period["color"],
            hovertemplate=f"<b>{period['period']}</b><br>{period['eon']} Eon · {period['era']} Era<br>"
                          f"Start: {period['start']} Ma<br>Life: {period['life']}<extra></extra>",
        ))

    fig_ts.update_layout(
        barmode="stack", height=350,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0", family="Source Sans 3"),
        legend=dict(orientation="h", y=-0.5, font=dict(size=8), bgcolor="rgba(0,0,0,0)", ncols=5),
        margin=dict(l=10,r=10,t=10,b=120),
        xaxis=dict(title="Millions of Years Ago", gridcolor="rgba(255,255,255,0.05)", color="#8a7d65",
                   autorange="reversed"),
        yaxis=dict(color="#8a7d65"),
    )
    st.plotly_chart(fig_ts, use_container_width=True)

    # Detail table
    st.markdown("<div class='section-heading'>PERIOD DETAILS</div>", unsafe_allow_html=True)
    sel_p = st.selectbox("Select a Period", [
        f"{g['period'] if g['period']!='—' else g['era']} ({g['start']} Ma)"
        for g in GEOLOGIC_TIME])
    idx_p = [f"{g['period'] if g['period']!='—' else g['era']} ({g['start']} Ma)"
             for g in GEOLOGIC_TIME].index(sel_p)
    gp = GEOLOGIC_TIME[idx_p]

    st.markdown(f"""
    <div class='glass-card' style='border-color:{gp["color"]}55;'>
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:16px;'>
            <div>
                <div style='color:{gp["color"]};font-family:Orbitron;font-size:0.85rem;margin-bottom:10px;'>
                {gp["period"] if gp["period"]!="—" else gp["era"]}
                </div>
                <div style='color:#94a3b8;font-size:0.8rem;line-height:2;'>
                🌐 <b style='color:#e2e8f0;'>Eon:</b> {gp["eon"]}<br>
                🌍 <b style='color:#e2e8f0;'>Era:</b> {gp["era"]}<br>
                🕐 <b style='color:#e2e8f0;'>Start:</b> {gp["start"]} Ma
                </div>
            </div>
            <div style='color:#94a3b8;font-size:0.8rem;'>
                🦎 <b style='color:#e2e8f0;'>Life & Events:</b><br><br>
                <span style='line-height:1.8;'>{gp["life"]}</span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: STRUCTURAL TOOLS
# ═══════════════════════════════════════════════════════════════
elif "Structural" in effective_page:
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
elif "Geography" in effective_page:
    st.markdown("<div class='section-heading'>GEOGRAPHY EXPLORER — INDIA TERRAIN & DRAINAGE</div>", unsafe_allow_html=True)

    layers_show = st.multiselect("Toggle Layers", ["Rivers","Mountains","Plate Boundaries","State Capitals","Seismic Zones"],
                                  default=["Rivers","Mountains"])

    fig_geo = go.Figure()
    # Major mountain ranges
    if "Mountains" in layers_show:
        mountains = [
            ("Himalayas",32.0,78.5),("Karakoram",35.5,76.5),("Aravalli",25.5,73.5),
            ("Vindhyas",23.5,78.0),("Satpura",21.5,76.5),("Eastern Ghats",17.5,82.0),
            ("Western Ghats",13.0,75.5),("Nilgiris",11.5,76.5),
        ]
        for name, lat, lon in mountains:
            fig_geo.add_trace(go.Scattergeo(lat=[lat], lon=[lon], text=[name],
                mode="markers+text", textposition="top right",
                marker=dict(size=10, color="#f59e0b", symbol="triangle-up"),
                textfont=dict(color="#f59e0b", size=9),
                name=name, hovertemplate=f"<b>{name}</b><extra></extra>"))

    # Rivers
    if "Rivers" in layers_show:
        for r in RIVERS[:4]:
            fig_geo.add_trace(go.Scattergeo(
                lat=[RIVERS.index(r)*2 + 20], lon=[80],
                mode="markers", marker=dict(size=8, color="#00d4ff"),
                name=r["name"], hovertemplate=f"<b>{r['name']}</b><br>Length: {r['length_km']} km<extra></extra>"))

    # State capitals
    if "State Capitals" in layers_show:
        capitals = [("New Delhi",28.6,77.2),("Mumbai",19.0,72.8),("Chennai",13.1,80.3),
                    ("Kolkata",22.5,88.4),("Hyderabad",17.4,78.5),("Bangalore",12.9,77.6),
                    ("Varanasi/BHU",25.3,83.0),("Jaipur",26.9,75.8),("Lucknow",26.8,80.9)]
        for name, lat, lon in capitals:
            bhu = "⭐" if "BHU" in name else "•"
            fig_geo.add_trace(go.Scattergeo(lat=[lat], lon=[lon], text=[f"{bhu} {name}"],
                mode="markers+text", textposition="top right",
                marker=dict(size=7, color="#10b981" if "BHU" in name else "#94a3b8"),
                textfont=dict(color="#10b981" if "BHU" in name else "#94a3b8", size=9),
                name=name, hovertemplate=f"<b>{name}</b><extra></extra>"))

    fig_geo.update_geos(scope="asia", lonaxis_range=[66, 100], lataxis_range=[5, 38],
        showland=True, landcolor="#1a2a1a", showocean=True, oceancolor="#020817",
        showcountries=True, countrycolor="rgba(255,255,255,0.2)",
        showcoastlines=True, coastlinecolor="rgba(0,212,255,0.5)",
        showrivers=True, rivercolor="rgba(0,160,255,0.5)",
        bgcolor="rgba(0,0,0,0)", showframe=False,
        showsubunits=True, subunitcolor="rgba(255,255,255,0.08)")
    fig_geo.update_layout(height=500, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
        legend=dict(bgcolor="rgba(10,22,40,0.7)", font=dict(size=9)))
    st.plotly_chart(fig_geo, use_container_width=True)

    st.markdown("<div class='section-heading'>INDIA PHYSIOGRAPHIC DIVISIONS</div>", unsafe_allow_html=True)
    physio = [
        ("🏔️","Himalayan Mountains","2,500 km range. 3 parallel zones: Himadri, Himachal, Siwaliks. Contains all 8000m+ peaks."),
        ("🌾","Northern Plains","700,000 km². Formed by Ganga-Indus-Brahmaputra alluvium. Most fertile, densely populated region."),
        ("⛰️","Peninsular Plateau","Oldest part of India (Precambrian craton). Average elevation 600-900m. Rich in minerals."),
        ("🌊","Coastal Plains","2 coasts: Western (narrow, steep — Western Ghats) and Eastern (broad, deltaic — Bay of Bengal)."),
        ("🏝️","Islands","Andaman & Nicobar (Bay of Bengal — volcanic arc), Lakshadweep (Arabian Sea — coral atolls)."),
    ]
    pc = st.columns(5)
    for i, (em, name, desc) in enumerate(physio):
        with pc[i]:
            st.markdown(f"""
            <div class='glass-card' style='padding:14px;text-align:center;'>
                <div style='font-size:1.6rem;margin-bottom:6px;'>{em}</div>
                <div style='color:#00d4ff;font-size:0.78rem;font-weight:600;margin-bottom:6px;'>{name}</div>
                <div style='color:#94a3b8;font-size:0.72rem;line-height:1.5;'>{desc}</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: WATERSHED EXPLORER
# ═══════════════════════════════════════════════════════════════
elif "Watershed" in effective_page:
    st.markdown("<div class='section-heading'>WATERSHED & RIVER BASIN EXPLORER</div>", unsafe_allow_html=True)

    sel_r = st.selectbox("Select River", [r["name"] for r in RIVERS])
    rdata = next(r for r in RIVERS if r["name"] == sel_r)

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"""
        <div class='glass-card'>
            <div style='color:#00d4ff;font-family:Orbitron;font-size:1rem;margin-bottom:14px;'>🌊 {rdata["name"]} River</div>
            <div style='color:#94a3b8;font-size:0.82rem;line-height:2.2;'>
            📏 <b style='color:#e2e8f0;'>Length:</b> {rdata["length_km"]:,} km<br>
            🏔️ <b style='color:#e2e8f0;'>Origin:</b> {rdata["origin"]}<br>
            🌊 <b style='color:#e2e8f0;'>Joins:</b> {rdata["joins"]}<br>
            📐 <b style='color:#e2e8f0;'>Basin Area:</b> {rdata["basin_km2"]:,} km²<br>
            🌿 <b style='color:#e2e8f0;'>Drainage Pattern:</b> {rdata["pattern"]}<br>
            🗺️ <b style='color:#e2e8f0;'>States:</b> {", ".join(rdata["states"])}<br>
            🌊 <b style='color:#e2e8f0;'>Major Tributaries:</b> {", ".join(rdata["tributaries"])}<br>
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class='glass-card'>
            <div style='color:#f59e0b;font-family:Orbitron;font-size:0.8rem;margin-bottom:10px;'>GEOLOGICAL NOTES</div>
            <div style='color:#94a3b8;font-size:0.8rem;line-height:1.7;'>{rdata["geo"]}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        # Basin comparison chart
        basin_data = {r["name"]: r["basin_km2"] for r in RIVERS}
        fig_basin = go.Figure(go.Bar(
            y=list(basin_data.keys()), x=list(basin_data.values()),
            orientation="h",
            marker=dict(color=list(range(len(RIVERS))),
                        colorscale=[[0,"#00d4ff"],[0.5,"#7c3aed"],[1,"#f59e0b"]]),
            hovertemplate="<b>%{y}</b><br>Basin: %{x:,} km²<extra></extra>"))
        fig_basin.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8a7d65", family="Source Sans 3"), height=280,
            margin=dict(l=5,r=5,t=5,b=5),
            title=dict(text="Basin Area (km²)", font=dict(size=11, color="#8a7d65")),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"), yaxis=dict())
        st.plotly_chart(fig_basin, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: SOIL EXPLORER
# ═══════════════════════════════════════════════════════════════
elif "Soil" in effective_page:
    st.markdown("<div class='section-heading'>SOIL EXPLORER — INDIA'S 7 MAJOR SOIL TYPES</div>", unsafe_allow_html=True)

    sel_s = st.selectbox("Select Soil Type", [s["name"] for s in SOILS])
    soil  = next(s for s in SOILS if s["name"] == sel_s)

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"""
        <div class='glass-card' style='border-color:{soil["color"]}55;'>
            <div style='display:flex;align-items:center;gap:12px;margin-bottom:14px;'>
                <div style='width:40px;height:40px;border-radius:8px;background:{soil["color"]};
                    border:2px solid {soil["color"]}88;flex-shrink:0;'></div>
                <div style='color:{soil["color"]};font-family:Orbitron;font-size:0.9rem;'>{soil["name"]}</div>
            </div>
            <div style='color:#94a3b8;font-size:0.8rem;line-height:2;'>
            📊 <b style='color:#e2e8f0;'>Area (% of India):</b> {soil["area_pct"]}%<br>
            🗺️ <b style='color:#e2e8f0;'>States:</b> {soil["states"]}<br>
            🌋 <b style='color:#e2e8f0;'>Formation:</b> {soil["formation"]}<br>
            🌾 <b style='color:#e2e8f0;'>Crops:</b> {soil["crops"]}<br>
            </div>
            <div style='color:#94a3b8;font-size:0.78rem;margin-top:10px;border-top:1px solid rgba(255,255,255,0.07);padding-top:8px;'>
            {soil["desc"]}
            </div>
        </div>""", unsafe_allow_html=True)

    with c2:
        fig_soil = go.Figure(go.Pie(
            labels=[s["name"] for s in SOILS],
            values=[s["area_pct"] for s in SOILS],
            hole=0.4,
            marker=dict(colors=[s["color"] for s in SOILS],
                        line=dict(color="rgba(0,0,0,0.3)", width=2)),
        ))
        fig_soil.update_traces(textfont_color="#f0e6d0",
            hovertemplate="<b>%{label}</b><br>%{value}% of India<extra></extra>")
        fig_soil.update_layout(paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0e6d0", family="Source Sans 3"),
            legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=5,r=5,t=5,b=5), height=320)
        st.plotly_chart(fig_soil, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: ECONOMIC GEOLOGY
# ═══════════════════════════════════════════════════════════════
elif "Economic" in effective_page:
    st.markdown("<div class='section-heading'>ECONOMIC GEOLOGY — INDIA'S MINERAL WEALTH</div>", unsafe_allow_html=True)

    sel_min = st.selectbox("Select Mineral/Resource", list(ECONOMIC_MINERALS.keys()))
    emin    = ECONOMIC_MINERALS[sel_min]

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"""
        <div class='glass-card' style='border-color:{emin["color"]}44;'>
            <div style='font-size:2rem;margin-bottom:8px;'>{emin["emoji"]}</div>
            <div style='color:#00d4ff;font-family:Orbitron;font-size:0.9rem;margin-bottom:12px;'>{sel_min}</div>
            <div style='color:#94a3b8;font-size:0.8rem;line-height:2;'>
            🏭 <b style='color:#e2e8f0;'>Primary Uses:</b> {emin["use"]}<br>
            🌏 <b style='color:#e2e8f0;'>India Rank:</b> {emin["india_rank"]}<br>
            </div>
        </div>""", unsafe_allow_html=True)

    with c2:
        fig_em = go.Figure(go.Pie(
            labels=list(emin["states"].keys()),
            values=list(emin["states"].values()),
            hole=0.4,
            marker=dict(colors=["#00d4ff","#7c3aed","#f59e0b","#10b981","#f87171","#a78bfa","#fbbf24"])
        ))
        fig_em.update_traces(textfont_color="#f0e6d0",
            hovertemplate="<b>%{label}</b>: %{value}% share<extra></extra>")
        fig_em.update_layout(paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0e6d0", family="Source Sans 3"),
            legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=5,r=5,t=5,b=5), height=270,
            title=dict(text=f"{sel_min} — State-wise Share", font=dict(size=11, color="#8a7d65")))
        st.plotly_chart(fig_em, use_container_width=True)

    # All minerals radar
    st.markdown("<div class='section-heading'>RESOURCE IMPORTANCE COMPARISON</div>", unsafe_allow_html=True)
    importance = {"Coal":9,"Iron Ore":9,"Bauxite":7,"Copper":5,"Zinc-Lead":8,"Chromite":7,"Gold":6,"Limestone":8}
    fig_rad = go.Figure(go.Scatterpolar(
        r=list(importance.values()) + [list(importance.values())[0]],
        theta=list(importance.keys()) + [list(importance.keys())[0]],
        fill="toself", line_color="#00d4ff",
        fillcolor="rgba(0,212,255,0.1)", name="Economic Value"))
    fig_rad.update_layout(polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(visible=True, range=[0,10], color="#475569", gridcolor="rgba(255,255,255,0.06)"),
        angularaxis=dict(color="#8a7d65", gridcolor="rgba(255,255,255,0.06)")),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0", family="Source Sans 3"), showlegend=False,
        height=360, margin=dict(l=40,r=40,t=20,b=20))
    st.plotly_chart(fig_rad, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: OCEANOGRAPHY
# ═══════════════════════════════════════════════════════════════
elif "Oceanography" in effective_page:
    st.markdown("<div class='section-heading'>OCEANOGRAPHY — INDIAN OCEAN</div>", unsafe_allow_html=True)

    fig_oc = go.Figure()
    # India EEZ approximate
    fig_oc.add_trace(go.Scattergeo(
        lat=[8, 8, 22, 30, 23, 8], lon=[68, 82, 90, 78, 68, 68],
        fill="toself", fillcolor="rgba(0,212,255,0.08)",
        line=dict(color="rgba(0,212,255,0.5)", width=1.5),
        name="India EEZ (Approx.)", mode="lines",
        hoverinfo="name"
    ))
    # Ocean currents (simplified)
    currents = [
        ([10, 12, 14],[55, 65, 75],"North Equatorial Current (Winter)","#00d4ff"),
        ([5, 8, 10],[80, 88, 95],"South Equatorial Current","#7c3aed"),
        ([15, 18, 22],[70, 68, 68],"Somali Current (Summer)","#f59e0b"),
        ([8, 6, 4],[70, 78, 85],"Equatorial Counter Current","#10b981"),
    ]
    for lat_c, lon_c, name_c, color_c in currents:
        fig_oc.add_trace(go.Scattergeo(lat=lat_c, lon=lon_c, mode="lines",
            line=dict(color=color_c, width=2.5), name=name_c,
            hovertemplate=f"<b>{name_c}</b><extra></extra>"))

    fig_oc.update_geos(scope="asia", lonaxis_range=[50, 110], lataxis_range=[-20, 35],
        showland=True, landcolor="#1a2a1a", showocean=True, oceancolor="#020817",
        showcountries=True, countrycolor="rgba(255,255,255,0.15)",
        showcoastlines=True, coastlinecolor="rgba(0,212,255,0.4)",
        bgcolor="rgba(0,0,0,0)", showframe=False)
    fig_oc.update_layout(height=440, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
        legend=dict(bgcolor="rgba(10,22,40,0.8)", font=dict(size=10)))
    st.plotly_chart(fig_oc, use_container_width=True)

    facts_oc = [
        ("🌊","Indian Ocean","3rd largest ocean (70.56 million km²). Only ocean bounded on 3 sides by land."),
        ("🏝️","EEZ","India's Exclusive Economic Zone = ~2.37 million km². Rich in fisheries and polymetallic nodules."),
        ("🌀","Monsoon","Indian Ocean drives the South Asian Monsoon — seasonal reversal of wind and current direction."),
        ("🦈","Biodiversity","Coral Triangle margins, whale sharks, dugongs — biodiversity hotspot."),
        ("📡","ONGC Bombay High","India's largest offshore oil field — 160 km off Mumbai. Produces ~8 MT oil/year."),
        ("🌡️","Temperature","Warm surface waters (>28°C near equator) drive powerful cyclones in Bay of Bengal."),
    ]
    fc_oc = st.columns(3)
    for i,(em,nm,ds) in enumerate(facts_oc):
        with fc_oc[i%3]:
            st.markdown(f"""
            <div class='glass-card' style='padding:12px 14px;'>
                <div style='font-size:1.3rem;margin-bottom:4px;'>{em}</div>
                <div style='color:#00d4ff;font-size:0.8rem;font-weight:600;margin-bottom:4px;'>{nm}</div>
                <div style='color:#94a3b8;font-size:0.74rem;line-height:1.5;'>{ds}</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: THIN SECTION GALLERY
# ═══════════════════════════════════════════════════════════════
elif "Thin Section" in effective_page:
    st.markdown("<div class='section-heading'>THIN SECTION GALLERY — OPTICAL MINERALOGY</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='glass-card' style='padding:10px 16px;margin-bottom:12px;'>
        <span style='color:#94a3b8;font-size:0.78rem;'>
        🔬 PPL = Plane Polarised Light · XPL = Cross Polarised Light (crossed nicols)
        </span>
    </div>""", unsafe_allow_html=True)

    cols = st.columns(3)
    for i, ts in enumerate(THIN_SECTIONS):
        with cols[i % 3]:
            st.markdown(f"""
            <div class='mineral-card' style='border-color:{ts["border"]}55;text-align:center;'>
                <div style='
                    width:100%;height:90px;
                    background:radial-gradient(circle,{ts["color"]},rgba(8,18,38,0.9));
                    border-radius:8px;margin-bottom:10px;
                    display:flex;align-items:center;justify-content:center;
                    border:1px solid {ts["border"]}44;
                    font-size:2rem;'>
                    {ts["emoji"]}
                </div>
                <div class='mineral-name' style='color:{ts["border"]};margin-bottom:6px;'>{ts["name"]}</div>
                <div class='mineral-desc'>{ts["desc"]}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-heading'>INTERFERENCE COLOUR CHART (MICHEL-LÉVY)</div>", unsafe_allow_html=True)
    orders  = ["1st Order","2nd Order","3rd Order","4th Order"]
    bio_ref = [0.04, 0.04, 0.04, 0.04]
    min_names = ["Chlorite\n(0.005–0.012)","Quartz\n(0.009)","Plagioclase\n(0.007–0.012)",
                 "Calcite\n(0.172)","Olivine\n(0.035)","Biotite\n(0.03–0.045)"]
    biref_vals = [0.009, 0.009, 0.01, 0.172, 0.035, 0.04]
    colors_br  = ["#10b981","#f59e0b","#94a3b8","#a78bfa","#84cc16","#f87171"]

    fig_ml = go.Figure()
    for nm, bv, cl in zip(min_names, biref_vals, colors_br):
        fig_ml.add_trace(go.Bar(x=[nm], y=[bv], marker_color=cl, name=nm,
            hovertemplate=f"<b>{nm}</b><br>Birefringence: {bv}<extra></extra>"))
    fig_ml.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a7d65", family="Source Sans 3"), height=260,
        margin=dict(l=5,r=5,t=5,b=5), showlegend=False,
        xaxis=dict(tickfont=dict(size=9)), yaxis=dict(title="Birefringence (δ)",
            gridcolor="rgba(255,255,255,0.05)"))
    st.plotly_chart(fig_ml, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: SEMESTER NOTES
# ═══════════════════════════════════════════════════════════════
elif "Notes" in effective_page:
    st.markdown("<div class='section-heading'>SEMESTER-WISE NOTES — BHU B.Sc. EARTH SCIENCE (4-YEAR UG)</div>", unsafe_allow_html=True)

    sem_tabs = st.tabs(list(NOTES.keys()))
    for tab, (sem, subjects) in zip(sem_tabs, NOTES.items()):
        with tab:
            for subject, points in subjects.items():
                with st.expander(f"📖 {subject}", expanded=False):
                    for pt in points:
                        st.markdown(f"""
                        <div class='glass-card' style='padding:12px 16px;margin-bottom:8px;'>
                            <div style='color:#94a3b8;font-size:0.8rem;line-height:1.65;'>{pt}</div>
                        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-heading'>EXAM QUICK REFERENCE</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class='glass-card'>
            <div style='color:#00d4ff;font-family:Orbitron;font-size:0.8rem;margin-bottom:10px;'>GEOLOGIC TIME SCALE</div>
            <div style='color:#94a3b8;font-size:0.76rem;line-height:2;'>
            🟡 Quaternary – 2.6 Ma–present<br>
            🟠 Neogene – 23–2.6 Ma<br>
            🟡 Paleogene – 66–23 Ma<br>
            🟢 Cretaceous – 145–66 Ma<br>
            🟢 Jurassic – 201–145 Ma<br>
            🟢 Triassic – 252–201 Ma<br>
            🔵 Permian – 299–252 Ma<br>
            🔵 Carboniferous – 359–299 Ma<br>
            🔵 Devonian – 419–359 Ma<br>
            🔵 Silurian – 444–419 Ma<br>
            🔵 Ordovician – 485–444 Ma<br>
            🔵 Cambrian – 541–485 Ma
            </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class='glass-card'>
            <div style='color:#f59e0b;font-family:Orbitron;font-size:0.8rem;margin-bottom:10px;'>INDIA KEY FACTS</div>
            <div style='color:#94a3b8;font-size:0.76rem;line-height:2;'>
            ⛰️ Highest Peak: Kangchenjunga (8,586m)<br>
            🌊 Longest River: Ganga (2,525 km in India)<br>
            💎 Oldest Rocks: Dharwar craton (~3.3 Ga)<br>
            🌋 Only Active Volcano: Barren Island<br>
            ⛏️ Largest Coal State: Jharkhand<br>
            🥇 Largest Gold Mines: Karnataka (KGF)<br>
            💎 Largest Mica: Andhra Pradesh<br>
            🟤 Largest Diamond Mine: Majhgawan (MP)<br>
            🧪 Deepest Mine: KGF (~3.8 km depth)<br>
            🌋 Biggest Flood Basalt: Deccan Traps<br>
            </div>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: GEO QUIZ
# ═══════════════════════════════════════════════════════════════
elif "Quiz" in effective_page:
    st.markdown("<div class='section-heading'>GEO QUIZ — TIMED · SCORED · RANDOMIZED</div>", unsafe_allow_html=True)

    total = len(QUIZ_QUESTIONS)
    if st.session_state.quiz_order is None:
        st.session_state.quiz_order = random.sample(range(total), total)

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
        q = QUIZ_QUESTIONS[st.session_state.quiz_order[idx]]
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
        grade = "🏆 Geology Expert!" if pct >= 90 else "⭐ Very Good" if pct >= 70 else "📚 Keep Studying" if pct >= 50 else "🔬 Beginner"
        st.markdown(f"""
        <div class='hero-banner'>
            <div style='font-family:Orbitron;font-size:2.5rem;color:#f59e0b;'>{sc}/{total}</div>
            <div style='font-size:1rem;color:#e2e8f0;margin:8px 0;'>{pct}% Correct</div>
            <div class='hero-badge'>{grade}</div>
        </div>""", unsafe_allow_html=True)
        if pct >= 90:
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
elif "Flashcard" in effective_page:
    st.markdown("<div class='section-heading'>FLASHCARDS — GEOLOGY TERMS & CONCEPTS</div>", unsafe_allow_html=True)

    total_fc = len(FLASHCARDS)
    fc = FLASHCARDS[st.session_state.fc_idx]
    mastered = len(st.session_state.fc_mastered)

    st.markdown(f"""
    <div style='display:flex;justify-content:space-between;margin-bottom:12px;'>
        <span style='color:#94a3b8;font-size:0.78rem;'>Card {st.session_state.fc_idx+1} of {total_fc}</span>
        <span style='color:#10b981;font-size:0.78rem;'>✅ Mastered: {mastered}/{total_fc}</span>
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
            if st.session_state.fc_idx not in st.session_state.fc_mastered:
                st.session_state.fc_mastered.append(st.session_state.fc_idx)
            st.session_state.fc_idx  = (st.session_state.fc_idx + 1) % total_fc
            st.session_state.fc_show = False
            st.rerun()

    prog_fc = mastered / total_fc
    st.markdown(f"""
    <div style='background:rgba(255,255,255,0.06);border-radius:8px;height:6px;margin-top:14px;'>
        <div style='background:linear-gradient(90deg,#10b981,#00d4ff);height:6px;border-radius:8px;
            width:{prog_fc*100:.1f}%;'></div>
    </div>
    <div style='color:#94a3b8;font-size:0.72rem;margin-top:4px;'>{int(prog_fc*100)}% mastered</div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: AI ASSISTANT
# ═══════════════════════════════════════════════════════════════
elif "AI Assistant" in effective_page:
    st.markdown("<div class='section-heading'>AI GEO ASSISTANT — GEOLOGY Q&A</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='glass-card' style='padding:10px 14px;margin-bottom:12px;'>
        <span style='color:#94a3b8;font-size:0.78rem;'>
        💡 Ask about: <span style='color:#00d4ff;'>geology · Himalaya · Deccan Traps · minerals · stratigraphy · metamorphism · earthquakes · BHU · soil · Gondwana</span>
        </span>
    </div>""", unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""<div class='chat-label-user'>YOU</div>
            <div class='chat-bubble-user'>{msg["text"]}</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class='chat-label-ai'>🌍 GEOSPHERE AI</div>
            <div class='chat-bubble-ai'>{msg["text"]}</div>""", unsafe_allow_html=True)

    user_q = st.text_input("Ask GeoSphere AI:", placeholder="What is metamorphism?", key="ai_inp")
    ca1, ca2 = st.columns([1, 4])
    with ca1:
        ask = st.button("🚀 Ask")
    with ca2:
        if st.button("🗑️ Clear"):
            st.session_state.chat_history = []
            st.rerun()

    if ask and user_q.strip():
        uql = user_q.lower()
        resp = None
        for kw, ans in AI_KNOWLEDGE.items():
            if kw in uql or any(w in uql for w in kw.split()):
                resp = ans
                break
        if not resp:
            if any(w in uql for w in ["hello","hi","hey","namaste"]):
                resp = "Hello! I'm GeoSphere AI 🌍 — your Earth Science assistant. Ask me about minerals, rocks, Indian geology, plate tectonics, earthquakes, or the BHU curriculum!"
            elif "mineral" in uql:
                resp = AI_KNOWLEDGE["metamorphism"]
            elif "rock" in uql:
                resp = AI_KNOWLEDGE["rock cycle"]
            elif "india" in uql:
                resp = AI_KNOWLEDGE["plate tectonics"]
            else:
                resp = f"Great geology question about '{user_q}'! My knowledge covers: geology basics, Deccan Traps, Himalayas, Mohs scale, plate tectonics, Indian minerals, metamorphism, earthquakes, soil types, Gondwana, stratigraphy, and BHU curriculum. Try one of those topics!"
        st.session_state.chat_history.append({"role":"user","text":user_q})
        st.session_state.chat_history.append({"role":"ai","text":resp})
        st.rerun()

    if not st.session_state.chat_history:
        st.markdown("""
        <div style='text-align:center;padding:40px;color:#334155;'>
            <div style='font-size:3rem;margin-bottom:10px;'>🌍</div>
            <div style='font-family:Orbitron;font-size:0.85rem;letter-spacing:2px;color:#475569;'>
            ASK YOUR FIRST QUESTION
            </div>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: HUMAN DIARY
# ═══════════════════════════════════════════════════════════════
elif "Diary" in effective_page:
    st.markdown("<div class='section-heading'>HUMAN DIARY — A GEOLOGIST'S JOURNEY AT BHU</div>", unsafe_allow_html=True)
    for entry in DIARY_ENTRIES:
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
elif "About" in effective_page or "Archive" in effective_page:
    st.session_state.about_visited = True

    st.markdown("<div class='section-heading'>About GeoSphere India</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class='glass-card'>
            <div style='color:#c9a84c;font-family:Playfair Display,Georgia,serif;
                font-size:0.95rem;font-weight:700;margin-bottom:14px;'>System Information</div>
            <div style='color:#8a7d65;font-size:0.85rem;line-height:2.4;font-family:Source Sans 3,sans-serif;'>
            Platform ............ GeoSphere India v2.0<br>
            Purpose ............. Earth Science · Learning · Exploration<br>
            Curriculum .......... BHU B.Sc. (Hons.) Earth Science (4-Year UG)<br>
            Sections ............ 20 Interactive Modules<br>
            Data Sources ........ GSI · USGS · BHU<br>
            Built With .......... Streamlit · Plotly · Python
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div class='glass-card' style='border-color:rgba(201,168,76,0.18);'>
            <div style='color:#6a5c3a;font-size:0.62rem;letter-spacing:2px;
                margin-bottom:10px;font-family:Source Sans 3,sans-serif;'>SYSTEM</div>
            <div style='font-size:0.82rem;color:#2a2416;line-height:2.4;font-family:Source Sans 3,sans-serif;'>
            Alias : <span style='color:#c9a84c;'>COMPUTER</span><br>
            Status : <span style='color:#a8d5a2;'>Online</span><br>
            Build : <span style='color:#6a5c3a;'>Stable</span>
            </div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class='glass-card' style='border-color:rgba(201,168,76,0.15);'>
            <div style='color:#6a5c3a;font-size:0.62rem;letter-spacing:2px;
                margin-bottom:10px;font-family:Source Sans 3,sans-serif;'>ARCHIVE STATISTICS</div>
            <div style='color:#2a2416;font-size:0.82rem;font-family:Source Sans 3,sans-serif;line-height:2.6;'>
            Years Active ............ <span style='color:#6a5c3a;'>11</span><br>
            Integrity ............... <span style='color:#6a5c3a;'>100%</span><br>
            Memories Lost ........... <span style='color:#6a5c3a;'>0</span>
            </div>
        </div>
        <div style='text-align:center;color:#2a2416;font-size:0.68rem;
            font-family:Source Sans 3,sans-serif;margin-top:6px;'>
            Latitude: 25.2677° N · Longitude: 82.9913° E
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(201,168,76,0.12);margin:20px 0;'>", unsafe_allow_html=True)

    # ── ACHIEVEMENT MODE TRIGGER ──
    # Sequence: logo 8+ clicks → visit this page → click version number
    if st.session_state.logo_clicks >= 8:
        st.markdown("""
        <div style='text-align:center;color:#3a3020;font-size:0.65rem;
            margin-bottom:8px;font-family:Source Sans 3,sans-serif;'>
        Build · v08.09.08.11
        </div>""", unsafe_allow_html=True)

        col_v1, col_v2, col_v3 = st.columns([2,1,2])
        with col_v2:
            if st.button("v08.09.08.11", key="version_btn"):
                st.session_state.rare_mode  = not st.session_state.rare_mode
                st.session_state.rare_timer = time.time()
                st.rerun()
    else:
        st.markdown("""
        <div style='text-align:center;color:#1e1a12;font-size:0.62rem;
            font-family:Source Sans 3,sans-serif;'>
        Build · v08.09.08.11
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(201,168,76,0.1);margin:18px 0;'>", unsafe_allow_html=True)

    # Geology facts
    st.markdown("<div class='section-heading'>Curious Geology Facts</div>", unsafe_allow_html=True)
    weird = [
        ("💎","Diamond forms at 150–200 km depth, then rockets to surface in kimberlite pipes — the fastest-moving magma known."),
        ("🌊","Ocean floor is entirely recycled every ~200 Ma. The oldest ocean crust is far younger than the continents."),
        ("🪨","Jack Hills Zircon (Australia) is 4.4 Ga old — almost as old as Earth. A single crystal, smaller than a grain of sand."),
        ("🌋","Tambora 1815 eruption cooled global temperatures by 0.5°C — 'The Year Without a Summer'."),
        ("🏔️","The Himalayas grow ~5mm/year but erosion keeps them from getting infinitely tall. A perfect natural balance."),
        ("🔥","Earth loses ~47 terawatts of heat through its surface — like 4.7 billion powerful heaters running continuously."),
    ]
    wc = st.columns(3)
    for i,(em,fact) in enumerate(weird):
        with wc[i%3]:
            st.markdown(f"""
            <div class='mineral-card'>
                <div style='font-size:1.6rem;margin-bottom:8px;'>{em}</div>
                <div style='color:#8a7d65;font-size:0.84rem;line-height:1.7;
                    font-family:Source Sans 3,sans-serif;'>{fact}</div>
            </div>""", unsafe_allow_html=True)

    # Hidden gem easter egg
    st.markdown("<br>", unsafe_allow_html=True)
    cx1, cx2, cx3 = st.columns(3)
    with cx2:
        if st.button("🥚 Hidden Gem", use_container_width=True):
            st.session_state.easter_count += 1
            st.rerun()
    gems = [
        "🌍 The core is as hot as the surface of the Sun — 5,500°C. Both unreachable. Both magnificent.",
        "💙 Every atom of calcium in your bones was forged in a dying star. You are literally made of stardust.",
        "🪨 Geology = geo (Earth) + logos (reason). The Language of Earth.",
        "⭐ GSI (est. 1851) mapped India's entire mineral wealth. You're part of that legacy.",
        "🌋 Basalt is the most common rock on Earth — and also on the Moon and Mars. It's universal.",
    ]
    if st.session_state.easter_count > 0:
        gi = (st.session_state.easter_count - 1) % len(gems)
        st.markdown(f"""
        <div class='glass-card' style='text-align:center;border-color:rgba(201,168,76,0.3);margin-top:14px;'>
            <div style='color:#c9a84c;font-size:0.95rem;line-height:1.9;
                font-family:Playfair Display,Georgia,serif;font-style:italic;'>{gems[gi]}</div>
            <div style='color:#3a3020;font-size:0.68rem;margin-top:10px;
                font-family:Source Sans 3,sans-serif;'>
                Gem {st.session_state.easter_count} discovered · Click again for another
            </div>
        </div>""", unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
    <div style='text-align:center;color:#1e1a12;font-size:0.62rem;
        padding:20px 0 8px;line-height:2.2;font-family:Source Sans 3,sans-serif;'>
        GeoSphere India · v08.09.08.11 · BHU Earth Science<br>
        Lat: 25.2677°N · Lon: 82.9913°E<br>
        <span style='color:#c9a84c;opacity:0.4;'>Dedicated to Curiosity.</span>
    </div>""", unsafe_allow_html=True)
