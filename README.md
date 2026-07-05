# GeoSphere India 🌍

An interactive Earth Science intelligence platform built for B.Sc. Earth Science students.

## Setup

**Streamlit Cloud:**
1. Upload all files maintaining the `pages/` folder structure
2. Set **Main file path** to `app.py` in Streamlit Cloud settings
3. Add `GEMINI_API_KEY` in Secrets for AI assistant

**Local:**
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Structure
```
app.py          ← Mission Control (home page)
utils.py        ← All shared data, CSS, helpers
pages/          ← 20 individual section pages
audio.mp3       ← Achievement mode audio
requirements.txt
```

## Features
- 20 interactive geology modules
- Live USGS earthquake data
- Wikipedia photos for minerals, rocks, soils, volcanoes
- Google Gemini AI assistant (add API key to secrets)
- 3D mineral crystal viewer (Three.js)
- GSI mineral deposit map
- BHU NEP syllabus aligned (all 8 semesters)
- Achievement/Rare mode easter egg
