"""Database package for PR Summarizer.

This package provides database connectivity and session management.
"""

from .session import get_database_session

__all__ = ["get_database_session"]