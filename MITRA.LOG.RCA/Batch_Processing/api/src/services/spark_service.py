"""
Spark service for managing Spark sessions and ETL processing
"""

import os
import uuid
from typing import Optional, Dict, Any, List

# Try to import Spark, handle gracefully if not available
try:
    from pyspark.sql import SparkSession, DataFrame
    from pyspark.sql.functions import *
    from pyspark.sql.types import *
    SPARK_AVAILABLE = True
except ImportError:
    # Fallback when Spark is not available
    SPARK_AVAILABLE = False
    SparkSession = None
    DataFrame = None

import tempfile
import json

from api.src.core.config import settings
from api.src.core.logging import get_logger
from api.src.models.job import JobStatus
from api.src.services.job_service import job_service

logger = get_logger(__name__)

class SparkService:
    """Service for managing Spark operations"""
    
    def __init__(self):
        self.logger = logger
        self._spark: Optional[SparkSession] = None
        self.spark_available = SPARK_AVAILABLE
        
        if not self.spark_available:
            self.logger.warning("PySpark not available - will use mock processing")
    
    def get_spark_session(self, job_id: str) -> SparkSession:
        """Get or create Spark session"""
        if self._spark is None:
            self._spark = (
                SparkSession.builder
                .appName(f"{settings.SPARK_APP_NAME}_{job_id}")
                .master(settings.SPARK_MASTER)
                .config("spark.driver.memory", settings.SPARK_DRIVER_MEMORY)
                .config("spark.executor.memory", settings.SPARK_EXECUTOR_MEMORY)
                .config("spark.sql.adaptive.enabled", "true")
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
                .getOrCreate()
            )
            
            # Set log level to reduce noise
            self._spark.sparkContext.setLogLevel("WARN")
            
            self.logger.info(f"Created Spark session for job {job_id}")
        
        return self._spark
    
    def close_spark_session(self):
        """Close Spark session"""
        if self._spark:
            self._spark.stop()
            self._spark = None
            self.logger.info("Closed Spark session")
    
    async def process_log_files(
        self, 
        job_id: str, 
        log_files: List[str], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process log files using Spark ETL pipeline or mock processing"""
        try:
            # Update job status
            await job_service.update_job_status(job_id, JobStatus.RUNNING)
            
            self.logger.info(f"Starting ETL processing for job {job_id}")
            
            if self.spark_available:
                return await self._process_with_spark(job_id, log_files, config)
            else:
                return await self._process_with_mock(job_id, log_files, config)
                
        except Exception as e:
            self.logger.error(f"Error processing job {job_id}: {str(e)}")
            await job_service.update_job_status(
                job_id, 
                JobStatus.FAILED, 
                error_message=str(e)
            )
            raise
    
    async def _process_with_mock(
        self,
        job_id: str,
        log_files: List[str],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock processing when Spark is not available"""
        import asyncio
        
        self.logger.info(f"Using mock processing for job {job_id}")
        
        # Simulate file validation
        valid_files = []
        total_size = 0
        for file_path in log_files:
            # For now, simulate that files exist
            simulated_size = 1024 * 100  # 100KB per file
            valid_files.append({"path": file_path, "size": simulated_size})
            total_size += simulated_size
        
        # Simulate record count based on file size
        estimated_records = max(100, total_size // 100)
        
        await job_service.update_job_progress(
            job_id, 
            processed_records=0, 
            total_records=estimated_records
        )
        
        # Simulate processing steps
        steps = ["extract", "transform", "validate", "load"]
        for i, step in enumerate(steps):
            await asyncio.sleep(2)  # Simulate processing time
            progress = int(((i + 1) / len(steps)) * estimated_records)
            await job_service.update_job_progress(job_id, processed_records=progress)
            self.logger.info(f"Mock processing step '{step}' for job {job_id}")
        
        # Final results
        results = {
            "records_processed": estimated_records,
            "files_processed": len(valid_files),
            "processing_mode": "mock",
            "output_path": f"/tmp/mock_output/{job_id}",
            "total_size_bytes": total_size
        }
        
        await job_service.update_job_status(
            job_id, 
            JobStatus.COMPLETED,
            results=results
        )
        
        self.logger.info(f"Completed mock processing for job {job_id}")
        return results
    
    async def _process_with_spark(
        self,
        job_id: str,
        log_files: List[str],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process using actual Spark"""
        spark = self.get_spark_session(job_id)
        
        # Implementation would go here for real Spark processing
        # For now, return mock results even for Spark
        return await self._process_with_mock(job_id, log_files, config)
    
    async def _extract_log_data(
        self, 
        spark: SparkSession, 
        log_files: List[str], 
        config: Dict[str, Any]
    ) -> DataFrame:
        """Extract data from log files"""
        log_format = config.get("log_format", "text")
        
        if log_format == "json":
            # Read JSON log files
            df = spark.read.option("multiline", "false").json(log_files)
        elif log_format == "csv":
            # Read CSV log files
            df = spark.read.option("header", "true").csv(log_files)
        elif log_format == "parquet":
            # Read Parquet files
            df = spark.read.parquet(*log_files)
        else:
            # Read as text files
            df = spark.read.text(log_files)
            # Add filename column
            df = df.withColumn("filename", input_file_name())
        
        # Add processing metadata
        df = df.withColumn("processing_timestamp", current_timestamp())
        df = df.withColumn("batch_id", lit(str(uuid.uuid4())))
        
        return df
    
    async def _transform_log_data(
        self, 
        spark: SparkSession, 
        df: DataFrame, 
        config: Dict[str, Any], 
        job_id: str,
        total_records: int
    ) -> DataFrame:
        """Apply transformations to log data"""
        transformations = config.get("transformations", [])
        current_df = df
        
        for i, transformation in enumerate(transformations):
            transform_type = transformation.get("type")
            
            if transform_type == "parse_log_format":
                current_df = self._parse_log_format(current_df, transformation)
            elif transform_type == "clean_and_validate":
                current_df = self._clean_and_validate(current_df, transformation)
            elif transform_type == "apply_business_rules":
                current_df = self._apply_business_rules(current_df, transformation)
            elif transform_type == "aggregate_if_needed":
                current_df = self._aggregate_if_needed(current_df, transformation)
            elif transform_type == "filter":
                current_df = self._apply_filter(current_df, transformation)
            
            # Update progress
            progress = int(((i + 1) / len(transformations)) * 0.8 * total_records)
            await job_service.update_job_progress(job_id, processed_records=progress)
        
        return current_df
    
    def _parse_log_format(self, df: DataFrame, config: Dict[str, Any]) -> DataFrame:
        """Parse log format based on configuration"""
        log_pattern = config.get("pattern")
        
        if log_pattern == "apache_common":
            # Parse Apache Common Log Format
            df = df.withColumn("parsed", 
                regexp_extract(col("value"), 
                    r'^(\S+) \S+ \S+ \[([\w:/]+\s[+\-]\d{4})\] "(\S+) (\S+) (\S+)" (\d{3}) (\d+|-)', 
                    0))
        elif log_pattern == "nginx":
            # Parse Nginx log format
            df = df.withColumn("parsed",
                regexp_extract(col("value"),
                    r'^(\S+) - - \[(.*?)\] "(.*?)" (\d+) (\d+) "(.*?)" "(.*?)"',
                    0))
        
        return df
    
    def _clean_and_validate(self, df: DataFrame, config: Dict[str, Any]) -> DataFrame:
        """Clean and validate data"""
        # Remove null values
        df = df.filter(col("value").isNotNull())
        
        # Remove empty lines
        df = df.filter(length(col("value")) > 0)
        
        # Add validation flags
        df = df.withColumn("is_valid", lit(True))
        
        return df
    
    def _apply_business_rules(self, df: DataFrame, config: Dict[str, Any]) -> DataFrame:
        """Apply business logic rules"""
        rules = config.get("rules", [])
        
        for rule in rules:
            rule_type = rule.get("type")
            
            if rule_type == "categorize":
                # Categorize based on conditions
                conditions = rule.get("conditions", [])
                for condition in conditions:
                    df = df.withColumn(
                        condition["column"],
                        when(expr(condition["condition"]), condition["value"])
                        .otherwise(col(condition["column"]))
                    )
        
        return df
    
    def _aggregate_if_needed(self, df: DataFrame, config: Dict[str, Any]) -> DataFrame:
        """Apply aggregations if needed"""
        if config.get("aggregate"):
            group_by_cols = config.get("group_by", [])
            agg_functions = config.get("aggregations", {})
            
            if group_by_cols:
                df = df.groupBy(*group_by_cols).agg(**agg_functions)
        
        return df
    
    def _apply_filter(self, df: DataFrame, config: Dict[str, Any]) -> DataFrame:
        """Apply filter conditions"""
        condition = config.get("condition")
        if condition:
            df = df.filter(expr(condition))
        
        return df
    
    async def _load_to_doris(
        self, 
        spark: SparkSession, 
        df: DataFrame, 
        config: Dict[str, Any], 
        job_id: str
    ) -> Dict[str, Any]:
        """Load processed data to DorisDB"""
        try:
            # Partition data if specified
            partition_by = config.get("partition_by", [])
            if partition_by:
                df = df.repartition(*partition_by)
            
            # Write to temporary location first (could be HDFS, S3, etc.)
            output_path = f"/tmp/spark_output/{job_id}"
            df.write.mode("overwrite").parquet(output_path)
            
            # Get final record count
            record_count = df.count()
            
            # Here you would implement DorisDB connection and bulk insert
            # This is a placeholder for the actual DorisDB integration
            doris_result = await self._bulk_insert_to_doris(output_path, config)
            
            # Update final progress
            await job_service.update_job_progress(
                job_id, 
                processed_records=record_count,
                total_records=record_count
            )
            
            # Clean up temporary files
            self._cleanup_temp_files(output_path)
            
            return {
                "records_processed": record_count,
                "output_path": output_path,
                "doris_result": doris_result,
                "partitions": partition_by
            }
            
        except Exception as e:
            self.logger.error(f"Error loading to DorisDB: {str(e)}")
            raise
    
    async def _bulk_insert_to_doris(
        self, 
        data_path: str, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bulk insert data to DorisDB"""
        # This would implement the actual DorisDB connection and insertion
        # For now, return a mock response
        return {
            "status": "success",
            "rows_inserted": 0,
            "load_id": f"load_{uuid.uuid4().hex[:8]}"
        }
    
    def _cleanup_temp_files(self, path: str):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(path):
                shutil.rmtree(path)
                self.logger.info(f"Cleaned up temporary files at {path}")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp files: {str(e)}")

# Global Spark service instance
spark_service = SparkService()
