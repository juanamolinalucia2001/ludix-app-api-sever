"""
Database configuration and session management.
Implements the Factory pattern for database session creation.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ludix_user:ludix_password@localhost:5432/ludix_db"
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# SessionLocal class - Factory pattern for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.
    Factory pattern: Creates a new session for each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
