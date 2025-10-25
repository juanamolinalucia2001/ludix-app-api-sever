from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG  # Show SQL queries in debug mode
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    """
    Database dependency for FastAPI.
    Creates a new database session for each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Observer Pattern: Database Event Listeners
from sqlalchemy import event
from datetime import datetime

def update_timestamp(mapper, connection, target):
    """Observer: Update timestamp on model changes"""
    if hasattr(target, 'updated_at'):
        target.updated_at = datetime.utcnow()

# Register the observer for all models with updated_at field
@event.listens_for(Base, 'mapper_configured', propagate=True)
def receive_mapper_configured(mapper, class_):
    """Register timestamp observer for models with updated_at field"""
    if hasattr(class_, 'updated_at'):
        event.listen(mapper, 'before_update', update_timestamp)
