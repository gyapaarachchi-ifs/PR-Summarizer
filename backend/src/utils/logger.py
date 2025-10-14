"""Structured logging utilities for PR Summarizer application.

This module provides structured logging capabilities using structlog,
with support for correlation IDs, performance metrics, and API logging.
"""

import logging
import sys
import time
from enum import Enum
from typing import Any, Dict, Optional, Union

import structlog
from structlog.types import Processor


class LogLevel(str, Enum):
    """Enumeration of supported log levels."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


def add_correlation_id(logger: Any, name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add correlation ID to log event if available.
    
    Args:
        logger: The logger instance
        name: The logger name
        event_dict: The event dictionary to modify
        
    Returns:
        Modified event dictionary with correlation ID if available
    """
    # Check if correlation_id is already in the event
    if "correlation_id" not in event_dict:
        # Try to get from logger context or other sources
        correlation_id = getattr(logger, "_correlation_id", None)
        if correlation_id:
            event_dict["correlation_id"] = correlation_id
    
    return event_dict


def add_timestamp(logger: Any, name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add ISO timestamp to log event.
    
    Args:
        logger: The logger instance
        name: The logger name
        event_dict: The event dictionary to modify
        
    Returns:
        Modified event dictionary with timestamp
    """
    event_dict["timestamp"] = time.time()
    return event_dict


def add_logger_name(logger: Any, name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add logger name to log event.
    
    Args:
        logger: The logger instance
        name: The logger name
        event_dict: The event dictionary to modify
        
    Returns:
        Modified event dictionary with logger name
    """
    event_dict["logger"] = name
    return event_dict


def configure_logging(
    level: LogLevel = LogLevel.INFO,
    json_format: bool = False,
    enable_correlation_id: bool = True
) -> None:
    """Configure structured logging for the application.
    
    Args:
        level: Minimum log level to output
        json_format: Whether to output logs in JSON format
        enable_correlation_id: Whether to enable correlation ID support
    """
    # Configure standard library logging
    log_level = getattr(logging, level.value)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,  # Force reconfiguration
    )
    
    # Set root logger level explicitly
    logging.getLogger().setLevel(log_level)
    
    # Build processor chain
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_logger_name,
        add_timestamp,
    ]
    
    if enable_correlation_id:
        processors.append(add_correlation_id)
    
    processors.extend([
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
    ])
    
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.value)
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "pr_summarizer", **context: Any) -> structlog.BoundLogger:
    """Get a structured logger instance with optional context.
    
    Args:
        name: Logger name (usually module name)
        **context: Additional context to bind to the logger
        
    Returns:
        Configured structured logger instance
    """
    logger = structlog.get_logger(name)
    
    if context:
        logger = logger.bind(**context)
    
    return logger


def log_api_request(
    method: str,
    path: str,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    request_body: Optional[Dict[str, Any]] = None,
    query_params: Optional[Dict[str, Any]] = None,
    **additional_context: Any
) -> None:
    """Log an incoming API request.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        user_id: User identifier if available
        request_id: Request correlation ID
        request_body: Request body data (will be sanitized)
        query_params: Query parameters
        **additional_context: Additional context to log
    """
    logger = get_logger("api.request")
    
    log_data = {
        "method": method,
        "path": path,
        "event_type": "api_request",
        **additional_context
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if request_id:
        log_data["request_id"] = request_id
    
    if request_body:
        # Note: In production, sensitive data should be sanitized
        log_data["request_body"] = request_body
    
    if query_params:
        log_data["query_params"] = query_params
    
    logger.info("API request received", **log_data)


def log_api_response(
    status_code: int,
    path: str,
    duration_ms: float,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    response_size: Optional[int] = None,
    error: Optional[str] = None,
    **additional_context: Any
) -> None:
    """Log an API response.
    
    Args:
        status_code: HTTP status code
        path: Request path
        duration_ms: Request duration in milliseconds
        user_id: User identifier if available
        request_id: Request correlation ID
        response_size: Response size in bytes
        error: Error message if request failed
        **additional_context: Additional context to log
    """
    logger = get_logger("api.response")
    
    log_data = {
        "status_code": status_code,
        "path": path,
        "duration_ms": duration_ms,
        "event_type": "api_response",
        **additional_context
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if request_id:
        log_data["request_id"] = request_id
    
    if response_size:
        log_data["response_size"] = response_size
    
    if error:
        log_data["error"] = error
    
    # Log as error if status code indicates failure
    if status_code >= 400:
        logger.error("API response sent", **log_data)
    else:
        logger.info("API response sent", **log_data)


def log_external_service_call(
    service: str,
    operation: str,
    url: str,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    request_id: Optional[str] = None,
    response_data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    **additional_context: Any
) -> None:
    """Log an external service API call.
    
    Args:
        service: Service name (github, gemini, jira, etc.)
        operation: Operation being performed
        url: Service endpoint URL
        status_code: HTTP status code from service
        duration_ms: Call duration in milliseconds
        request_id: Request correlation ID
        response_data: Response data from service (sanitized)
        error: Error message if call failed
        **additional_context: Additional context to log
    """
    logger = get_logger(f"external.{service}")
    
    log_data = {
        "service": service,
        "operation": operation,
        "url": url,
        "event_type": "external_service_call",
        **additional_context
    }
    
    if status_code:
        log_data["status_code"] = status_code
    
    if duration_ms:
        log_data["duration_ms"] = duration_ms
    
    if request_id:
        log_data["request_id"] = request_id
    
    if response_data:
        # Note: Sensitive data should be sanitized in production
        log_data["response_data"] = response_data
    
    if error:
        log_data["error"] = error
    
    # Log as error if status code indicates failure or error present
    if error or (status_code and status_code >= 400):
        logger.error("External service call", **log_data)
    else:
        logger.info("External service call", **log_data)


def log_performance_metric(
    operation: str,
    duration_ms: float,
    success: bool,
    request_id: Optional[str] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **additional_context: Any
) -> None:
    """Log a performance metric.
    
    Args:
        operation: Operation name
        duration_ms: Operation duration in milliseconds
        success: Whether operation was successful
        request_id: Request correlation ID
        error: Error message if operation failed
        metadata: Additional operation metadata
        **additional_context: Additional context to log
    """
    logger = get_logger("performance")
    
    log_data = {
        "operation": operation,
        "duration_ms": duration_ms,
        "success": success,
        "event_type": "performance_metric",
        **additional_context
    }
    
    if request_id:
        log_data["request_id"] = request_id
    
    if error:
        log_data["error"] = error
    
    if metadata:
        log_data["metadata"] = metadata
    
    # Log as warning if operation failed
    if not success:
        logger.warning("Performance metric", **log_data)
    else:
        logger.info("Performance metric", **log_data)


# Export main functions and classes
__all__ = [
    "LogLevel",
    "configure_logging",
    "get_logger",
    "log_api_request",
    "log_api_response", 
    "log_external_service_call",
    "log_performance_metric",
]