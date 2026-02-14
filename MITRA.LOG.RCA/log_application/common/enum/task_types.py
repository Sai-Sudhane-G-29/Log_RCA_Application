"""
Task type enumerations for log application.
"""
class LogTaskType:
    """
    Enumeration of log application task types.
    
    These values should be used instead of hardcoded task names to ensure
    consistency and enable loose coupling between API and worker components.
    """
    
    # Log analysis tasks
    PROCESS_LOGS = "process_logs"
    ANALYZE_ERRORS = "analyze_errors"
    GENERATE_RCA_REPORT = "generate_rca_report"