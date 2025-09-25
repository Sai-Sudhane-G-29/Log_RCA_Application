"""
Database utilities for batch processing
"""

import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from contextlib import contextmanager
import pymysql

from api.src.core.config import settings
from api.src.core.logging import get_logger
from api.src.db.database import SessionLocal

logger = get_logger(__name__)

class DatabaseManager:
    """Database utility class for managing connections and operations"""
    
    def __init__(self):
        self.logger = logger
    
    @contextmanager
    def get_db_session(self):
        """Get database session with automatic cleanup"""
        session = SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_db_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            self.logger.error(f"Database connection test failed: {str(e)}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results"""
        try:
            with self.get_db_session() as session:
                result = session.execute(text(query), params or {})
                if result.returns_rows:
                    columns = result.keys()
                    rows = result.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                else:
                    session.commit()
                    return []
        except Exception as e:
            self.logger.error(f"Error executing query: {str(e)}")
            raise

class DorisDBManager:
    """DorisDB utility class for managing connections and operations"""
    
    def __init__(self):
        self.logger = logger
        self.host = settings.DORIS_HOST
        self.port = settings.DORIS_PORT
        self.username = settings.DORIS_USERNAME
        self.password = settings.DORIS_PASSWORD
        self.database = settings.DORIS_DATABASE
    
    def get_connection(self):
        """Get DorisDB connection"""
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                charset='utf8mb4'
            )
            return connection
        except Exception as e:
            self.logger.error(f"Error connecting to DorisDB: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """Test DorisDB connection"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"DorisDB connection test failed: {str(e)}")
            return False
    
    def create_table(self, table_name: str, schema: Dict[str, str]) -> bool:
        """Create table in DorisDB"""
        try:
            columns = []
            for column_name, column_type in schema.items():
                columns.append(f"`{column_name}` {column_type}")
            
            columns_sql = ",\n    ".join(columns)
            
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                {columns_sql}
            )
            DISTRIBUTED BY HASH(`id`) BUCKETS 10
            PROPERTIES (
                "replication_num" = "1"
            )
            """
            
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info(f"Created table {table_name} in DorisDB")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating table {table_name}: {str(e)}")
            return False
    
    def bulk_insert(self, table_name: str, data: List[Dict[str, Any]]) -> bool:
        """Bulk insert data into DorisDB table"""
        try:
            if not data:
                return True
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get column names from the first row
            columns = list(data[0].keys())
            placeholders = ', '.join(['%s'] * len(columns))
            columns_sql = ', '.join([f'`{col}`' for col in columns])
            
            insert_sql = f"INSERT INTO `{table_name}` ({columns_sql}) VALUES ({placeholders})"
            
            # Prepare data for bulk insert
            values = []
            for row in data:
                values.append(tuple(row[col] for col in columns))
            
            cursor.executemany(insert_sql, values)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            self.logger.info(f"Bulk inserted {len(data)} records into {table_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error bulk inserting into {table_name}: {str(e)}")
            return False
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute query on DorisDB"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error executing DorisDB query: {str(e)}")
            raise
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a table"""
        try:
            query = f"DESCRIBE `{table_name}`"
            columns = self.execute_query(query)
            
            count_query = f"SELECT COUNT(*) as count FROM `{table_name}`"
            count_result = self.execute_query(count_query)
            row_count = count_result[0]['count'] if count_result else 0
            
            return {
                "table_name": table_name,
                "columns": columns,
                "row_count": row_count
            }
            
        except Exception as e:
            self.logger.error(f"Error getting table info for {table_name}: {str(e)}")
            return {}

class MigrationManager:
    """Database migration utility"""
    
    def __init__(self):
        self.logger = logger
    
    def create_tables(self) -> bool:
        """Create all required tables"""
        try:
            from api.src.models.job import Base
            from api.src.db.database import engine
            
            # Create tables
            Base.metadata.create_all(bind=engine)
            
            self.logger.info("Database tables created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating tables: {str(e)}")
            return False
    
    def drop_tables(self) -> bool:
        """Drop all tables (use with caution)"""
        try:
            from api.src.models.job import Base
            from api.src.db.database import engine
            
            # Drop tables
            Base.metadata.drop_all(bind=engine)
            
            self.logger.info("Database tables dropped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error dropping tables: {str(e)}")
            return False
    
    def migrate_data(self, source_table: str, destination_table: str, mapping: Dict[str, str]) -> bool:
        """Migrate data between tables with column mapping"""
        try:
            db_manager = DatabaseManager()
            
            # Read data from source table
            source_columns = ', '.join(mapping.keys())
            source_query = f"SELECT {source_columns} FROM {source_table}"
            source_data = db_manager.execute_query(source_query)
            
            # Transform data according to mapping
            transformed_data = []
            for row in source_data:
                transformed_row = {}
                for source_col, dest_col in mapping.items():
                    transformed_row[dest_col] = row[source_col]
                transformed_data.append(transformed_row)
            
            # Insert into destination table
            if transformed_data:
                dest_columns = ', '.join(mapping.values())
                placeholders = ', '.join([f":{col}" for col in mapping.values()])
                insert_query = f"INSERT INTO {destination_table} ({dest_columns}) VALUES ({placeholders})"
                
                with db_manager.get_db_session() as session:
                    for row in transformed_data:
                        session.execute(text(insert_query), row)
                    session.commit()
            
            self.logger.info(f"Migrated {len(transformed_data)} records from {source_table} to {destination_table}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error migrating data: {str(e)}")
            return False

# Global instances
db_manager = DatabaseManager()
doris_manager = DorisDBManager()
migration_manager = MigrationManager()
