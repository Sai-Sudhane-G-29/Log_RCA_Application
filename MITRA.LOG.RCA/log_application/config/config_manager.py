# Option 1: Direct access to config instances
from mitra_ai_foundation.common.config import common_config, worker_config

print(f"App Name: {common_config.app_name}")
print(f"Redis Host: {common_config.redis.host}")
print(f"Worker Concurrency: {worker_config.celery.worker_concurrency}")

# Option 2: Using the config manager
from mitra_ai_foundation.common.config import config_manager

config = config_manager.common_config
worker = config_manager.worker_config

# Option 3: Using dependency injection (for FastAPI)
from mitra_ai_foundation.common.config import get_common_settings, get_worker_settings

@app.get("/config")
async def get_config(settings: CommonConfig = Depends(get_common_settings)):
    return {
        "app_name": settings.app_name,
        "environment": settings.environment
    }