"""
Pydantic schemas for the Real Estate Agent application.

These are the contracts between each stage of the pipeline:
1. Stage 1 LLM extraction outputs → HouseFeatures
2. HouseFeatures is serialized to DataFrame and passed to the ML model
3. ML model predictions are wrapped in AgentResponse

CRITICAL: The field names here must exactly match the sklearn pipeline
column names. Any mismatch will silently break the prediction chain.
The 10 fields are:
  GrLivArea, BedroomAbvGr, FullBath, HalfBath, TotalBsmtSF, GarageArea,
  OverallQual, YearBuilt, Neighborhood, HouseStyle
"""

from pydantic import BaseModel, Field
from typing import Optional


class HouseFeatures(BaseModel):
    """
    Structured features extracted by Stage 1 LLM.
    
    These are the 10 features that the sklearn ML model was trained on.
    Field names MUST match exactly the sklearn pipeline column names
    or the model prediction will fail.
    
    All fields are Optional because Stage 1 may not find every feature
    in the user's query. Missing fields are filled with training-set
    medians in app/predictor.py AFTER the user has had a chance
    to manually provide values via the Streamlit UI.
    """

    GrLivArea: Optional[float] = Field(
        None,
        description="Above-ground living area in square feet"
    )
    
    BedroomAbvGr: Optional[int] = Field(
        None,
        description="Number of bedrooms above grade (ground level)"
    )
    
    FullBath: Optional[int] = Field(
        None,
        description="Number of full bathrooms"
    )
    
    HalfBath: Optional[int] = Field(
        None,
        description="Number of half bathrooms (toilet + sink only)"
    )
    
    TotalBsmtSF: Optional[float] = Field(
        None,
        description="Total basement square footage"
    )
    
    GarageArea: Optional[float] = Field(
        None,
        description="Size of garage in square feet"
    )
    
    OverallQual: Optional[int] = Field(
        None,
        ge=1,
        le=10,
        description="Overall quality rating from 1 (poor) to 10 (excellent)"
    )
    
    YearBuilt: Optional[int] = Field(
        None,
        ge=1800,
        le=2024,
        description="Year the house was originally constructed"
    )
    
    Neighborhood: Optional[str] = Field(
        None,
        description="Neighborhood name (Ames, IA). Examples: NAmes, CollgCr, OldTown"
    )
    
    HouseStyle: Optional[str] = Field(
        None,
        description="Style of house. One of: 1Story, 2Story, 1.5Fin, SFoyer, SLvl"
    )

    class Config:
        """Pydantic config for JSON schema generation."""
        json_schema_extra = {
            "example": {
                "GrLivArea": 1500.0,
                "BedroomAbvGr": 3,
                "FullBath": 2,
                "HalfBath": 0,
                "TotalBsmtSF": 1000.0,
                "GarageArea": 440.0,
                "OverallQual": 7,
                "YearBuilt": 2000,
                "Neighborhood": "NAmes",
                "HouseStyle": "1Story"
            }
        }


class ExtractionResult(BaseModel):
    """
    Output of Stage 1 LLM extraction.
    
    This is returned by the /extract endpoint so the UI can show the user:
    - What features were successfully extracted
    - What features are missing
    - Whether more information is needed to make a reliable prediction
    
    The 'features' field is a HouseFeatures object that will be passed
    to the user for review and manual fill-in before going to the ML model.
    """

    features: HouseFeatures = Field(
        ...,
        description="Extracted house features (may contain null values)"
    )
    
    extracted_fields: list[str] = Field(
        default_factory=list,
        description="List of field names the LLM successfully extracted"
    )
    
    missing_fields: list[str] = Field(
        default_factory=list,
        description="List of field names that were not found in the query"
    )
    
    confidence: str = Field(
        default="low",
        description="Extraction confidence: 'high' (7+ fields), 'medium' (4-6), 'low' (<4)"
    )
    
    needs_clarification: bool = Field(
        default=True,
        description="True if extraction is incomplete and user input is needed"
    )


class PredictionRequest(BaseModel):
    """
    Request body for the /predict endpoint.
    
    Sent by the Streamlit UI after the user has reviewed and optionally
    filled in missing features. These features are the direct input
    to the ML pipeline.predict() method.
    """

    query: str = Field(
        ...,
        description="The original user query (echoed for context)"
    )
    
    features: HouseFeatures = Field(
        ...,
        description="Confirmed house features (may include user-filled values)"
    )


class AgentResponse(BaseModel):
    """
    Final response returned by the /predict endpoint and displayed
    to the user in the Streamlit frontend.
    
    This is the output of the full two-stage LLM + ML pipeline:
      1. Stage 1 extracts features or uses user-provided features
      2. Features → ML model → predicted price
      3. Predicted price + features → Stage 2 → interpretation
    """

    predicted_price: float = Field(
        ...,
        description="ML-predicted sale price in USD"
    )
    
    interpretation: str = Field(
        ...,
        description="Stage 2 LLM interpretation explaining the price in natural language"
    )
    
    extracted_fields: list[str] = Field(
        default_factory=list,
        description="Fields that were used in the prediction"
    )
    
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Fields that fell back to training-set medians"
    )
    
    confidence: str = Field(
        default="low",
        description="Confidence level of the prediction"
    )
    
    warning: Optional[str] = Field(
        None,
        description="Optional warning (e.g., if confidence is low)"
    )


class ErrorResponse(BaseModel):
    """
    Error response body returned when a request fails.
    
    Used by FastAPI's HTTPException to provide structured error
    information to the UI with both technical detail and a
    user-friendly fallback message.
    """

    error: str = Field(
        ...,
        description="Brief error type or category"
    )
    
    detail: str = Field(
        ...,
        description="Technical detail for debugging"
    )
    
    fallback_message: str = Field(
        ...,
        description="User-friendly message to display in the UI"
    )
