# Quick Setup Guide

## Getting Started with Docker

Since you're facing Docker Hub authentication issues, here are the steps to get the system running:

### Option 1: Use the Simple Docker Compose (Recommended for testing)

```bash
# Use the simple docker-compose file
docker compose -f docker-compose.simple.yml up --build
```

This will start:
- PostgreSQL database
- Redis for job queuing
- The batch processing application

### Option 2: Run Locally (If Docker issues persist)

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start PostgreSQL and Redis locally:**
   ```bash
   # Using Docker for just these services
   docker run -d --name postgres -e POSTGRES_DB=batch_processing -e POSTGRES_USER=batch_user -e POSTGRES_PASSWORD=batch_password -p 5432:5432 postgres:15-alpine
   docker run -d --name redis -p 6379:6379 redis:7-alpine
   ```

3. **Set environment variables:**
   ```bash
   export DATABASE_URL="postgresql://batch_user:batch_password@localhost:5432/batch_processing"
   export REDIS_URL="redis://localhost:6379/0"
   ```

4. **Run the application:**
   ```bash
   cd api
   python main.py
   ```

### Testing the Application

Once running, you can test the endpoints:

1. **Health check:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **API documentation:**
   Open http://localhost:8000/docs in your browser

3. **Create a test job:**
   ```bash
   curl -X POST "http://localhost:8000/batch/jobs" \
     -H "Content-Type: application/json" \
     -d '{
       "job_type": "log_etl",
       "log_files": ["/tmp/test.log"],
       "priority": 5
     }'
   ```

## Current Status

The system is configured to work without PySpark initially, using mock processing. This allows you to:
- Test the API endpoints
- Verify job creation and management
- Check the job queue functionality
- Monitor job status and progress

## Next Steps

Once the basic system is running:
1. Add PySpark to requirements.txt if needed
2. Configure DorisDB integration
3. Add real file processing logic
4. Implement proper error handling and monitoring

## Troubleshooting

- If you get import errors, make sure you're in the correct directory
- Check that PostgreSQL and Redis are running
- Verify port 8000 is available
- Check the logs in the container or terminal output
