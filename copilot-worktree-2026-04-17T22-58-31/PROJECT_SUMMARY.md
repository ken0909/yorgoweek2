# Project Summary: AI Real Estate Agent

## What You've Built

A complete **two-stage LLM + ML pipeline** for predicting house prices from natural language descriptions.

**Live Demo Flow:**
1. User enters: *"3 bedroom house in a good neighborhood with a 2 car garage"*
2. Stage 1 LLM (Gemini) extracts: `{"BedroomAbvGr": 3, "GarageArea": 440, ...}`
3. ML Model (sklearn) predicts: `$250,000`
4. Stage 2 LLM (Gemini) explains: *"This home is priced above the market median..."*
5. Streamlit UI displays results

---

## Files Created

### 📁 Core Application (app/)

| File | Lines | Purpose |
|------|-------|---------|
| **main.py** | ~130 | FastAPI app with `/extract` and `/predict` endpoints |
| **schemas.py** | ~220 | Pydantic models (HouseFeatures, ExtractionResult, AgentResponse) |
| **llm_chain.py** | ~350 | Two-stage LLM orchestration (stage1_extract, stage2_interpret) |
| **predictor.py** | ~190 | ML model loader and predict() function |
| **prompts.py** | ~150 | LLM prompt templates (V1, V2, Stage 2) |
| **model/** | — | Subdirectory for pipeline.joblib and train_stats.json |

### 🎨 Frontend (ui/)

| File | Lines | Purpose |
|------|-------|---------|
| **streamlit_app.py** | ~290 | Multi-step web UI in Streamlit |

### 📓 Training (notebooks/)

| File | Format | Purpose |
|------|--------|---------|
| **ml_pipeline.ipynb** | Jupyter | 8 sections: EDA → feature selection → preprocessing → model training → evaluation → serialization → prompt testing |

### 📦 Configuration & Docker

| File | Purpose |
|------|---------|
| **requirements.txt** | Pinned Python dependencies |
| **Dockerfile** | Multi-stage Docker build (commented) |
| **.env.template** | Template for environment variables |
| **.gitignore** | Prevents committing secrets |
| **__init__.py** | Python package initialization |

### 📚 Documentation

| File | Purpose |
|------|---------|
| **README.md** | Quick start, architecture overview, API reference |
| **IMPLEMENTATION_GUIDE.md** | Deep dive: architecture, data flow, design decisions |
| **PROJECT_SUMMARY.md** | This file |

---

## Architecture Principles

### 1. **Field Name Consistency** (CRITICAL)

The 10 feature names MUST be identical across all files:

```
schemas.py (HouseFeatures)
    ↓
predictor.py (FEATURE_COLUMNS)
    ↓
prompts.py (Stage 1 JSON keys)
    ↓
ml_pipeline.ipynb (FEATURE_NAMES)
```

**The 10 features:**
- GrLivArea, BedroomAbvGr, FullBath, HalfBath, TotalBsmtSF, GarageArea
- OverallQual, YearBuilt, Neighborhood, HouseStyle

### 2. **JSON as Bridge**

Stage 1 JSON is **not** just for display — it's the **direct input** to the ML model:

```
Gemini API
    ↓ (returns JSON with 10 keys)
DataFrame[10 columns]
    ↓
sklearn Pipeline.predict()
    ↓
$250,000 (predicted price)
```

### 3. **Data Leakage Prevention**

Every transformer (imputer, scaler, encoder) fits on **training data only**:

- Training set: Statistics learned (median, categories, mean/std)
- Validation/Test: Statistics applied (no learning)

### 4. **Error Handling**

All external API calls (Gemini, ML model) have try/except:
- Never crash
- Always return degraded but usable responses
- Log errors to stdout (visible in Docker logs)

### 5. **Modular Design**

Each file has a single responsibility:
- `main.py` → HTTP layer
- `schemas.py` → Validation contracts
- `llm_chain.py` → LLM orchestration
- `predictor.py` → ML predictions
- `prompts.py` → LLM prompts

---

## How to Run Everything

### **Step 1: Install & Configure**

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your Gemini API key
cp .env.template .env
# Edit .env and add GEMINI_API_KEY from https://makersuite.google.com/app/apikeys
```

### **Step 2: Generate ML Model**

```bash
# Run the training notebook
jupyter notebook notebooks/ml_pipeline.ipynb

# This generates:
#   - app/model/pipeline.joblib (serialized model)
#   - app/model/train_stats.json (training statistics)
```

### **Step 3: Start Backend**

```bash
# Terminal 1: Start FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000

# Visit http://localhost:8000/docs to test endpoints
```

### **Step 4: Start Frontend**

```bash
# Terminal 2: Start Streamlit UI
streamlit run streamlit_app.py

# Opens http://localhost:8501 in browser
```

### **Step 5: Test End-to-End**

1. Open http://localhost:8501
2. Enter: "3 bedroom house, 2 full baths, 1500 sqft living area, good neighborhood"
3. Click "Extract Features" → See extracted values
4. Click "Predict Price" → See predicted price + interpretation
5. Observe logs in FastAPI terminal

### **Alternative: Docker**

```bash
docker build -t real-estate-agent:v1 .
docker run -p 8000:8000 --env-file .env real-estate-agent:v1

# Then start Streamlit locally (it connects to Docker backend)
streamlit run streamlit_app.py
```

---

## Key Code Examples

### Example 1: How Stage 1 Extracts Features

```python
# llm_chain.py - User query → JSON → HouseFeatures
user_query = "3 bedroom house in a good neighborhood with a 2 car garage"

# Step 1: Format prompt
prompt = STAGE1_PROMPT_V2.format(query=user_query)

# Step 2: Call Gemini
raw_response = _call_gemini(prompt)
# Returns: {"GrLivArea": null, "BedroomAbvGr": 3, ..., "GarageArea": 440, ...}

# Step 3: Parse and validate
parsed = json.loads(raw_response)
features = HouseFeatures(**parsed)

# Step 4: Return with metadata
return ExtractionResult(
    features=features,
    extracted_fields=["BedroomAbvGr", "GarageArea"],
    missing_fields=["GrLivArea", "FullBath", ...],
    confidence="medium",
    needs_clarification=True
)
```

### Example 2: How ML Model Predicts

```python
# predictor.py - HouseFeatures → $250,000
features = HouseFeatures(
    GrLivArea=1500.0,
    BedroomAbvGr=3,
    FullBath=2,
    HalfBath=0,
    # ... remaining fields ...
)

# Step 1: Convert to dict
data = features.model_dump()

# Step 2: Fill nulls with training-set medians
for col, fallback in FALLBACKS.items():
    if data.get(col) is None:
        data[col] = fallback

# Step 3: Convert to DataFrame with correct column order
df = pd.DataFrame([data])[FEATURE_COLUMNS]

# Step 4: Predict
prediction = pipeline.predict(df)[0]
return 250000.0
```

### Example 3: How Stage 2 Interprets

```python
# llm_chain.py - Features + Price + Stats → Interpretation
interpretation = stage2_interpret(
    features=HouseFeatures(...),
    predicted_price=250000.0,
    train_stats={
        "median_price": 180000.0,
        "price_10th_percentile": 88000.0,
        "price_90th_percentile": 335000.0,
        "price_std": 79000.0
    }
)

# Returns:
# "This home is priced above the market median ($180,000) at $250,000,
#  representing about a 39% premium. The above-ground living area of 1500 sqft..."
```

---

## File Checklist

Before deployment, verify all files exist:

```bash
✓ app/main.py
✓ app/schemas.py
✓ app/llm_chain.py
✓ app/predictor.py
✓ app/prompts.py
✓ app/__init__.py
✓ app/model/           (created by notebook)
✓ ui/streamlit_app.py
✓ notebooks/ml_pipeline.ipynb
✓ Dockerfile
✓ requirements.txt
✓ .env.template
✓ .gitignore
✓ README.md
✓ IMPLEMENTATION_GUIDE.md
✓ PROJECT_SUMMARY.md (this file)
```

---

## Common Mistakes to Avoid

❌ **Mistake 1**: Committing `.env` file with API key
```bash
# Wrong:
git add .env
git commit -m "Add API key"

# Right:
# .env is in .gitignore, only commit .env.template
```

❌ **Mistake 2**: Using test set before final evaluation
```python
# Wrong:
X_train, X_test = split(X)
preprocessor.fit(X_train + X_test)  # Data leakage!

# Right:
preprocessor.fit(X_train)           # Fit only on train
transform(X_test)                   # Apply to test
```

❌ **Mistake 3**: Renaming features in Pydantic but not in ML pipeline
```python
# Wrong:
class HouseFeatures(BaseModel):
    bedrooms: Optional[int]  # Changed name!

# Right:
class HouseFeatures(BaseModel):
    BedroomAbvGr: Optional[int]  # Must match sklearn
```

❌ **Mistake 4**: Hardcoding API key instead of loading from .env
```python
# Wrong:
genai.configure(api_key="AIza...")  # Visible in code!

# Right:
load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Cannot connect to backend` | Start FastAPI: `uvicorn main:app --host 0.0.0.0 --port 8000` |
| `GEMINI_API_KEY not set` | Create `.env` file with key from https://makersuite.google.com/app/apikeys |
| `Pipeline not found` | Run notebook Section 7: `jupyter notebook notebooks/ml_pipeline.ipynb` |
| `JSON parse error` | Check Gemini API key is valid, quota not exceeded |
| `Docker build fails` | Run from project root: `docker build -t real-estate-agent:v1 .` |

---

## Learning Outcomes

By studying this codebase, you'll learn:

✅ **Two-stage LLM pipelines** — Extract, then interpret
✅ **Prompt engineering & versioning** — A/B test prompts in notebooks
✅ **ML pipeline design** — ColumnTransformer, no data leakage
✅ **FastAPI design patterns** — Multiple endpoints, error handling
✅ **Pydantic validation** — Schema contracts for data flow
✅ **Docker containerization** — From development to production
✅ **Error handling strategies** — Graceful degradation
✅ **API design** — REST endpoints, JSON serialization
✅ **Production-ready code** — Comments, logging, fallbacks

---

## Timeline Estimate

| Phase | Time | Deliverable |
|-------|------|-------------|
| **Setup** | 5-10 min | Python env, dependencies |
| **ML Training** | 5-10 min | Pipeline.joblib, stats.json |
| **API Testing** | 5 min | FastAPI docs at /docs |
| **UI Testing** | 5 min | Streamlit at localhost:8501 |
| **End-to-end** | 10 min | Full query → prediction flow |
| **Total** | ~40 min | Complete working system |

---

## Next Levels (Bootcamp Extensions)

### Level 1: Expand the Features
- Add 10 more features → train on 20 features
- Update all schemas, predictor, prompts, notebook

### Level 2: Ensemble Models
- Train 5 different models
- Average predictions for robustness
- Track which model won on val set

### Level 3: Prompt A/B Testing
- Create V3, V4, V5 of Stage 1 prompt
- Compare on 20 test queries
- Score by: JSON validity, field extraction, accuracy

### Level 4: Real-Time Model Monitoring
- Log all predictions
- Store in database
- Retrain model monthly
- Track accuracy drift over time

### Level 5: Multi-LLM Comparison
- Test Gemini, GPT-4, Claude
- Compare speed, accuracy, cost
- Switch LLM at runtime via config

---

## Final Thoughts

This system demonstrates **production-ready patterns**:

1. **Separation of concerns** — Each file has one job
2. **Explicit contracts** — Pydantic schemas enforce rules
3. **Error handling** — Never crash, always return something
4. **Logging** — Visible in Docker logs for debugging
5. **Testing** — Notebook includes A/B testing for prompts
6. **Comments** — Every line explains what and why
7. **Reproducibility** — random_state=42, pinned versions
8. **Deployment-ready** — Dockerfile works out of the box

**Now build something amazing! 🚀**

---

## Support

- **FastAPI docs:** Visit http://localhost:8000/docs
- **Streamlit docs:** https://docs.streamlit.io/
- **Pydantic docs:** https://docs.pydantic.dev/
- **scikit-learn docs:** https://scikit-learn.org/
- **Google Generative AI:** https://ai.google.dev/
