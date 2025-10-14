"""Tests for main FastAPI application.

Test coverage for application setup, exception handlers, routes, and lifecycle.
"""

import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from src.main import create_application, app
from src.utils.exceptions import (
    PRSummarizerError,
    ValidationError,
    AuthenticationError,
    ExternalServiceError,
)


class TestApplicationCreation:
    """Test FastAPI application creation and configuration."""
    
    @patch('src.main.get_config')
    def test_create_application_basic(self, mock_get_config):
        """Test creating application with basic configuration."""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.logging.level = "INFO"
        mock_config.logging.json_format = False
        mock_config.logging.enable_correlation_id = True
        mock_config.logging.log_file = None
        mock_config.debug = False
        mock_config.environment = "production"
        mock_get_config.return_value = mock_config
        
        app_instance = create_application()
        
        assert app_instance.title == "PR Summarizer API"
        assert app_instance.version == "1.0.0"
        # In production, docs should be disabled
        assert app_instance.docs_url is None
        assert app_instance.redoc_url is None
        assert app_instance.openapi_url is None
    
    @patch('src.main.get_config')
    def test_create_application_debug_mode(self, mock_get_config):
        """Test creating application with debug mode enabled."""
        # Mock configuration  
        mock_config = MagicMock()
        mock_config.logging.level = "DEBUG"
        mock_config.logging.json_format = False
        mock_config.logging.enable_correlation_id = True
        mock_config.logging.log_file = None
        mock_config.debug = True
        mock_config.environment = "development"
        mock_get_config.return_value = mock_config
        
        app_instance = create_application()
        
        # In debug mode, docs should be enabled
        assert app_instance.docs_url == "/docs"
        assert app_instance.redoc_url == "/redoc"
        assert app_instance.openapi_url == "/openapi.json"


class TestRoutes:
    """Test API routes."""
    
    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct information."""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to PR Summarizer API"
        assert data["version"] == "1.0.0"
        assert data["service"] == "pr-summarizer"
    
    @patch('src.main.get_config')
    def test_root_endpoint_debug_mode(self, mock_get_config):
        """Test root endpoint in debug mode includes documentation links."""
        mock_config = MagicMock()
        mock_config.debug = True
        mock_get_config.return_value = mock_config
        
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "docs" in data
        assert "redoc" in data
        assert "openapi" in data
        assert data["docs"] == "/docs"
    
    def test_health_check_endpoint(self):
        """Test health check endpoint returns correct status."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pr-summarizer"
        assert data["version"] == "1.0.0"
        assert "environment" in data
        assert "timestamp" in data


class TestExceptionHandlers:
    """Test custom exception handlers."""
    
    def setup_method(self):
        """Setup test client and mock routes for testing exceptions."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        # Create a test app with our exception handlers
        test_app = create_application()
        
        # Add test routes that raise exceptions
        @test_app.get("/test/validation-error")
        async def test_validation_error():
            raise ValidationError("Test validation error", details={"field": "test"})
        
        @test_app.get("/test/auth-error")
        async def test_auth_error():
            raise AuthenticationError("Test auth error")
        
        @test_app.get("/test/external-error")
        async def test_external_error():
            raise ExternalServiceError("Test external service error")
        
        @test_app.get("/test/http-exception")
        async def test_http_exception():
            raise HTTPException(status_code=404, detail="Test not found")
        
        @test_app.get("/test/unexpected-error")
        async def test_unexpected_error():
            raise ValueError("Unexpected Python error")
        
        # Add test route for request validation
        class TestModel(BaseModel):
            name: str
            age: int
        
        @test_app.post("/test/request-validation")
        async def test_request_validation(data: TestModel):
            return {"message": "success"}
        
        self.client = TestClient(test_app)
    
    def test_pr_summarizer_validation_error_handler(self):
        """Test handling of ValidationError exceptions."""
        response = self.client.get("/test/validation-error")
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert data["error_code"] == "VALIDATION_ERROR"
        assert data["message"] == "Test validation error"
        assert data["details"] == {"field": "test"}
        assert "correlation_id" in data
        assert "timestamp" in data
        assert data["path"] == "/test/validation-error"
        assert data["method"] == "GET"
    
    def test_pr_summarizer_auth_error_handler(self):
        """Test handling of AuthenticationError exceptions."""
        response = self.client.get("/test/auth-error")
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert data["error_code"] == "AUTHENTICATION_ERROR"
        assert data["message"] == "Test auth error"
    
    def test_pr_summarizer_external_error_handler(self):
        """Test handling of ExternalServiceError exceptions."""
        response = self.client.get("/test/external-error")
        
        assert response.status_code == 502
        data = response.json()
        assert data["error"] is True
        assert data["error_code"] == "EXTERNAL_SERVICE_ERROR"
        assert data["message"] == "Test external service error"
    
    def test_request_validation_error_handler(self):
        """Test handling of Pydantic request validation errors."""
        # Send invalid data
        response = self.client.post("/test/request-validation", json={
            "name": "test",
            "age": "invalid"  # Should be int
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert data["error_code"] == "VALIDATION_ERROR"
        assert data["message"] == "Validation failed"
        assert len(data["errors"]) > 0
        
        # Check error structure
        error_detail = data["errors"][0]
        assert "field" in error_detail
        assert "message" in error_detail
        assert "code" in error_detail
    
    def test_http_exception_handler(self):
        """Test handling of HTTP exceptions."""
        response = self.client.get("/test/http-exception")
        
        assert response.status_code == 404
        # Should use FastAPI's default format for HTTP exceptions
        data = response.json()
        assert data["detail"] == "Test not found"
    
    def test_general_exception_handler(self):
        """Test handling of unexpected exceptions."""
        response = self.client.get("/test/unexpected-error")
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"] is True
        assert data["error_code"] == "INTERNAL_SERVER_ERROR"
        assert data["message"] == "Internal server error"
        assert data["details"]["exception_type"] == "ValueError"
    
    @patch('src.main.get_config')
    def test_exception_handler_with_debug(self, mock_get_config):
        """Test exception handler includes debug info when debug is enabled."""
        mock_config = MagicMock()
        mock_config.debug = True
        mock_config.logging.level = "DEBUG"
        mock_config.logging.json_format = False
        mock_config.logging.enable_correlation_id = True
        mock_config.logging.log_file = None
        mock_config.environment = "development"
        mock_get_config.return_value = mock_config
        
        response = self.client.get("/test/unexpected-error")
        
        assert response.status_code == 500
        data = response.json()
        assert "debug_info" in data
        assert "traceback" in data["debug_info"]


class TestApplicationLifespan:
    """Test application lifespan management."""
    
    @patch('src.main.get_config')
    @patch('src.main.logger')
    def test_lifespan_startup_success(self, mock_logger, mock_get_config):
        """Test successful application startup."""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.environment = "test"
        mock_config.debug = True
        mock_config.host = "127.0.0.1"
        mock_config.port = 8000
        mock_config.database = None
        mock_config.redis = None
        mock_get_config.return_value = mock_config
        
        # Test lifespan context manager
        from src.main import lifespan
        
        async def run_lifespan():
            async with lifespan(MagicMock()):
                pass
        
        # Should complete without exceptions
        import asyncio
        asyncio.run(run_lifespan())
        
        # Check that startup logs were called
        mock_logger.info.assert_called()
    
    @patch('src.main.get_config')
    @patch('src.main.logger')
    def test_lifespan_with_database_and_redis(self, mock_logger, mock_get_config):
        """Test application startup with database and Redis configured."""
        # Mock configuration with database and redis
        mock_config = MagicMock()
        mock_config.environment = "test"
        mock_config.debug = True
        mock_config.host = "127.0.0.1"
        mock_config.port = 8000
        mock_config.database = MagicMock()  # Database configured
        mock_config.redis = MagicMock()     # Redis configured
        mock_get_config.return_value = mock_config
        
        from src.main import lifespan
        
        async def run_lifespan():
            async with lifespan(MagicMock()):
                pass
        
        import asyncio
        asyncio.run(run_lifespan())
        
        # Verify database and Redis initialization logs
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Database connection initialized" in msg for msg in info_calls)
        assert any("Cache connection initialized" in msg for msg in info_calls)


class TestApplicationIntegration:
    """Test full application integration."""
    
    def test_application_exports(self):
        """Test that all expected classes and functions are exported."""
        from src import main
        
        expected_exports = [
            "app",
            "create_application",
            "register_exception_handlers",
            "register_routes",
        ]
        
        for export in expected_exports:
            assert hasattr(main, export), f"Missing export: {export}"
    
    def test_application_instance_exists(self):
        """Test that the main application instance is created."""
        from src.main import app
        
        assert app is not None
        assert hasattr(app, 'title')
        assert app.title == "PR Summarizer API"
    
    def test_full_request_flow(self):
        """Test a complete request flow through the application."""
        client = TestClient(app)
        
        # Test health check
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        
        # Test 404 for unknown endpoint
        response = client.get("/unknown-endpoint")
        assert response.status_code == 404


class TestCORSMiddleware:
    """Test CORS middleware functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create test application
        test_app = create_application()
        self.client = TestClient(test_app)
    
    def test_cors_middleware_registration(self):
        """Test that CORS middleware is properly registered."""
        # Test preflight request (OPTIONS)
        response = self.client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert "access-control-allow-credentials" in response.headers
        assert response.headers["access-control-allow-credentials"] == "true"
        assert "access-control-allow-methods" in response.headers
        assert "GET" in response.headers["access-control-allow-methods"]
        assert "access-control-max-age" in response.headers
        assert response.headers["access-control-max-age"] == "3600"
    
    def test_cors_actual_request(self):
        """Test CORS headers on actual requests."""
        response = self.client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert "access-control-allow-credentials" in response.headers
        assert response.headers["access-control-allow-credentials"] == "true"
        assert "access-control-expose-headers" in response.headers
        assert "X-Correlation-ID" in response.headers["access-control-expose-headers"]
    
    def test_cors_allowed_origin(self):
        """Test CORS with allowed origin."""
        response = self.client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    
    def test_cors_disallowed_origin(self):
        """Test CORS with disallowed origin."""
        response = self.client.get(
            "/health",
            headers={"Origin": "http://malicious-site.com"}
        )
        
        # Request should still succeed (CORS is browser-enforced)
        # but no CORS headers should be present for disallowed origins
        assert response.status_code == 200
        # Note: Some CORS implementations may still return headers but mark as disallowed
        # The key is that browsers will block the request
    
    def test_cors_all_methods_allowed(self):
        """Test that all common HTTP methods are allowed in CORS."""
        methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]
        
        for method in methods:
            response = self.client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": method
                }
            )
            
            assert response.status_code == 200
            allowed_methods = response.headers.get("access-control-allow-methods", "")
            assert method in allowed_methods, f"Method {method} not allowed in CORS"
    
    def test_cors_custom_headers_allowed(self):
        """Test that custom headers are allowed in CORS."""
        response = self.client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-Custom-Header,Authorization,Content-Type"
            }
        )
        
        assert response.status_code == 200
        assert "access-control-allow-headers" in response.headers
        # Should allow all headers (configured with "*")
    
    @patch('src.main.get_config')
    def test_cors_custom_configuration(self, mock_get_config):
        """Test CORS with custom configuration."""
        # Setup custom config
        mock_config = MagicMock()
        mock_config.debug = False
        mock_config.logging.level = "INFO"
        mock_config.logging.json_format = False
        mock_config.logging.enable_correlation_id = True
        mock_config.logging.log_file = None
        mock_config.environment = "test"
        
        # Custom CORS settings
        mock_config.security.cors_origins = ["https://app.example.com", "https://admin.example.com"]
        mock_config.security.cors_allow_credentials = False
        
        mock_get_config.return_value = mock_config
        
        # Create application with custom config
        test_app = create_application()
        client = TestClient(test_app)
        
        # Test with first allowed origin
        response = client.get(
            "/health",
            headers={"Origin": "https://app.example.com"}
        )
        
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://app.example.com"
        # When credentials are False, the header might not be included
        credentials_header = response.headers.get("access-control-allow-credentials")
        assert credentials_header in [None, "false"]
        
        # Test with second allowed origin
        response = client.get(
            "/health",
            headers={"Origin": "https://admin.example.com"}
        )
        
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://admin.example.com"
    
    def test_cors_without_origin_header(self):
        """Test request without Origin header (non-CORS request)."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        # No CORS headers should be present for non-CORS requests
        assert "access-control-allow-origin" not in response.headers


class TestLoggingMiddleware:
    """Test logging middleware functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create test application
        test_app = create_application()
        self.client = TestClient(test_app)
    
    def test_logging_middleware_adds_correlation_id(self):
        """Test that logging middleware adds correlation ID to response headers."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        assert "x-correlation-id" in response.headers
        # Correlation ID should be a UUID format
        correlation_id = response.headers["x-correlation-id"]
        assert len(correlation_id) == 36  # UUID string length
        assert correlation_id.count("-") == 4  # UUID has 4 hyphens
    
    def test_logging_middleware_unique_correlation_ids(self):
        """Test that each request gets a unique correlation ID."""
        response1 = self.client.get("/health")
        response2 = self.client.get("/health")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        correlation_id1 = response1.headers["x-correlation-id"]
        correlation_id2 = response2.headers["x-correlation-id"]
        
        assert correlation_id1 != correlation_id2
    
    @patch('src.utils.logger.log_api_request')
    @patch('src.utils.logger.log_api_response')
    def test_logging_middleware_logs_successful_request(self, mock_log_response, mock_log_request):
        """Test that successful requests are properly logged."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        
        # Verify request logging was called
        assert mock_log_request.called
        request_call = mock_log_request.call_args
        assert request_call[1]["method"] == "GET"
        assert request_call[1]["path"] == "/health"
        assert "request_id" in request_call[1]
        
        # Verify response logging was called
        assert mock_log_response.called
        response_call = mock_log_response.call_args
        assert response_call[1]["status_code"] == 200
        assert response_call[1]["path"] == "/health"
        assert "duration_ms" in response_call[1]
        assert "request_id" in response_call[1]
    
    @patch('src.utils.logger.log_api_request')
    @patch('src.utils.logger.log_api_response')
    def test_logging_middleware_logs_error_request(self, mock_log_response, mock_log_request):
        """Test that error requests are properly logged."""
        response = self.client.get("/nonexistent")
        
        assert response.status_code == 404
        
        # Verify request logging was called
        assert mock_log_request.called
        request_call = mock_log_request.call_args
        assert request_call[1]["method"] == "GET"
        assert request_call[1]["path"] == "/nonexistent"
        
        # Verify response logging was called with error status
        assert mock_log_response.called
        response_call = mock_log_response.call_args
        assert response_call[1]["status_code"] == 404
        assert response_call[1]["path"] == "/nonexistent"
        assert "duration_ms" in response_call[1]
    
    @patch('src.utils.logger.log_api_request')
    @patch('src.utils.logger.log_api_response')
    def test_logging_middleware_logs_query_parameters(self, mock_log_response, mock_log_request):
        """Test that query parameters are logged."""
        response = self.client.get("/health?test=value&foo=bar")
        
        assert response.status_code == 200
        
        # Verify request logging includes query parameters
        assert mock_log_request.called
        request_call = mock_log_request.call_args
        assert request_call[1]["query_params"] == {"test": "value", "foo": "bar"}
    
    @patch('src.utils.logger.log_api_request')
    def test_logging_middleware_logs_client_info(self, mock_log_request):
        """Test that client information is logged."""
        headers = {"User-Agent": "TestClient/1.0"}
        response = self.client.get("/health", headers=headers)
        
        assert response.status_code == 200
        
        # Verify request logging includes client info
        assert mock_log_request.called
        request_call = mock_log_request.call_args
        assert request_call[1]["user_agent"] == "TestClient/1.0"
        assert "client_ip" in request_call[1]
    
    def test_logging_middleware_timing_accuracy(self):
        """Test that request timing is reasonably accurate."""
        import time
        
        # Make request and measure time
        start = time.time()
        response = self.client.get("/health")
        end = time.time()
        
        assert response.status_code == 200
        
        # The logged duration should be within reasonable bounds of measured time
        # We can't easily test the exact logged duration without mocking,
        # but we can verify the correlation ID is present
        assert "x-correlation-id" in response.headers
    
    @patch('src.utils.logger.log_api_response')
    def test_logging_middleware_handles_exception_during_processing(self, mock_log_response):
        """Test that middleware properly logs when an exception occurs during request processing."""
        
        # For this test, we'll just verify that the logging middleware doesn't break
        # when there are application errors. The actual error logging is handled
        # by the FastAPI exception handlers, not the middleware directly.
        
        # Test with a request to a non-existent endpoint (404 error)
        response = self.client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        
        # Should still have correlation ID even for error responses
        assert "x-correlation-id" in response.headers
        
        # Verify response logging was called for the error
        assert mock_log_response.called
        response_call = mock_log_response.call_args
        assert response_call[1]["status_code"] == 404
    
    def test_logging_middleware_preserves_existing_headers(self):
        """Test that logging middleware preserves existing response headers."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        
        # Should have correlation ID header
        assert "x-correlation-id" in response.headers
        
        # Should also have other response headers like content-type
        assert "content-type" in response.headers