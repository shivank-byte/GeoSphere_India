# GeoSphere India — AI Assistant
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

st.set_page_config(page_title="AI Assistant — GeoSphere India", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")
init_session_state()
inject_css()
render_sidebar()

# Home button
if st.button("⬅ Home", key="home_btn"):
    st.switch_page("app.py")

render_hero_image("Robot", "AI Geo Assistant", "ASK ANYTHING ABOUT EARTH SCIENCE")

st.markdown("<div class='section-heading'>AI GEO ASSISTANT — GEOLOGY Q&A</div>", unsafe_allow_html=True)

gemini_key = ""
try:
    gemini_key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    pass

if gemini_key:
    st.markdown("""
    <div class='glass-card' style='padding:10px 14px;margin-bottom:12px;border-color:rgba(16,185,129,0.3);'>
        <span style='color:#10b981;font-size:0.78rem;'>
        🟢 Gemini connected — ask anything about geology or Earth science.
        </span>
    </div>""", unsafe_allow_html=True)
else:
    st.markdown("""
    <div class='glass-card' style='padding:10px 14px;margin-bottom:12px;'>
        <span style='color:#94a3b8;font-size:0.78rem;'>
        💡 Ask about: <span style='color:#00d4ff;'>geology · Himalaya · Deccan Traps · minerals · rocks · stratigraphy · metamorphism · earthquakes · volcanoes · rivers · soil · Gondwana · geological time</span>
        </span>
    </div>""", unsafe_allow_html=True)

# Display chat history
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class='chat-label-user'>YOU</div>
        <div class='chat-bubble-user'>{msg["text"]}</div>
        """, unsafe_allow_html=True)
    else:
        _src = msg.get("source", "local")
        _badge = ("<span style='background:rgba(16,185,129,0.15);color:#10b981;font-size:0.6rem;"
                   "padding:1px 7px;border-radius:8px;margin-left:6px;'>🟢 Gemini · high confidence</span>"
                   if _src == "gemini" else
                   "<span style='background:rgba(245,158,11,0.15);color:#f59e0b;font-size:0.6rem;"
                   "padding:1px 7px;border-radius:8px;margin-left:6px;'>📚 Local knowledge base</span>")
        st.markdown(f"""
        <div class='chat-label-ai'>🌍 GEOSPHERE AI{_badge}</div>
        <div class='chat-bubble-ai'>{msg["text"]}</div>
        """, unsafe_allow_html=True)

if not st.session_state.chat_history:
    st.markdown("""
    <div style='text-align:center;padding:40px;color:#334155;'>
        <div style='font-size:3rem;margin-bottom:10px;'>🌍</div>
        <div style='font-family:Orbitron;font-size:0.85rem;letter-spacing:2px;color:#475569;'>
        ASK YOUR FIRST QUESTION
        </div>
    </div>""", unsafe_allow_html=True)

user_q = st.text_input("Ask GeoSphere AI:", placeholder="Tell me about the Himalayas...", key="ai_inp")
ca1, ca2 = st.columns([1, 4])
with ca1:
    ask = st.button("🚀 Ask")
with ca2:
    if st.button("🗑️ Clear"):
        st.session_state.chat_history = []
        st.rerun()

def local_knowledge_answer(q):
    ql = q.lower().strip()
    for kw in AI_KNOWLEDGE_KEYS_SORTED:
        pattern = r'\b' + re.escape(kw) + r'\b' if " " not in kw else re.escape(kw)
        if re.search(pattern, ql):
            return AI_KNOWLEDGE[kw]
    hits = []
    for sem, subjects in NOTES.items():
        for subj, points in subjects.items():
            for pt in points:
                pt_lower = pt.lower()
                words = [w for w in re.findall(r'\w+', ql) if len(w) > 4]
                if words and sum(1 for w in words if w in pt_lower) >= 2:
                    hits.append((sem, subj, pt))
    if hits:
        sem, subj, pt = hits[0]
        clean = re.sub(r'\*\*(.*?)\*\*', r'\1', pt)
        return f"[{sem} — {subj}]\n\n{clean}"
    if any(w in ql for w in ["hello","hi","hey","namaste","hlo"]):
        return "Hello! I'm GeoSphere AI 🌍 — your Earth Science assistant. Ask me anything about geology, mineralogy, petrology, stratigraphy, structural geology, Indian geology, geomorphology, or Earth science!"
    cats = [
        (["himalaya","himalayas","mountain","everest","mcт","mbt","mft"], "himalaya"),
        (["mineral","mineralogy","crystal","hardness","mohs","streak","lustre","luster","cleavage"], "mineralogy"),
        (["rock","igneous","sedimentary","metamorphic","basalt","granite","schist","gneiss","petrology"], "rock cycle"),
        (["plate","tectonic","subduction","convergent","divergent","transform","pangaea","gondwana"], "plate tectonics"),
        (["earthquake","seismic","magnitude","richter","fault","epicenter","p wave","s wave"], "seismic"),
        (["volcano","eruption","lava","magma","pyroclastic","stratovolcano","caldera","deccan"], "volcanic eruption"),
        (["fossil","palaeontology","paleontology","stratigraphy","permian","cretaceous","jurassic"], "paleontology"),
        (["soil","alluvial","laterite","black soil","regur","red soil","weathering"], "alluvial"),
        (["river","ganga","brahmaputra","watershed","drainage","basin","delta"], "watershed"),
        (["ocean","marine","oceanography","current","monsoon","sea","bay of bengal","arabian sea"], "ocean trench"),
        (["time scale","geological time","eon","era","period","epoch","precambrian","cambrian"], "geological time scale"),
        (["diamond","kimberlite","gold","copper","iron ore","bauxite","chromite","zinc","coal"], "diamond"),
        (["gneiss","schist","metamorphism","barrovian","facies","foliation"], "gneiss"),
        (["sandstone","limestone","shale","conglomerate","sediment","clastic","carbonate"], "limestone"),
    ]
    for keywords, fallback_key in cats:
        if any(k in ql for k in keywords):
            if fallback_key in AI_KNOWLEDGE:
                return AI_KNOWLEDGE[fallback_key]
    return (f"Great question about '{q}'! For unlimited geology Q&A, add GEMINI_API_KEY to Streamlit secrets. "
            "Try asking about: Himalayas, Deccan Traps, minerals, rocks, plate tectonics, earthquakes, "
            "volcanoes, fossils, stratigraphy, Indian rivers, soils, or the geological time scale.")

if ask and user_q.strip():
    st.session_state.chat_history.append({"role": "user", "text": user_q})
    if gemini_key:
        # Stream Gemini response — collect into string first, then store
        resp_placeholder = st.empty()
        full_resp = ""
        with resp_placeholder.container():
            st.markdown("<div class='chat-label-ai'>🌍 GEOSPHERE AI</div>", unsafe_allow_html=True)
            stream_box = st.empty()
            _prior_history = st.session_state.chat_history[:-1]  # exclude the message just appended
            for chunk in gemini_stream(user_q, gemini_key, history=_prior_history):
                full_resp += chunk
                stream_box.markdown(f"<div class='chat-bubble-ai'>{full_resp}▌</div>", unsafe_allow_html=True)
            stream_box.markdown(f"<div class='chat-bubble-ai'>{full_resp}</div>", unsafe_allow_html=True)
        st.session_state.chat_history.append({"role": "ai", "text": full_resp or local_knowledge_answer(user_q),
                                               "source": "gemini" if full_resp else "local"})
    else:
        resp = local_knowledge_answer(user_q)
        st.session_state.chat_history.append({"role": "ai", "text": resp, "source": "local"})
    st.rerun()


# Suggested questions as clickable chips
_suggested = [
    "Tell me about the Himalayas",
    "What are the Deccan Traps?",
    "Explain plate tectonics in India",
    "What is the Mohs hardness scale?",
    "How do earthquakes occur?",
    "What is metamorphism?",
    "Tell me about Indian rivers",
    "What is the geological time scale?",
]
st.markdown("<div style='margin-bottom:12px;'>", unsafe_allow_html=True)
_chip_cols = st.columns(4)
for ci, sq in enumerate(_suggested):
    with _chip_cols[ci % 4]:
        if st.button(sq, key=f"chip_{ci}", use_container_width=True):
            st.session_state.chat_history.append({"role":"user","text":sq})
            _gemini_key2 = ""
            try:
                _gemini_key2 = st.secrets.get("GEMINI_API_KEY","")
            except Exception:
                pass
            if _gemini_key2:
                _full = ""
                _prior = st.session_state.chat_history[:-1]
                for _chunk in gemini_stream(sq, _gemini_key2, history=_prior):
                    _full += _chunk
                resp = _full or local_knowledge_answer(sq)
                src = "gemini" if _full else "local"
            else:
                resp = local_knowledge_answer(sq)
                src = "local"
            st.session_state.chat_history.append({"role":"ai","text":resp,"source":src})
            st.rerun()
st.markdown("</div>", unsafe_allow_html=True)
