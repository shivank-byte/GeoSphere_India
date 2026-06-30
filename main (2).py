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
#  REAL PHOTO FETCH — Wikipedia REST API, cached, fails silently
# ═══════════════════════════════════════════════════════
@st.cache_data(show_spinner=False, ttl=86400)
def get_wiki_image(title: str):
    """Fetch a representative photo URL for a topic from Wikipedia's API.
    Returns None on any failure so the UI can gracefully skip the image."""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
        r = requests.get(url, timeout=6, headers={"User-Agent": "GeoSphereIndia/1.0"})
        if r.status_code == 200:
            data = r.json()
            thumb = data.get("thumbnail", {}).get("source") or data.get("originalimage", {}).get("source")
            return thumb
    except Exception:
        pass
    return None

def show_wiki_photo(title: str, caption: str = None, width: int = None):
    """Render a real photo inline if available, otherwise render nothing (no broken-image icon)."""
    img_url = get_wiki_image(title)
    if img_url:
        try:
            st.image(img_url, caption=caption or title, use_container_width=(width is None))
        except Exception:
            pass

# ═══════════════════════════════════════════════════════
#  ACHIEVEMENT MODE — Urdu-styled navigation labels (labels only, not content)
# ═══════════════════════════════════════════════════════
URDU_NAV_LABELS = {
    "🌌 Mission Control":      "🌌 مشن کنٹرول",
    "🗺️ Geological Map":       "🗺️ ارضیاتی نقشہ",
    "🌋 Plate Tectonics":      "🌋 تہہ حرکیات",
    "💎 Mineral Explorer":     "💎 معدنیات",
    "🌍 Earthquake Dashboard": "🌍 زلزلہ ڈیش بورڈ",
    "📅 Geological Time Scale":"📅 ارضیاتی وقت",
    "🧪 Soil Explorer":        "🧪 مٹی کی تحقیق",
    "🪙 Economic Geology":     "🪙 معاشی ارضیات",
    "🪨 Rock Explorer":        "🪨 چٹانیں",
    "🌋 Volcano Explorer":     "🌋 آتش فشاں",
    "🧭 Structural Tools":     "🧭 ساختی آلات",
    "🌿 Geography Explorer":   "🌿 جغرافیہ",
    "🌊 Watershed Explorer":   "🌊 آبی ذخائر",
    "🌊 Oceanography":         "🌊 بحریات",
    "🔬 Thin Section Gallery": "🔬 پتلی تہہ گیلری",
    "📚 Semester Notes":       "📚 نوٹس",
    "🧠 Geo Quiz":             "🧠 سوالنامہ",
    "🃏 Flashcards":           "🃏 فلیش کارڈز",
    "🤖 AI Assistant":         "🤖 معاون",
    "📓 Field Diary":          "📓 ڈائری",
    "🥚 About & Archive":      "🥚 تعارف",
}

def urdu_label(text: str) -> str:
    """Return the Urdu-styled label for a nav item when achievement mode is active."""
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
    position: fixed !important;
    top: 50% !important;
    left: 0 !important;
    transform: translateY(-50%) !important;
    z-index: 999999 !important;
    pointer-events: auto !important;
}
[data-testid="collapsedControl"]:hover {
    background: rgba(201,168,76,0.35) !important;
    box-shadow: 3px 0 16px rgba(201,168,76,0.35) !important;
}
[data-testid="collapsedControl"] svg { 
    fill: #c9a84c !important;
    width: 20px !important;
    height: 20px !important;
    pointer-events: none !important;
}
section[data-testid="stSidebarCollapsedControl"] { 
    opacity: 1 !important; 
    visibility: visible !important;
    display: block !important;
    pointer-events: all !important;
    z-index: 999999 !important;
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
     "desc":"Standard reference. Covers Earth processes from minerals to plate tectonics. Excellent figures."},
    {"title":"Earth Materials","author":"Hefferan & O'Brien","subject":"Sem 1 – Earth Materials","stars":4,
     "desc":"Modern mineralogy and petrology reference. Good coverage of optical properties and Indian examples."},
    {"title":"Principles of Geomorphology","author":"W.D. Thornbury","subject":"Sem 2 – Geomorphology","stars":5,
     "desc":"Landmark work on landform evolution. Essential for Indian physiographic divisions and drainage patterns."},
    {"title":"Optical Mineralogy","author":"W.A. Deer, Howie & Zussman","subject":"Sem 2 – Mineralogy","stars":5,
     "desc":"The definitive petrography reference. Optical properties of all rock-forming minerals under polarised light."},
    {"title":"Petrology of Igneous & Metamorphic Rocks","author":"Hyndman","subject":"Sem 3 – Petrology","stars":4,
     "desc":"Detailed igneous and metamorphic petrography. Good companion to Deccan Traps and Himalayan studies."},
    {"title":"Structural Geology","author":"M.P. Billings","subject":"Sem 3 – Structural Geology","stars":5,
     "desc":"Rigorous treatment of folds, faults, and foliations. Used extensively in structural geology practical classes."},
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
]

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
    {"date":"Day 1 — The Beginning","text":"First day in the Geology department. The corridors smelled of minerals and old maps. Picked up a piece of basalt from the lab counter and thought — this rock type covers 500,000 km² of India. The Deccan Traps. Everything starts to feel connected."},
    {"date":"Day 47 — Field Practical","text":"Vindhyan sandstone in the afternoon sun. Ran fingers along cross-bedding that formed 600 million years ago. Time stops making human sense out here. The professor said: 'You're not looking at rock. You're reading a letter from the Proterozoic.'"},
    {"date":"Day 89 — The Thin Section","text":"First polarising microscope session. Quartz glowing blue, feldspar in grey, biotite exploding in amber under crossed polars. A whole world in a 0.03mm slice. Started to understand why geologists obsess over microscopes."},
    {"date":"Day 156 — Exam Season","text":"Structural geology diagrams at 2am. Folds, faults, foliations. The Himalayan orogeny plays on repeat in the mind. India crashing into Eurasia at 5 cm/yr — too slow to feel, too powerful to stop. Still going."},
    {"date":"Day 203 — Monsoon Lab","text":"Rain outside, thin sections inside. Someone found pyrite in a Vindhyan sample and the whole lab leaned in. Fool's Gold — but only a fool would dismiss it. Tells you about oxygen levels, fluid pathways, deep-time chemistry."},
    {"date":"Day 241 — First Map","text":"Drew my first proper geological map today — contacts, strike and dip symbols, a fault line I almost missed until the outcrop pattern gave it away. The professor's red pen found three errors. Each one taught me to look slower."},
    {"date":"Day 298 — Mineral Identification Practical","text":"Hardness kits, streak plates, dilute HCl. Calcite fizzed right on cue. Realized geology is half memory, half detective work — every property is a clue, and you're never allowed to guess."},
    {"date":"Day 334 — A Quiet Outcrop","text":"Found a small roadcut nobody talks about — tight little folds in phyllite, easy to walk past. Sat there for twenty minutes just looking. Some of the best lessons aren't in the syllabus, they're in the rocks nobody photographs."},
    {"date":"Day 372 — Fossil Find","text":"A cast of Glossopteris in a shale sample passed around the lab like treasure. A leaf that once grew across Gondwana — India, Africa, Antarctica, Australia, all one. Held proof of a vanished world in one hand."},
    {"date":"Day 410 — Night Before the Field Trip","text":"Boots packed, hand lens checked twice, notebook still mostly empty. Tomorrow: real outcrops, real weather, real mistakes. Somewhere between nervous and impatient. This is the part nobody warns you you'll miss later."},
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
    dot_display = "·" * min(clicks, 10)
    click_hint  = ""
    if   clicks == 0:  click_hint = "· · ·"
    elif clicks < 5:   click_hint = dot_display
    elif clicks < 10:  click_hint = "▸ SYSTEM ONLINE"
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

    if st.session_state.logo_clicks >= 5:
        st.markdown("""
        <div style='background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.2);
            border-radius:10px;padding:10px;margin-bottom:8px;'>
            <div style='color:#4a4230;font-size:0.6rem;letter-spacing:2px;'>SYSTEM</div>
            <div style='color:#c9a84c;font-family:Source Sans 3,sans-serif;font-size:0.72rem;margin-top:5px;line-height:2;'>
                Alias : COMPUTER<br>Status : Online<br>Build : Stable
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.session_state.logo_clicks >= 10:
            panda_img = get_wiki_image("Giant panda")
            panda_html = f'<img src="{panda_img}" class="panda-photo">' if panda_img else '<div style="font-size:5rem;">🐼</div>'
            st.markdown(f"""
            <div class='panda-overlay'>
                <div class='panda-content'>
                    {panda_html}
                    <div class='panda-text'>Hadd ho.</div>
                </div>
            </div>""", unsafe_allow_html=True)

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

    page = st.radio("", SIDEBAR_PAGES, label_visibility="collapsed", key="sidebar_page_radio",
                     format_func=urdu_label)

    # Session state for sub-page from Mission Control radial dial
    if "sub_page" not in st.session_state:
        st.session_state.sub_page = None

    # Sidebar mini status badges
    st.markdown("""<hr style='border-color:rgba(201,168,76,0.12);margin:14px 0;'>""", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center;margin:6px 0 12px;'>
        <span class='float-badge'>🌋 Live</span>
        <span class='float-badge'>🌍 Earth Science</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size:0.6rem;color:#2a2416;text-align:center;padding:6px 0;line-height:2;
        font-family:Source Sans 3,sans-serif;'>
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
        <span class='hero-badge'>EARTH SCIENCE · {datetime.datetime.now().strftime("%d %b %Y")}</span>
    </div>
    """, unsafe_allow_html=True)
else:
    hero_sub_text = "زمینی سائنس کا ذہین پلیٹ فارم" if st.session_state.get("rare_mode") else "EARTH SCIENCE INTELLIGENCE PLATFORM"
    st.markdown(f"""
    <div class='hero-banner'>
        <p class='hero-title'>GeoSphere India</p>
        <p class='hero-sub' style='{"font-family:\\'Noto Nastaliq Urdu\\',serif;font-size:1.1rem;" if st.session_state.get("rare_mode") else ""}'>{hero_sub_text}</p>
        <span class='hero-badge'>EARTH SCIENCE · {datetime.datetime.now().strftime("%d %b %Y")}</span>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE ROUTING — sidebar pages + sub_page from radial dial
# ═══════════════════════════════════════════════════════════════
# Sub-page overrides sidebar selection when set from radial dial
effective_page = st.session_state.get("sub_page") or page

# Reliable in-app "Home" button — phone back-gesture can't be intercepted
# inside a Streamlit single-page app, so this is the dependable way back.
if effective_page != "🌌 Mission Control":
    home_col1, home_col2 = st.columns([1, 8])
    with home_col1:
        if st.button("⬅ Home", key="global_home_btn"):
            st.session_state.sub_page = None
            st.rerun()

# ═══════════════════════════════════════════════════════════════
#  PAGE: MISSION CONTROL  (default / home)
# ═══════════════════════════════════════════════════════════════
if effective_page not in [
    "🗺️ Geological Map","🌋 Plate Tectonics","💎 Mineral Explorer",
    "🌍 Earthquake Dashboard","📅 Geological Time Scale","🧪 Soil Explorer",
    "🪙 Economic Geology","🪨 Rock Explorer","🌋 Volcano Explorer",
    "🧭 Structural Tools","🌿 Geography Explorer","🌊 Watershed Explorer",
    "🌊 Oceanography","🔬 Thin Section Gallery","📚 Semester Notes",
    "🧠 Geo Quiz","🃏 Flashcards","🤖 AI Assistant","📓 Field Diary",
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
            type="buttons", showactive=False, direction="left",
            buttons=[
                dict(
                    label="▶ Rotate",
                    method="animate",
                    args=[None, dict(frame=dict(duration=80, redraw=True),
                                      fromcurrent=True, mode="immediate",
                                      transition=dict(duration=0))]
                ),
                dict(
                    label="⏸ Pause",
                    method="animate",
                    args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode="immediate",
                                        transition=dict(duration=0))]
                ),
            ],
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
        ("📓","Field Diary"),
        ("🥚","About & Archive"),
    ]
    dial_cols = st.columns(4)
    for i, (em, name) in enumerate(EXTRA_PAGES):
        with dial_cols[i % 4]:
            btn_label = urdu_label(f"{em} {name}")
            if st.button(btn_label, key=f"dial_{i}", use_container_width=True):
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
            legend=dict(orientation="h", y=-1.1, font=dict(size=9, color="#f0e6d0"), bgcolor="rgba(0,0,0,0)"),
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
            legend=dict(font=dict(size=9, color="#f0e6d0"), bgcolor="rgba(0,0,0,0)"),
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

    if "pt_animating" not in st.session_state:
        st.session_state.pt_animating = False
    if "pt_ma" not in st.session_state:
        st.session_state.pt_ma = 50

    pcol1, pcol2 = st.columns([1, 5])
    with pcol1:
        if st.session_state.pt_animating:
            if st.button("⏸ Pause"):
                st.session_state.pt_animating = False
                st.rerun()
        else:
            if st.button("▶ Animate"):
                st.session_state.pt_animating = True
                st.rerun()
    with pcol2:
        ma = st.slider("⏱️ Time (Million Years Ago → Present)", min_value=0, max_value=100,
                       value=st.session_state.pt_ma, step=5, format="%d Ma",
                       disabled=st.session_state.pt_animating)
        if not st.session_state.pt_animating:
            st.session_state.pt_ma = ma
        else:
            ma = st.session_state.pt_ma

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
        legend=dict(bgcolor="rgba(10,22,40,0.85)", font=dict(size=11, color="#f0e6d0"))
    )
    st.plotly_chart(fig_tec, use_container_width=True)

    if st.session_state.pt_animating:
        time.sleep(0.5)
        st.session_state.pt_ma = (st.session_state.pt_ma - 5) % 105
        if st.session_state.pt_ma > 100:
            st.session_state.pt_ma = 0
        st.rerun()

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
                    show_wiki_photo(r["name"], caption=r["name"])
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
                   search_r.lower() in r["composition"].lower() or search_r.lower() in r["formation"].lower()
                   or search_r.lower() in r["use"].lower() or search_r.lower() in r["india"].lower()]
            if not res:
                st.warning("No rocks found. Try different keywords.")
            else:
                for rt, r in res:
                    show_wiki_photo(r["name"], caption=r["name"])
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
                show_wiki_photo(m["name"], caption=m["name"])
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
            show_wiki_photo(v["name"], caption=v["name"])
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
        legend=dict(orientation="h", y=-0.5, font=dict(size=8, color="#f0e6d0"), bgcolor="rgba(0,0,0,0)"),
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

    # Rivers — drawn as actual flowing paths (start to mouth), not single dots
    if "Rivers" in layers_show:
        for r in RIVERS:
            if "path" in r:
                path_lats = [p[0] for p in r["path"]]
                path_lons = [p[1] for p in r["path"]]
                fig_geo.add_trace(go.Scattergeo(
                    lat=path_lats, lon=path_lons, mode="lines",
                    line=dict(color="#00d4ff", width=2.5),
                    name=r["name"],
                    hovertemplate=f"<b>{r['name']}</b><br>Length: {r['length_km']} km<extra></extra>"))

    # State capitals
    if "State Capitals" in layers_show:
        capitals = [("New Delhi",28.6,77.2),("Mumbai",19.0,72.8),("Chennai",13.1,80.3),
                    ("Kolkata",22.5,88.4),("Hyderabad",17.4,78.5),("Bangalore",12.9,77.6),
                    ("Varanasi",25.3,83.0),("Jaipur",26.9,75.8),("Lucknow",26.8,80.9)]
        for name, lat, lon in capitals:
            fig_geo.add_trace(go.Scattergeo(lat=[lat], lon=[lon], text=[name],
                mode="markers+text", textposition="top right",
                marker=dict(size=7, color="#94a3b8"),
                textfont=dict(color="#94a3b8", size=9),
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
        legend=dict(bgcolor="rgba(10,22,40,0.85)", font=dict(size=9, color="#f0e6d0"),
                    bordercolor="rgba(0,212,255,0.3)", borderwidth=1))
    st.plotly_chart(fig_geo, use_container_width=True)

    st.markdown("""
    <div class='glass-card' style='padding:12px 16px;margin-bottom:14px;'>
        <span style='color:#94a3b8;font-size:0.8rem;line-height:1.7;'>
        🗺️ <b style='color:#00d4ff;'>How to read this map:</b> toggle layers above to compare terrain features.
        Mountain ranges (▲ orange) mark uplift zones — note how they border the plains they shed sediment into.
        Rivers (cyan lines) trace from Himalayan/Peninsular source regions down to their deltas, generally
        following the regional slope. Hover over any marker or line for details.
        </span>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-heading'>INDIA PHYSIOGRAPHIC DIVISIONS</div>", unsafe_allow_html=True)
    physio = [
        ("🏔️","Himalayan Mountains","2,500 km range. 3 parallel zones: Himadri (Greater Himalaya, >7000m, includes Everest & Kangchenjunga), Himachal (Lesser Himalaya, 1000-4500m), and Siwaliks (outer foothills, youngest, 600-1500m). Formed by ongoing India-Eurasia collision since ~50 Ma."),
        ("🌾","Northern Plains","700,000 km². Built from Ganga-Indus-Brahmaputra alluvium deposited over millions of years. Sub-divided into Bhabar (gravel belt at the foothills), Terai (marshy belt), Bhangar (older, higher alluvium) and Khadar (newer, flood-renewed alluvium). India's most fertile, densely populated region."),
        ("⛰️","Peninsular Plateau","Oldest part of India — a stable Precambrian craton over 3 billion years old in places. Average elevation 600-900m, includes the Deccan Plateau (lava-capped basalt), Chota Nagpur Plateau (mineral-rich), and Malwa Plateau. Tilted, eroded, and rich in minerals like iron, coal, and bauxite."),
        ("🌊","Coastal Plains","Two distinct coasts: Western Coastal Plain (narrow, steep, backed by the Western Ghats — includes Konkan and Malabar coasts) and Eastern Coastal Plain (broad, deltaic, fed by major rivers draining into the Bay of Bengal — includes Coromandel and Northern Circars)."),
        ("🏝️","Islands","Andaman & Nicobar Islands (Bay of Bengal) — a volcanic/tectonic arc linked to the Sunda subduction zone, home to India's only active volcano. Lakshadweep (Arabian Sea) — low coral atolls built on a submerged plateau, geologically very different from the Andamans."),
    ]
    pc = st.columns(5)
    for i, (em, name, desc) in enumerate(physio):
        with pc[i]:
            st.markdown(f"""
            <div class='glass-card' style='padding:14px;text-align:center;'>
                <div style='font-size:1.6rem;margin-bottom:6px;'>{em}</div>
                <div style='color:#00d4ff;font-size:0.78rem;font-weight:600;margin-bottom:6px;'>{name}</div>
                <div style='color:#94a3b8;font-size:0.68rem;line-height:1.5;'>{desc}</div>
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
        show_wiki_photo(f"{rdata['name']} River", caption=f"{rdata['name']} River — reference photo (Wikipedia)")
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

    # Flow path map — origin to mouth for the selected river
    if "path" in rdata:
        st.markdown("<div class='section-heading'>RIVER COURSE — ORIGIN TO MOUTH</div>", unsafe_allow_html=True)
        path = rdata["path"]
        plats = [p[0] for p in path]
        plons = [p[1] for p in path]
        fig_river = go.Figure()
        fig_river.add_trace(go.Scattergeo(
            lat=plats, lon=plons, mode="lines",
            line=dict(color="#00d4ff", width=3.5),
            hovertemplate=f"<b>{rdata['name']}</b><extra></extra>", showlegend=False))
        fig_river.add_trace(go.Scattergeo(
            lat=[plats[0]], lon=[plons[0]], mode="markers+text",
            text=["Origin"], textposition="top right",
            marker=dict(size=11, color="#34d399", symbol="circle"),
            textfont=dict(color="#34d399", size=10),
            name="Origin", hovertemplate=f"<b>Origin:</b> {rdata['origin']}<extra></extra>"))
        fig_river.add_trace(go.Scattergeo(
            lat=[plats[-1]], lon=[plons[-1]], mode="markers+text",
            text=["Mouth"], textposition="bottom right",
            marker=dict(size=11, color="#f87171", symbol="diamond"),
            textfont=dict(color="#f87171", size=10),
            name="Mouth", hovertemplate=f"<b>Joins:</b> {rdata['joins']}<extra></extra>"))
        fig_river.update_geos(scope="asia", lonaxis_range=[65, 98], lataxis_range=[5, 36],
            showland=True, landcolor="#1a2a1a", showocean=True, oceancolor="#020817",
            showcountries=True, countrycolor="rgba(255,255,255,0.18)",
            showcoastlines=True, coastlinecolor="rgba(0,212,255,0.4)",
            bgcolor="rgba(0,0,0,0)", showframe=False)
        fig_river.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
            legend=dict(bgcolor="rgba(10,22,40,0.85)", font=dict(size=10, color="#f0e6d0"),
                        bordercolor="rgba(0,212,255,0.3)", borderwidth=1))
        st.plotly_chart(fig_river, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: SOIL EXPLORER
# ═══════════════════════════════════════════════════════════════
elif "Soil" in effective_page:
    st.markdown("<div class='section-heading'>SOIL EXPLORER — INDIA'S 7 MAJOR SOIL TYPES</div>", unsafe_allow_html=True)

    sel_s = st.selectbox("Select Soil Type", [s["name"] for s in SOILS])
    soil  = next(s for s in SOILS if s["name"] == sel_s)

    c1, c2 = st.columns([1, 1])
    with c1:
        show_wiki_photo(soil.get("wiki_term", soil["name"]), caption=f"{soil['name']} — reference photo (Wikipedia)")
        st.markdown(f"""
        <div class='glass-card' style='border-color:{soil["color"]}55;'>
            <div style='display:flex;align-items:center;gap:12px;margin-bottom:14px;'>
                <div style='width:40px;height:40px;border-radius:8px;background:{soil["color"]};
                    border:2px solid {soil["color"]}88;flex-shrink:0;display:flex;align-items:center;
                    justify-content:center;font-size:1.3rem;'>{soil["emoji"]}</div>
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
            legend=dict(font=dict(size=9, color="#f0e6d0"), bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=5,r=5,t=5,b=5), height=320)
        st.plotly_chart(fig_soil, use_container_width=True)

    # Soil distribution map of India — approximate regional spread by soil type
    st.markdown("<div class='section-heading'>SOIL DISTRIBUTION ACROSS INDIA</div>", unsafe_allow_html=True)
    soil_regions = {
        "Alluvial Soil":   [(28,77),(26,80),(25,83),(24,88),(27,94),(31,75)],
        "Black (Regur) Soil": [(19,74),(21,77),(17,79),(22,73)],
        "Red & Yellow Soil":  [(20,84),(22,85),(23,86),(15,78),(13,79)],
        "Laterite Soil":      [(10,76),(12,75.5),(25,91.5),(26,92.5),(11,76.5)],
        "Mountain Soil":      [(33,76),(31,78),(28,94),(27,93)],
        "Arid (Desert) Soil": [(27,71),(26,72),(28,73)],
        "Saline/Alkaline Soil": [(30,75),(29,76),(28,79)],
    }
    fig_smap = go.Figure()
    for s in SOILS:
        pts = soil_regions.get(s["name"], [])
        if pts:
            fig_smap.add_trace(go.Scattergeo(
                lat=[p[0] for p in pts], lon=[p[1] for p in pts],
                mode="markers", marker=dict(size=14, color=s["color"], opacity=0.75,
                                             line=dict(width=1, color="rgba(255,255,255,0.4)")),
                name=s["name"], hovertemplate=f"<b>{s['name']}</b><extra></extra>"))
    fig_smap.update_geos(scope="asia", lonaxis_range=[66, 98], lataxis_range=[6, 37],
        showland=True, landcolor="#1a2a1a", showocean=True, oceancolor="#020817",
        showcountries=True, countrycolor="rgba(255,255,255,0.18)",
        showcoastlines=True, coastlinecolor="rgba(0,212,255,0.4)",
        bgcolor="rgba(0,0,0,0)", showframe=False)
    fig_smap.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
        legend=dict(bgcolor="rgba(10,22,40,0.85)", font=dict(size=10, color="#f0e6d0"),
                    bordercolor="rgba(201,168,76,0.3)", borderwidth=1))
    st.plotly_chart(fig_smap, use_container_width=True)
    st.markdown("""
    <div class='glass-card' style='padding:10px 16px;'>
        <span style='color:#94a3b8;font-size:0.76rem;'>
        🗺️ Markers show approximate regional concentration, not exact boundaries — actual soil
        distribution varies at much finer scale based on local geology, rainfall, and drainage.
        </span>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE: ECONOMIC GEOLOGY
# ═══════════════════════════════════════════════════════════════
elif "Economic" in effective_page:
    st.markdown("<div class='section-heading'>ECONOMIC GEOLOGY — INDIA'S MINERAL WEALTH</div>", unsafe_allow_html=True)

    sel_min = st.selectbox("Select Mineral/Resource", list(ECONOMIC_MINERALS.keys()))
    emin    = ECONOMIC_MINERALS[sel_min]

    c1, c2 = st.columns([1, 1])
    with c1:
        show_wiki_photo(sel_min, caption=f"{sel_min} — reference photo (Wikipedia)")
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
            legend=dict(font=dict(size=9, color="#f0e6d0"), bgcolor="rgba(0,0,0,0)"),
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

    # Ocean currents — smooth curved paths with directional arrowheads
    def curve(lat0, lon0, lat1, lon1, bend, n=12):
        """Generate a smooth curved path between two points with a perpendicular bend."""
        pts = []
        dlat, dlon = lat1 - lat0, lon1 - lon0
        # perpendicular offset direction
        plat, plon = -dlon, dlat
        norm = (plat**2 + plon**2) ** 0.5 or 1
        plat, plon = plat / norm, plon / norm
        for i in range(n + 1):
            t = i / n
            curve_amt = bend * math.sin(math.pi * t)
            lat = lat0 + dlat * t + plat * curve_amt
            lon = lon0 + dlon * t + plon * curve_amt
            pts.append((lat, lon))
        return pts

    currents = [
        (8, 55, 14, 78, 3.5, "North Equatorial Current (Winter)", "#00d4ff"),
        (5, 80, 10, 98, -3.0, "South Equatorial Current", "#c084fc"),
        (15, 70, 23, 68, 2.5, "Somali Current (Summer)", "#f59e0b"),
        (8, 70, 4, 88, -2.5, "Equatorial Counter Current", "#34d399"),
    ]
    for lat0, lon0, lat1, lon1, bend, name_c, color_c in currents:
        path = curve(lat0, lon0, lat1, lon1, bend)
        lats_c = [p[0] for p in path]
        lons_c = [p[1] for p in path]
        fig_oc.add_trace(go.Scattergeo(
            lat=lats_c, lon=lons_c, mode="lines",
            line=dict(color=color_c, width=3, dash="solid"),
            name=name_c,
            hovertemplate=f"<b>{name_c}</b><extra></extra>"
        ))
        # Arrowhead marker at the end of the path showing flow direction
        bear_lat0, bear_lon0 = lats_c[-2], lons_c[-2]
        bear_lat1, bear_lon1 = lats_c[-1], lons_c[-1]
        angle = math.degrees(math.atan2(bear_lon1 - bear_lon0, bear_lat1 - bear_lat0))
        fig_oc.add_trace(go.Scattergeo(
            lat=[lats_c[-1]], lon=[lons_c[-1]], mode="markers",
            marker=dict(symbol="triangle-up", size=11, color=color_c,
                        angle=angle, line=dict(width=1, color="#0c1428")),
            showlegend=False, hoverinfo="skip"
        ))

    fig_oc.update_geos(scope="asia", lonaxis_range=[50, 110], lataxis_range=[-20, 35],
        showland=True, landcolor="#1a2a1a", showocean=True, oceancolor="#020817",
        showcountries=True, countrycolor="rgba(255,255,255,0.15)",
        showcoastlines=True, coastlinecolor="rgba(0,212,255,0.4)",
        bgcolor="rgba(0,0,0,0)", showframe=False)
    fig_oc.update_layout(height=440, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0e6d0"), margin=dict(l=0,r=0,t=0,b=0),
        legend=dict(bgcolor="rgba(10,22,40,0.85)", font=dict(size=10, color="#f0e6d0"),
                    bordercolor="rgba(0,212,255,0.3)", borderwidth=1))
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
    st.markdown("<div class='section-heading'>SEMESTER-WISE NOTES — B.Sc. EARTH SCIENCE (4-YEAR UG)</div>", unsafe_allow_html=True)

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

                    # Recommended books for this subject — link out via Google Books search
                    matching_books = [b for b in BOOKS if subject.lower() in b["subject"].lower()
                                       or b["subject"].split("–")[-1].strip().lower() in subject.lower()]
                    if matching_books:
                        st.markdown("<div style='color:#c9a84c;font-size:0.78rem;margin:10px 0 6px;font-weight:600;'>📚 Recommended Reading</div>", unsafe_allow_html=True)
                        for b in matching_books:
                            gbooks_url = "https://www.google.com/search?tbm=bks&q=" + \
                                         (b["title"] + " " + b["author"]).replace(" ", "+")
                            stars = "⭐" * b["stars"]
                            st.markdown(f"""
                            <a href="{gbooks_url}" target="_blank" style="text-decoration:none;">
                            <div class='glass-card' style='padding:10px 14px;margin-bottom:6px;
                                border-color:rgba(201,168,76,0.25);transition:border-color 0.2s;'>
                                <div style='color:#e8c96a;font-size:0.82rem;font-weight:600;'>{b["title"]} <span style='font-size:0.7rem;color:#8a7d65;'>↗</span></div>
                                <div style='color:#8a7d65;font-size:0.72rem;'>{b["author"]} · {stars}</div>
                            </div>
                            </a>""", unsafe_allow_html=True)

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

    quiz_sections = ["All Sections"] + sorted(set(q.get("section", "General") for q in QUIZ_QUESTIONS))
    sel_quiz_section = st.selectbox("Filter by Section", quiz_sections, key="quiz_section_filter")

    if sel_quiz_section == "All Sections":
        active_questions = QUIZ_QUESTIONS
    else:
        active_questions = [q for q in QUIZ_QUESTIONS if q.get("section", "General") == sel_quiz_section]

    total = len(active_questions)
    if (st.session_state.quiz_order is None
            or st.session_state.get("quiz_section_used") != sel_quiz_section
            or len(st.session_state.quiz_order) != total):
        st.session_state.quiz_order = random.sample(range(total), total)
        st.session_state.quiz_section_used = sel_quiz_section
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
elif "AI Assistant" in effective_page:
    st.markdown("<div class='section-heading'>AI GEO ASSISTANT — GEOLOGY Q&A</div>", unsafe_allow_html=True)

    gemini_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
    if gemini_key:
        st.markdown("""
        <div class='glass-card' style='padding:10px 14px;margin-bottom:12px;'>
            <span style='color:#94a3b8;font-size:0.78rem;'>
            🌐 Powered by Gemini — ask anything about geology or Earth science, not just the topics below.
            </span>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='glass-card' style='padding:10px 14px;margin-bottom:12px;'>
            <span style='color:#94a3b8;font-size:0.78rem;'>
            💡 Ask about: <span style='color:#00d4ff;'>geology · Himalaya · Deccan Traps · minerals · rocks · stratigraphy · metamorphism · earthquakes · volcanoes · rivers · soil · Gondwana · geological time</span>
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

    def local_knowledge_answer(user_q):
        uql = user_q.lower()
        for kw in AI_KNOWLEDGE_KEYS_SORTED:
            pattern = r'\b' + re.escape(kw) + r'\b' if " " not in kw else re.escape(kw)
            if re.search(pattern, uql):
                return AI_KNOWLEDGE[kw]
        if any(re.search(r'\b' + w + r'\b', uql) for w in ["hello","hi","hey","namaste"]):
            return "Hello! I'm GeoSphere AI 🌍 — your Earth Science assistant. Ask me about minerals, rocks, Indian geology, plate tectonics, earthquakes, soils, rivers, or the geological time scale!"
        elif "mineral" in uql:
            return AI_KNOWLEDGE["mineralogy"]
        elif "rock" in uql:
            return AI_KNOWLEDGE["rock cycle"]
        elif "india" in uql:
            return AI_KNOWLEDGE["plate tectonics"]
        return f"That's an interesting question about '{user_q}'! I don't have a specific answer for that exact phrasing yet — try asking about a specific topic like minerals, rocks, plate tectonics, earthquakes, volcanoes, rivers, soils, or geological time periods, and I'll do my best."

    def gemini_answer(user_q, api_key):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            system_instruction = (
                "You are GeoSphere AI, a friendly Earth Science assistant focused on geology, "
                "with special expertise in Indian geology (Himalayas, Deccan Traps, Indian rivers, "
                "minerals, soils, seismic zones). Answer clearly and concisely (3-6 sentences unless "
                "more detail is truly needed). If the question is unrelated to geology/Earth science, "
                "gently redirect back to geology topics."
            )
            payload = {
                "system_instruction": {"parts": [{"text": system_instruction}]},
                "contents": [{"role": "user", "parts": [{"text": user_q}]}],
                "generationConfig": {"temperature": 0.6, "maxOutputTokens": 500},
            }
            r = requests.post(url, json=payload, timeout=20)
            if r.status_code == 200:
                data = r.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return None
        except Exception:
            return None

    if ask and user_q.strip():
        resp = None
        if gemini_key:
            with st.spinner("Thinking..."):
                resp = gemini_answer(user_q, gemini_key)
        if not resp:
            resp = local_knowledge_answer(user_q)
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
    st.markdown("<div class='section-heading'>FIELD DIARY — A GEOLOGIST'S JOURNEY</div>", unsafe_allow_html=True)
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
            Platform ............ GeoSphere India<br>
            Purpose ............. Earth Science · Learning · Exploration<br>
            Sections ............ 20 Interactive Modules<br>
            Data Sources ........ GSI · USGS<br>
            Built With .......... Streamlit · Plotly · Python
            </div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("""
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
        "⭐ GSI (est. 1851) mapped India's entire mineral wealth — among the oldest geological surveys in the world.",
        "🌋 Basalt is the most common rock on Earth — and also on the Moon and Mars. It's universal.",
        "💎 A diamond takes over a billion years to form, then can reach the surface in mere hours via kimberlite eruption.",
        "🏔️ Mount Everest's summit limestone once sat at the bottom of an ancient ocean — the Tethys Sea.",
        "🌊 The Mariana Trench is so deep that Everest could fit inside it with over 2 km of water still above the peak.",
        "🪐 Earth's magnetic field has flipped polarity hundreds of times in its history — the last full reversal was ~780,000 years ago.",
        "🔥 Lightning can fuse sand into glass instantly, creating natural tubes called fulgurites.",
        "🌳 Some petrified wood retains its original cell structure in perfect detail, replaced atom by atom with silica.",
        "🧊 Glaciers can be blue because ice absorbs red light and scatters blue — the same reason the sky is blue.",
        "🌑 The Moon is slowly drifting away from Earth at about 3.8 cm per year — roughly the speed your fingernails grow.",
        "🦴 Most fossils form not from bone, but from minerals slowly replacing bone after burial — a process called permineralization.",
        "🌋 Yellowstone sits atop one of the largest active volcanic systems on Earth, fed by a deep mantle hotspot.",
        "💧 Nearly all of Earth's water is older than the Sun — formed in interstellar ice before our solar system existed.",
        "🪨 Granite takes millions of years to cool from magma — its large crystals are a direct record of that slow journey.",
        "🌍 If Earth's history were condensed into 24 hours, humans would appear in the last few seconds before midnight.",
        "🧂 Salt domes can trap oil and gas so effectively that geologists actively search for them during petroleum exploration.",
        "🌋 Pumice is the only rock that can float on water, thanks to its trapped volcanic gas bubbles.",
    ]
    if st.session_state.easter_count > 0:
        prev = st.session_state.get("last_gem_idx", -1)
        gi = random.randrange(len(gems))
        while gi == prev and len(gems) > 1:
            gi = random.randrange(len(gems))
        st.session_state.last_gem_idx = gi
        st.markdown(f"""
        <div class='glass-card' style='text-align:center;border-color:rgba(201,168,76,0.3);margin-top:14px;'>
            <div style='color:#c9a84c;font-size:0.95rem;line-height:1.9;
                font-family:Playfair Display,Georgia,serif;font-style:italic;'>{gems[gi]}</div>
        </div>""", unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
    <div style='text-align:center;color:#1e1a12;font-size:0.62rem;
        padding:20px 0 8px;line-height:2.2;font-family:Source Sans 3,sans-serif;'>
        GeoSphere India · Earth Science Platform<br>
        Lat: 25.2677°N · Lon: 82.9913°E<br>
        <span style='color:#c9a84c;opacity:0.4;'>Dedicated to Curiosity.</span>
    </div>""", unsafe_allow_html=True)
