---
title: NegotiAI
emoji: 🤝
colorFrom: yellow
colorTo: red
sdk: gradio
sdk_version: "6.19.0"
app_file: app.py
pinned: false
---
# NegotiAI — Adaptive AI Negotiation & Sales Preparation Platform

NegotiAI helps users **prepare before** important real-world negotiations —
internship/salary offers, product sales, and real estate/property deals.

It does not negotiate on your behalf. Think of it like a flight simulator:
you prepare, practice, and get scored before the real conversation.

Built for the Decoding Data Science (DDS) Academy AI Application Building
Challenge.

## Features

| Feature | Status |
| --- | --- |
| **Prepare** — strategy, objections, responses, walk-away point, confidence tips | ✅ Working |
| **Practice** — live negotiation against an AI persona (recruiter, customer, or property seller), with full conversation memory | ✅ Working |
| **Feedback** — scored visual scorecard (confidence, persuasion, objection handling, communication, emotional control, closing) generated from your actual Practice conversation | ✅ Working |

## Tech Stack

- **Language:** Python
- **UI + Backend:** [Gradio](https://gradio.app) (`gr.Blocks` + `gr.Tabs`, single Python app, no separate frontend/backend)
- **AI:** Google Gemini API (`gemini-2.5-flash`) via the official `google-genai` SDK
- **Secrets:** `.env` locally / Hugging Face Secrets when deployed (never committed)
- **Deployment:** Hugging Face Spaces

## Project Structure

- `app.py` — Gradio UI (3 tabs) + all app logic
- `prompts.py` — All AI system prompts, kept separate from app logic
- `requirements.txt` — Python dependencies
- `.env.example` — Template for your API key (copy to `.env`, never commit `.env`)
- `.gitignore`

## Setup (Windows 10, Python 3.14.5)

1. **Get a free Gemini API key:** [Google AI Studio](https://aistudio.google.com) → "Get API key."
2. **Create and activate a virtual environment:** `py -3.14 -m venv .venv` then `.venv\Scripts\activate`
3. **Install dependencies:** `pip install -r requirements.txt`
4. **Add your API key:** copy `.env.example` to `.env`, then set `GEMINI_API_KEY=your_real_key_here`
5. **Run the app:** `python app.py`, then open the local URL shown in the terminal (usually `http://127.0.0.1:7860`). Three tabs: **Prepare**, **Practice**, **Feedback**.

## How to use it

1. **Prepare** — pick a scenario, describe your situation, get a structured strategy.
2. **Practice** — pick a scenario, click "Start Practice Session," then negotiate against the AI persona in real time.
3. **Feedback** — after a Practice conversation, click "Get Feedback Report" to get a scored scorecard based on what you actually said.

## Roadmap

- [x] Environment setup + Preparation Mode
- [x] Practice Mode (multi-turn AI persona negotiation)
- [x] Feedback Report (structured scoring + visual scorecard)
- [ ] Deploy to Hugging Face Spaces (in progress)
- [ ] Re-add Reset/Clear button (lost when migrating to `gr.Blocks`)
- [ ] Demo video + slides
- [ ] Final submission

## Disclaimer

NegotiAI is a preparation and coaching tool. It does not replace human judgment or professional/legal advice during real negotiations.