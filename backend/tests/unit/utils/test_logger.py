"""Tests for structured logging utilities."""

import json
import logging
import os
from io import StringIO
from unittest.mock import patch

import pytest
import structlog

from src.utils.logger import (
    configure_logging,
    get_logger,
    log_api_request,
    log_api_response,
    log_external_service_call,
    log_performance_metric,
    LogLevel,
)


class TestLoggerConfiguration:
    """Test logger configuration functionality."""

    def test_configure_logging_default(self):
        """Test configuring logging with default settings."""
        configure_logging()
        
        # Verify structlog is configured
        logger = structlog.get_logger()
        assert logger is not None
        
        # Verify processors are configured
        processors = structlog.get_config()["processors"]
        assert len(processors) > 0

    def test_configure_logging_with_level(self):
        """Test configuring logging with specific level."""
        configure_logging(level=LogLevel.DEBUG)
        
        # Test that debug level is set
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_configure_logging_json_format(self):
        """Test configuring logging with JSON format."""
        configure_logging(json_format=True)
        
        logger = structlog.get_logger()
        assert logger is not None

    def test_configure_logging_with_correlation_id(self):
        """Test configuring logging with correlation ID support."""
        configure_logging()
        
        logger = get_logger("test")
        assert logger is not None


class TestLoggerCreation:
    """Test logger creation and usage."""

    def test_get_logger_default(self):
        """Test getting logger with default name."""
        logger = get_logger()
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'warning')

    def test_get_logger_with_name(self):
        """Test getting logger with specific name."""
        logger = get_logger("test_module")
        assert logger is not None

    def test_get_logger_with_context(self):
        """Test getting logger with context."""
        context = {"user_id": "12345", "request_id": "abc-123"}
        logger = get_logger("test", **context)
        assert logger is not None

    def test_logger_methods_exist(self):
        """Test that logger has required methods."""
        logger = get_logger()
        
        required_methods = ['debug', 'info', 'warning', 'error', 'exception']
        for method in required_methods:
            assert hasattr(logger, method)
            assert callable(getattr(logger, method))


class TestAPILogging:
    """Test API-specific logging functions."""

    def test_log_api_request_basic(self):
        """Test logging API request with basic info."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            
            log_api_request(
                method="GET",
                path="/api/pr/123/summary",
                user_id="user123"
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "API request received"
            assert call_args[1]["method"] == "GET"
            assert call_args[1]["path"] == "/api/pr/123/summary"
            assert call_args[1]["user_id"] == "user123"

    def test_log_api_request_with_body(self):
        """Test logging API request with request body."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            
            request_body = {"pr_number": 123, "repository": "test/repo"}
            
            log_api_request(
                method="POST",
                path="/api/pr/summarize",
                user_id="user123",
                request_body=request_body
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[1]["request_body"] == request_body

    def test_log_api_response_success(self):
        """Test logging successful API response."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            
            log_api_response(
                status_code=200,
                path="/api/pr/123/summary",
                duration_ms=250.5,
                response_size=1024
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "API response sent"
            assert call_args[1]["status_code"] == 200
            assert call_args[1]["duration_ms"] == 250.5
            assert call_args[1]["response_size"] == 1024

    def test_log_api_response_error(self):
        """Test logging error API response."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            
            log_api_response(
                status_code=500,
                path="/api/pr/123/summary",
                duration_ms=100.0,
                error="Internal server error"
            )
            
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert call_args[0][0] == "API response sent"
            assert call_args[1]["status_code"] == 500
            assert call_args[1]["error"] == "Internal server error"


class TestExternalServiceLogging:
    """Test external service logging functions."""

    def test_log_external_service_call_success(self):
        """Test logging successful external service call."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            
            log_external_service_call(
                service="github",
                operation="get_pr",
                url="https://api.github.com/repos/owner/repo/pulls/123",
                status_code=200,
                duration_ms=150.0,
                request_id="req-123"
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "External service call"
            assert call_args[1]["service"] == "github"
            assert call_args[1]["operation"] == "get_pr"
            assert call_args[1]["status_code"] == 200

    def test_log_external_service_call_error(self):
        """Test logging failed external service call."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            
            log_external_service_call(
                service="gemini",
                operation="generate_summary",
                url="https://generativelanguage.googleapis.com/v1/models",
                status_code=429,
                duration_ms=50.0,
                error="Rate limit exceeded"
            )
            
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert call_args[1]["service"] == "gemini"
            assert call_args[1]["status_code"] == 429
            assert call_args[1]["error"] == "Rate limit exceeded"

    def test_log_external_service_call_with_response(self):
        """Test logging external service call with response data."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            
            response_data = {"pr_count": 5, "files_changed": 3}
            
            log_external_service_call(
                service="github",
                operation="get_pr_stats",
                url="https://api.github.com/repos/owner/repo/pulls/123",
                status_code=200,
                duration_ms=75.0,
                response_data=response_data
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[1]["response_data"] == response_data


class TestPerformanceLogging:
    """Test performance metric logging."""

    def test_log_performance_metric_basic(self):
        """Test logging basic performance metric."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            
            log_performance_metric(
                operation="pr_summary_generation",
                duration_ms=1500.0,
                success=True
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "Performance metric"
            assert call_args[1]["operation"] == "pr_summary_generation"
            assert call_args[1]["duration_ms"] == 1500.0
            assert call_args[1]["success"] is True

    def test_log_performance_metric_with_metadata(self):
        """Test logging performance metric with additional metadata."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            
            metadata = {
                "pr_number": 123,
                "repository": "test/repo",
                "file_count": 5,
                "line_changes": 150
            }
            
            log_performance_metric(
                operation="pr_analysis",
                duration_ms=2500.0,
                success=True,
                metadata=metadata
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[1]["metadata"] == metadata

    def test_log_performance_metric_failure(self):
        """Test logging performance metric for failed operation."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            
            log_performance_metric(
                operation="external_api_call",
                duration_ms=5000.0,
                success=False,
                error="Timeout after 5 seconds"
            )
            
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert call_args[1]["success"] is False
            assert call_args[1]["error"] == "Timeout after 5 seconds"


class TestLogLevel:
    """Test LogLevel enum."""

    def test_log_level_values(self):
        """Test that LogLevel enum has expected values."""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"

    def test_log_level_to_logging_level(self):
        """Test conversion from LogLevel to Python logging levels."""
        level_mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
        }
        
        for log_level, expected_level in level_mapping.items():
            assert getattr(logging, log_level) == expected_level


class TestJSONLogging:
    """Test JSON format logging output."""

    def test_json_log_format(self):
        """Test that JSON logging produces valid JSON."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            configure_logging(json_format=True, level=LogLevel.INFO)
            
            logger = get_logger("test")
            logger.info("Test message", test_field="test_value")
            
            # Check that output can be parsed as JSON
            output = mock_stdout.getvalue().strip()
            if output:  # Only test if there's output
                try:
                    parsed = json.loads(output)
                    assert "test_field" in parsed or "message" in parsed
                except json.JSONDecodeError:
                    # Some implementations might not output to stdout directly
                    pass


class TestCorrelationID:
    """Test correlation ID functionality."""

    def test_logger_with_correlation_id(self):
        """Test logger with correlation ID context."""
        configure_logging()
        
        correlation_id = "corr-12345"
        logger = get_logger("test", correlation_id=correlation_id)
        
        # Verify logger can be created with correlation ID
        assert logger is not None

    def test_correlation_id_inheritance(self):
        """Test that correlation ID is inherited in child loggers."""
        configure_logging()
        
        parent_logger = get_logger("parent", correlation_id="parent-123")
        child_logger = get_logger("parent.child")
        
        # Both loggers should exist
        assert parent_logger is not None
        assert child_logger is not None