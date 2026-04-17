"""
Streamlit frontend for the Real Estate Agent.

UX Flow:
  Step 1 — Text area: user enters natural language query
  Step 2 — "Extract Features" button → POST /extract
  Step 3 — Show extracted features (green checkmarks) + missing features (input fields)
  Step 4 — "Predict Price" button → POST /predict
  Step 5 — Show predicted price with st.metric()
  Step 6 — Show Stage 2 interpretation in st.info()
  Step 7 — If confidence == "low" → st.warning()
  Step 8 — On any API error → st.error()

State management:
  - st.session_state persists data between button clicks
  - Extraction results are cached so clicking "Predict" doesn't re-extract
"""

import streamlit as st
import requests
import os
from typing import Optional

# Page configuration
st.set_page_config(
    page_title="Real Estate Agent",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# API endpoint configuration
# Default to http://localhost:8000
# Override with environment variable API_URL if provided
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Initialize session state variables
if "query" not in st.session_state:
    st.session_state.query = ""
if "extracted_features" not in st.session_state:
    st.session_state.extracted_features = None
if "predicted_price" not in st.session_state:
    st.session_state.predicted_price = None
if "interpretation" not in st.session_state:
    st.session_state.interpretation = None


def check_api_health() -> bool:
    """Check if the backend API is reachable."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except Exception:
        return False


def extract_features(query: str) -> Optional[dict]:
    """Call the /extract endpoint to extract house features."""
    try:
        response = requests.post(
            f"{API_URL}/extract",
            json={"query": query},
            timeout=15
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Extraction failed: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(
            f"Cannot connect to backend at {API_URL}. "
            f"Is the FastAPI app running?"
        )
        return None
    except Exception as e:
        st.error(f"Extraction error: {str(e)}")
        return None


def predict_with_features(query: str, features: dict) -> Optional[dict]:
    """Call the /predict endpoint with confirmed features."""
    try:
        response = requests.post(
            f"{API_URL}/predict",
            json={"query": query, "features": features},
            timeout=15
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Prediction failed: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(
            f"Cannot connect to backend at {API_URL}. "
            f"Is the FastAPI app running?"
        )
        return None
    except Exception as e:
        st.error(f"Prediction error: {str(e)}")
        return None


# Main title
st.title("🏠 Real Estate Agent")
st.markdown(
    "Describe a house and get an AI-powered price prediction powered by LLMs and ML"
)

# Check API health
if not check_api_health():
    st.error(
        f"❌ Backend API not reachable at {API_URL}\n\n"
        f"Please ensure the FastAPI app is running:\n"
        f"`uvicorn main:app --host 0.0.0.0 --port 8000`"
    )
    st.stop()

st.success(f"✅ Connected to backend at {API_URL}")

# Step 1: User input
st.subheader("Step 1: Describe the House")
query = st.text_area(
    "Describe a house (natural language):",
    value=st.session_state.query,
    height=80,
    placeholder="Example: 3 bedroom house in a good neighborhood with a 2 car garage..."
)
st.session_state.query = query

# Step 2: Extract features button
if st.button("Extract Features", use_container_width=True):
    if not query.strip():
        st.warning("Please enter a description first")
    else:
        with st.spinner("Extracting features..."):
            result = extract_features(query)
            if result:
                st.session_state.extracted_features = result
                st.success("Features extracted!")

# Step 3: Show extraction results and missing fields
if st.session_state.extracted_features:
    st.subheader("Step 2: Review Extracted Features")
    
    extraction = st.session_state.extracted_features
    features = extraction.get("features", {})
    extracted_fields = extraction.get("extracted_fields", [])
    missing_fields = extraction.get("missing_fields", [])
    confidence = extraction.get("confidence", "low")
    needs_clarification = extraction.get("needs_clarification", False)
    
    # Show confidence and warnings
    col1, col2 = st.columns(2)
    with col1:
        confidence_color = (
            "green" if confidence == "high"
            else "orange" if confidence == "medium"
            else "red"
        )
        st.markdown(
            f"**Confidence:** :{confidence_color}[{confidence.upper()}]"
        )
    
    with col2:
        num_extracted = len(extracted_fields)
        num_total = num_extracted + len(missing_fields)
        st.markdown(f"**Fields extracted:** {num_extracted}/{num_total}")
    
    if needs_clarification:
        st.warning(
            "⚠️ Many features are missing. Please fill in the missing fields below "
            "for a more accurate prediction."
        )
    
    # Extracted features (read-only display)
    if extracted_fields:
        st.markdown("**✅ Extracted Features:**")
        cols = st.columns(2)
        for i, field in enumerate(extracted_fields):
            value = features.get(field)
            col = cols[i % 2]
            col.markdown(f"- **{field}:** {value}")
    
    # Missing fields (user input)
    if missing_fields:
        st.markdown("**❌ Missing Features (please fill in):**")
        
        # Build a form for the user to fill in missing fields
        with st.form("missing_fields_form"):
            for field in missing_fields:
                if field in ["GrLivArea", "TotalBsmtSF", "GarageArea"]:
                    # Float fields
                    features[field] = st.number_input(
                        f"{field} (square feet):",
                        value=None,
                        step=100.0
                    )
                elif field in ["BedroomAbvGr", "FullBath", "HalfBath", "OverallQual", "YearBuilt"]:
                    # Integer fields
                    features[field] = st.number_input(
                        f"{field}:",
                        value=None,
                        step=1
                    )
                elif field in ["Neighborhood", "HouseStyle"]:
                    # String fields
                    features[field] = st.text_input(f"{field}:")
            
            submitted = st.form_submit_button(
                "Confirm & Predict Price",
                use_container_width=True
            )
            
            if submitted:
                # Step 4: Call /predict with confirmed features
                with st.spinner("Predicting price..."):
                    result = predict_with_features(query, features)
                    if result:
                        st.session_state.predicted_price = result.get("predicted_price")
                        st.session_state.interpretation = result.get("interpretation")
    else:
        # All fields extracted — user can go straight to prediction
        if st.button("Predict Price", use_container_width=True, type="primary"):
            with st.spinner("Predicting price..."):
                result = predict_with_features(query, features)
                if result:
                    st.session_state.predicted_price = result.get("predicted_price")
                    st.session_state.interpretation = result.get("interpretation")


# Step 5, 6, 7: Show prediction results
if st.session_state.predicted_price is not None:
    st.subheader("Step 3: Prediction Result")
    
    # Display the predicted price prominently
    st.metric(
        label="Predicted Sale Price",
        value=f"${st.session_state.predicted_price:,.0f}",
        delta=None
    )
    
    # Display the Stage 2 interpretation
    if st.session_state.interpretation:
        st.info(st.session_state.interpretation)
    
    # Show warning if confidence is low
    extraction = st.session_state.extracted_features
    if extraction and extraction.get("confidence") == "low":
        st.warning(
            "⚠️ Low confidence prediction. The model had to infer many features. "
            "For more accurate results, provide more details about the property."
        )
    
    # Option to start over
    if st.button("Start Over", use_container_width=True):
        st.session_state.query = ""
        st.session_state.extracted_features = None
        st.session_state.predicted_price = None
        st.session_state.interpretation = None
        st.rerun()


# Footer
st.divider()
st.markdown(
    """
    **How it works:**
    1. Describe a house in natural language
    2. AI extracts structured features using Gemini LLM
    3. ML model trained on Ames Housing dataset predicts the price
    4. AI interprets the prediction in natural language
    
    **Model:** scikit-learn pipeline (Ridge / RandomForest / GradientBoosting)
    **LLM:** Google Gemini API (gemini-2.5-flash)
    **Dataset:** Ames Housing (Kaggle)
    """
)
