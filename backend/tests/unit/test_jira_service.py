"""
Unit tests for Jira service.

This module tests the Jira service functionality including
ticket data retrieval, ticket ID validation, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from src.services.jira import JiraService, JiraValidationError


class TestJiraService:
    """Unit tests for JiraService class."""
    
    @pytest.fixture
    def jira_service(self):
        """Create a JiraService instance for testing."""
        return JiraService()
        
    @pytest.fixture
    def mock_ticket_data(self) -> Dict[str, Any]:
        """Mock Jira ticket data for testing."""
        return {
            "key": "PROJ-456",
            "fields": {
                "summary": "Implement user authentication system",
                "description": "Add JWT-based authentication with role management",
                "status": {
                    "name": "In Progress"
                },
                "priority": {
                    "name": "High"
                },
                "issuetype": {
                    "name": "Story"
                },
                "assignee": {
                    "displayName": "John Developer",
                    "emailAddress": "john@company.com"
                },
                "reporter": {
                    "displayName": "Jane Manager",
                    "emailAddress": "jane@company.com"
                },
                "created": "2025-01-10T09:00:00.000+0000",
                "updated": "2025-01-15T14:30:00.000+0000",
                "project": {
                    "key": "PROJ",
                    "name": "Main Project"
                },
                "components": [
                    {"name": "Authentication"},
                    {"name": "Security"}
                ],
                "labels": ["security", "backend", "api"]
            }
        }
        
    def test_service_initialization(self, jira_service):
        """Test that JiraService initializes correctly."""
        assert isinstance(jira_service, JiraService)
        
    def test_valid_jira_ticket_validation(self, jira_service):
        """Test validation of valid Jira ticket IDs."""
        valid_tickets = [
            "PROJ-123",
            "DEV-456",
            "FEATURE-789",
            "BUG-1",
            "SUPPORT-999999",
            "A-1",
            "LONGPROJECTNAME-123"
        ]
        
        for ticket in valid_tickets:
            # Should not raise exception for valid ticket IDs
            jira_service._validate_ticket_id(ticket)
            
    def test_invalid_jira_ticket_validation(self, jira_service):
        """Test validation of invalid Jira ticket IDs."""
        invalid_tickets = [
            "invalid-format",  # Lowercase prefix
            "123-PROJ",  # Number-prefix format
            "PROJ_123",  # Underscore separator
            "PROJ-",  # Missing number
            "-123",  # Missing prefix
            "PROJ",  # Missing separator and number
            "PROJ-ABC",  # Non-numeric suffix
            "",  # Empty string
            None,  # None value
            "proj-123",  # Lowercase
            "PROJ 123",  # Space separator
            "PROJ.123"  # Dot separator
        ]
        
        for ticket in invalid_tickets:
            with pytest.raises(JiraValidationError):
                jira_service._validate_ticket_id(ticket)
                
    def test_extract_ticket_key(self, jira_service):
        """Test extraction of ticket key from ID."""
        ticket_id = "PROJ-456"
        key = jira_service._extract_ticket_key(ticket_id)
        
        assert key == "PROJ-456"
        
    def test_extract_project_and_number(self, jira_service):
        """Test extraction of project code and number from ticket ID."""
        ticket_id = "PROJ-456"
        project, number = jira_service._extract_project_info(ticket_id)
        
        assert project == "PROJ"
        assert number == 456
        
    @patch('src.services.jira.JIRA')
    async def test_get_ticket_details_success(self, mock_jira_class, jira_service, mock_ticket_data):
        """Test successful ticket data retrieval."""
        # Mock the Jira API client
        mock_jira = Mock()
        mock_issue = Mock()
        
        # Configure mock chain
        mock_jira_class.return_value = mock_jira
        mock_jira.issue.return_value = mock_issue
        
        # Configure issue mock with data
        mock_issue.key = mock_ticket_data["key"]
        mock_issue.fields = Mock()
        
        for field_key, field_value in mock_ticket_data["fields"].items():
            setattr(mock_issue.fields, field_key, field_value)
            
        # Test the method
        ticket_id = "PROJ-456"
        result = await jira_service.get_ticket_details(ticket_id)
        
        # Verify API calls
        mock_jira.issue.assert_called_once_with("PROJ-456")
        
        # Verify result structure
        assert isinstance(result, dict)
        assert result["key"] == "PROJ-456"
        assert result["summary"] == "Implement user authentication system"
        assert result["status"] == "In Progress"
        
    async def test_get_ticket_details_invalid_id(self, jira_service):
        """Test ticket data retrieval with invalid ticket ID."""
        invalid_id = "invalid-format"
        
        with pytest.raises(JiraValidationError) as exc_info:
            await jira_service.get_ticket_details(invalid_id)
            
        assert "Invalid Jira ticket ID format" in str(exc_info.value)
        
    @patch('src.services.jira.JIRA')
    async def test_get_ticket_details_api_error(self, mock_jira_class, jira_service):
        """Test ticket data retrieval with Jira API error."""
        # Mock Jira API to raise exception
        mock_jira = Mock()
        mock_jira_class.return_value = mock_jira
        mock_jira.issue.side_effect = Exception("Jira API Error")
        
        ticket_id = "PROJ-456"
        
        with pytest.raises(Exception) as exc_info:
            await jira_service.get_ticket_details(ticket_id)
            
        assert "Jira API Error" in str(exc_info.value)
        
    @patch('src.services.jira.JIRA')
    async def test_get_ticket_details_ticket_not_found(self, mock_jira_class, jira_service):
        """Test ticket data retrieval with ticket not found."""
        from jira.exceptions import JIRAError
        
        # Mock Jira API to raise JIRAError
        mock_jira = Mock()
        mock_jira_class.return_value = mock_jira
        mock_jira.issue.side_effect = JIRAError("Issue Does Not Exist", status_code=404)
        
        ticket_id = "PROJ-999999"
        
        with pytest.raises(Exception):
            await jira_service.get_ticket_details(ticket_id)
            
    def test_format_ticket_data(self, jira_service, mock_ticket_data):
        """Test formatting of raw ticket data."""
        # Create mock issue object
        mock_issue = Mock()
        mock_issue.key = mock_ticket_data["key"]
        mock_issue.fields = Mock()
        
        for field_key, field_value in mock_ticket_data["fields"].items():
            setattr(mock_issue.fields, field_key, field_value)
            
        # Test formatting
        result = jira_service._format_ticket_data(mock_issue)
        
        assert isinstance(result, dict)
        assert result["key"] == "PROJ-456"
        assert result["summary"] == "Implement user authentication system"
        assert result["status"] == "In Progress"
        assert result["priority"] == "High"
        assert result["issue_type"] == "Story"
        
    def test_ticket_data_includes_all_required_fields(self, jira_service, mock_ticket_data):
        """Test that formatted ticket data includes all required fields."""
        mock_issue = Mock()
        mock_issue.key = mock_ticket_data["key"]
        mock_issue.fields = Mock()
        
        for field_key, field_value in mock_ticket_data["fields"].items():
            setattr(mock_issue.fields, field_key, field_value)
            
        result = jira_service._format_ticket_data(mock_issue)
        
        required_fields = [
            "key", "summary", "description", "status", 
            "priority", "issue_type", "assignee", "reporter"
        ]
        
        for field in required_fields:
            assert field in result, f"Required field '{field}' missing"
            
    def test_handle_missing_optional_fields(self, jira_service):
        """Test handling of missing optional fields."""
        # Create mock with minimal required fields
        mock_issue = Mock()
        mock_issue.key = "PROJ-456"
        mock_issue.fields = Mock()
        
        # Set required fields
        mock_issue.fields.summary = "Test summary"
        mock_issue.fields.description = "Test description"
        mock_issue.fields.status = Mock(name="Open")
        mock_issue.fields.priority = Mock(name="Medium")
        mock_issue.fields.issuetype = Mock(name="Task")
        
        # Leave optional fields as None
        mock_issue.fields.assignee = None
        mock_issue.fields.reporter = None
        mock_issue.fields.components = None
        mock_issue.fields.labels = None
        
        result = jira_service._format_ticket_data(mock_issue)
        
        assert result["assignee"] is None
        assert result["reporter"] is None
        assert result["components"] == []
        assert result["labels"] == []
        
    @patch('src.services.jira.JIRA')
    async def test_get_ticket_data_alias_method(self, mock_jira_class, jira_service, mock_ticket_data):
        """Test the get_ticket_data alias method."""
        # Mock the Jira API client
        mock_jira = Mock()
        mock_issue = Mock()
        
        mock_jira_class.return_value = mock_jira
        mock_jira.issue.return_value = mock_issue
        
        mock_issue.key = mock_ticket_data["key"]
        mock_issue.fields = Mock()
        
        for field_key, field_value in mock_ticket_data["fields"].items():
            setattr(mock_issue.fields, field_key, field_value)
            
        # Test the alias method
        ticket_id = "PROJ-456"
        result = await jira_service.get_ticket_data(ticket_id)
        
        # Should return same result as get_ticket_details
        assert isinstance(result, dict)
        assert result["key"] == "PROJ-456"
        
    def test_jira_validation_error_message(self):
        """Test JiraValidationError provides clear error messages."""
        error = JiraValidationError("Invalid ticket format")
        assert str(error) == "Invalid ticket format"
        
    def test_ticket_regex_pattern(self, jira_service):
        """Test the ticket ID regex pattern matching."""
        # This tests the internal regex pattern used for validation
        pattern = r"^[A-Z]+[A-Z0-9]*-\d+$"
        
        import re
        
        valid_tickets = [
            "PROJ-123",
            "DEV-456", 
            "FEATURE123-789"
        ]
        
        invalid_tickets = [
            "proj-123",  # Lowercase
            "PROJ_123",  # Underscore
            "123-PROJ"   # Number first
        ]
        
        for ticket in valid_tickets:
            assert re.match(pattern, ticket), f"Valid ticket {ticket} should match pattern"
            
        for ticket in invalid_tickets:
            assert not re.match(pattern, ticket), f"Invalid ticket {ticket} should not match pattern"
            
    def test_extract_components_list(self, jira_service):
        """Test extraction of components from Jira fields."""
        mock_components = [
            Mock(name="Authentication"),
            Mock(name="Security"),
            Mock(name="API")
        ]
        
        result = jira_service._extract_components(mock_components)
        
        assert isinstance(result, list)
        assert len(result) == 3
        assert "Authentication" in result
        assert "Security" in result
        assert "API" in result
        
    def test_extract_labels_list(self, jira_service):
        """Test extraction of labels from Jira fields."""
        mock_labels = ["security", "backend", "api", "high-priority"]
        
        result = jira_service._extract_labels(mock_labels)
        
        assert isinstance(result, list)
        assert len(result) == 4
        assert "security" in result
        assert "backend" in result
        
    def test_format_user_info(self, jira_service):
        """Test formatting of user information from Jira fields."""
        mock_user = Mock()
        mock_user.displayName = "John Doe"
        mock_user.emailAddress = "john@example.com"
        
        result = jira_service._format_user(mock_user)
        
        assert isinstance(result, dict)
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        
    def test_format_user_info_none(self, jira_service):
        """Test formatting of None user information."""
        result = jira_service._format_user(None)
        
        assert result is None