"""
FastAPI application for the Real Estate Agent.

This is the REST API backend that connects:
  - Streamlit UI to HTTP POST requests
  - Stage 1 LLM extraction (/extract endpoint)
  - ML model prediction (/predict endpoint)
  - Stage 2 LLM interpretation (embedded in /predict)

Two main endpoints:

1. POST /extract
   - Stage 1 only (no ML model)
   - Takes a natural language query
   - Returns extracted features + confidence + missing fields
   - UI uses this to show user what was found and ask for fill-ins

2. POST /predict
   - Full pipeline (Stage 1 + ML + Stage 2)
   - Takes user-provided features from UI
   - Returns predicted price + interpretation + confidence
   - This is what the user sees as the final answer
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import PredictionRequest, AgentResponse, ExtractionResult
from predictor import predict, train_stats
from llm_chain import stage1_extract, stage2_interpret

# Create FastAPI application instance
app = FastAPI(
    title="AI Real Estate Agent",
    description="Two-stage LLM plus ML pipeline for house price prediction",
    version="1.0.0"
)

# Add CORS middleware to allow requests from Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Health check endpoint for Docker and Streamlit UI."""
    return {"status": "ok"}


@app.post("/extract", response_model=ExtractionResult)
def extract_features(body: dict):
    """
    Extract house features from natural language query (Stage 1 only).
    
    Streamlit UI calls this first to show extracted features and ask
    the user to fill in any missing values.
    
    Request: {"query": "3 bedroom house in a good neighborhood..."}
    
    Response: ExtractionResult with features, confidence, extracted/missing fields
    """
    query = body.get("query", "").strip()
    
    if not query:
        raise HTTPException(
            status_code=400,
            detail="query field is required and cannot be empty"
        )
    
    return stage1_extract(query)


@app.post("/predict", response_model=AgentResponse)
def predict_price(request: PredictionRequest):
    """
    Full prediction pipeline: extract (if needed) → ML model → interpret.
    
    Steps:
      1. Use user-provided features OR run Stage 1 extraction
      2. Pass features to ML model for price prediction
      3. Pass features + price to Stage 2 LLM for interpretation
      4. Return AgentResponse
    
    Request: PredictionRequest with query and features (HouseFeatures)
    
    Response: AgentResponse with price, interpretation, confidence
    """
    try:
        # Determine which features to use
        provided = {
            k: v for k, v in request.features.model_dump().items()
            if v is not None
        }

        if provided:
            # User provided features — use them directly
            features = request.features
            extracted = list(provided.keys())
            missing = [
                k for k in request.features.model_dump()
                if request.features.model_dump()[k] is None
            ]
            confidence = (
                "high" if len(extracted) >= 7
                else "medium" if len(extracted) >= 4
                else "low"
            )
        else:
            # No features provided — run Stage 1 extraction
            extraction = stage1_extract(request.query)
            features = extraction.features
            extracted = extraction.extracted_fields
            missing = extraction.missing_fields
            confidence = extraction.confidence

        # Pass features to ML model
        predicted_price = predict(features)

        # Generate Stage 2 interpretation
        interpretation = stage2_interpret(features, predicted_price, train_stats)

        return AgentResponse(
            predicted_price=predicted_price,
            interpretation=interpretation,
            extracted_fields=extracted,
            missing_fields=missing,
            confidence=confidence,
            warning=(
                "Low confidence — many features missing or inferred from defaults."
                if confidence == "low" else None
            )
        )

    except Exception as e:
        print(f"[main] /predict failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )
