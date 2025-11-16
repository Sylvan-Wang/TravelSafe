# TravelSafe
🧭 TravelSafe
A calm, smart safety layer for solo travelers and international students

(Hackathon Prototype · Built with JS / FastAPI / Gemma · USC Annenberg)

📌 Overview

TravelSafe is a lightweight safety-oriented travel assistant that combines:

Live country information (population, region, languages, currencies)

A curated safety snapshot (crime, politics, health, natural hazards)

A practical crisis playbook for unexpected situations

A USC/OIS integration stub for university-specific safety resources

The goal is to provide calm, clear, non-alarmist guidance for solo travelers—especially international students—while keeping the tool simple, fast, and offline-friendly when needed.

This project was built as part of a USC hackathon and research exploration in Applied Communication, UX, and AI-assisted safety design.

🎯 Motivation

International travel usually begins with fun planning:
destinations, attractions, restaurants, itineraries.

However, first-time or solo travelers often lack:

A safety layer on top of their planning

Practical risk orientation

Easy access to emergency contacts

A mental model for what to do if something goes wrong

TravelSafe fills this gap with a structured, low-stress safety brief, combining calm UX writing and simple risk modeling.

🛠️ Features
✅ 1. Country Search

Search any country and instantly receive:

live demographic/meta info

a clean orientation to region + subregion

curated safety data matched by country code

✅ 2. Country Profile (NLP-style templates)

A template-based micro-NLP layer generates:

a country-level introduction

region explanation

capital, population, languages, currencies

This ensures consistency, clarity, and a warm, educational tone.

✅ 3. Safety Snapshot

A simple, visual, 1–5 scale showing:

Crime & petty theft

Political stability

Health infrastructure

Natural hazard exposure

Text summaries are generated dynamically from data.

✅ 4. Crisis / Safe Mode

A calm “What to do if something goes wrong” section including:

lost passport

medical emergencies

protests or disruptions

general solo-travel rules

Q&A box for quick guidance

✅ 5. USC Support Layer (Demo Stub)

A dedicated module showing how TravelSafe can plug into
USC OIS (Office of International Services) or USC safety infrastructure.

Contains placeholder fields for:

USC emergency number

Student health insurance

Pre-approved medical providers abroad

Embassy/consulate info

Region-specific advisories

Traveler registration (e.g., STEP)

This can be wired to real OIS/USC APIs in the future.

🧩 Architecture
Frontend

Vanilla HTML/CSS/JS

Calm, minimal UI

Modular functions for rendering:

buildCountryProfileText

buildSafetySnapshotText

renderCountryInfo()

renderUSCSupportDemo()

Backend (optional)

FastAPI backend used in extended version

Gemma 3 model for possible NLP enhancements

Whisper integration planned for offline voice inputs

Data

REST Countries API

Custom-curated safety dataset

USC demo dataset (static stub)

📂 File Structure (Simplified)
/project-root
│── index.html
│── tn.js                 # main logic
│── styles.css
│── country_safety.json   # custom risk preset
│── usc_demo_data.js      # USC support stub
│── README.md
│── /assets               # icons, demo screenshots

🚀 Getting Started
1. Clone or download
git clone https://github.com/xxxx/TravelSafe

2. Open in browser

No build process required:

open index.html

3. Search a country

Try: Italy, France, Japan, China

You'll instantly see:

Country profile

Safety snapshot

Crisis mode

USC support demo panel

🧪 Demo Scenarios
Scenario 1 — “I want to understand a country quickly”

Search “Italy” →
See profile, risk snapshot, region, crisis checklist.

Scenario 2 — “I lost my passport”

Go to Crisis Mode → "lost passport" preset.

Scenario 3 — “I’m a USC student traveling abroad”

Open the USC support layer card.

🔮 Future Development
1️⃣ USC + OIS Integration

Real-time emergency updates

Auto-loaded student insurance info

Push-based risk alerts

Tied to USC international travel systems

2️⃣ AI Safety Assistant

Use Claude / Gemini / Gemma to power:

calm safety Q&A

micro-guidance during emergencies

personalized checklists

3️⃣ International Travel Data Expansion

Integrate:

WHO / UN datasets

Weather & natural hazard feeds

US/UK/CAN government advisories

4️⃣ Offline Crisis Mode

For unstable networks during emergencies.

🎨 USC Brand Readiness (for embedding into OIS portal)
USC Colors

Cardinal — #990000

Gold — #FFCC00

USC Typography

Adobe Caslon Pro (serif)

Lato / Inter (web)

Style Goals

calm

trustworthy

minimal motion

non-alarmist

A USC-themed CSS variant can be added within 30–40 minutes.

🙏 Acknowledgements

Built by Sylvan
USC Annenberg School for Communication & Journalism
Applied Communication Research Program

Thanks to:
Colleagues, mentors, and USC international support teams who inspired this work.
