"""
Utility functions for file operations and management
"""

import os
import shutil
import glob
from typing import List, Optional, Dict, Any
from pathlib import Path
import hashlib
import json
from datetime import datetime

from api.src.core.config import settings
from api.src.core.logging import get_logger

logger = get_logger(__name__)

class FileManager:
    """Utility class for file operations"""
    
    @staticmethod
    def validate_file_paths(file_paths: List[str]) -> Dict[str, Any]:
        """Validate that file paths exist and are accessible"""
        validation_result = {
            "valid_files": [],
            "invalid_files": [],
            "total_size": 0,
            "errors": []
        }
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    validation_result["valid_files"].append({
                        "path": file_path,
                        "size": file_size,
                        "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
                    validation_result["total_size"] += file_size
                else:
                    validation_result["invalid_files"].append(file_path)
                    validation_result["errors"].append(f"File not found: {file_path}")
            except Exception as e:
                validation_result["invalid_files"].append(file_path)
                validation_result["errors"].append(f"Error accessing {file_path}: {str(e)}")
        
        return validation_result
    
    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = "md5") -> Optional[str]:
        """Calculate hash of a file"""
        try:
            hash_algo = hashlib.new(algorithm)
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_algo.update(chunk)
            return hash_algo.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return None
    
    @staticmethod
    def create_backup(file_path: str, backup_dir: str) -> Optional[str]:
        """Create backup of a file"""
        try:
            os.makedirs(backup_dir, exist_ok=True)
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{timestamp}_{filename}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {str(e)}")
            return None
    
    @staticmethod
    def cleanup_temp_files(temp_dir: str, max_age_hours: int = 24):
        """Clean up temporary files older than specified hours"""
        try:
            if not os.path.exists(temp_dir):
                return
            
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            cleaned_count = 0
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > max_age_seconds:
                            os.remove(file_path)
                            cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"Error removing temp file {file_path}: {str(e)}")
            
            logger.info(f"Cleaned up {cleaned_count} temporary files")
        except Exception as e:
            logger.error(f"Error cleaning temp files: {str(e)}")
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """Get detailed information about a file"""
        try:
            stat = os.stat(file_path)
            return {
                "path": file_path,
                "name": os.path.basename(file_path),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "is_readable": os.access(file_path, os.R_OK),
                "is_writable": os.access(file_path, os.W_OK),
                "extension": os.path.splitext(file_path)[1].lower()
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return {}
    
    @staticmethod
    def find_log_files(directory: str, pattern: str = "*.log") -> List[str]:
        """Find log files in a directory matching a pattern"""
        try:
            search_pattern = os.path.join(directory, "**", pattern)
            files = glob.glob(search_pattern, recursive=True)
            return sorted(files)
        except Exception as e:
            logger.error(f"Error finding log files in {directory}: {str(e)}")
            return []
    
    @staticmethod
    def ensure_directory(directory: str) -> bool:
        """Ensure directory exists, create if it doesn't"""
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {str(e)}")
            return False
    
    @staticmethod
    def safe_file_move(source: str, destination: str) -> bool:
        """Safely move a file with error handling"""
        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination)
            FileManager.ensure_directory(dest_dir)
            
            # Move the file
            shutil.move(source, destination)
            logger.info(f"Moved file from {source} to {destination}")
            return True
        except Exception as e:
            logger.error(f"Error moving file from {source} to {destination}: {str(e)}")
            return False

class ConfigManager:
    """Utility class for configuration management"""
    
    @staticmethod
    def load_job_config(config_file: str) -> Dict[str, Any]:
        """Load job configuration from file"""
        try:
            with open(config_file, 'r') as f:
                if config_file.endswith('.json'):
                    return json.load(f)
                elif config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    import yaml
                    return yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {config_file}")
        except Exception as e:
            logger.error(f"Error loading config from {config_file}: {str(e)}")
            return {}
    
    @staticmethod
    def save_job_config(config: Dict[str, Any], config_file: str) -> bool:
        """Save job configuration to file"""
        try:
            FileManager.ensure_directory(os.path.dirname(config_file))
            
            with open(config_file, 'w') as f:
                if config_file.endswith('.json'):
                    json.dump(config, f, indent=2)
                elif config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    import yaml
                    yaml.dump(config, f, default_flow_style=False)
                else:
                    raise ValueError(f"Unsupported config file format: {config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config to {config_file}: {str(e)}")
            return False
    
    @staticmethod
    def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries"""
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager.merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def validate_config(config: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration against a schema"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Basic validation logic (in a real implementation, use jsonschema)
        for required_field in schema.get("required", []):
            if required_field not in config:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Required field missing: {required_field}")
        
        return validation_result

class MetricsCollector:
    """Utility class for collecting and calculating metrics"""
    
    @staticmethod
    def calculate_throughput(records_processed: int, time_elapsed: float) -> float:
        """Calculate processing throughput"""
        if time_elapsed <= 0:
            return 0.0
        return records_processed / time_elapsed
    
    @staticmethod
    def calculate_success_rate(successful: int, total: int) -> float:
        """Calculate success rate percentage"""
        if total <= 0:
            return 0.0
        return (successful / total) * 100
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
