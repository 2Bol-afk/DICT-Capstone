# Sadiang-Abay Crop Recommendation System

An offline-capable crop recommendation system for Filipino farmer cooperatives. Uses ML (scikit-learn) for crop prediction, a local LLM (Ollama/Qwen2.5) for AI explanations, and NLLB-200 for offline Tagalog translation.

## Run

```
cd app
py -m pip install fastapi uvicorn joblib pandas scikit-learn requests transformers torch sentencepiece firebase-admin psutil
py -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000

## Login
- **Admin:** username `admin`, password `admin` → redirects to admin dashboard
- **Farmer:** enter farmer name → redirects to farmer dashboard

## Stack
- Backend: Python / FastAPI / Firestore
- ML: scikit-learn RandomForest crop recommendation
- AI Explain: Ollama (qwen2.5:3b) — offline LLM
- Translation: facebook/nllb-200-distilled-600M — offline Tagalog
- Frontend: Vanilla HTML + Tailwind CSS
