# Every Complaint Heard (PS-07, Metro Operations)

Offline-first complaint triage for Gujarat Metro station controllers.

## What it does

- Sorts complaints (Gujarati, Hindi, English, Gujlish) into Safety, Cleanliness, Fare, Lifts, Staff Behaviour
- Urgency score (0-100), highest first
- Draft replies in the complainant's language
- Local SQLite storage; sync button pushes pending items when network is back

## Run

pip install -r requirements.txt
streamlit run app.py
Optional AI: install Ollama and run `ollama pull gemma3:4b` (works fully offline).

## Offline design

Keyword + script-based triage and templates need no network. Gemma runs locally via Ollama
(fallback classifier for unseen wording, plus reply improvement). Without Ollama, the app still works.

## Honest notes

- Sync is simulated (no real server yet).
- Sample complaints, keyword lists and reply templates are my own synthetic data.
- Code was written with AI assistance (Claude).

## PPP idea

Metro owns the data; a private partner maintains the app per station subscription.
