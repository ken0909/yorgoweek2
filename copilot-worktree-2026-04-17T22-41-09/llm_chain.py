"""
Two-stage LLM chain for the Real Estate Agent.

STAGE 1 — Feature Extraction:
  Input:  Natural language query from user
  Output: HouseFeatures (structured JSON with the 10 ML features)
  
  Uses STAGE1_PROMPT_V2 (chosen by Section 8 of ml_pipeline.ipynb).
  Returns ExtractionResult with confidence level and missing fields list.
  On any error, returns degraded response (empty features, all fields missing).

STAGE 2 — Prediction Interpretation:
  Input:  HouseFeatures + predicted price + training set statistics
  Output: Natural language explanation of the prediction
  
  Uses STAGE2_PROMPT to generate 3-4 sentences placing the price in market context
  and explaining which features drove the prediction.
  On any error, returns a fallback interpretation (just the raw numbers).

LLM: Google Gemini API (gemini-2.5-flash model)
Library: google-generativeai
API Key: Loaded from .env file as GEMINI_API_KEY

Error handling:
  - Both stage1_extract and stage2_interpret catch all exceptions
  - Return usable degraded responses rather than crashing
  - Errors are logged to stdout for debugging in Docker logs
"""

import json
import re
import os
from dotenv import load_dotenv

import google.generativeai as genai

from schemas import HouseFeatures, ExtractionResult
from prompts import STAGE1_PROMPT_V2, STAGE2_PROMPT

# Load environment variables from .env file
# This reads GEMINI_API_KEY and any other config
load_dotenv()

# Configure the Gemini API client with API key from environment
# The API key is a 39-character string starting with AIza...
# Never hardcode this — always load from environment
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Create a GenerativeModel client for the fast (flash) model
# gemini-2.5-flash is fast enough for real-time predictions (<1 second)
# and accurate enough for feature extraction
model = genai.GenerativeModel("gemini-2.5-flash")

# List of feature field names for validation and construction
# Must match the 10 fields in HouseFeatures schema and sklearn pipeline
FEATURE_FIELDS = [
    "GrLivArea",
    "BedroomAbvGr",
    "FullBath",
    "HalfBath",
    "TotalBsmtSF",
    "GarageArea",
    "OverallQual",
    "YearBuilt",
    "Neighborhood",
    "HouseStyle"
]


def _call_gemini(prompt: str) -> str:
    """
    Thin wrapper around the Gemini API call.
    
    Separated from stage1_extract and stage2_interpret so that:
    1. Both stages can reuse this function
    2. This function can be mocked in unit tests
    3. Retry logic and error handling can be centralized here in the future
    
    Args:
        prompt (str): The full prompt to send to Gemini
        
    Returns:
        str: The raw text response from the LLM
        
    Raises:
        Exception: If the API call fails (no retry logic here)
    """
    response = model.generate_content(prompt)
    return response.text


def _strip_fences(text: str) -> str:
    """
    Remove markdown code fences from LLM output.
    
    Gemini sometimes wraps JSON in ```json ... ``` markdown fences
    even when explicitly told not to. This function strips them.
    
    Examples:
        Input:  ```json\n{"key": "value"}\n```
        Output: {"key": "value"}
        
        Input:  ```\n{"key": "value"}\n```
        Output: {"key": "value"}
    
    Args:
        text (str): Raw LLM output potentially containing code fences
        
    Returns:
        str: Text with fences removed and stripped of whitespace
    """
    # Remove opening and closing ```json or ``` fences
    # Regex explanation:
    #   ``` — matches three backticks
    #   (?:json)? — optionally matches "json" after backticks (?: means non-capturing)
    # re.sub replaces all matches with empty string
    text = re.sub(r'```(?:json)?', '', text)
    return text.strip()


def stage1_extract(query: str) -> ExtractionResult:
    """
    Stage 1 of the LLM chain: Extract house features from natural language.
    
    This is the ENTRY POINT of the two-stage pipeline. It takes a natural
    language query from the user and extracts 10 structured features
    that feed directly into the ML model.
    
    The JSON keys must exactly match the sklearn pipeline column names.
    This function validates that and returns confidence levels so the UI
    can prompt the user to fill in missing values.
    
    Flow:
      1. Format STAGE1_PROMPT_V2 with the user query
      2. Call Gemini (with error handling)
      3. Parse the returned JSON
      4. Validate and construct HouseFeatures
      5. Return ExtractionResult with confidence, extracted fields, missing fields
    
    On any error (API failure, JSON parse failure, validation failure):
      - Log the error to stdout (for Docker logs)
      - Return a degraded ExtractionResult with empty features and all fields missing
      - This allows the UI to show the user and ask them to fill in manually
    
    Args:
        query (str): Natural language description of a house
        
    Returns:
        ExtractionResult: Structured features with confidence and field metadata
    """
    
    # Step 1: Format the Stage 1 prompt with the user's query
    # STAGE1_PROMPT_V2.format(query=query) replaces {query} placeholder
    prompt = STAGE1_PROMPT_V2.format(query=query)

    try:
        # Step 2: Call Gemini API
        # _call_gemini is a wrapper that catches its own errors
        raw = _call_gemini(prompt)
        
        # Step 3: Strip markdown fences (if Gemini added them)
        cleaned = _strip_fences(raw)
        
        # Step 4: Parse JSON
        # If this fails, json.JSONDecodeError is caught below
        data = json.loads(cleaned)

        # Step 5: Validate and construct HouseFeatures
        # Extract only the 10 feature fields from the LLM response
        # If the LLM returned {"bedrooms": 3}, that key won't be in FEATURE_FIELDS,
        # so it will be silently ignored (this is why confidence scores matter)
        feature_data = {k: data.get(k) for k in FEATURE_FIELDS}
        features = HouseFeatures(**feature_data)

        # Extract metadata from the LLM response
        # If the LLM didn't return these keys, we compute them from what we extracted
        extracted = data.get("extracted_fields", [
            k for k in FEATURE_FIELDS if data.get(k) is not None
        ])
        missing = data.get("missing_fields", [
            k for k in FEATURE_FIELDS if data.get(k) is None
        ])
        confidence = data.get("confidence", "low")
        
        # needs_clarification: is the extraction sufficient to make a prediction?
        # Threshold: fewer than 4 fields means we should ask the user for more info
        needs_clarification = data.get("needs_clarification", len(extracted) < 4)

        # Step 6: Return the successful ExtractionResult
        return ExtractionResult(
            features=features,
            extracted_fields=extracted,
            missing_fields=missing,
            confidence=confidence,
            needs_clarification=needs_clarification
        )

    except json.JSONDecodeError as e:
        # JSON parsing failed — the LLM returned invalid JSON
        # Log for debugging but don't crash — return degraded response
        print(f"[stage1] JSON parse failed: {e}\nRaw output: {raw}")
        return ExtractionResult(
            features=HouseFeatures(),  # Empty features (all null)
            extracted_fields=[],
            missing_fields=FEATURE_FIELDS,  # All fields missing
            confidence="low",
            needs_clarification=True
        )
        
    except Exception as e:
        # Catch-all for any other error: API failure, validation error, etc.
        print(f"[stage1] Unexpected error: {e}")
        return ExtractionResult(
            features=HouseFeatures(),
            extracted_fields=[],
            missing_fields=FEATURE_FIELDS,
            confidence="low",
            needs_clarification=True
        )


def stage2_interpret(
    features: HouseFeatures,
    predicted_price: float,
    train_stats: dict
) -> str:
    """
    Stage 2 of the LLM chain: Interpret the ML prediction in natural language.
    
    Given:
      - The confirmed HouseFeatures (what was fed to the ML model)
      - The predicted price from the ML model
      - Training set statistics (median, percentiles, std dev)
    
    Generate a 3-4 sentence explanation that:
      1. Compares the price to the market median (high/low/typical)
      2. Identifies specific features that drove the prediction
      3. Places the price in the market range (bottom, upper, etc.)
      4. Ends with an actionable observation
    
    Flow:
      1. Serialize HouseFeatures to JSON (only non-null values)
      2. Format STAGE2_PROMPT with features, price, and stats
      3. Call Gemini
      4. Return the interpretation string
    
    On any error:
      - Log to stdout
      - Return a fallback interpretation (raw numbers with no analysis)
      - This keeps the UI from breaking even if Gemini fails
    
    Args:
        features (HouseFeatures): The house features that were predicted on
        predicted_price (float): The ML model's predicted price in USD
        train_stats (dict): Training set statistics
          Keys: median_price, price_10th_percentile, price_90th_percentile, price_std
        
    Returns:
        str: Natural language interpretation of the prediction
    """
    
    # Step 1: Serialize HouseFeatures to JSON
    # Only include non-null values (if a field is None, it won't appear in the JSON)
    # This makes the output cleaner and more readable for the Stage 2 LLM
    features_json = json.dumps(
        {k: v for k, v in features.model_dump().items() if v is not None},
        indent=2
    )

    # Step 2: Format the Stage 2 prompt with all the context
    # Inject features, predicted price, and market statistics
    prompt = STAGE2_PROMPT.format(
        features_json=features_json,
        predicted_price=predicted_price,
        median_price=train_stats["median_price"],
        p10=train_stats["price_10th_percentile"],
        p90=train_stats["price_90th_percentile"],
        std=train_stats["price_std"]
    )

    try:
        # Step 3: Call Gemini and return the interpretation
        return _call_gemini(prompt).strip()
        
    except Exception as e:
        # If Gemini fails, return a fallback interpretation
        # This is a degraded but still useful response to show the user
        print(f"[stage2] Gemini call failed: {e}")
        return (
            f"The predicted price is ${predicted_price:,.0f}. "
            f"Market median is ${train_stats['median_price']:,.0f}. "
            f"(Full interpretation unavailable — Gemini API error.)"
        )
