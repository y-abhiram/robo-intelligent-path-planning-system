"""
Advanced logging configuration with request tracking and performance monitoring.
"""
import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .config import settings


def setup_logging():
    """Configure application-wide logging with custom formatting."""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("robot_control.log")
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests with timing information."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request details and response time."""
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"Incoming request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000  # Convert to ms

            # Add custom header with processing time
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

            # Log response details
            logger.info(
                f"Completed: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Duration: {process_time:.2f}ms"
            )

            return response
        except Exception as e:
            logger.error(
                f"Error processing request: {request.method} {request.url.path} "
                f"Error: {str(e)}"
            )
            raise


class PerformanceLogger:
    """Context manager for logging operation performance."""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"Starting operation: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.time() - self.start_time) * 1000
        if exc_type is None:
            logger.info(
                f"Completed operation: {self.operation_name} "
                f"Duration: {duration:.2f}ms"
            )
        else:
            logger.error(
                f"Failed operation: {self.operation_name} "
                f"Duration: {duration:.2f}ms "
                f"Error: {exc_val}"
            )
