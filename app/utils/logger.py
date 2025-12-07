"""
Logging configuration for the application
"""
import logging
import sys
from typing import Optional

# Configure root logger
_logger: Optional[logging.Logger] = None


def get_logger(name: str = "app") -> logging.Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name, typically __name__ of the module
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        
        # Get log level from settings if available
        try:
            from app.config import settings
            log_level = getattr(settings, 'log_level', 'INFO')
            handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
            logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        except Exception:
            handler.setLevel(logging.INFO)
            logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

