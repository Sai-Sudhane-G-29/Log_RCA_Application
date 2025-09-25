"""
Database configuration and connection
"""

import databases
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from api.src.core.config import settings

# Database connection
database = databases.Database(settings.DATABASE_URL)
metadata = sqlalchemy.MetaData()

# SQLAlchemy setup
engine = sqlalchemy.create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_database():
    """Get database connection"""
    return database

def get_db_session():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
