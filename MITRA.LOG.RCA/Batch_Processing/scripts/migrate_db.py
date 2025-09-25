"""
Database migration script for creating initial tables
"""

from sqlalchemy import create_engine
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.src.models.job import Base
from api.src.core.config import settings
from api.src.core.logging import get_logger, setup_logging

def create_tables():
    """Create all database tables"""
    setup_logging()
    logger = get_logger(__name__)
    
    try:
        # Create database engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database tables created successfully")
        print("✅ Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        print(f"❌ Error creating tables: {str(e)}")
        sys.exit(1)

def drop_tables():
    """Drop all database tables"""
    setup_logging()
    logger = get_logger(__name__)
    
    try:
        # Create database engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        
        logger.info("Database tables dropped successfully")
        print("✅ Database tables dropped successfully")
        
    except Exception as e:
        logger.error(f"Error dropping tables: {str(e)}")
        print(f"❌ Error dropping tables: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration script")
    parser.add_argument(
        "action", 
        choices=["create", "drop"], 
        help="Action to perform: create or drop tables"
    )
    
    args = parser.parse_args()
    
    if args.action == "create":
        create_tables()
    elif args.action == "drop":
        drop_tables()
