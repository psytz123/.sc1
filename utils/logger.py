"""
Centralized logging configuration for Beverly Knits Raw Material Planner
"""

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path


class LoggerConfig:
    """Centralized logger configuration"""
    
    def __init__(self, log_dir: str = "logs", app_name: str = "beverly_knits"):
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.log_dir.mkdir(exist_ok=True)
        
    def get_logger(self, name: str, level: str = "INFO") -> logging.Logger:
        """
        Get a configured logger instance
        
        Args:
            name: Logger name (usually __name__)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        
        # Avoid adding handlers multiple times
        if logger.handlers:
            return logger
            
        logger.setLevel(getattr(logging, level.upper()))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler with rotation
        log_file = self.log_dir / f"{self.app_name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger


# Global logger configuration instance
logger_config = LoggerConfig()

# Convenience function for getting loggers
def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Get a configured logger instance"""
    return logger_config.get_logger(name, level)