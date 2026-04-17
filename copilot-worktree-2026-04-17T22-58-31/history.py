"""
History and analytics endpoints for the Real Estate Agent.

These endpoints allow users to:
1. Retrieve past predictions
2. View extraction logs (for debugging)
3. Get statistics about model performance
4. Delete old records
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db, Prediction, ExtractionLog

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/predictions")
def list_predictions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a paginated list of all predictions.
    
    Query parameters:
      - skip: number of records to skip (default: 0)
      - limit: maximum number of records to return (default: 100)
    
    Returns: List of predictions ordered by most recent first
    """
    predictions = db.query(Prediction).order_by(
        desc(Prediction.created_at)
    ).offset(skip).limit(limit).all()
    return predictions


@router.get("/predictions/{prediction_id}")
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single prediction by ID.
    
    Returns: Prediction record with all details
    Raises: 404 if prediction not found
    """
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id
    ).first()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    return prediction


@router.delete("/predictions/{prediction_id}")
def delete_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """
    Delete a single prediction by ID.
    
    Returns: Success message
    Raises: 404 if prediction not found
    """
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id
    ).first()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    db.delete(prediction)
    db.commit()
    
    return {"message": f"Prediction {prediction_id} deleted successfully"}


@router.get("/extractions")
def list_extractions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve extraction logs (Stage 1 LLM output).
    
    Useful for debugging extraction failures and auditing LLM performance.
    
    Query parameters:
      - skip: number of records to skip (default: 0)
      - limit: maximum number of records to return (default: 100)
    
    Returns: List of extraction logs ordered by most recent first
    """
    logs = db.query(ExtractionLog).order_by(
        desc(ExtractionLog.created_at)
    ).offset(skip).limit(limit).all()
    return logs


@router.get("/extractions/{extraction_id}")
def get_extraction(extraction_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single extraction log by ID.
    
    Returns: Extraction log with all details
    Raises: 404 if extraction log not found
    """
    log = db.query(ExtractionLog).filter(
        ExtractionLog.id == extraction_id
    ).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Extraction log not found")
    
    return log


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Get aggregate statistics about predictions.
    
    Returns:
      - total_predictions: Number of predictions made
      - avg_price: Average predicted price
      - confidence_distribution: Count of high/medium/low confidence predictions
      - latest_prediction: Most recent prediction record
    """
    from sqlalchemy import func
    
    total = db.query(func.count(Prediction.id)).scalar()
    
    if total == 0:
        return {
            "total_predictions": 0,
            "avg_price": None,
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
            "latest_prediction": None
        }
    
    avg_price = db.query(func.avg(Prediction.predicted_price)).scalar()
    
    confidence_dist = db.query(
        Prediction.confidence,
        func.count(Prediction.id)
    ).group_by(Prediction.confidence).all()
    
    confidence_distribution = {
        "high": 0,
        "medium": 0,
        "low": 0
    }
    for conf, count in confidence_dist:
        if conf in confidence_distribution:
            confidence_distribution[conf] = count
    
    latest = db.query(Prediction).order_by(
        desc(Prediction.created_at)
    ).first()
    
    return {
        "total_predictions": total,
        "avg_price": float(avg_price) if avg_price else None,
        "confidence_distribution": confidence_distribution,
        "latest_prediction": latest
    }


@router.delete("/predictions/older-than/{days}")
def delete_old_predictions(days: int, db: Session = Depends(get_db)):
    """
    Delete predictions older than N days.
    
    Useful for cleanup and GDPR compliance.
    
    Path parameter:
      - days: Delete predictions older than this many days
    
    Returns: Count of deleted predictions
    """
    from datetime import datetime, timedelta
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    count = db.query(Prediction).filter(
        Prediction.created_at < cutoff
    ).delete()
    
    db.commit()
    
    return {"deleted": count, "cutoff_date": cutoff.isoformat()}
