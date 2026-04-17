# Complete File Manifest: Real Estate Agent

This document describes every file in the project and its purpose.

## 📂 Project Structure

```
real-estate-agent/
├── 📄 Core Application Files (6 files)
├── 🎨 Frontend (1 file)
├── 📓 Training & Analysis (1 file)
├── 📦 Configuration (3 files)
├── 🐳 Deployment (1 file)
└── 📚 Documentation (5 files)
```

---

## 📄 CORE APPLICATION FILES

### 1. **main.py** (130 lines)
**Purpose**: FastAPI REST API server

**Content**:
- `FastAPI()` app initialization
- `@app.get("/health")` → Health check endpoint
- `@app.post("/extract")` → Stage 1 LLM extraction
- `@app.post("/predict")` → Full pipeline (extract + ML + interpret)
- CORS middleware for cross-origin requests
- Error handling with HTTPException

**Imports**:
- `fastapi`, `CORSMiddleware`
- `schemas.py` (PredictionRequest, AgentResponse, ExtractionResult)
- `predictor.py` (predict function, train_stats)
- `llm_chain.py` (stage1_extract, stage2_interpret)

**How it works**:
```
HTTP Request → FastAPI routing → Call LLM/ML functions → HTTP Response
```

---

### 2. **schemas.py** (220 lines)
**Purpose**: Pydantic data validation schemas

**Content**:
- `HouseFeatures` — 10 ML features (all Optional[...])
  - Numerical: GrLivArea, BedroomAbvGr, FullBath, HalfBath, TotalBsmtSF, GarageArea, YearBuilt
  - Ordinal: OverallQual (1-10)
  - Nominal: Neighborhood, HouseStyle
  
- `ExtractionResult` — Output of Stage 1 LLM
  - features: HouseFeatures
  - extracted_fields, missing_fields: list[str]
  - confidence: "high" | "medium" | "low"
  - needs_clarification: bool
  
- `PredictionRequest` — Input to /predict
  - query: str
  - features: HouseFeatures
  
- `AgentResponse` — Final output
  - predicted_price: float
  - interpretation: str (Stage 2)
  - extracted_fields, missing_fields: list[str]
  - confidence: str
  - warning: Optional[str]
  
- `ErrorResponse` — Error responses

**Why Pydantic?**
- Automatic validation (e.g., OverallQual must be 1-10)
- JSON serialization
- OpenAPI documentation generation
- Type hints for IDE autocomplete

---

### 3. **llm_chain.py** (350 lines)
**Purpose**: Two-stage LLM orchestration

**Content**:
- `_call_gemini(prompt: str) → str` — Wrapper around Gemini API
- `_strip_fences(text: str) → str` — Remove markdown code fences
- `stage1_extract(query: str) → ExtractionResult` — Feature extraction
- `stage2_interpret(features, price, stats) → str` — Price interpretation

**Key Features**:
- Error handling with try/except
- Returns degraded responses on failure (never crashes)
- Logs errors to stdout (visible in Docker logs)
- JSON parsing with fallback

**Stage 1 Process**:
1. Format STAGE1_PROMPT_V2 with user query
2. Call Gemini API
3. Strip markdown fences (if present)
4. Parse JSON and validate into HouseFeatures
5. Return ExtractionResult with confidence and missing fields

**Stage 2 Process**:
1. Serialize HouseFeatures to JSON (non-null only)
2. Format STAGE2_PROMPT with features, price, market stats
3. Call Gemini API for interpretation
4. Return natural language explanation

**Error Handling**:
- JSON parse fails → Return empty ExtractionResult
- Gemini API fails → Return fallback interpretation with raw numbers
- Validation fails → Return empty features, ask user to fill in manually

---

### 4. **predictor.py** (190 lines)
**Purpose**: ML model loading and prediction

**Content**:
- `pipeline` — Loaded sklearn Pipeline (at module import time)
- `train_stats` — Training set statistics (JSON loaded at startup)
- `FEATURE_COLUMNS` — List of 10 feature names (in correct order)
- `FALLBACKS` — Training-set medians for null imputation
- `predict(features: HouseFeatures) → float` — Main prediction function

**Key Insights**:
- Pipeline loads once at startup, not per-request (latency: 5-10ms)
- FEATURE_COLUMNS enforces exact column order (required for sklearn)
- FALLBACKS use training-set statistics (no data leakage)
- Nulls filled AFTER user review in Streamlit

**Prediction Flow**:
```
HouseFeatures dict
    ↓ (fill nulls with FALLBACKS)
DataFrame[10 cols]
    ↓ (ensure column order matches sklearn)
pipeline.predict()
    ├─ ColumnTransformer (preprocessing)
    └─ Regressor (Ridge/RandomForest/GradientBoosting)
    ↓
float (predicted price)
```

---

### 5. **prompts.py** (150 lines)
**Purpose**: LLM prompt templates with versioning

**Content**:
- `STAGE1_PROMPT_V1` — Basic extraction prompt
- `STAGE1_PROMPT_V2` — Step-by-step thinking (chosen by notebook)
- `STAGE2_PROMPT` — Price interpretation template
- `PROMPTS_FOR_TESTING` — Dict for A/B testing
- `TEST_QUERIES` — 3 test queries for comparison

**Critical Features**:
- JSON keys match sklearn column names exactly
  - ❌ `{"bedrooms": 3}` → Wrong!
  - ✅ `{"BedroomAbvGr": 3}` → Correct!
- Inference rules for common queries
  - "2 car garage" → GarageArea = 440.0
  - "luxury" → OverallQual = 9
  - "starter home" → OverallQual = 5
- Version notes: V2 uses step-by-step thinking for better extraction

**Testing Strategy** (in ml_pipeline.ipynb Section 8):
- Compare V1 vs V2 on 3 test queries
- Score by: JSON validity, field extraction, key matching
- Choose winner with evidence

---

### 6. **__init__.py** (5 lines)
**Purpose**: Python package marker

**Content**:
- Module docstring
- Makes directory importable as a Python package

---

## 🎨 FRONTEND

### **streamlit_app.py** (290 lines)
**Purpose**: Interactive web UI for the application

**Features**:
- **Step 1**: Text area for user input
- **Step 2**: "Extract Features" button → POST /extract
- **Step 3**: Two-column layout
  - Left: Extracted features (read-only, green checkmarks)
  - Right: Missing features (input fields for user)
- **Step 4**: "Predict Price" button → POST /predict
- **Step 5**: Display predicted price with st.metric()
- **Step 6**: Show Stage 2 interpretation in st.info()
- **Step 7**: Warning if confidence is low
- **Step 8**: Error handling with st.error()

**State Management**:
- `st.session_state` persists data between button clicks
- Extraction results cached (click "Predict" doesn't re-extract)

**API Integration**:
- `requests.post()` to /extract and /predict endpoints
- `requests.get()` to /health for connection check
- Timeout: 15 seconds for each request
- Error handling for ConnectionError

**Configuration**:
- API_URL from `os.getenv("API_URL", "http://localhost:8000")`
- Override with environment variable for remote backends

---

## 📓 TRAINING & ANALYSIS

### **ml_pipeline.ipynb** (24KB, 8 sections)
**Purpose**: ML model training and prompt testing

**Section 1: EDA (Exploratory Data Analysis)**
- Load Ames Housing CSV
- Show shape, dtypes, null counts
- Plot SalePrice distribution
- Show top correlations with SalePrice

**Section 2: Feature Selection**
- Select 10 final features (CRITICAL: exact names)
- Extract X (features) and y (target)

**Section 3: Three-Way Split**
- Train (70%), Validation (15%), Test (15%)
- random_state=42 for reproducibility
- Print proportions

**Section 4: Preprocessing Pipeline**
- ColumnTransformer with 3 branches:
  - Numerical: impute median → scale
  - Ordinal: impute → ordinal encode [1-10]
  - Nominal: impute → one-hot encode (handle_unknown)
- Every transformer fit on training data only (no leakage)

**Section 5: Model Comparison**
- Train Ridge, RandomForest, GradientBoosting
- Compare on Train/Val metrics
- Choose best by validation RMSE
- Print justification

**Section 6: Test Set Evaluation**
- Evaluate best model on test set EXACTLY ONCE
- Print: Test RMSE, Test R²

**Section 7: Serialization**
- Save pipeline: `joblib.dump(pipeline, "app/model/pipeline.joblib")`
- Save stats: `json.dump(train_stats, "app/model/train_stats.json")`
- Statistics: median_price, mean_price, p10, p90, std

**Section 8: Prompt Versioning Experiments**
- Test STAGE1_PROMPT_V1 vs STAGE1_PROMPT_V2
- On 3 test queries
- Score by: JSON validity, field extraction, key matching
- Choose winner with evidence

---

## 📦 CONFIGURATION FILES

### **requirements.txt** (40 lines)
**Purpose**: Python dependencies (pinned versions)

**Key Packages**:
- `fastapi==0.104.1` — Web framework
- `uvicorn[standard]==0.24.0` — ASGI server
- `pydantic>=2.0.0` — Validation
- `scikit-learn==1.3.2` — ML models
- `pandas==2.1.1` — Data manipulation
- `numpy==1.26.0` — Numerical operations
- `joblib==1.3.2` — Model serialization
- `streamlit==1.28.1` — Web UI
- `python-dotenv==1.0.0` — Environment variables
- `google-generativeai==0.3.0` — Gemini API
- `requests==2.31.0` — HTTP client
- `jupyter`, `notebook`, `matplotlib`, `seaborn` — Notebooks & plotting

**Version Strategy**:
- Major version locked (e.g., 2.x.x)
- Minor/patch versions specified for reproducibility
- Allows pip to pull compatible security updates

---

### **.env.template** (10 lines)
**Purpose**: Template for environment variables

**Content**:
- `GEMINI_API_KEY=your_gemini_api_key_here` — API key from Google
- `API_URL=http://localhost:8000` — Backend URL (optional)

**Never commit `.env` to git** — Contains secrets!

---

### **.gitignore** (50 lines)
**Purpose**: Prevent committing sensitive/generated files

**Ignores**:
- `.env` — Environment variables with secrets
- `__pycache__/` — Python cache
- `*.pyc` — Compiled Python
- `venv/`, `.venv/` — Virtual environments
- `.ipynb_checkpoints/` — Notebook cache
- `.joblib` — Model files (regenerated)
- `.csv` — Data files
- `.vscode/`, `.idea/` — IDE configs
- `.DS_Store`, `Thumbs.db` — OS files

---

## 🐳 DEPLOYMENT

### **Dockerfile** (50 lines, heavily commented)
**Purpose**: Docker build configuration

**Build Strategy**:
```dockerfile
FROM python:3.11-slim         # Minimal base image
WORKDIR /app                  # Set working directory
COPY requirements.txt .       # Copy deps (layer cache)
RUN pip install -r ...        # Install (cached if unchanged)
COPY . .                      # Copy app code
EXPOSE 8000                   # Document port
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key Points**:
- Layer caching: requirements.txt copied before app code
- `--host 0.0.0.0` required for Docker port mapping
- `slim` base image (~150MB, not Alpine)
- Every line has explanatory comment

**Build**: `docker build -t real-estate-agent:v1 .`
**Run**: `docker run -p 8000:8000 --env-file .env real-estate-agent:v1`

---

## 📚 DOCUMENTATION

### **README.md** (420 lines)
**Purpose**: Quick start and comprehensive reference

**Sections**:
- System architecture overview (with ASCII diagram)
- Quick start (setup, train, run)
- Project structure
- CRITICAL architecture notes
- API endpoints (/extract, /predict, /health)
- Environment variables
- Technology stack
- Detailed code explanations
- Troubleshooting guide
- Performance notes
- Production deployment (Docker, Kubernetes)
- License

**Audience**: Anyone (beginners to experienced developers)

---

### **IMPLEMENTATION_GUIDE.md** (420 lines)
**Purpose**: Deep dive into system design

**Sections**:
- Architecture overview (detailed diagram)
- Data flow from request to response (11 steps)
- Critical design decisions (with justifications)
- Error handling strategy
- Deployment checklist
- Testing scenarios
- Extension ideas (Level 1-5)
- References

**Focus**: Explain the WHY behind each design choice

**Audience**: Developers who want to understand the system deeply

---

### **PROJECT_SUMMARY.md** (380 lines)
**Purpose**: Executive summary and examples

**Sections**:
- What you've built (high-level overview)
- Key features and architecture principles
- How to run everything (5 steps)
- Key code examples (Stage 1, ML, Stage 2)
- File checklist
- Common mistakes to avoid
- Troubleshooting table
- Learning outcomes
- Timeline estimate
- Extension ideas (bootcamp levels)

**Focus**: Practical, examples-driven

**Audience**: Bootcamp students, team members

---

### **ARCHITECTURE_DIAGRAM.txt** (400+ lines)
**Purpose**: Visual system architecture

**Content**:
- ASCII diagrams showing:
  - User interface layer (Streamlit)
  - FastAPI backend layer
  - Stage 1 extraction (Gemini)
  - Schema validation (Pydantic)
  - ML prediction layer (sklearn)
  - Stage 2 interpretation (Gemini)
- Data flow summary with 11 steps
- Critical points highlighted
- Fallback/error handling shown

**Format**: Pure ASCII (viewable in any editor)

**Audience**: Visual learners, architecture reviews

---

### **CHECKLIST.md** (350 lines)
**Purpose**: Pre-deployment verification

**Sections**:
- Files created (checkbox list)
- Pre-deployment checks (5 categories)
- ML model generation
- API backend testing
- Frontend testing
- End-to-end testing (4 test cases)
- Docker deployment (optional)
- Verification test cases (3 examples)
- Debugging tips
- Common commands
- Final sign-off

**Use Before**: Deploying to production

**Audience**: Anyone deploying the application

---

## 🔗 File Dependencies

```
main.py
├── schemas.py (imports: HouseFeatures, ExtractionResult, PredictionRequest, AgentResponse)
├── predictor.py (imports: predict, train_stats, FALLBACKS)
└── llm_chain.py (imports: stage1_extract, stage2_interpret)

llm_chain.py
├── schemas.py (imports: HouseFeatures, ExtractionResult)
└── prompts.py (imports: STAGE1_PROMPT_V2, STAGE2_PROMPT)

predictor.py
├── schemas.py (imports: HouseFeatures)
└── model/pipeline.joblib (external file, loaded at import)

streamlit_app.py
└── requests library (imports: requests)

ml_pipeline.ipynb
├── schemas.py (imports: HouseFeatures)
├── prompts.py (imports: STAGE1_PROMPT_V1, STAGE1_PROMPT_V2)
└── model/train_stats.json (external file, used for testing)
```

---

## 📊 Statistics

| Category | Count | Lines/Size |
|----------|-------|-----------|
| **Python Files** | 5 | ~1,200 lines |
| **Jupyter Notebook** | 1 | 24 KB |
| **Documentation** | 5 | ~1,900 lines |
| **Configuration** | 3 | ~100 lines |
| **Docker** | 1 | ~50 lines |
| **Total** | 15 files | ~3,250 lines (code + docs) |

---

## ✅ Quality Checklist

- [x] Every Python file has module docstring
- [x] Every function has docstring with purpose, args, returns
- [x] Every non-obvious line has explanatory comment
- [x] Error handling with try/except on all external calls
- [x] No hardcoded secrets (all in .env)
- [x] No data leakage (train/val/test splits respected)
- [x] Field names consistent across all files
- [x] Dockerfile tested and works end-to-end
- [x] Documentation comprehensive and examples-driven
- [x] Pydantic schemas validate all inputs

---

## 🚀 Deployment Path

1. **Local Dev**: Clone → pip install → jupyter notebook → uvicorn + streamlit
2. **Docker**: docker build → docker run (port 8000)
3. **Cloud**: Push image → Deploy with env file → Monitor logs

---

## 📝 Notes for Users

- All code is **educational** — every line explained
- **No external databases** — everything in-memory
- **No authentication** — for bootcamp learning only
- **Single-threaded** — fine for 1-2 concurrent users
- **Graceful degradation** — never crashes, always returns something

---

**Total Project Size**: ~15 files, ~3,250 lines (code + documentation)
**Setup Time**: ~10-15 minutes (with API key)
**Training Time**: ~5-10 minutes (notebook)
**Runtime**: <10 seconds per prediction (3-6s including LLM calls)
