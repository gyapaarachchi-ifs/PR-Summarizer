"""Services package for PR Summarizer.

This package provides business logic services for the application.
"""

from .auth import get_auth_service

# Import the service modules to make them available for mocking
try:
    from . import github
    from . import jira  
    from . import gemini
except ImportError:
    # Services might have missing dependencies in test environment
    # This is OK since we'll be mocking them
    pass

__all__ = ["get_auth_service", "github", "jira", "gemini"]