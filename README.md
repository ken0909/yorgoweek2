# Real Estate Agent: AI-Powered House Price Prediction

A bootcamp project combining a **two-stage LLM pipeline** with **machine learning** to predict house prices from natural language descriptions.

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

## Quick Start

### 1. Setup

```bash
# Clone the repository
git clone <repo-url>
cd real-estate-agent

# Install dependencies
pip install -r requirements.txt

# Create .env file with your Gemini API key
cp .env.template .env
# Edit .env and add your GEMINI_API_KEY (get from https://makersuite.google.com/app/apikeys)
```

### 2. Train the ML Model

```bash
# Run the Jupyter notebook to train the model
jupyter notebook notebooks/ml_pipeline.ipynb

# This generates:
#   - app/model/pipeline.joblib (serialized ML model)
#   - app/model/train_stats.json (training statistics)
```

### 3. Run the Backend (FastAPI)

```bash
# Start the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000

# Visit http://localhost:8000/docs for the API documentation
```

### 4. Run the Frontend (Streamlit)

```bash
# In another terminal, start the Streamlit app
streamlit run streamlit_app.py

# This will open http://localhost:8501 in your browser
```

### 5. Using Docker

```bash
# Build the Docker image
docker build -t real-estate-agent:v1 .

# Run the container
docker run -p 8000:8000 --env-file .env real-estate-agent:v1

# The API will be available at http://localhost:8000
```

## Project Structure

```
real-estate-agent/
├── notebooks/
│   └── ml_pipeline.ipynb          # EDA, model training, prompt testing
├── app/
│   ├── main.py                    # FastAPI application
│   ├── schemas.py                 # Pydantic models (contracts)
│   ├── predictor.py               # ML model loader + predict()
│   ├── llm_chain.py               # Stage 1 & Stage 2 LLM orchestration
│   ├── prompts.py                 # Versioned prompt templates
│   ├── __init__.py
│   └── model/
│       ├── pipeline.joblib        # Serialized sklearn pipeline
│       └── train_stats.json        # Training statistics
├── ui/
│   └── streamlit_app.py           # Streamlit web interface
├── Dockerfile                     # Docker configuration
├── requirements.txt               # Python dependencies (pinned versions)
├── .env.template                  # Template for environment variables
└── README.md                      # This file
```

## CRITICAL Architecture Notes

### 1. Field Name Consistency

The 10 feature names must match **exactly** across all components:

```
HouseFeatures schema (schemas.py)
    ↓
FEATURE_COLUMNS in predictor.py
    ↓
JSON keys in Stage 1 prompt (prompts.py)
    ↓
sklearn pipeline column order
```

**The 10 features:**
- `GrLivArea` — Above-ground living area (sqft)
- `BedroomAbvGr` — Number of bedrooms
- `FullBath` — Full bathrooms
- `HalfBath` — Half bathrooms
- `TotalBsmtSF` — Total basement area (sqft)
- `GarageArea` — Garage area (sqft)
- `OverallQual` — Overall quality (1-10, ordinal)
- `YearBuilt` — Year built
- `Neighborhood` — Neighborhood (categorical)
- `HouseStyle` — House style (categorical)

**Any mismatch will silently break the pipeline.** For example:
- ❌ Stage 1 returns `{"bedrooms": 3}` instead of `{"BedroomAbvGr": 3}`
- ❌ Predictor looks for `{"BedroomAbvGr": ...}` in the input
- ❌ The feature is missing, so a fallback is used
- ❌ Accuracy drops

### 2. JSON is the Bridge

The JSON produced by Stage 1 is **not** just for display. It is the **direct input** to the ML model:

```
Stage 1 JSON (10 fields)
    ↓ (convert to dict → DataFrame)
ML Model (Pipeline.predict)
    ↓ (returns predicted price)
```

The exact column names matter at every step.

### 3. Data Leakage Prevention

Every transformer (Imputer, Scaler, Encoder) is **fit on training data only**:

```python
# Correct (no leakage)
preprocessor.fit(X_train)          # Learn statistics from train
X_train_processed = transform(X_train)
X_val_processed = transform(X_val)
X_test_processed = transform(X_test)

# Wrong (data leakage!)
preprocessor.fit(X_combined)        # Learn from train + val + test
X_train_processed = transform(X_train)
```

Training set statistics (median, mean, std) are fit on `X_train` and applied to all three sets.

### 4. Fallbacks Only After User Review

```
User Query
    ↓
Stage 1 Extraction (may have nulls)
    ↓
Streamlit UI (user fills in missing values)
    ↓
Confirmed Features (some still null after user fill-in)
    ↓
ML Predictor (fills remaining nulls with training medians)
    ↓
Prediction
```

Fallbacks use **training set medians** to represent "a typical house."

## API Endpoints

### `POST /extract`
Extract house features from a natural language query (Stage 1 only).

**Request:**
```json
{
  "query": "3 bedroom house in a good neighborhood with a 2 car garage"
}
```

**Response (ExtractionResult):**
```json
{
  "features": {
    "GrLivArea": 1500.0,
    "BedroomAbvGr": 3,
    "FullBath": 2,
    "HalfBath": 0,
    "TotalBsmtSF": 1000.0,
    "GarageArea": 440.0,
    "OverallQual": 7,
    "YearBuilt": 2000,
    "Neighborhood": "CollgCr",
    "HouseStyle": "1Story"
  },
  "extracted_fields": ["GrLivArea", "BedroomAbvGr", "FullBath", ...],
  "missing_fields": ["TotalBsmtSF"],
  "confidence": "high",
  "needs_clarification": false
}
```

### `POST /predict`
Full pipeline: extract (if needed) → ML model → interpret.

**Request:**
```json
{
  "query": "3 bedroom house...",
  "features": {
    "GrLivArea": 1500.0,
    "BedroomAbvGr": 3,
    ...
  }
}
```

**Response (AgentResponse):**
```json
{
  "predicted_price": 250000.0,
  "interpretation": "This home is priced above the median ($180,000) at $250,000...",
  "extracted_fields": ["GrLivArea", "BedroomAbvGr", ...],
  "missing_fields": [],
  "confidence": "high",
  "warning": null
}
```

### `GET /health`
Health check endpoint for Docker and load balancers.

**Response:**
```json
{
  "status": "ok"
}
```

## Environment Variables

Create a `.env` file (never commit to git):

```bash
# Required: Google Gemini API key
GEMINI_API_KEY=your_api_key_here

# Optional: Backend API URL (default: http://localhost:8000)
API_URL=http://localhost:8000
```

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend** | FastAPI | 0.104.1 |
| **Server** | Uvicorn | 0.24.0 |
| **ML** | scikit-learn | 1.3.2 |
| **Data** | pandas | 2.1.1 |
| **Serialization** | joblib | 1.3.2 |
| **Frontend** | Streamlit | 1.28.1 |
| **LLM** | Google Gemini API | (latest) |
| **Python** | 3.11 | - |

## Code Explanation

### `schemas.py`
Pydantic models defining contracts between stages:
- `HouseFeatures` — 10 ML features
- `ExtractionResult` — Stage 1 output
- `PredictionRequest` — /predict input
- `AgentResponse` — Final output

**Why Pydantic?** Automatic validation, JSON serialization, OpenAPI documentation.

### `prompts.py`
LLM prompt templates with versioning:
- `STAGE1_PROMPT_V1` — Basic extraction
- `STAGE1_PROMPT_V2` — Step-by-step thinking (chosen by ml_pipeline.ipynb Section 8)
- `STAGE2_PROMPT` — Price interpretation

**Why versioning?** A/B testing in the notebook to find the best-performing prompt.

### `predictor.py`
ML model loading and prediction:
- Loads `pipeline.joblib` at module import (once, not per-request)
- Fills nulls with training-set medians
- Converts `HouseFeatures` → DataFrame → prediction

**Why load at import time?** Reduces per-request latency from ~100ms to ~5-10ms.

### `llm_chain.py`
Two-stage LLM orchestration:
- `stage1_extract()` — Call Gemini for feature extraction
- `stage2_interpret()` — Call Gemini for price interpretation
- Error handling with fallback responses

**Why separate?** The UI can call /extract to show the user before calling /predict.

### `main.py`
FastAPI application with two endpoints:
- `POST /extract` — Stage 1 only (extraction)
- `POST /predict` — Full pipeline (extract + ML + interpret)
- `GET /health` — Health check

**Why two endpoints?** Separates concerns and allows UI to show extracted features before prediction.

### `streamlit_app.py`
Web UI with multi-step flow:
1. User enters description
2. Click "Extract Features" → /extract
3. Review extracted features, fill in missing
4. Click "Predict Price" → /predict
5. Show predicted price + interpretation

**Why Streamlit?** Fast to prototype, no JavaScript needed.

### `ml_pipeline.ipynb`
Notebook with 8 sections:
1. **EDA** — Load, explore, plot Ames Housing data
2. **Feature Selection** — Choose 10 features
3. **Three-Way Split** — 70/15/15 train/val/test
4. **Preprocessing Pipeline** — ColumnTransformer with imputation, scaling, encoding
5. **Model Comparison** — Ridge vs RandomForest vs GradientBoosting
6. **Test Evaluation** — Final model performance (run once)
7. **Serialization** — Save pipeline and statistics
8. **Prompt Experiments** — Compare Stage 1 prompt versions

**Why so detailed?** Explains every line, prevents common mistakes, teaches best practices.

## Troubleshooting

### Issue: "Cannot connect to backend at http://localhost:8000"

**Solution:** Start the FastAPI server first:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Issue: "GEMINI_API_KEY environment variable not set"

**Solution:** Create .env file with your API key:
```bash
cp .env.template .env
# Edit .env and add your key from https://makersuite.google.com/app/apikeys
```

### Issue: "Pipeline not found at app/model/pipeline.joblib"

**Solution:** Run the training notebook to generate the model:
```bash
jupyter notebook notebooks/ml_pipeline.ipynb
# Run all cells through Section 7 (Serialization)
```

### Issue: "JSON parse failed" in logs

**Solution:** Gemini returned invalid JSON. Check:
1. The prompt is valid (prompts.py)
2. Gemini API key is correct
3. API quota is not exceeded

### Issue: Docker build fails with "requirements.txt not found"

**Solution:** Make sure you're in the project root directory:
```bash
cd real-estate-agent
docker build -t real-estate-agent:v1 .
```

## Performance Notes

| Operation | Latency | Notes |
|-----------|---------|-------|
| **ML Prediction** | 5-10ms | Model loaded at startup |
| **Stage 1 LLM** | 1-3 seconds | Network call to Gemini |
| **Stage 2 LLM** | 1-3 seconds | Network call to Gemini |
| **/extract endpoint** | 1-3s | Stage 1 only |
| **/predict endpoint** | 3-6s | All three stages |

**Optimization opportunities:**
- Cache Gemini responses by query hash
- Use model batching for multiple predictions
- Implement async LLM calls (google-generativeai supports asyncio)

## Testing

```bash
# Test the API directly
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"query": "3 bedroom house"}'

# Test the health check
curl http://localhost:8000/health
```

## Production Deployment

### Docker on Cloud

```bash
# Build and push to container registry
docker build -t my-registry/real-estate-agent:v1 .
docker push my-registry/real-estate-agent:v1

# Deploy with environment variables
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=<key> \
  my-registry/real-estate-agent:v1
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: real-estate-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: real-estate-agent
  template:
    metadata:
      labels:
        app: real-estate-agent
    spec:
      containers:
      - name: api
        image: my-registry/real-estate-agent:v1
        ports:
        - containerPort: 8000
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-secret
              key: api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
```

## License

MIT License — See LICENSE file for details.

## Bootcamp Notes

This project demonstrates:
- ✅ Two-stage LLM pipeline (extraction + interpretation)
- ✅ ML model training with scikit-learn
- ✅ Strict data leakage prevention (train/val/test splits)
- ✅ Pydantic schema validation
- ✅ FastAPI REST API with error handling
- ✅ Docker containerization
- ✅ Prompt engineering and A/B testing
- ✅ Production-ready code with comments
- ✅ Graceful error handling and fallbacks

All code is extensively commented to explain **what** and **why**, making it ideal for learning.
