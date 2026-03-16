"""
WHY: SQLAlchemy ORM models for database schema
  - Type-safe ORM layer (prevents SQL injection)
  - Automatic schema migration support (Alembic)
  - Relationship management (foreign keys, joins)
  - Built-in validation hooks

HOW:
  - Base class with declarative_base()
  - Each model = one database table
  - Column types match PostgreSQL types

ALTERNATIVE not chosen:
  - Raw SQL: Error-prone, no type safety
  - Peewee ORM: Lighter but less powerful
"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, DECIMAL, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# Declarative base for all models
Base = declarative_base()


class Claim(Base):
    """
    Claims table: Core claim submission and metadata.
    
    Why this schema:
      - claim_id: Unique identifier
      - text: Full claim narrative (for NLP processing)
      - category: Type of claim (auto, home, health, life)
      - urgency: Priority level (critical, high, medium, low)
      - amount: Claim amount in dollars
      - claimant_id: Reference to claimant
      - provider_id: Reference to service provider
      - created_at: Timestamp for auditing
    """
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)  # Full claim narrative
    category = Column(String(50), nullable=False)  # auto, home, health, life
    urgency = Column(String(20), nullable=False)  # critical, high, medium, low
    amount = Column(DECIMAL(15, 2), nullable=False)
    claimant_id = Column(String(100), nullable=False, index=True)
    provider_id = Column(String(100), nullable=True, index=True)
    status = Column(String(50), default="pending")  # pending, approved, rejected, under_review
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    fraud_scores = relationship("FraudScore", back_populates="claim", cascade="all, delete-orphan")
    explanations = relationship("Explanation", back_populates="claim", cascade="all, delete-orphan")
    feedbacks = relationship("UserFeedback", back_populates="claim", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_claims_created_at", "created_at"),
        Index("ix_claims_claimant_provider", "claimant_id", "provider_id"),
    )


class FraudScore(Base):
    """
    Fraud scores table: ML model predictions for each claim.
    
    Why this schema:
      - ml_score: XGBoost raw prediction (0-100)
      - pattern_score: Pattern matching confidence (0-100)
      - ensemble_score: Final weighted fraud score (0-100)
      - confidence: Confidence in ensemble score (0-1)
      - model_version: Track which model generated this
      - flagged: Boolean for high-risk claims
    """
    __tablename__ = "fraud_scores"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    ml_score = Column(Float, nullable=False)  # XGBoost prediction
    pattern_score = Column(Float, nullable=False)  # Pattern matching score
    ensemble_score = Column(Float, nullable=False)  # Final score (0-100)
    confidence = Column(Float, nullable=False)  # Confidence level (0-1)
    model_version = Column(String(20), nullable=False)  # v1.0, v2.1, etc.
    flagged = Column(Boolean, default=False)  # High-risk flag
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    claim = relationship("Claim", back_populates="fraud_scores")


class Explanation(Base):
    """
    Explanations table: LLM-generated explanations for fraud decisions.
    
    Why this schema:
      - llm_explanation: Human-readable text (500 chars max)
      - sources: JSON array of fact sources (for RAG audit trail)
      - explanation_confidence: LLM confidence (0-1)
      - model_used: Which LLM (groq, openai, template)
      - hallucination_score: Risk of hallucination (0-1)
      - generated_at: Timestamp (for tracing)
    """
    __tablename__ = "explanations"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    llm_explanation = Column(Text, nullable=False)  # The explanation text
    sources = Column(JSON, nullable=True)  # Array of source facts used
    explanation_confidence = Column(Float, nullable=False)  # LLM confidence (0-1)
    model_used = Column(String(20), nullable=False)  # groq, openai, template
    hallucination_score = Column(Float, nullable=True)  # Risk of hallucination
    model_version = Column(String(20), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    claim = relationship("Claim", back_populates="explanations")


class UserFeedback(Base):
    """
    User feedback table: Auditor corrections and feedback.
    
    Why this schema:
      - feedback_type: correction, approved, disputed
      - corrected_label: What auditor thinks is correct (if correction)
      - corrected_score: Auditor's fraud score estimate
      - comments: Free-form auditor notes
      - auditor_id: Which auditor gave feedback (for tracking)
    """
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    auditor_id = Column(String(100), nullable=False, index=True)
    feedback_type = Column(String(50), nullable=False)  # correction, approved, disputed
    corrected_label = Column(String(20), nullable=True)  # What auditor thinks (if correction)
    corrected_score = Column(Float, nullable=True)  # Auditor's fraud score estimate
    comments = Column(Text, nullable=True)  # Free-form notes
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    claim = relationship("Claim", back_populates="feedbacks")


class AuditLog(Base):
    """
    Audit logs table: Track all actions for compliance.
    
    Why this schema:
      - action: What happened (submit_claim, generate_explanation, etc.)
      - user_id: Who did it
      - claim_id: Related claim (if applicable)
      - details: JSON with additional context
      - timestamp: When it happened
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=True)
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="SET NULL"), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class FraudPattern(Base):
    """
    Fraud patterns table: Known patterns for pattern matching.
    
    Why this schema:
      - pattern_description: Human description of pattern
      - keywords: Keywords to search for
      - historical_examples: Example cases matching pattern
      - detection_rule: Rule used to detect (for future matching)
      - severity: Risk level (low, medium, high)
    """
    __tablename__ = "fraud_patterns"

    id = Column(Integer, primary_key=True, index=True)
    pattern_description = Column(String(255), nullable=False)
    keywords = Column(JSON, nullable=False)  # Array of keywords
    historical_examples = Column(JSON, nullable=True)  # Array of example claim IDs
    detection_rule = Column(Text, nullable=False)  # Rule/logic for detection
    severity = Column(String(20), nullable=False)  # low, medium, high
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
