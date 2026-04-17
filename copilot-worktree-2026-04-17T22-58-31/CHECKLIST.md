# Deployment Checklist

Complete this checklist before running the application.

## ✅ Files Created

- [x] **Core Application Files**
  - [x] `main.py` — FastAPI application (2 endpoints + health check)
  - [x] `schemas.py` — Pydantic models (HouseFeatures, etc.)
  - [x] `llm_chain.py` — LLM orchestration (Stage 1 & Stage 2)
  - [x] `predictor.py` — ML model loader and predict()
  - [x] `prompts.py` — Versioned LLM prompts (V1 & V2)
  - [x] `__init__.py` — Python package initialization

- [x] **Frontend**
  - [x] `streamlit_app.py` — Web UI (4-step flow)

- [x] **Training**
  - [x] `ml_pipeline.ipynb` — 8-section Jupyter notebook

- [x] **Configuration**
  - [x] `requirements.txt` — Pinned dependencies
  - [x] `Dockerfile` — Docker build instructions
  - [x] `.env.template` — Environment variable template
  - [x] `.gitignore` — Prevent committing secrets

- [x] **Documentation**
  - [x] `README.md` — Quick start and API reference
  - [x] `IMPLEMENTATION_GUIDE.md` — Deep dive into architecture
  - [x] `PROJECT_SUMMARY.md` — Overview and examples
  - [x] `ARCHITECTURE_DIAGRAM.txt` — Visual system architecture
  - [x] `CHECKLIST.md` — This file

## 📋 Pre-Deployment Checks

### 1. Environment Setup

- [ ] Python 3.11+ installed: `python --version`
- [ ] pip available: `pip --version`
- [ ] Git available: `git --version`
- [ ] Docker installed (optional): `docker --version`

### 2. API Keys and Secrets

- [ ] Created `.env` file: `cp .env.template .env`
- [ ] Added GEMINI_API_KEY to `.env`
  - [ ] Get key from: https://makersuite.google.com/app/apikeys
  - [ ] Key starts with `AIza...`
  - [ ] Do NOT commit `.env` file

### 3. Dependencies

- [ ] Installed requirements: `pip install -r requirements.txt`
- [ ] Verify key packages:
  - [ ] `pip show fastapi`
  - [ ] `pip show scikit-learn`
  - [ ] `pip show streamlit`
  - [ ] `pip show google-generativeai`
  - [ ] `pip show pydantic`

### 4. ML Model Generation

- [ ] Downloaded Ames Housing dataset (train.csv)
  - [ ] From: https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques
  - [ ] Placed in: `notebooks/train.csv` (or same dir as ml_pipeline.ipynb)
- [ ] Ran `jupyter notebook notebooks/ml_pipeline.ipynb`
  - [ ] Section 1-7 completed without errors
  - [ ] Generated files exist:
    - [ ] `app/model/pipeline.joblib` (10-50 MB)
    - [ ] `app/model/train_stats.json` (< 1 KB)

### 5. API Backend

- [ ] Started FastAPI server: `uvicorn main:app --host 0.0.0.0 --port 8000`
- [ ] Server logs show: `Uvicorn running on http://0.0.0.0:8000`
- [ ] Health check passes: `curl http://localhost:8000/health`
  - [ ] Response: `{"status":"ok"}`
- [ ] OpenAPI docs accessible: `curl http://localhost:8000/docs`
  - [ ] Response includes JSON schema

### 6. Frontend

- [ ] Started Streamlit: `streamlit run streamlit_app.py`
- [ ] Browser opened to: `http://localhost:8501`
- [ ] UI loads without errors
- [ ] Text area is visible
- [ ] "Extract Features" button is clickable

### 7. End-to-End Testing

- [ ] **Test 1: Feature Extraction**
  - [ ] Enter query: "3 bedroom house, 2 full baths, good neighborhood"
  - [ ] Click "Extract Features"
  - [ ] Extracted fields show (green checkmarks)
  - [ ] Missing fields show (input boxes)
  - [ ] Confidence is medium or higher

- [ ] **Test 2: Manual Fill-In**
  - [ ] Fill in missing fields manually
  - [ ] Click "Predict Price"
  - [ ] Wait for prediction
  - [ ] Price displayed (e.g., "$250,000")
  - [ ] Interpretation shows below price

- [ ] **Test 3: Minimal Input**
  - [ ] Enter: "3 bedroom house"
  - [ ] Click "Extract Features"
  - [ ] Most fields are missing
  - [ ] Confidence is "low"
  - [ ] Needs clarification = true

- [ ] **Test 4: Error Recovery**
  - [ ] Stop FastAPI server
  - [ ] Try to extract in Streamlit
  - [ ] Error message shows: "Cannot connect to backend"
  - [ ] Restart FastAPI
  - [ ] Try again → works

## 🐳 Docker Deployment (Optional)

### Build Docker Image

- [ ] Run: `docker build -t real-estate-agent:v1 .`
- [ ] Output shows: `Successfully tagged real-estate-agent:v1`
- [ ] Image size is reasonable: `docker images real-estate-agent:v1`

### Run Docker Container

- [ ] Run: `docker run -p 8000:8000 --env-file .env real-estate-agent:v1`
- [ ] Container starts: `Uvicorn running on http://0.0.0.0:8000`
- [ ] Health check works: `curl http://localhost:8000/health`
- [ ] Stop container: `Ctrl+C`

### Push to Registry (Optional)

- [ ] Tag image: `docker tag real-estate-agent:v1 my-registry/real-estate-agent:v1`
- [ ] Push: `docker push my-registry/real-estate-agent:v1`
- [ ] Verify in registry

## 📊 Verification Test Cases

Run these test queries and verify behavior:

### Test Case 1: High Information Query

```
Query: "Luxury 4-bedroom, 3-full-bath house with 4000 sqft living area,
        2000 sqft basement, 3-car garage, built in 2020, excellent condition
        (9/10 quality), located in an upscale neighborhood"

Expected:
  - Extracted fields: 9/10
  - Confidence: HIGH
  - Predicted price: $400,000-500,000
  - Interpretation: Should mention luxury, excellent quality, above-market
```

### Test Case 2: Minimal Information Query

```
Query: "House"

Expected:
  - Extracted fields: 0/10
  - Confidence: LOW
  - Needs clarification: TRUE
  - Missing fields: All 10 fields
  - Interpretation: Should ask for more details
```

### Test Case 3: Ambiguous Query

```
Query: "Nice house, good size, decent quality, somewhere in the Midwest"

Expected:
  - Extracted fields: 2-4/10
  - Confidence: MEDIUM
  - Missing fields: 6-8 fields
  - Predicted price: Average (around median)
```

## 🔍 Debugging Tips

If something doesn't work:

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run: `pip install -r requirements.txt` |
| `GEMINI_API_KEY not found` | Check `.env` file exists and is in project root |
| `Pipeline not found` | Run ml_pipeline.ipynb Section 7 |
| `Cannot connect to backend` | Start FastAPI: `uvicorn main:app --host 0.0.0.0 --port 8000` |
| `Connection refused: 8501` | Start Streamlit: `streamlit run streamlit_app.py` |
| `JSON parse error in logs` | Check Gemini API key is valid |
| `Port already in use` | Kill process: `lsof -ti:8000` or change port |

## 📝 Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.template .env
# Edit .env with your GEMINI_API_KEY

# Run training notebook
jupyter notebook notebooks/ml_pipeline.ipynb

# Start FastAPI backend (Terminal 1)
uvicorn main:app --host 0.0.0.0 --port 8000

# Start Streamlit frontend (Terminal 2)
streamlit run streamlit_app.py

# Docker
docker build -t real-estate-agent:v1 .
docker run -p 8000:8000 --env-file .env real-estate-agent:v1

# Test API
curl http://localhost:8000/health
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"query": "3 bedroom house"}'

# Stop all
Ctrl+C in both terminals
```

## ✅ Final Sign-Off

- [ ] All files created and in correct locations
- [ ] All dependencies installed
- [ ] .env file configured with API key
- [ ] ML model generated (pipeline.joblib + stats.json)
- [ ] FastAPI backend starts without errors
- [ ] Streamlit frontend launches without errors
- [ ] End-to-end test passes (query → extraction → prediction → interpretation)
- [ ] Error handling works (graceful degradation)
- [ ] Documentation is complete and clear

## 🚀 Ready to Deploy!

Once all checkboxes are complete, your Real Estate Agent application is ready to use!

Next steps:
1. Share the project with teammates
2. Explain the architecture using ARCHITECTURE_DIAGRAM.txt
3. Have teammates run through deployment checklist
4. Start building extensions (Level 1-5 in PROJECT_SUMMARY.md)

## 📞 Support

If you encounter issues:
1. Check TROUBLESHOOTING section in README.md
2. Review IMPLEMENTATION_GUIDE.md for detailed explanations
3. Check logs in terminal for error messages
4. Verify all files exist with correct content
5. Test individual components (API, ML model, LLM)

Good luck! 🎉
