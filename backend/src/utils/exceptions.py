"""Custom exception classes for PR Summarizer application.

This module defines a hierarchy of exceptions used throughout the application
to provide structured error handling with detailed context information.
"""

from typing import Any, Dict, Optional


class PRSummarizerError(Exception):
    """Base exception class for all PR Summarizer errors.
    
    Provides a foundation for structured error handling with optional
    detailed context information that can be serialized for logging
    and API responses.
    
    Attributes:
        message: Human-readable error message
        details: Optional dictionary with additional error context
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the exception with message and optional details.
        
        Args:
            message: Human-readable error description
            details: Optional dictionary with additional context
        """
        super().__init__(message)
        self.message = message
        self.details = details
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization.
        
        Returns:
            Dictionary representation of the exception with type, message, and details
        """
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ValidationError(PRSummarizerError):
    """Exception raised for input validation errors.
    
    Used when user input or data validation fails, providing specific
    context about which field or value caused the validation failure.
    """
    pass


class ExternalServiceError(PRSummarizerError):
    """Base exception for external service communication errors.
    
    Used as a base class for all errors related to external API calls
    or service integrations (GitHub, Gemini, Jira, Confluence, etc.).
    """
    pass


class GitHubAPIError(ExternalServiceError):
    """Exception raised for GitHub API errors.
    
    Handles errors from GitHub API calls including authentication failures,
    rate limiting, repository access issues, and API response errors.
    """
    pass


class GeminiAPIError(ExternalServiceError):
    """Exception raised for Google Gemini API errors.
    
    Handles errors from Gemini API calls including quota exceeded,
    authentication failures, and content generation errors.
    """
    pass


class JiraAPIError(ExternalServiceError):
    """Exception raised for Jira API errors.
    
    Handles errors from Jira API calls including authentication failures,
    issue access problems, and API response errors.
    """
    pass


class ConfluenceAPIError(ExternalServiceError):
    """Exception raised for Confluence API errors.
    
    Handles errors from Confluence API calls including authentication failures,
    page access problems, and API response errors.
    """
    pass


class ConfigurationError(PRSummarizerError):
    """Exception raised for application configuration errors.
    
    Used when required configuration values are missing, invalid,
    or inconsistent. Provides context about which configuration
    parameter caused the issue.
    """
    pass


class AuthenticationError(PRSummarizerError):
    """Exception raised for authentication and authorization errors.
    
    Used when API tokens are invalid, expired, or lack sufficient
    permissions for the requested operation.
    """
    pass


class RateLimitError(ExternalServiceError):
    """Exception raised when external service rate limits are exceeded.
    
    Provides information about the rate limit including current usage,
    limits, and reset time to help with retry logic and user feedback.
    """
    pass


# Export all exception classes for easy importing
__all__ = [
    "PRSummarizerError",
    "ValidationError", 
    "ExternalServiceError",
    "GitHubAPIError",
    "GeminiAPIError",
    "JiraAPIError",
    "ConfluenceAPIError",
    "ConfigurationError",
    "AuthenticationError",
    "RateLimitError",
]