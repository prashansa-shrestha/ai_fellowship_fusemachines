# Week 15 / 16 — Applied AI & Engineering AI Systems

Deliverables under this folder:

- **[`task1_ai_assistant/`](task1_ai_assistant/README.md)** — Course assistant with Gemini,
  RAG (FAISS), Ollama local fallback, **and a W16 multi-agent agentic loop**
  (Researcher + Verifier, evidence notebook, eval harness). See that README for the
  architecture diagram and assessment write-up (context engineering, agentic pattern,
  evaluation).

- **[`task2_productionize_router/`](task2_productionize_router/README.md)** — W15 Task 2:
  productionized Week 13 LSTM AG_NEWS classifier (ONNX, FastAPI, Streamlit).

Shared `.env` (Gemini API key) at this level.

## Quick start (agentic assistant)

```bash
# .env in this directory:
GEMINI_API_KEY=your_key_here

cd task1_ai_assistant
pip install -r requirements.txt
python ingest.py
uvicorn app.main:app --reload --port 8000

# Evaluation harness (writes eval/results/report.md)
python -m eval.harness
```
