"""
Middleware for the Valheim Teams application.

Provides request tracking, logging, and other cross-cutting concerns.
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    
    Features:
    - Generates unique request ID for tracing
    - Logs request method, path, and processing time
    - Adds request_id to log context
    - Logs response status code
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Store request_id in request state
        request.state.request_id = request_id
        
        # Create log record with request_id
        log_extra = {'request_id': request_id}
        
        # Log incoming request
        logger.info(
            f"{request.method} {request.url.path}",
            extra=log_extra
        )
        
        # Track processing time
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            # Log response
            logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s",
                extra=log_extra
            )
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"{request.method} {request.url.path} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.3f}s",
                extra=log_extra,
                exc_info=True
            )
            raise


class RequestIdContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject request_id into logging context.
    
    This ensures all logs during request processing include the request_id.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or create request_id
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Add to logging context (thread-local for async)
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = request_id
            return record
        
        logging.setLogRecordFactory(record_factory)
        
        try:
            response = await call_next(request)
            return response
        finally:
            # Restore original factory
            logging.setLogRecordFactory(old_factory)
