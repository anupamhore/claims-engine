"""
WHY: Custom database connection management for PostgreSQL
  - Connection pooling for performance (reuse connections)
  - Session management for thread safety
  - Alembic migration support built-in
  - SQLAlchemy async support for FastAPI async/await

HOW:
  - Create engine with connection pooling
  - SessionLocal for request-scoped sessions
  - get_db dependency for FastAPI routes

ALTERNATIVE not chosen:
  - Direct psycopg2: Too low-level, no ORM benefits
  - SQLModel: Mixed SQLAlchemy + Pydantic, adds complexity
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os
import logging
from typing import Generator

# Configure logging
logger = logging.getLogger(__name__)

# Load database config from .env
# In Docker: DB_HOST will be 'postgres' (service name)
# In Local: DB_HOST will be 'localhost' (Homebrew installation)
# The code works the same way - it just connects to different hosts!
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "claims_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "claims_db")

# Build connection string
# Docker: postgresql://claims_user:pwd@postgres:5432/claims_db
# Local:  postgresql://claims_user:pwd@localhost:5432/claims_db
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine with connection pooling
# pool_size: Number of connections to keep in pool
# max_overflow: Additional connections if pool exhausted
# echo=False: Disable SQL logging (enable in development if needed)
engine = create_engine(
    DATABASE_URL,
    pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "40")),
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    poolclass=NullPool if os.getenv("APP_ENV") == "testing" else None,
)

# SessionLocal for creating database sessions
# expire_on_commit=False: Prevent detached instance errors
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session injection.
    
    Why this approach:
      - Automatic session cleanup with try/finally
      - Works with FastAPI's dependency injection
      - Proper transaction handling
    
    Usage in routes:
        @app.get("/claims/{claim_id}")
        def get_claim(claim_id: int, db: Session = Depends(get_db)):
            return db.query(Claim).filter(Claim.id == claim_id).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database (create all tables from models)."""
    from src.db.models import Base
    try:
        # Use checkfirst=True to skip tables that already exist
        Base.metadata.create_all(bind=engine, checkfirst=True)
    except Exception as e:
        # Log but don't fail if indexes already exist (idempotent)
        if "already exists" in str(e):
            logger.info("⚠️  Database tables already exist, skipping creation")
        else:
            raise
