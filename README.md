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

NegotiAI helps users prepare before important real-world negotiations, including internship or salary offers, product sales, and real estate or property deals.

It does not negotiate on the user's behalf. It works like a flight simulator for negotiation: users prepare, practise, and receive feedback before the real conversation.

Built for the Decoding Data Science Academy Build AI Application Challenge.

## Live App

Hugging Face Spaces:  
https://huggingface.co/spaces/vishnu220506/NegotiAI

## GitHub Repository

https://github.com/vishnu220506/NegotiAI

## Features

| Feature | Status |
| --- | --- |
| Prepare Mode — strategy, objections, responses, walk-away point, confidence tips | Working |
| Practice Mode — live negotiation against an AI persona with conversation memory | Working |
| Feedback Mode — scored visual scorecard based on the user's practice conversation | Working |

## MVP Scenarios

1. Internship / Salary Negotiation
2. Product Sales Negotiation
3. Real Estate / Property Investment Negotiation

## Tech Stack

- Language: Python
- UI and backend: Gradio using `gr.Blocks` and `gr.Tabs`
- AI model: Google Gemini API using `gemini-2.5-flash-lite`
- SDK: `google-genai`
- Secrets: `.env` locally and Hugging Face Secrets when deployed
- Deployment: Hugging Face Spaces
- Version control: GitHub

## Project Structure

- `app.py` — Gradio UI, Prepare Mode, Practice Mode, Feedback Mode, API calls, and error handling
- `prompts.py` — system prompts, practice personas, and feedback scoring prompt
- `requirements.txt` — Python dependencies
- `.env.example` — safe template for the Gemini API key
- `.gitignore` — prevents secrets and virtual environment files from being committed

## Setup

1. Create a Gemini API key from Google AI Studio.
2. Create a virtual environment:

```powershell
py -3.14 -m venv .venv