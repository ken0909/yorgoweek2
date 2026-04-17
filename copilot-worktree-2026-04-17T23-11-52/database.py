"""
Database configuration and models for the Real Estate Agent.

This module handles:
1. SQLAlchemy engine and session setup (connects to Postgres)
2. Base declarative class for all models
3. Database models: User, Prediction, ExtractionLog
4. Initialization function to create tables on startup

Models are designed to support:
- Storing extracted features and predictions
- Tracking extraction confidence and missing fields
- Audit trail of predictions and user interactions
- Multi-user support (optional, for future expansion)
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Build the Postgres connection URL from environment variables
# Format: postgresql+psycopg2://user:password@host:port/database
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/real_estate_agent"
)

# Create SQLAlchemy engine
# echo=True logs all SQL queries (verbose, useful for debugging)
# pool_pre_ping=True ensures connections are alive before using them
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# SessionLocal is the factory function for creating database sessions
# Each request will get its own session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all declarative models
Base = declarative_base()


class User(Base):
    """User model for multi-tenant support (optional, for future expansion)."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class ExtractionLog(Base):
    """
    Stores Stage 1 LLM extraction results.
    
    This is valuable for:
    - Debugging extraction failures
    - Auditing LLM performance
    - Retraining LLM prompts based on real user queries
    """
    
    __tablename__ = "extraction_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    extracted_fields = Column(JSON)  # List of field names the LLM extracted
    missing_fields = Column(JSON)    # List of field names the LLM missed
    confidence = Column(String)      # "high", "medium", "low"
    features = Column(JSON)          # Full HouseFeatures JSON
    needs_clarification = Column(Boolean, default=True)
    error = Column(String, nullable=True)  # If extraction failed, store error message
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ExtractionLog(id={self.id}, confidence={self.confidence}, query={self.query[:50]}...)>"


class Prediction(Base):
    """
    Stores full prediction results from /predict endpoint.
    
    This is the main audit trail of predictions made by the system.
    Includes features, model output, LLM interpretation, confidence, etc.
    """
    
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Input data
    query = Column(String, index=True)
    features = Column(JSON)  # Full HouseFeatures JSON
    
    # Model output
    predicted_price = Column(Float, index=True)
    
    # LLM Stage 2 interpretation
    interpretation = Column(String)
    
    # Metadata about the prediction
    extracted_fields = Column(JSON)
    missing_fields = Column(JSON)
    confidence = Column(String)  # "high", "medium", "low"
    warning = Column(String, nullable=True)
    
    # Optional: link to extraction log (if extraction was needed)
    extraction_log_id = Column(Integer, ForeignKey("extraction_logs.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, price=${self.predicted_price:,.0f}, confidence={self.confidence})>"


def init_db():
    """
    Create all tables in the database.
    
    Called once at FastAPI startup.
    If tables already exist, SQLAlchemy's create_all() is idempotent (safe to call multiple times).
    """
    print("[database] Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("[database] Tables created successfully")


def get_db():
    """
    FastAPI dependency for injecting a database session into route handlers.
    
    Usage in endpoints:
        @app.get("/predictions")
        def get_predictions(db: Session = Depends(get_db)):
            return db.query(Prediction).all()
    
    The session is automatically closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
