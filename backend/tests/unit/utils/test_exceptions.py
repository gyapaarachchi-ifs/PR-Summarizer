"""Tests for custom exception classes."""

import pytest
from src.utils.exceptions import (
    PRSummarizerError,
    ValidationError,
    ExternalServiceError,
    GitHubAPIError,
    GeminiAPIError,
    JiraAPIError,
    ConfluenceAPIError,
    ConfigurationError,
    AuthenticationError,
    RateLimitError,
)


class TestPRSummarizerError:
    """Test base exception class."""

    def test_base_exception_creation(self):
        """Test creating base exception with message."""
        error = PRSummarizerError("Base error message")
        assert str(error) == "Base error message"
        assert error.message == "Base error message"
        assert error.details is None

    def test_base_exception_with_details(self):
        """Test creating base exception with details."""
        details = {"code": "E001", "field": "username"}
        error = PRSummarizerError("Error with details", details=details)
        assert str(error) == "Error with details"
        assert error.message == "Error with details"
        assert error.details == details

    def test_base_exception_inheritance(self):
        """Test that base exception inherits from Exception."""
        error = PRSummarizerError("Test")
        assert isinstance(error, Exception)


class TestValidationError:
    """Test validation exception class."""

    def test_validation_error_creation(self):
        """Test creating validation error."""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"
        assert isinstance(error, PRSummarizerError)

    def test_validation_error_with_field_details(self):
        """Test validation error with field-specific details."""
        details = {"field": "pr_number", "value": "invalid"}
        error = ValidationError("PR number must be an integer", details=details)
        assert error.details["field"] == "pr_number"
        assert error.details["value"] == "invalid"


class TestExternalServiceError:
    """Test external service exception class."""

    def test_external_service_error_creation(self):
        """Test creating external service error."""
        error = ExternalServiceError("Service unavailable")
        assert str(error) == "Service unavailable"
        assert isinstance(error, PRSummarizerError)

    def test_external_service_error_with_service_details(self):
        """Test external service error with service-specific details."""
        details = {"service": "github", "status_code": 503}
        error = ExternalServiceError("GitHub API unavailable", details=details)
        assert error.details["service"] == "github"
        assert error.details["status_code"] == 503


class TestGitHubAPIError:
    """Test GitHub API exception class."""

    def test_github_api_error_creation(self):
        """Test creating GitHub API error."""
        error = GitHubAPIError("Repository not found")
        assert str(error) == "Repository not found"
        assert isinstance(error, ExternalServiceError)

    def test_github_api_error_with_response_details(self):
        """Test GitHub API error with response details."""
        details = {"status_code": 404, "response": {"message": "Not Found"}}
        error = GitHubAPIError("Repository not found", details=details)
        assert error.details["status_code"] == 404
        assert error.details["response"]["message"] == "Not Found"


class TestGeminiAPIError:
    """Test Gemini API exception class."""

    def test_gemini_api_error_creation(self):
        """Test creating Gemini API error."""
        error = GeminiAPIError("API quota exceeded")
        assert str(error) == "API quota exceeded"
        assert isinstance(error, ExternalServiceError)

    def test_gemini_api_error_with_quota_details(self):
        """Test Gemini API error with quota details."""
        details = {"quota_type": "requests_per_minute", "limit": 60}
        error = GeminiAPIError("Rate limit exceeded", details=details)
        assert error.details["quota_type"] == "requests_per_minute"
        assert error.details["limit"] == 60


class TestJiraAPIError:
    """Test Jira API exception class."""

    def test_jira_api_error_creation(self):
        """Test creating Jira API error."""
        error = JiraAPIError("Issue not found")
        assert str(error) == "Issue not found"
        assert isinstance(error, ExternalServiceError)


class TestConfluenceAPIError:
    """Test Confluence API exception class."""

    def test_confluence_api_error_creation(self):
        """Test creating Confluence API error."""
        error = ConfluenceAPIError("Page not found")
        assert str(error) == "Page not found"
        assert isinstance(error, ExternalServiceError)


class TestConfigurationError:
    """Test configuration exception class."""

    def test_configuration_error_creation(self):
        """Test creating configuration error."""
        error = ConfigurationError("Missing API key")
        assert str(error) == "Missing API key"
        assert isinstance(error, PRSummarizerError)

    def test_configuration_error_with_config_details(self):
        """Test configuration error with config details."""
        details = {"config_key": "GITHUB_TOKEN", "source": "environment"}
        error = ConfigurationError("GitHub token not configured", details=details)
        assert error.details["config_key"] == "GITHUB_TOKEN"
        assert error.details["source"] == "environment"


class TestAuthenticationError:
    """Test authentication exception class."""

    def test_authentication_error_creation(self):
        """Test creating authentication error."""
        error = AuthenticationError("Invalid token")
        assert str(error) == "Invalid token"
        assert isinstance(error, PRSummarizerError)

    def test_authentication_error_with_auth_details(self):
        """Test authentication error with auth details."""
        details = {"token_type": "github", "expires_at": "2024-01-01T00:00:00Z"}
        error = AuthenticationError("Token expired", details=details)
        assert error.details["token_type"] == "github"
        assert error.details["expires_at"] == "2024-01-01T00:00:00Z"


class TestRateLimitError:
    """Test rate limit exception class."""

    def test_rate_limit_error_creation(self):
        """Test creating rate limit error."""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert isinstance(error, ExternalServiceError)

    def test_rate_limit_error_with_limit_details(self):
        """Test rate limit error with limit details."""
        details = {
            "service": "github",
            "limit": 5000,
            "remaining": 0,
            "reset_at": "2024-01-01T01:00:00Z"
        }
        error = RateLimitError("GitHub rate limit exceeded", details=details)
        assert error.details["service"] == "github"
        assert error.details["limit"] == 5000
        assert error.details["remaining"] == 0
        assert error.details["reset_at"] == "2024-01-01T01:00:00Z"


class TestExceptionToDict:
    """Test exception serialization to dictionary."""

    def test_exception_to_dict_basic(self):
        """Test converting exception to dictionary."""
        error = PRSummarizerError("Test error")
        error_dict = error.to_dict()
        
        expected = {
            "type": "PRSummarizerError",
            "message": "Test error",
            "details": None
        }
        assert error_dict == expected

    def test_exception_to_dict_with_details(self):
        """Test converting exception with details to dictionary."""
        details = {"field": "test", "value": 123}
        error = ValidationError("Validation failed", details=details)
        error_dict = error.to_dict()
        
        expected = {
            "type": "ValidationError",
            "message": "Validation failed",
            "details": {"field": "test", "value": 123}
        }
        assert error_dict == expected

    def test_nested_exception_to_dict(self):
        """Test converting nested exception to dictionary."""
        github_error = GitHubAPIError("API error", details={"status_code": 404})
        error_dict = github_error.to_dict()
        
        expected = {
            "type": "GitHubAPIError",
            "message": "API error",
            "details": {"status_code": 404}
        }
        assert error_dict == expected