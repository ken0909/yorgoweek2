"""
ML Model loader and prediction function.

This module handles:
1. Loading the serialized sklearn pipeline from disk (once at startup)
2. Loading training set statistics for Stage 2 LLM context
3. Filling any remaining null features with training-set medians
4. Converting HouseFeatures to a DataFrame with the correct column order
5. Passing the DataFrame to the pipeline for prediction

CRITICAL: The column names in the DataFrame MUST match exactly what the
sklearn pipeline was trained on. This is enforced via the FEATURE_COLUMNS
list, which must be in the exact order used during training.

Data leakage prevention: The FALLBACKS (median imputation) are computed
from the TRAINING SET only, never from test or validation data.
"""

import joblib
import json
import pandas as pd
from pathlib import Path
from schemas import HouseFeatures

# Paths to serialized model and statistics
# Path(__file__).parent resolves to the directory containing this file
# In production: /app/model/pipeline.joblib
# In dev: ./model/pipeline.joblib
MODEL_PATH = Path(__file__).parent / "model" / "pipeline.joblib"
STATS_PATH = Path(__file__).parent / "model" / "train_stats.json"

# Load at module import time — FastAPI loads this once at startup,
# not on every request. This keeps prediction latency low (5-10ms per prediction).
try:
    pipeline = joblib.load(MODEL_PATH)
    print(f"[predictor] Loaded pipeline from {MODEL_PATH}")
except FileNotFoundError as e:
    print(f"[predictor] ERROR: Pipeline not found at {MODEL_PATH}")
    print(f"[predictor] Run notebooks/ml_pipeline.ipynb Section 7 to generate it")
    raise e

try:
    with open(STATS_PATH) as f:
        train_stats = json.load(f)
    print(f"[predictor] Loaded training statistics from {STATS_PATH}")
except FileNotFoundError as e:
    print(f"[predictor] ERROR: Training stats not found at {STATS_PATH}")
    raise e


# These 10 column names MUST match exactly the order used when the
# sklearn ColumnTransformer was fit during training.
# If you change this list, you must retrain the model.
# Order matters: the pipeline applies transformers in this order.
FEATURE_COLUMNS = [
    "GrLivArea",        # float: above-ground living area sqft
    "BedroomAbvGr",     # int: number of bedrooms
    "FullBath",         # int: full bathrooms
    "HalfBath",         # int: half bathrooms
    "TotalBsmtSF",      # float: basement sqft
    "GarageArea",       # float: garage sqft
    "OverallQual",      # int: ordinal quality 1-10
    "YearBuilt",        # int: construction year
    "Neighborhood",     # str: categorical neighborhood
    "HouseStyle"        # str: categorical house style
]


# FALLBACK VALUES FOR NULL FEATURES
# These are computed from the TRAINING SET ONLY (no data leakage).
# They represent "a typical house" in the Ames housing data.
# Used only when a feature is still null after user has had a chance
# to fill it in via the Streamlit UI.
# Median is chosen (not mean) because it's more robust to outliers.
FALLBACKS = {
    "GrLivArea": 1464.0,      # training set median living area
    "BedroomAbvGr": 3,        # median bedrooms
    "FullBath": 2,            # median full baths
    "HalfBath": 0,            # median half baths (most common: 0 or 1)
    "TotalBsmtSF": 991.0,     # median basement area
    "GarageArea": 480.0,      # median garage area
    "OverallQual": 6,         # median overall quality (5-6 is typical)
    "YearBuilt": 1973,        # median construction year
    "Neighborhood": "NAmes",  # most common neighborhood in Ames
    "HouseStyle": "1Story"    # most common house style
}


def predict(features: HouseFeatures) -> float:
    """
    Predict the house sale price using the sklearn ML model.
    
    Pipeline:
      1. Convert HouseFeatures Pydantic model to a dict
      2. Fill any null values with training-set medians
      3. Build a single-row DataFrame with columns in the correct order
         (order matters for sklearn pipeline)
      4. Pass the DataFrame to pipeline.predict()
      5. Return the predicted price as a Python float
    
    Args:
        features (HouseFeatures): House features to predict from
        
    Returns:
        float: Predicted sale price in USD
        
    Raises:
        ValueError: If the pipeline or features are invalid
        Exception: If the sklearn pipeline predict() fails
    """
    
    # Step 1: Convert Pydantic model to dict
    # model_dump() returns {key: value, ...} including nulls
    data = features.model_dump()
    
    # Step 2: Fill null values with training-set medians
    # This ensures the DataFrame has no nulls, which would break the pipeline
    for col, fallback in FALLBACKS.items():
        if data.get(col) is None:
            data[col] = fallback
            # Log which fallbacks were used — useful for debugging
            # In production, these logs go to the Docker container logs
            print(f"[predictor] Using fallback for {col}: {fallback}")
    
    # Step 3: Build a single-row DataFrame with columns in the correct order
    # The order of columns MUST match the order used during sklearn pipeline training.
    # This is why we select columns using FEATURE_COLUMNS list, not from data dict.
    # dict[col] returns the value for that column name.
    df = pd.DataFrame([data])[FEATURE_COLUMNS]
    
    # Step 4: Pass the DataFrame to the sklearn pipeline
    # The pipeline includes:
    #   - ColumnTransformer: numerical scaling, ordinal encoding, one-hot encoding
    #   - Regressor: Ridge, RandomForest, or GradientBoosting
    # It returns an array of predictions. Since we have 1 row, [0] gets the first (only) prediction.
    prediction = pipeline.predict(df)[0]
    
    # Step 5: Convert numpy float64 to Python float for JSON serialization
    # This ensures the value can be safely serialized and transmitted over HTTP
    return float(prediction)
