"""Input validation utilities for PR Summarizer application.

This module provides Pydantic-based validation helpers for common
input types used throughout the application.
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

from pydantic import BaseModel, Field, validator
from pydantic import ValidationError as PydanticValidationError

from src.utils.exceptions import ValidationError


class BaseValidator(ABC):
    """Base class for all input validators."""
    
    @abstractmethod
    def validate(self, value: Any) -> Any:
        """Validate input value and return validated result.
        
        Args:
            value: Value to validate
            
        Returns:
            Validated value
            
        Raises:
            ValidationError: If validation fails
        """
        pass


class PRNumberValidator(BaseValidator):
    """Validator for pull request numbers."""
    
    def validate(self, value: Union[int, str]) -> int:
        """Validate PR number.
        
        Args:
            value: PR number as int or string
            
        Returns:
            Validated PR number as integer
            
        Raises:
            ValidationError: If PR number is invalid
        """
        try:
            if isinstance(value, str):
                # Handle string with leading zeros
                value = value.lstrip('0') or '0'
                pr_number = int(value)
            else:
                pr_number = int(value)
            
            if pr_number <= 0:
                raise ValidationError(
                    "PR number must be a positive integer",
                    details={"field": "pr_number", "value": value}
                )
            
            return pr_number
            
        except (ValueError, TypeError) as e:
            raise ValidationError(
                "PR number must be a valid positive integer",
                details={"field": "pr_number", "value": value, "error": str(e)}
            )


class RepositoryValidator(BaseValidator):
    """Validator for GitHub repository identifiers."""
    
    REPO_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$')
    
    def validate(self, value: str) -> str:
        """Validate repository identifier.
        
        Args:
            value: Repository identifier in format 'owner/repo'
            
        Returns:
            Validated repository identifier
            
        Raises:
            ValidationError: If repository identifier is invalid
        """
        if not isinstance(value, str) or not value:
            raise ValidationError(
                "Repository identifier must be a non-empty string",
                details={"field": "repository", "value": value}
            )
        
        if not self.REPO_PATTERN.match(value):
            raise ValidationError(
                "Repository identifier must be in format 'owner/repo'",
                details={"field": "repository", "value": value}
            )
        
        parts = value.split('/')
        if len(parts) != 2:
            raise ValidationError(
                "Repository identifier must contain exactly one slash",
                details={"field": "repository", "value": value}
            )
        
        owner, repo = parts
        if not owner or not repo:
            raise ValidationError(
                "Both owner and repository name must be non-empty",
                details={"field": "repository", "value": value}
            )
        
        return value


class GitHubURLValidator(BaseValidator):
    """Validator for GitHub URLs."""
    
    def validate(self, value: str) -> str:
        """Validate GitHub URL.
        
        Args:
            value: GitHub URL
            
        Returns:
            Validated GitHub URL
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not isinstance(value, str) or not value:
            raise ValidationError(
                "GitHub URL must be a non-empty string",
                details={"field": "github_url", "value": value}
            )
        
        try:
            parsed = urlparse(value)
        except Exception as e:
            raise ValidationError(
                "Invalid URL format",
                details={"field": "github_url", "value": value, "error": str(e)}
            )
        
        # Check if URL has valid scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            raise ValidationError(
                "GitHub URL format is invalid - missing scheme or domain",
                details={"field": "github_url", "value": value}
            )
        
        if parsed.scheme != 'https':
            raise ValidationError(
                "GitHub URL must use HTTPS",
                details={"field": "github_url", "value": value}
            )
        
        valid_hosts = ['github.com', 'api.github.com']
        if parsed.netloc not in valid_hosts:
            raise ValidationError(
                f"GitHub URL must be from GitHub ({', '.join(valid_hosts)})",
                details={"field": "github_url", "value": value}
            )
        
        # For github.com URLs, ensure there's a repository path
        if parsed.netloc == 'github.com' and not parsed.path.strip('/'):
            raise ValidationError(
                "GitHub URL must include a repository path",
                details={"field": "github_url", "value": value}
            )
        
        return value


class APIKeyValidator(BaseValidator):
    """Validator for API keys."""
    
    MIN_LENGTH = 20
    
    def validate(self, value: str) -> str:
        """Validate API key.
        
        Args:
            value: API key string
            
        Returns:
            Validated API key
            
        Raises:
            ValidationError: If API key is invalid
        """
        if not isinstance(value, str):
            raise ValidationError(
                "API key must be a string",
                details={"field": "api_key", "value": "[REDACTED]"}
            )
        
        if not value or value.isspace():
            raise ValidationError(
                "API key cannot be empty",
                details={"field": "api_key", "value": "[REDACTED]"}
            )
        
        if len(value) < self.MIN_LENGTH:
            raise ValidationError(
                f"API key must be at least {self.MIN_LENGTH} characters long",
                details={"field": "api_key", "value": "[REDACTED]"}
            )
        
        if ' ' in value:
            raise ValidationError(
                "API key cannot contain spaces",
                details={"field": "api_key", "value": "[REDACTED]"}
            )
        
        return value


class PaginationValidator(BaseValidator):
    """Validator for pagination parameters."""
    
    def __init__(self, default_page: int = 1, default_size: int = 20):
        """Initialize with default values.
        
        Args:
            default_page: Default page number
            default_size: Default page size
        """
        self.default_page = default_page
        self.default_size = default_size
    
    def validate(self, value: Dict[str, Any]) -> Dict[str, int]:
        """Validate pagination parameters.
        
        Args:
            value: Dictionary with 'page' and 'size' keys
            
        Returns:
            Validated pagination parameters
            
        Raises:
            ValidationError: If pagination parameters are invalid
        """
        if not isinstance(value, dict):
            raise ValidationError(
                "Pagination parameters must be a dictionary",
                details={"field": "pagination", "value": value}
            )
        
        if 'page' not in value or 'size' not in value:
            raise ValidationError(
                "Pagination parameters must include 'page' and 'size'",
                details={"field": "pagination", "value": value}
            )
        
        try:
            page = int(value['page'])
            size = int(value['size'])
        except (ValueError, TypeError) as e:
            raise ValidationError(
                "Pagination page and size must be integers",
                details={"field": "pagination", "value": value, "error": str(e)}
            )
        
        if page < 1:
            raise ValidationError(
                "Pagination page number must be positive",
                details={"field": "pagination", "page": page}
            )
        
        if size < 1 or size > 100:
            raise ValidationError(
                "Pagination page size must be between 1 and 100",
                details={"field": "pagination", "size": size}
            )
        
        return {"page": page, "size": size}
    
    def validate_with_defaults(self, value: Dict[str, Any]) -> Dict[str, int]:
        """Validate pagination with default values for missing keys.
        
        Args:
            value: Dictionary with optional 'page' and 'size' keys
            
        Returns:
            Validated pagination parameters with defaults applied
        """
        # Apply defaults for missing keys
        complete_value = {
            "page": value.get("page", self.default_page),
            "size": value.get("size", self.default_size)
        }
        
        return self.validate(complete_value)


class FilePathValidator(BaseValidator):
    """Validator for file paths."""
    
    def validate(self, value: str) -> str:
        """Validate file path.
        
        Args:
            value: File path string
            
        Returns:
            Validated file path
            
        Raises:
            ValidationError: If file path is invalid
        """
        if not isinstance(value, str) or not value:
            raise ValidationError(
                "File path must be a non-empty string",
                details={"field": "file_path", "value": value}
            )
        
        # Check for absolute paths
        if value.startswith('/') or (len(value) > 1 and value[1] == ':'):
            raise ValidationError(
                "File path must be relative, not absolute",
                details={"field": "file_path", "value": value}
            )
        
        # Check for parent directory references
        if '..' in value:
            raise ValidationError(
                "File path cannot contain parent directory references (..)",
                details={"field": "file_path", "value": value}
            )
        
        # Check for home directory references and absolute paths with special chars
        if value.startswith('~') or value.startswith('/'):
            raise ValidationError(
                "File path cannot start with home directory (~) or root (/)",
                details={"field": "file_path", "value": value}
            )
        
        # Check for current directory references
        if value.startswith('./'):
            raise ValidationError(
                "File path cannot start with current directory reference (./)",
                details={"field": "file_path", "value": value}
            )
        
        # Check for double slashes
        if '//' in value:
            raise ValidationError(
                "File path cannot contain double slashes",
                details={"field": "file_path", "value": value}
            )
        
        # Check for backslashes (Windows paths)
        if '\\' in value:
            raise ValidationError(
                "File path must use forward slashes, not backslashes",
                details={"field": "file_path", "value": value}
            )
        
        return value


# Convenience functions for direct validation
def validate_pr_number(value: Union[int, str]) -> int:
    """Validate pull request number.
    
    Args:
        value: PR number to validate
        
    Returns:
        Validated PR number as integer
        
    Raises:
        ValidationError: If validation fails
    """
    return PRNumberValidator().validate(value)


def validate_repository_identifier(value: str) -> str:
    """Validate repository identifier.
    
    Args:
        value: Repository identifier to validate
        
    Returns:
        Validated repository identifier
        
    Raises:
        ValidationError: If validation fails
    """
    return RepositoryValidator().validate(value)


def validate_github_url(value: str) -> str:
    """Validate GitHub URL.
    
    Args:
        value: GitHub URL to validate
        
    Returns:
        Validated GitHub URL
        
    Raises:
        ValidationError: If validation fails
    """
    return GitHubURLValidator().validate(value)


def validate_api_key(value: str) -> str:
    """Validate API key.
    
    Args:
        value: API key to validate
        
    Returns:
        Validated API key
        
    Raises:
        ValidationError: If validation fails
    """
    return APIKeyValidator().validate(value)


def validate_pagination_params(value: Dict[str, Any]) -> Dict[str, int]:
    """Validate pagination parameters.
    
    Args:
        value: Pagination parameters to validate
        
    Returns:
        Validated pagination parameters
        
    Raises:
        ValidationError: If validation fails
    """
    return PaginationValidator().validate(value)


def validate_file_path(value: str) -> str:
    """Validate file path.
    
    Args:
        value: File path to validate
        
    Returns:
        Validated file path
        
    Raises:
        ValidationError: If validation fails
    """
    return FilePathValidator().validate(value)


# Export all validators and functions
__all__ = [
    "BaseValidator",
    "PRNumberValidator",
    "RepositoryValidator", 
    "GitHubURLValidator",
    "APIKeyValidator",
    "PaginationValidator",
    "FilePathValidator",
    "validate_pr_number",
    "validate_repository_identifier",
    "validate_github_url",
    "validate_api_key",
    "validate_pagination_params",
    "validate_file_path",
]