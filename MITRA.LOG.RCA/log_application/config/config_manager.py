"""
Configuration manager for the log application.

This module imports and uses the foundation's config manager.
"""
from mitra_ai_foundation.common.config.config_manager import ConfigManager

# Import and use the foundation's config manager
config_manager = ConfigManager()

# Export the configs for easy access
common_config = config_manager.common_config
worker_config = config_manager.worker_config