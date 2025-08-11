"""
Database connection and session management utilities.
"""

import os
from typing import Generator
from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Base class for all ORM models
Base = declarative_base()

def get_database_url() -> str:
    """Get database URL from environment variable with fallback for development."""
    return os.getenv(
        "DATABASE_URL", 
        "postgresql://newsfrontier:dev_password@localhost:5432/newsfrontier_db"
    )

def create_engine(database_url: str = None):
    """Create SQLAlchemy engine with optimal configuration."""
    if database_url is None:
        database_url = get_database_url()
    
    return sqlalchemy_create_engine(
        database_url,
        echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections after 1 hour
    )

def create_session_maker(engine=None):
    """Create a session maker with the given engine."""
    if engine is None:
        engine = create_engine()
    
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency function to get database session."""
    SessionLocal = create_session_maker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()