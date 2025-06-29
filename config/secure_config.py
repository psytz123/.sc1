"""
Secure configuration management for Beverly Knits
"""

import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from utils.logger import get_logger

logger = get_logger(__name__)


class SecureConfig:
    """Secure configuration management with environment variable support"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize secure configuration
        
        Args:
            env_file: Path to .env file (defaults to .env in project root)
        """
        self.env_file = env_file or ".env"
        self._load_environment()
        self._validate_secrets()
        
    def _load_environment(self):
        """Load environment variables from .env file"""
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)
            logger.info(f"Loaded environment from {self.env_file}")
        else:
            logger.warning(f"Environment file {self.env_file} not found")
            
    def _validate_secrets(self):
        """Validate that no hardcoded secrets are present"""
        sensitive_keys = [
            'API_KEY', 'SECRET', 'PASSWORD', 'TOKEN', 
            'PRIVATE_KEY', 'ACCESS_KEY'
        ]
        
        for key in os.environ:
            for sensitive in sensitive_keys:
                if sensitive in key.upper():
                    value = os.environ[key]
                    # Check for placeholder values
                    if value and ('your_' in value.lower() or 
                                 'placeholder' in value.lower() or
                                 'example' in value.lower()):
                        logger.warning(
                            f"Placeholder value detected for {key}. "
                            "Please update with actual credentials."
                        )
                        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with fallback to environment variables
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        # First check environment variables
        env_value = os.environ.get(key)
        if env_value is not None:
            return env_value
            
        # Then check uppercase version
        env_value = os.environ.get(key.upper())
        if env_value is not None:
            return env_value
            
        return default
        
    def get_secret(self, key: str) -> Optional[str]:
        """
        Get secret value from environment
        
        Args:
            key: Secret key
            
        Returns:
            Secret value or None if not found
            
        Raises:
            ValueError: If secret is not properly configured
        """
        value = self.get(key)
        
        if value is None:
            logger.error(f"Secret {key} not found in environment")
            raise ValueError(f"Required secret {key} not configured")
            
        # Validate it's not a placeholder
        if ('your_' in value.lower() or 
            'placeholder' in value.lower() or
            'example' in value.lower()):
            logger.error(f"Secret {key} contains placeholder value")
            raise ValueError(
                f"Secret {key} not properly configured. "
                "Please update with actual credentials."
            )
            
        return value
        
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration from environment"""
        return {
            'host': self.get('DB_HOST', 'localhost'),
            'port': int(self.get('DB_PORT', 5432)),
            'database': self.get('DB_NAME', 'beverly_knits'),
            'user': self.get('DB_USER', 'postgres'),
            'password': self.get_secret('DB_PASSWORD') if self.get('DB_PASSWORD') else None
        }
        
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration from environment"""
        config = {}
        
        # Check for various API keys
        api_keys = [
            'GEMINI_API_KEY',
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY',
            'XAI_API_KEY',
            'OPENROUTER_API_KEY'
        ]
        
        for key in api_keys:
            try:
                value = self.get_secret(key)
                if value:
                    config[key.lower()] = value
            except ValueError:
                # Key not found or is placeholder
                pass
                
        return config


# Global secure configuration instance
secure_config = SecureConfig()