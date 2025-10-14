"""Jira service for interacting with Jira API."""

from typing import Dict, Any
import re


class JiraServiceError(Exception):
    """Base exception for Jira service errors."""
    pass


class JiraValidationError(JiraServiceError):
    """Exception for Jira validation errors."""
    pass


class JiraService:
    """Service for Jira API operations."""
    
    def __init__(self, server_url: str = None, username: str = None, api_token: str = None):
        """Initialize Jira service."""
        self.server_url = server_url
        self.username = username
        self.api_token = api_token
        
    async def get_ticket_details(self, ticket_id: str) -> Dict[str, Any]:
        """Get ticket details from Jira API."""
        # Validate ticket ID format first
        if not self._is_valid_ticket_id(ticket_id):
            raise JiraValidationError(f"Invalid Jira ticket ID format: {ticket_id}")
        
        # Temporary stub for TDD - simulate successful response for valid ticket IDs
        return {
            "key": ticket_id,
            "fields": {
                "summary": "Mock Jira Ticket",
                "description": "Mock ticket description",
                "status": {"name": "In Progress"},
                "priority": {"name": "High"},
                "issuetype": {"name": "Story"},
                "assignee": {"displayName": "Test User"}
            }
        }
    
    def _is_valid_ticket_id(self, ticket_id: str) -> bool:
        """Validate Jira ticket ID format (e.g., PROJ-123)."""
        pattern = r'^[A-Z][A-Z0-9]+-\d+$'
        return bool(re.match(pattern, ticket_id))