"""Tests for error response models.

Test coverage for all error response models and factory functions.
"""

import json
from datetime import datetime
from typing import Dict, Any

import pytest

from src.models.error_responses import (
    ErrorDetail,
    ErrorResponse,
    ValidationErrorResponse,
    NotFoundErrorResponse,
    UnauthorizedErrorResponse,
    ForbiddenErrorResponse,
    RateLimitErrorResponse,
    InternalServerErrorResponse,
    ExternalServiceErrorResponse,
    create_error_response,
    create_validation_error_response,
    create_not_found_response,
    create_external_service_error_response,
)
from src.utils.exceptions import (
    ValidationError,
    ExternalServiceError,
    GitHubAPIError,
    AuthenticationError,
)


class TestErrorDetail:
    """Test ErrorDetail model."""
    
    def test_error_detail_creation(self):
        """Test creating error detail with required fields."""
        detail = ErrorDetail(
            message="Test error message",
            code="TEST_ERROR"
        )
        
        assert detail.field is None
        assert detail.message == "Test error message"
        assert detail.code == "TEST_ERROR"
        assert detail.value is None
    
    def test_error_detail_with_all_fields(self):
        """Test creating error detail with all fields."""
        detail = ErrorDetail(
            field="email",
            message="Invalid email format",
            code="INVALID_EMAIL",
            value="invalid-email"
        )
        
        assert detail.field == "email"
        assert detail.message == "Invalid email format"
        assert detail.code == "INVALID_EMAIL"
        assert detail.value == "invalid-email"


class TestErrorResponse:
    """Test ErrorResponse model."""
    
    def test_error_response_creation(self):
        """Test creating error response with required fields."""
        response = ErrorResponse(
            error_code="TEST_ERROR",
            message="Test error message",
            status_code=400
        )
        
        assert response.error is True
        assert response.error_code == "TEST_ERROR"
        assert response.message == "Test error message"
        assert response.status_code == 400
        assert response.correlation_id is not None
        assert isinstance(response.timestamp, datetime)
        assert response.details is None
        assert response.errors is None
        assert response.path is None
        assert response.method is None
        assert response.debug_info is None
    
    def test_error_response_with_all_fields(self):
        """Test creating error response with all fields."""
        error_details = [
            ErrorDetail(field="name", message="Required field", code="REQUIRED")
        ]
        
        response = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Validation failed",
            status_code=422,
            correlation_id="test-correlation-id",
            details={"source": "test"},
            errors=error_details,
            path="/api/test",
            method="POST",
            debug_info={"debug": True}
        )
        
        assert response.error_code == "VALIDATION_ERROR"
        assert response.message == "Validation failed"
        assert response.status_code == 422
        assert response.correlation_id == "test-correlation-id"
        assert response.details == {"source": "test"}
        assert len(response.errors) == 1
        assert response.errors[0].field == "name"
        assert response.path == "/api/test"
        assert response.method == "POST"
        assert response.debug_info == {"debug": True}
    
    def test_error_response_json_serialization(self):
        """Test error response JSON serialization."""
        response = ErrorResponse(
            error_code="TEST_ERROR",
            message="Test message",
            status_code=400
        )
        
        json_data = response.model_dump()
        
        assert json_data["error"] is True
        assert json_data["error_code"] == "TEST_ERROR"
        assert json_data["message"] == "Test message"
        assert json_data["status_code"] == 400
        assert "correlation_id" in json_data
        assert "timestamp" in json_data


class TestSpecificErrorResponses:
    """Test specific error response models."""
    
    def test_validation_error_response(self):
        """Test ValidationErrorResponse defaults."""
        response = ValidationErrorResponse()
        
        assert response.error_code == "VALIDATION_ERROR"
        assert response.message == "Validation failed"
        assert response.status_code == 422
    
    def test_not_found_error_response(self):
        """Test NotFoundErrorResponse defaults."""
        response = NotFoundErrorResponse()
        
        assert response.error_code == "NOT_FOUND"
        assert response.message == "Resource not found"
        assert response.status_code == 404
    
    def test_unauthorized_error_response(self):
        """Test UnauthorizedErrorResponse defaults."""
        response = UnauthorizedErrorResponse()
        
        assert response.error_code == "UNAUTHORIZED"
        assert response.message == "Authentication required"
        assert response.status_code == 401
    
    def test_forbidden_error_response(self):
        """Test ForbiddenErrorResponse defaults."""
        response = ForbiddenErrorResponse()
        
        assert response.error_code == "FORBIDDEN"
        assert response.message == "Access denied"
        assert response.status_code == 403
    
    def test_rate_limit_error_response(self):
        """Test RateLimitErrorResponse defaults."""
        response = RateLimitErrorResponse()
        
        assert response.error_code == "RATE_LIMIT_EXCEEDED"
        assert response.message == "Rate limit exceeded"
        assert response.status_code == 429
    
    def test_internal_server_error_response(self):
        """Test InternalServerErrorResponse defaults."""
        response = InternalServerErrorResponse()
        
        assert response.error_code == "INTERNAL_SERVER_ERROR"
        assert response.message == "Internal server error"
        assert response.status_code == 500
    
    def test_external_service_error_response(self):
        """Test ExternalServiceErrorResponse defaults."""
        response = ExternalServiceErrorResponse()
        
        assert response.error_code == "EXTERNAL_SERVICE_ERROR"
        assert response.message == "External service error"
        assert response.status_code == 502
        assert response.service is None
    
    def test_external_service_error_with_service(self):
        """Test ExternalServiceErrorResponse with service."""
        response = ExternalServiceErrorResponse(service="GitHub")
        
        assert response.service == "GitHub"


class TestCreateErrorResponse:
    """Test create_error_response factory function."""
    
    def test_create_error_response_from_pr_summarizer_error(self):
        """Test creating error response from PRSummarizerError."""
        error = ValidationError(
            "Test validation error",
            details={"field": "test"}
        )
        
        response = create_error_response(error)
        
        assert response.error_code == "VALIDATION_ERROR"
        assert response.message == "Test validation error"
        assert response.status_code == 422
        assert response.details == {"field": "test"}
        assert response.correlation_id is not None
    
    def test_create_error_response_with_context(self):
        """Test creating error response with context information."""
        error = AuthenticationError("Access denied")
        
        response = create_error_response(
            error,
            correlation_id="test-id",
            path="/api/resource",
            method="GET"
        )
        
        assert response.correlation_id == "test-id"
        assert response.path == "/api/resource"
        assert response.method == "GET"
    
    def test_create_error_response_with_debug(self):
        """Test creating error response with debug information."""
        error = GitHubAPIError("GitHub API error")
        error.debug_info = {"api_response": "test"}
        
        response = create_error_response(error, include_debug=True)
        
        assert response.debug_info == {"api_response": "test"}
    
    def test_create_error_response_from_standard_exception(self):
        """Test creating error response from standard Python exception."""
        error = ValueError("Standard Python error")
        
        response = create_error_response(error)
        
        assert response.error_code == "INTERNAL_SERVER_ERROR"
        assert response.message == "Internal server error"
        assert response.status_code == 500
        assert response.details == {"exception_type": "ValueError"}
    
    def test_create_error_response_from_standard_exception_with_debug(self):
        """Test creating error response from standard exception with debug."""
        error = ValueError("Standard Python error")
        
        response = create_error_response(error, include_debug=True)
        
        assert "traceback" in response.debug_info
        assert response.debug_info["exception_type"] == "ValueError"


class TestCreateValidationErrorResponse:
    """Test create_validation_error_response factory function."""
    
    def test_create_validation_error_response_basic(self):
        """Test creating validation error response with basic errors."""
        errors = [
            {
                "field": "email",
                "message": "Invalid email format",
                "code": "INVALID_EMAIL",
                "value": "invalid-email"
            },
            {
                "field": "age",
                "message": "Must be positive",
                "code": "INVALID_VALUE",
                "value": -5
            }
        ]
        
        response = create_validation_error_response(errors)
        
        assert response.error_code == "VALIDATION_ERROR"
        assert response.message == "Validation failed"
        assert response.status_code == 422
        assert len(response.errors) == 2
        assert response.details["error_count"] == 2
        
        # Check first error
        assert response.errors[0].field == "email"
        assert response.errors[0].message == "Invalid email format"
        assert response.errors[0].code == "INVALID_EMAIL"
        assert response.errors[0].value == "invalid-email"
        
        # Check second error
        assert response.errors[1].field == "age"
        assert response.errors[1].message == "Must be positive"
        assert response.errors[1].code == "INVALID_VALUE"
        assert response.errors[1].value == -5
    
    def test_create_validation_error_response_with_context(self):
        """Test creating validation error response with context."""
        errors = [{"field": "name", "message": "Required", "code": "REQUIRED"}]
        
        response = create_validation_error_response(
            errors,
            correlation_id="test-id",
            path="/api/users",
            method="POST"
        )
        
        assert response.correlation_id == "test-id"
        assert response.path == "/api/users"
        assert response.method == "POST"
    
    def test_create_validation_error_response_minimal_errors(self):
        """Test creating validation error response with minimal error data."""
        errors = [{"message": "Error occurred"}]
        
        response = create_validation_error_response(errors)
        
        assert len(response.errors) == 1
        assert response.errors[0].field is None
        assert response.errors[0].message == "Error occurred"
        assert response.errors[0].code == "VALIDATION_ERROR"
        assert response.errors[0].value is None


class TestCreateNotFoundResponse:
    """Test create_not_found_response factory function."""
    
    def test_create_not_found_response_basic(self):
        """Test creating not found response with resource type."""
        response = create_not_found_response("User")
        
        assert response.error_code == "NOT_FOUND"
        assert response.message == "User not found"
        assert response.status_code == 404
        assert response.details["resource"] == "User"
        assert response.details["resource_id"] is None
    
    def test_create_not_found_response_with_id(self):
        """Test creating not found response with resource ID."""
        response = create_not_found_response("Pull Request", "123")
        
        assert response.message == "Pull Request not found (ID: 123)"
        assert response.details["resource"] == "Pull Request"
        assert response.details["resource_id"] == "123"
    
    def test_create_not_found_response_with_context(self):
        """Test creating not found response with context."""
        response = create_not_found_response(
            "Repository",
            "owner/repo",
            correlation_id="test-id",
            path="/api/repos/owner/repo",
            method="GET"
        )
        
        assert response.correlation_id == "test-id"
        assert response.path == "/api/repos/owner/repo"
        assert response.method == "GET"


class TestCreateExternalServiceErrorResponse:
    """Test create_external_service_error_response factory function."""
    
    def test_create_external_service_error_response_basic(self):
        """Test creating external service error response."""
        response = create_external_service_error_response(
            "GitHub",
            "API rate limit exceeded"
        )
        
        assert response.error_code == "EXTERNAL_SERVICE_ERROR"
        assert response.message == "GitHub service error: API rate limit exceeded"
        assert response.status_code == 502
        assert response.service == "GitHub"
        assert response.details["service"] == "GitHub"
    
    def test_create_external_service_error_response_with_details(self):
        """Test creating external service error response with service details."""
        service_details = {
            "status_code": 429,
            "retry_after": 3600,
            "endpoint": "/api/repos"
        }
        
        response = create_external_service_error_response(
            "GitHub",
            "Rate limit exceeded",
            service_details=service_details
        )
        
        assert response.details["service"] == "GitHub"
        assert response.details["status_code"] == 429
        assert response.details["retry_after"] == 3600
        assert response.details["endpoint"] == "/api/repos"
    
    def test_create_external_service_error_response_with_context(self):
        """Test creating external service error response with context."""
        response = create_external_service_error_response(
            "Gemini",
            "API timeout",
            correlation_id="test-id",
            path="/api/summarize",
            method="POST"
        )
        
        assert response.correlation_id == "test-id"
        assert response.path == "/api/summarize"
        assert response.method == "POST"


class TestErrorResponseIntegration:
    """Test error response integration scenarios."""
    
    def test_error_response_serialization_complete(self):
        """Test complete error response serialization."""
        response = ValidationErrorResponse(
            correlation_id="test-123",
            errors=[
                ErrorDetail(
                    field="email",
                    message="Invalid format",
                    code="INVALID_EMAIL",
                    value="bad-email"
                )
            ],
            path="/api/users",
            method="POST",
            details={"validation_stage": "input"}
        )
        
        json_str = response.model_dump_json()
        data = json.loads(json_str)
        
        assert data["error"] is True
        assert data["error_code"] == "VALIDATION_ERROR"
        assert data["correlation_id"] == "test-123"
        assert len(data["errors"]) == 1
        assert data["errors"][0]["field"] == "email"
        assert data["path"] == "/api/users"
        assert data["method"] == "POST"
    
    def test_error_responses_exports(self):
        """Test that all expected classes and functions are exported."""
        from src.models import error_responses
        
        expected_exports = [
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
        
        for export in expected_exports:
            assert hasattr(error_responses, export), f"Missing export: {export}"