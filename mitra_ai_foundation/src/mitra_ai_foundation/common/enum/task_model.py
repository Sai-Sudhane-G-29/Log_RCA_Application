from enum import Enum

class TaskCategory(str, Enum):
    """Categories of tasks."""
    LONG_RUNNING = "long_running"
    LOG_ANALYSIS = "log_analysis"
    DATA_PROCESSING = "data_processing"
    SYSTEM = "system"
    RCA = "rca"

class LongRunningTaskType(str, Enum):
    """Long-running task types."""
    BACKGROUND_PROCESSING = "background_processing"
    DATA_ANALYSIS = "data_analysis"
    REPORT_GENERATION = "report_generation"
    BATCH_PROCESSING = "batch_processing"

class LogAnalysisTaskType(str, Enum):
    """Log analysis task types."""
    PATTERN_MATCHING = "pattern_matching"
    ANOMALY_DETECTION = "anomaly_detection"
    CORRELATION_ANALYSIS = "correlation_analysis"
    LOG_PARSING = "log_parsing"

# Main task type enum that includes all types
class TaskType(str, Enum):
    """Comprehensive enumeration of all task types."""
    
    # Long-running tasks
    LONG_RUNNING_TASK = "long_running_task"
    BACKGROUND_PROCESSING = "background_processing"
    DATA_ANALYSIS = "data_analysis"
    REPORT_GENERATION = "report_generation"
    BATCH_PROCESSING = "batch_processing"
    
    # Log analysis tasks
    LOG_ANALYSIS = "log_analysis"
    PATTERN_MATCHING = "pattern_matching"
    ANOMALY_DETECTION = "anomaly_detection"
    CORRELATION_ANALYSIS = "correlation_analysis"
    LOG_PARSING = "log_parsing"
    
    # Add other categories as needed...
    
    def __str__(self):
        return self.value