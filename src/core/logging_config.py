"""
Logging configuration for Beverly Knits ML Integration
"""

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path


def setup_logging(config_path: str = "config/zen_ml_config.json"):
    """
    Set up logging configuration based on settings in config file.
    
    Args:
        config_path: Path to configuration file
    """
    # Default logging configuration
    log_config = {
        "level": "INFO",
        "file": "logs/ml_integration.log",
        "max_file_size_mb": 100,
        "backup_count": 5,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
    
    # Try to load from config file
    try:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                if 'logging' in config:
                    log_config.update(config['logging'])
    except Exception as e:
        print(f"Warning: Could not load logging config: {e}")
    
    # Create logs directory if it doesn't exist
    log_file = Path(log_config['file'])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_config['level']))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_config['level']))
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_config['file'],
        maxBytes=log_config['max_file_size_mb'] * 1024 * 1024,
        backupCount=log_config['backup_count']
    )
    file_handler.setLevel(getattr(logging, log_config['level']))
    file_formatter = logging.Formatter(log_config['format'])
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Log startup message
    logging.info("=" * 60)
    logging.info(f"Beverly Knits ML Integration Started - {datetime.now()}")
    logging.info(f"Log Level: {log_config['level']}")
    logging.info(f"Log File: {log_config['file']}")
    logging.info("=" * 60)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class MLOperationLogger:
    """Context manager for logging ML operations with timing"""
    
    def __init__(self, operation_name: str, logger: logging.Logger = None):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
        
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.operation_name}...")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation_name} in {duration:.2f} seconds"
            )
        else:
            self.logger.error(
                f"Failed {self.operation_name} after {duration:.2f} seconds: {exc_val}"
            )
        
        return False  # Don't suppress exceptions


# Initialize logging when module is imported
if __name__ != "__main__":
    setup_logging()