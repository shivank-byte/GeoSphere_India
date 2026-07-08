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
audio.mp3       ← Ambient / Achievement-mode theme (toggle in sidebar, auto-plays on achievement unlock)
requirements.txt
```

## Features
- 20 interactive geology modules, each with a Wikipedia hero image
- Live USGS earthquake feed (cached, rolling time window — never goes stale) + live sidebar seismic index
- Wikipedia photos for minerals, rocks, soils, volcanoes, tectonic events, index fossils
- Google Gemini AI assistant with session memory + suggested-question chips (add API key to secrets)
- 3D mineral crystal viewer (Three.js)
- GSI mineral deposit map + satellite/overview toggle + schematic crustal cross-sections per province
- Animated subduction cross-section, Himalayan thrust cross-section (MFT/MBT/MCT/STDS)
- Field Identification Guide, Mohs-to-everyday-object hardness comparison
- Rock Explorer hand-specimen vs thin-section comparison + field location maps
- Volcano VEI scale + Barren Island deep dive
- Geo Quiz with Rapid Fire mode + auto-graded difficulty levels
- Flashcards with spaced repetition
- BHU NEP syllabus aligned (all 8 semesters) + key terms + likely exam questions
- Achievement / Rare mode hidden feature (with its own theme song)
