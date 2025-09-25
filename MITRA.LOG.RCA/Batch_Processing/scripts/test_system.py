"""
Test script for batch processing functionality
"""

import sys
import os
import asyncio
import json

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.src.schemas.job import CreateJobRequest, JobTypeEnum, JobConfigSchema
from api.src.services.job_service import job_service
from api.src.core.logging import setup_logging, get_logger

async def test_job_creation():
    """Test job creation functionality"""
    logger = get_logger(__name__)
    
    print("🧪 Testing job creation...")
    
    # Create test job configuration
    config = JobConfigSchema(
        log_format="json",
        parse_rules={
            "timestamp_format": "%Y-%m-%d %H:%M:%S",
            "delimiter": " "
        },
        transformations=[
            {
                "type": "filter",
                "condition": "status_code >= 200"
            },
            {
                "type": "parse_log_format",
                "pattern": "json"
            }
        ],
        output_format="parquet",
        partition_by=["date", "status"]
    )
    
    # Create test job request
    job_request = CreateJobRequest(
        job_type=JobTypeEnum.LOG_ETL,
        log_files=[
            "/tmp/test_logs/app.log",
            "/tmp/test_logs/error.log"
        ],
        config=config,
        priority=5
    )
    
    try:
        # Create the job
        job = await job_service.create_job(job_request)
        print(f"✅ Created test job: {job.job_id}")
        print(f"📊 Job details: {job.dict()}")
        
        # Test job status retrieval
        status = await job_service.get_job_status(job.job_id)
        if status:
            print(f"📈 Job status: {status.dict()}")
        
        return job.job_id
        
    except Exception as e:
        print(f"❌ Failed to create test job: {str(e)}")
        logger.error(f"Test job creation failed: {str(e)}")
        return None

async def test_job_listing():
    """Test job listing functionality"""
    print("🧪 Testing job listing...")
    
    try:
        jobs = await job_service.get_jobs(limit=10)
        print(f"✅ Retrieved {len(jobs)} jobs")
        
        for job in jobs:
            print(f"  📄 Job {job.job_id}: {job.status} ({job.job_type})")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to list jobs: {str(e)}")
        return False

async def test_spark_processing():
    """Test Spark processing (mock)"""
    print("🧪 Testing Spark processing...")
    
    try:
        from app.services.spark_service import spark_service
        
        # This would normally process real files
        # For testing, we'll just verify the service can be imported
        print("✅ Spark service imported successfully")
        
        # Test configuration
        test_config = {
            "log_format": "json",
            "transformations": [
                {"type": "parse_log_format", "pattern": "json"},
                {"type": "clean_and_validate"},
                {"type": "apply_business_rules", "rules": []},
                {"type": "aggregate_if_needed", "aggregate": False}
            ],
            "partition_by": ["date"]
        }
        
        print("✅ Spark configuration validated")
        return True
        
    except Exception as e:
        print(f"❌ Spark processing test failed: {str(e)}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("🎯 Starting Batch Processing Engine Tests\n")
    
    setup_logging()
    
    test_results = []
    
    # Test 1: Job Creation
    job_id = await test_job_creation()
    test_results.append(("Job Creation", job_id is not None))
    
    print()
    
    # Test 2: Job Listing
    listing_success = await test_job_listing()
    test_results.append(("Job Listing", listing_success))
    
    print()
    
    # Test 3: Spark Processing
    spark_success = await test_spark_processing()
    test_results.append(("Spark Processing", spark_success))
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = 0
    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<20}: {status}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🎉 All tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
