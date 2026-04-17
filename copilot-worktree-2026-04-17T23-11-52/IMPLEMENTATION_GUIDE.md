# Real Estate Agent: Complete Implementation Guide

This document explains every line of code and the architecture in detail.

## Architecture Overview

```
User (Streamlit UI)
    ↓ (POST /extract)
FastAPI Backend
    ├→ Stage 1 LLM (Gemini) — Extract features from text
    │   └→ Returns JSON: {GrLivArea: 1500, BedroomAbvGr: 3, ...}
    │
    ├→ ML Model (sklearn Pipeline)
    │   ├→ ColumnTransformer (preprocessing)
    │   │   ├→ Numerical: impute median → scale
    │   │   ├→ Ordinal: impute → ordinal encode [1-10]
    │   │   └→ Nominal: impute → one-hot encode (handle unknown)
    │   │
    │   └→ Regressor (Ridge / RandomForest / GradientBoosting)
    │       └→ Predicts SalePrice
    │
    └→ Stage 2 LLM (Gemini) — Interpret prediction
        └→ Returns string: "This home is priced above median..."
```

## Data Flow: Request to Response

### Step 1: User enters query in Streamlit

```python
# streamlit_app.py
query = st.text_area("Describe a house...")
# Example: "3 bedroom house in a good neighborhood with a 2 car garage"
```

### Step 2: Streamlit calls /extract endpoint

```python
# streamlit_app.py
response = requests.post(
    "http://localhost:8000/extract",
    json={"query": query}
)
```

### Step 3: FastAPI /extract endpoint receives request

```python
# main.py
@app.post("/extract", response_model=ExtractionResult)
def extract_features(body: dict):
    query = body.get("query", "").strip()
    return stage1_extract(query)  # Call Stage 1 LLM
```

### Step 4: Stage 1 LLM extraction

```python
# llm_chain.py
def stage1_extract(query: str) -> ExtractionResult:
    # Format the prompt with the user's query
    prompt = STAGE1_PROMPT_V2.format(query=query)
    
    # Call Gemini API
    raw = _call_gemini(prompt)
    
    # Example response:
    # {
    #   "GrLivArea": 1500.0,
    #   "BedroomAbvGr": 3,
    #   "FullBath": 2,
    #   "HalfBath": 0,
    #   "TotalBsmtSF": 1000.0,
    #   "GarageArea": 440.0,
    #   "OverallQual": 7,
    #   "YearBuilt": 2000,
    #   "Neighborhood": "CollgCr",
    #   "HouseStyle": "1Story",
    #   "extracted_fields": [...],
    #   "missing_fields": [...],
    #   "confidence": "high"
    # }
    
    # Parse JSON and validate into HouseFeatures schema
    parsed = json.loads(cleaned)
    features = HouseFeatures(**parsed)
    
    return ExtractionResult(
        features=features,
        extracted_fields=[...],
        missing_fields=[...],
        confidence="high"
    )
```

### Step 5: Streamlit displays extraction results

```python
# streamlit_app.py shows:
# ✅ Extracted Features:
#    - GrLivArea: 1500.0
#    - BedroomAbvGr: 3
#    - FullBath: 2
#
# ❌ Missing Features (user fills these in):
#    - TotalBsmtSF: [text input field]
#    - HouseStyle: [text input field]
```

### Step 6: User confirms/fills features and clicks "Predict Price"

```python
# streamlit_app.py sends confirmed features
features = {
    "GrLivArea": 1500.0,
    "BedroomAbvGr": 3,
    "FullBath": 2,
    "HalfBath": 0,
    "TotalBsmtSF": 1000.0,    # User filled in
    "GarageArea": 440.0,
    "OverallQual": 7,
    "YearBuilt": 2000,
    "Neighborhood": "CollgCr",
    "HouseStyle": "1Story"     # User filled in
}

response = requests.post(
    "http://localhost:8000/predict",
    json={"query": query, "features": features}
)
```

### Step 7: FastAPI /predict endpoint

```python
# main.py
@app.post("/predict", response_model=AgentResponse)
def predict_price(request: PredictionRequest):
    # Use the user-provided features
    features = request.features
    
    # Pass to ML model (predictor.py)
    predicted_price = predict(features)
    
    # Generate interpretation (Stage 2 LLM)
    interpretation = stage2_interpret(features, predicted_price, train_stats)
    
    return AgentResponse(
        predicted_price=250000.0,
        interpretation="This home is priced above the market median...",
        confidence="high"
    )
```

### Step 8: ML model prediction

```python
# predictor.py - predict()
def predict(features: HouseFeatures) -> float:
    # Convert HouseFeatures to dict
    data = features.model_dump()
    # {
    #   "GrLivArea": 1500.0,
    #   "BedroomAbvGr": 3,
    #   ...,
    #   "HouseStyle": "1Story"
    # }
    
    # Fill any remaining nulls with training-set medians
    for col, fallback in FALLBACKS.items():
        if data.get(col) is None:
            data[col] = fallback
    
    # Convert to DataFrame with correct column order
    df = pd.DataFrame([data])[FEATURE_COLUMNS]
    # This ensures columns are in the exact order the sklearn
    # pipeline was trained on
    
    # Pass through the sklearn pipeline
    prediction = pipeline.predict(df)[0]
    
    return float(prediction)  # → 250000.0
```

### Step 9: ML model internals (what happens in pipeline.predict)

The sklearn Pipeline includes:

```python
# From ml_pipeline.ipynb Section 4

# 1. ColumnTransformer (preprocessing)
preprocessor = ColumnTransformer([
    # Branch 1: Numerical features
    ("numerical", Pipeline([
        SimpleImputer(strategy="median"),     # Fill NaN with median
        StandardScaler(),                      # Scale: (x - mean) / std
    ]), ["GrLivArea", "BedroomAbvGr", ...]),
    
    # Branch 2: Ordinal features (quality 1-10)
    ("ordinal", Pipeline([
        SimpleImputer(strategy="most_frequent"),
        OrdinalEncoder(categories=[[1,2,...,10]]),  # Preserve order
    ]), ["OverallQual"]),
    
    # Branch 3: Nominal (categorical) features
    ("nominal", Pipeline([
        SimpleImputer(strategy="most_frequent"),
        OneHotEncoder(handle_unknown="ignore"),  # Create binary columns
    ]), ["Neighborhood", "HouseStyle"]),
])

# 2. Regressor (chosen by ml_pipeline.ipynb Section 5)
regressor = RandomForestRegressor(n_estimators=200, random_state=42)

# Full pipeline
pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", regressor),
])

# When pipeline.predict(df) is called:
# 1. df is passed through preprocessor (scaling, encoding)
# 2. Output is passed to regressor
# 3. Regressor makes prediction
```

### Step 10: Stage 2 LLM interpretation

```python
# llm_chain.py - stage2_interpret()
def stage2_interpret(features, predicted_price, train_stats):
    # Format Stage 2 prompt with features, price, and market stats
    prompt = STAGE2_PROMPT.format(
        features_json=json.dumps(non_null_features, indent=2),
        predicted_price=predicted_price,
        median_price=train_stats["median_price"],
        p10=train_stats["price_10th_percentile"],
        p90=train_stats["price_90th_percentile"],
        std=train_stats["price_std"]
    )
    
    # Example:
    # "House features used as ML model input:
    #  {
    #    "GrLivArea": 1500.0,
    #    "BedroomAbvGr": 3,
    #    ...
    #  }
    #
    #  ML model predicted price: $250,000
    #
    #  Market context from training data:
    #    - Median sale price: $180,000
    #    - Typical range (10-90%): $88,000 to $335,000
    #    - Standard deviation: $79,000
    #
    #  Write 3-4 sentences explaining the price..."
    
    # Call Gemini
    interpretation = _call_gemini(prompt)
    
    # Example response:
    # "This home is priced above the market median ($180,000) at $250,000,
    #  representing about a 39% premium. The above-ground living area of 1500 sqft
    #  and strong overall quality rating (7/10) push the price upward, while the 
    #  average garage area provides moderate value. With features this strong, this 
    #  property falls in the upper quarter of the market, suggesting good value 
    #  for its quality."
    
    return interpretation
```

### Step 11: Streamlit displays final results

```python
# streamlit_app.py
st.metric(
    label="Predicted Sale Price",
    value=f"${250000:,.0f}"
)

st.info(interpretation)  # Display Stage 2 output

if confidence == "low":
    st.warning("Low confidence prediction...")
```

## Critical Design Decisions

### 1. Why 10 Features?

**Answer**: 10 is the sweet spot:
- **Too few** (<5): Not enough information to predict accurately
- **Too many** (>20): Harder to extract from natural language, harder to explain

The 10 features are selected based on:
- **Correlation with SalePrice** (from EDA in Section 1)
- **Easy to extract** from natural language ("3 bedrooms" = BedroomAbvGr: 3)
- **Diverse types** (numerical, ordinal, categorical) for demonstration

### 2. Why Two LLM Stages?

**Answer**: Separation of concerns:
- **Stage 1** (extraction): Specific task, can be tested/A-B tested
- **Stage 2** (interpretation): Produces user-friendly text from numbers

Example of when Stage 1 fails but Stage 2 doesn't:
- User: "Old house, falling apart"
- Stage 1: `{"OverallQual": null}` (can't extract exact rating)
- Predictor: Fills with fallback (6)
- Stage 2: Still works (generates text based on the prediction)

### 3. Why Fallbacks in Predictor, Not in Stage 1?

**Bad design**:
```python
# Stage 1 LLM extracts: {"OverallQual": null}
# → Stage 1 tries to fill: {"OverallQual": 6}
# → What if the user wants to override? Can't tell which was guessed.
```

**Good design**:
```python
# Stage 1 LLM extracts: {"OverallQual": null}
# → Stage 1 returns: needs_clarification=true, asks user
# → User can fill in, or click "Predict" with null
# → Predictor fills with fallback (user knows this happened)
```

### 4. Why Pydantic Schemas?

**Answer**: Automatic validation + OpenAPI documentation:

```python
class HouseFeatures(BaseModel):
    OverallQual: Optional[int] = Field(None, ge=1, le=10)
    # This automatically validates that OverallQual is 1-10
    # If LLM returns {"OverallQual": 11}, it will fail validation
```

### 5. Why Three Splits (Train/Val/Test)?

**Answer**: Prevent overfitting:
- **Train (70%)**: Used to fit preprocessor and model
- **Val (15%)**: Used to select between models (Section 5)
- **Test (15%)**: Used only once for final evaluation (Section 6)

If you use val to select AND test to select, you've "trained" on test data.

### 6. Why `handle_unknown='ignore'` for OneHotEncoder?

**Answer**: Stage 1 may extract an unseen neighborhood:

```python
# Training data neighborhoods: NAmes, CollgCr, OldTown
# Stage 1 extracts: Neighborhood="UnknownTown"
# Without handle_unknown='ignore': ERROR
# With handle_unknown='ignore': Maps to [0, 0, 0] (all unknowns)
```

## Error Handling Strategy

Every function that calls an external API has try/except:

```python
# llm_chain.py - stage1_extract()
try:
    raw = _call_gemini(prompt)
    parsed = json.loads(cleaned)
    features = HouseFeatures(**parsed)
    return ExtractionResult(features=features, ...)
except json.JSONDecodeError:
    # Return degraded response
    return ExtractionResult(features=HouseFeatures(), ...)
except Exception:
    # Return degraded response
    return ExtractionResult(features=HouseFeatures(), ...)
```

**Philosophy**: Never crash. Always return something usable:
- Stage 1 extraction fails? Return empty features, ask user to fill in manually
- Stage 2 interpretation fails? Return raw numbers with no analysis
- ML prediction fails? Return error via FastAPI HTTPException

## Deployment Checklist

- [ ] **Environment**: Create `.env` file with `GEMINI_API_KEY`
- [ ] **ML Model**: Run `ml_pipeline.ipynb` to generate `pipeline.joblib` and `train_stats.json`
- [ ] **Dependencies**: `pip install -r requirements.txt`
- [ ] **Backend**: `uvicorn main:app --host 0.0.0.0 --port 8000`
- [ ] **Frontend**: `streamlit run streamlit_app.py`
- [ ] **Docker** (optional): `docker build -t real-estate-agent:v1 . && docker run -p 8000:8000 --env-file .env real-estate-agent:v1`

## Testing Prompts

### Test Query 1: Extract high-quality features
```
"Luxury property with 4 bedrooms, 3 full baths, 3500 sqft living area,
 2000 sqft basement, 3-car garage, built in 2020, excellent condition (9/10),
 located in an upscale neighborhood"
```

**Expected**: High confidence, most fields extracted

### Test Query 2: Minimal information
```
"3 bedroom house"
```

**Expected**: Medium/low confidence, many missing fields

### Test Query 3: Ambiguous information
```
"Nice house, good size, decent quality"
```

**Expected**: Low confidence, vague field values

## Next Steps / Extensions

1. **Add more features**: Expand from 10 to 20+ features for better accuracy
2. **Ensemble models**: Combine predictions from multiple models
3. **Confidence intervals**: Return price range ±10% instead of single value
4. **Historical data**: Store user queries and predictions for model retraining
5. **A/B testing**: Compare Stage 2 prompt variations on interpretations
6. **Vector search**: Use embeddings to find similar houses in training data
7. **Real-time model updates**: Retrain pipeline monthly/quarterly
8. **Multi-language**: Support Spanish, Chinese, etc. for Stage 1 extraction

## References

- **Ames Housing Dataset**: https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques
- **scikit-learn Preprocessing**: https://scikit-learn.org/stable/modules/preprocessing.html
- **FastAPI**: https://fastapi.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/
- **Streamlit**: https://docs.streamlit.io/
- **Google Generative AI**: https://ai.google.dev/

---

**Remember**: Every line of code is commented to explain **what** and **why**.
If something is unclear, check the docstrings and inline comments first.
