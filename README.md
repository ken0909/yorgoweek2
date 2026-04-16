## System Architecture

```
User Input (Natural Language)
         ↓
Stage 1 LLM (Gemini) — Extract Features → JSON
         ↓
ML Model (sklearn) — Predict SalePrice
         ↓
Stage 2 LLM (Gemini) — Interpret Prediction
         ↓
Streamlit UI — Display Results
```

## Key Features

- **Two-Stage LLM Pipeline**: Natural language extraction → structured features
- **ML Prediction**: Trained on Ames Housing dataset (sklearn pipeline)
- **Docker-Ready**: Containerized FastAPI backend
- **Streamlit Frontend**: Interactive web UI
- **Error Handling**: Graceful degradation on API failures
- **Data Leakage Prevention**: Strict separation of train/val/test splits
