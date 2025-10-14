"""Standardized error response models for PR Summarizer API.

This module provides consistent error response models that integrate with
the exception system and provide structured error information to API clients.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict, field_serializer

from src.utils.exceptions import PRSummarizerError


class ErrorDetail(BaseModel):
    """Individual error detail item."""
    
    field: Optional[str] = Field(None, description="Field name that caused the error")
    message: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")
    value: Optional[Any] = Field(None, description="Value that caused the error")


class ErrorResponse(BaseModel):
    """Standardized error response model for API endpoints."""
    
    # Core error information
    error: bool = Field(True, description="Always true for error responses")
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    
    # Request context
    correlation_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique request correlation ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Error timestamp in UTC")
    
    # Error details
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    errors: Optional[List[ErrorDetail]] = Field(None, description="Field-specific validation errors")
    
    # HTTP context
    status_code: int = Field(..., description="HTTP status code")
    path: Optional[str] = Field(None, description="Request path that caused the error")
    method: Optional[str] = Field(None, description="HTTP method used")
    
    # Development information (only in debug mode)
    debug_info: Optional[Dict[str, Any]] = Field(None, description="Debug information (development only)")

    model_config = ConfigDict()
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime) -> str:
        """Serialize timestamp to ISO format with Z suffix."""
        return dt.isoformat() + "Z"


class ValidationErrorResponse(ErrorResponse):
    """Error response for validation failures."""
    
    error_code: str = Field(default="VALIDATION_ERROR", description="Machine-readable error code")
    message: str = Field(default="Validation failed", description="Human-readable error message")
    status_code: int = Field(default=422, description="HTTP status code")


class NotFoundErrorResponse(ErrorResponse):
    """Error response for resource not found."""
    
    error_code: str = Field(default="NOT_FOUND", description="Machine-readable error code")
    message: str = Field(default="Resource not found", description="Human-readable error message")
    status_code: int = Field(default=404, description="HTTP status code")


class UnauthorizedErrorResponse(ErrorResponse):
    """Error response for authentication failures."""
    
    error_code: str = Field(default="UNAUTHORIZED", description="Machine-readable error code")
    message: str = Field(default="Authentication required", description="Human-readable error message")
    status_code: int = Field(default=401, description="HTTP status code")


class ForbiddenErrorResponse(ErrorResponse):
    """Error response for authorization failures."""
    
    error_code: str = Field(default="FORBIDDEN", description="Machine-readable error code")
    message: str = Field(default="Access denied", description="Human-readable error message")
    status_code: int = Field(default=403, description="HTTP status code")


class RateLimitErrorResponse(ErrorResponse):
    """Error response for rate limit exceeded."""
    
    error_code: str = Field(default="RATE_LIMIT_EXCEEDED", description="Machine-readable error code")
    message: str = Field(default="Rate limit exceeded", description="Human-readable error message")
    status_code: int = Field(default=429, description="HTTP status code")


class InternalServerErrorResponse(ErrorResponse):
    """Error response for internal server errors."""
    
    error_code: str = Field(default="INTERNAL_SERVER_ERROR", description="Machine-readable error code")
    message: str = Field(default="Internal server error", description="Human-readable error message")
    status_code: int = Field(default=500, description="HTTP status code")


class ExternalServiceErrorResponse(ErrorResponse):
    """Error response for external service failures."""
    
    error_code: str = Field(default="EXTERNAL_SERVICE_ERROR", description="Machine-readable error code")
    message: str = Field(default="External service error", description="Human-readable error message")
    status_code: int = Field(default=502, description="HTTP status code")
    service: Optional[str] = Field(None, description="Name of the external service that failed")


# Type union for all possible error responses
AnyErrorResponse = Union[
    ErrorResponse,
    ValidationErrorResponse,
    NotFoundErrorResponse,
    UnauthorizedErrorResponse,
    ForbiddenErrorResponse,
    RateLimitErrorResponse,
    InternalServerErrorResponse,
    ExternalServiceErrorResponse,
]


def create_error_response(
    exception: Union[Exception, PRSummarizerError],
    correlation_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
    include_debug: bool = False
) -> ErrorResponse:
    """Create an error response from an exception.
    
    Args:
        exception: The exception that occurred
        correlation_id: Optional correlation ID for request tracking
        path: Optional request path
        method: Optional HTTP method
        include_debug: Whether to include debug information
        
    Returns:
        Appropriate error response model
    """
    if correlation_id is None:
        correlation_id = str(uuid4())
    
    # Handle PRSummarizerError exceptions
    if isinstance(exception, PRSummarizerError):
        # Map exception types to error codes and status codes
        from src.utils.exceptions import (
            ValidationError as ValidationErr,
            AuthenticationError,
            ExternalServiceError,
            GitHubAPIError,
            GeminiAPIError,
            JiraAPIError,
            ConfluenceAPIError,
            ConfigurationError,
            RateLimitError,
        )
        
        error_code = "UNKNOWN_ERROR"
        status_code = 500
        
        if isinstance(exception, ValidationErr):
            error_code = "VALIDATION_ERROR"
            status_code = 422
        elif isinstance(exception, AuthenticationError):
            error_code = "AUTHENTICATION_ERROR"
            status_code = 401
        elif isinstance(exception, RateLimitError):
            error_code = "RATE_LIMIT_EXCEEDED"
            status_code = 429
        elif isinstance(exception, (GitHubAPIError, GeminiAPIError, JiraAPIError, ConfluenceAPIError)):
            error_code = "EXTERNAL_SERVICE_ERROR"
            status_code = 502
        elif isinstance(exception, ConfigurationError):
            error_code = "CONFIGURATION_ERROR"
            status_code = 500
        elif isinstance(exception, ExternalServiceError):
            error_code = "EXTERNAL_SERVICE_ERROR"
            status_code = 502
        
        error_response = ErrorResponse(
            error_code=error_code,
            message=str(exception),
            correlation_id=correlation_id,
            details=exception.details,
            status_code=status_code,
            path=path,
            method=method
        )
        
        if include_debug and hasattr(exception, 'debug_info'):
            error_response.debug_info = exception.debug_info
            
        return error_response
    
    # Handle standard Python exceptions
    error_response = InternalServerErrorResponse(
        correlation_id=correlation_id,
        path=path,
        method=method,
        details={"exception_type": type(exception).__name__}
    )
    
    if include_debug:
        import traceback
        error_response.debug_info = {
            "exception_type": type(exception).__name__,
            "traceback": traceback.format_exc()
        }
    
    return error_response


def create_validation_error_response(
    errors: List[Dict[str, Any]],
    correlation_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None
) -> ValidationErrorResponse:
    """Create a validation error response from field errors.
    
    Args:
        errors: List of field validation errors
        correlation_id: Optional correlation ID for request tracking
        path: Optional request path
        method: Optional HTTP method
        
    Returns:
        Validation error response
    """
    if correlation_id is None:
        correlation_id = str(uuid4())
    
    error_details = []
    for error in errors:
        error_detail = ErrorDetail(
            field=error.get('field'),
            message=error.get('message', 'Validation failed'),
            code=error.get('code', 'VALIDATION_ERROR'),
            value=error.get('value')
        )
        error_details.append(error_detail)
    
    return ValidationErrorResponse(
        correlation_id=correlation_id,
        errors=error_details,
        path=path,
        method=method,
        details={"error_count": len(errors)}
    )


def create_not_found_response(
    resource: str,
    resource_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None
) -> NotFoundErrorResponse:
    """Create a not found error response.
    
    Args:
        resource: Type of resource that was not found
        resource_id: Optional ID of the resource
        correlation_id: Optional correlation ID for request tracking
        path: Optional request path
        method: Optional HTTP method
        
    Returns:
        Not found error response
    """
    if correlation_id is None:
        correlation_id = str(uuid4())
    
    message = f"{resource} not found"
    if resource_id:
        message += f" (ID: {resource_id})"
    
    return NotFoundErrorResponse(
        message=message,
        correlation_id=correlation_id,
        path=path,
        method=method,
        details={
            "resource": resource,
            "resource_id": resource_id
        }
    )


def create_external_service_error_response(
    service: str,
    error_message: str,
    correlation_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
    service_details: Optional[Dict[str, Any]] = None
) -> ExternalServiceErrorResponse:
    """Create an external service error response.
    
    Args:
        service: Name of the external service
        error_message: Error message from the service
        correlation_id: Optional correlation ID for request tracking
        path: Optional request path
        method: Optional HTTP method
        service_details: Optional additional service details
        
    Returns:
        External service error response
    """
    if correlation_id is None:
        correlation_id = str(uuid4())
    
    details = {"service": service}
    if service_details:
        details.update(service_details)
    
    return ExternalServiceErrorResponse(
        message=f"{service} service error: {error_message}",
        correlation_id=correlation_id,
        service=service,
        path=path,
        method=method,
        details=details
    )


# Export all models and functions
__all__ = [
    # Core models
    "ErrorDetail",
    "ErrorResponse",
    
    # Specific error response models
    "ValidationErrorResponse",
    "NotFoundErrorResponse", 
    "UnauthorizedErrorResponse",
    "ForbiddenErrorResponse",
    "RateLimitErrorResponse",
    "InternalServerErrorResponse",
    "ExternalServiceErrorResponse",
    
    # Type unions
    "AnyErrorResponse",
    
    # Factory functions
    "create_error_response",
    "create_validation_error_response",
    "create_not_found_response",
    "create_external_service_error_response",
]