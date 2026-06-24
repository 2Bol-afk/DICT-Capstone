# AI Agents

This project was built with Claude Code (claude-sonnet-4-6).

## Agent Instructions
- Backend: FastAPI app in `main.py`, DB functions in `db.py`
- Frontend: Static HTML in `frontend/` served by FastAPI at root
- Run server: `py -m uvicorn main:app --reload`
- Models: `crop_model.pkl` (sklearn), Ollama qwen2.5:3b, NLLB-200 in `model/huggingface/`
- DB: SQLite at `readings.db`
