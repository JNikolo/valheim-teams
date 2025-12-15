"""
Logging configuration for the Valheim Teams application.

Provides structured logging with different formatters for development and production,
request ID tracking, and optional file logging.
"""

import logging
import sys
from typing import Optional
from datetime import datetime

from .config import settings


class ColoredFormatter(logging.Formatter):
    """
    Colored log formatter for console output.
    
    Makes logs easier to read in development by adding colors based on log level.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }

    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Format the message
        result = super().format(record)
        
        # Reset levelname for next use
        record.levelname = levelname
        
        return result


class RequestIdFilter(logging.Filter):
    """
    Adds request_id to log records for request tracing.
    
    If no request_id is set, uses '-' as placeholder.
    """
    
    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = '-'
        return True


def setup_logging(
    level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    Configure application-wide logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format style ('simple' or 'detailed')
        log_file: Optional path to log file
    """
    level = level or settings.log_level
    log_format = log_format or settings.log_format
    log_file = log_file or settings.log_file

    # Determine log level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Define formatters
    if log_format == "simple":
        console_format = '%(levelname)s: %(message)s'
        file_format = '%(asctime)s - %(levelname)s - %(message)s'
    else:  # detailed
        console_format = (
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | '
            '%(request_id)s | %(message)s'
        )
        file_format = (
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | '
            'line:%(lineno)d | %(request_id)s | %(message)s'
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    if settings.debug:
        # Use colored formatter in development
        console_formatter = ColoredFormatter(
            console_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        console_formatter = logging.Formatter(
            console_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(RequestIdFilter())
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(numeric_level)
            file_formatter = logging.Formatter(
                file_format,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            file_handler.addFilter(RequestIdFilter())
            root_logger.addHandler(file_handler)
            
            logging.info(f"Logging to file: {log_file}")
        except Exception as e:
            logging.warning(f"Could not set up file logging: {e}")

    # Configure third-party loggers
    # Reduce noise from libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # SQLAlchemy logging - show queries only in DEBUG mode
    if settings.debug:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Log startup info
    logging.info(f"Logging configured - Level: {level}, Format: {log_format}")
    logging.debug(f"Debug mode: {settings.debug}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Name of the module (typically __name__)
        
    Returns:
        Configured logger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("Processing request")
    """
    return logging.getLogger(name)
