"""
Unit tests for Gemini service.

This module tests the Gemini AI service functionality including
summary generation, prompt handling, and error management.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any
from datetime import datetime

from src.services.gemini import GeminiService
from src.models.pr_summary import PRSummary, ProcessingStatus


class TestGeminiService:
    """Unit tests for GeminiService class."""
    
    @pytest.fixture
    def gemini_service(self):
        """Create a GeminiService instance for testing."""
        return GeminiService()
        
    @pytest.fixture
    def mock_pr_data(self) -> Dict[str, Any]:
        """Mock PR data for testing."""
        return {
            "number": 123,
            "title": "Add user authentication",
            "body": "This PR adds JWT-based user authentication to the application.",
            "state": "open",
            "additions": 234,
            "deletions": 56,
            "changed_files": 8,
            "commits": 5,
            "html_url": "https://github.com/owner/repo/pull/123"
        }
        
    @pytest.fixture
    def mock_jira_data(self) -> Dict[str, Any]:
        """Mock Jira ticket data for testing."""
        return {
            "key": "PROJ-456",
            "summary": "Implement user authentication system",
            "description": "Add JWT-based authentication with role management",
            "status": "In Progress",
            "priority": "High",
            "issue_type": "Story"
        }
        
    def test_service_initialization_with_defaults(self, gemini_service):
        """Test that GeminiService initializes with default values."""
        assert isinstance(gemini_service, GeminiService)
        assert gemini_service.model_name == "gemini-pro"
        
    def test_service_initialization_with_custom_params(self):
        """Test service initialization with custom parameters."""
        service = GeminiService(api_key="test-key", model_name="gemini-1.5-pro")
        assert service.api_key == "test-key"
        assert service.model_name == "gemini-1.5-pro"
        
    async def test_generate_summary_returns_pr_summary(self, gemini_service, mock_pr_data, mock_jira_data):
        """Test that generate_summary returns a PRSummary object."""
        result = await gemini_service.generate_summary(
            pr_data=mock_pr_data,
            jira_data=mock_jira_data
        )
        
        assert isinstance(result, PRSummary)
        assert result.github_pr_url == "https://github.com/owner/repo/pull/123"
        assert result.jira_ticket_id == "PROJ-456"
        assert result.status == ProcessingStatus.COMPLETED
        
    async def test_generate_summary_with_pr_data_only(self, gemini_service, mock_pr_data):
        """Test summary generation with only PR data (no Jira)."""
        result = await gemini_service.generate_summary(
            pr_data=mock_pr_data,
            jira_data=None
        )
        
        assert isinstance(result, PRSummary)
        assert result.github_pr_url == "https://github.com/owner/repo/pull/123"
        assert result.jira_ticket_id is None
        assert result.status == ProcessingStatus.COMPLETED
        
    async def test_generate_summary_includes_all_sections(self, gemini_service, mock_pr_data, mock_jira_data):
        """Test that generated summary includes all required sections."""
        result = await gemini_service.generate_summary(
            pr_data=mock_pr_data,
            jira_data=mock_jira_data
        )
        
        # Verify all 6 required sections are present and not empty
        assert result.business_context
        assert result.code_change_summary
        assert result.business_code_impact
        assert result.suggested_test_cases
        assert result.risk_complexity
        assert result.reviewer_guidance
        
        # Verify sections have meaningful content (not just placeholders)
        assert len(result.business_context) > 10
        assert len(result.code_change_summary) > 10
        assert len(result.business_code_impact) > 10
        assert isinstance(result.suggested_test_cases, list)
        assert len(result.suggested_test_cases) > 0
        
    async def test_generate_summary_with_confluence_data(self, gemini_service, mock_pr_data):
        """Test summary generation with Confluence data."""
        mock_confluence_data = {
            "pages": [
                {
                    "title": "Authentication Architecture",
                    "content": "JWT implementation guidelines and security considerations"
                }
            ]
        }
        
        result = await gemini_service.generate_summary(
            pr_data=mock_pr_data,
            jira_data=None,
            confluence_data=mock_confluence_data
        )
        
        assert isinstance(result, PRSummary)
        # Business context should incorporate Confluence information
        assert "authentication" in result.business_context.lower()
        
    async def test_generate_summary_with_options(self, gemini_service, mock_pr_data):
        """Test summary generation with custom options."""
        options = {
            "focus_areas": ["security", "performance"],
            "detail_level": "high",
            "include_code_examples": True
        }
        
        result = await gemini_service.generate_summary(
            pr_data=mock_pr_data,
            options=options
        )
        
        assert isinstance(result, PRSummary)
        # Should incorporate focus areas in the analysis
        assert any(area in result.reviewer_guidance.lower() 
                  for area in ["security", "performance"])
        
    def test_build_prompt_with_pr_data(self, gemini_service, mock_pr_data):
        """Test prompt building with PR data."""
        prompt = gemini_service._build_prompt(
            pr_data=mock_pr_data,
            jira_data=None
        )
        
        assert isinstance(prompt, str)
        assert "Add user authentication" in prompt  # PR title
        assert "234" in prompt  # Additions count
        assert "JWT-based" in prompt  # PR description
        
    def test_build_prompt_with_jira_data(self, gemini_service, mock_pr_data, mock_jira_data):
        """Test prompt building with both PR and Jira data."""
        prompt = gemini_service._build_prompt(
            pr_data=mock_pr_data,
            jira_data=mock_jira_data
        )
        
        assert isinstance(prompt, str)
        assert "PROJ-456" in prompt  # Jira ticket key
        assert "authentication system" in prompt  # Jira summary
        assert "High" in prompt  # Jira priority
        
    def test_build_prompt_includes_required_sections(self, gemini_service, mock_pr_data):
        """Test that prompt includes instructions for all required sections."""
        prompt = gemini_service._build_prompt(pr_data=mock_pr_data)
        
        required_sections = [
            "business_context",
            "code_change_summary", 
            "business_code_impact",
            "suggested_test_cases",
            "risk_complexity",
            "reviewer_guidance"
        ]
        
        for section in required_sections:
            assert section in prompt.lower()
            
    async def test_parse_ai_response_valid_json(self, gemini_service):
        """Test parsing of valid AI response JSON."""
        mock_response = """{
            "business_context": "User authentication feature",
            "code_change_summary": "Added JWT authentication",
            "business_code_impact": "Enhanced security",
            "suggested_test_cases": ["Test login", "Test logout"],
            "risk_complexity": "Medium complexity",
            "reviewer_guidance": "Focus on security validation"
        }"""
        
        result = gemini_service._parse_ai_response(mock_response)
        
        assert isinstance(result, dict)
        assert result["business_context"] == "User authentication feature"
        assert isinstance(result["suggested_test_cases"], list)
        
    async def test_parse_ai_response_with_markdown(self, gemini_service):
        """Test parsing AI response that includes markdown formatting."""
        mock_response = """```json
        {
            "business_context": "User authentication feature",
            "code_change_summary": "Added JWT authentication",
            "business_code_impact": "Enhanced security",
            "suggested_test_cases": ["Test login", "Test logout"],
            "risk_complexity": "Medium complexity",
            "reviewer_guidance": "Focus on security validation"
        }
        ```"""
        
        result = gemini_service._parse_ai_response(mock_response)
        
        assert isinstance(result, dict)
        assert result["business_context"] == "User authentication feature"
        
    async def test_parse_ai_response_invalid_json(self, gemini_service):
        """Test handling of invalid AI response JSON."""
        mock_response = "This is not valid JSON"
        
        with pytest.raises(Exception):
            gemini_service._parse_ai_response(mock_response)
            
    def test_create_pr_summary_object(self, gemini_service, mock_pr_data):
        """Test creation of PRSummary object from parsed data."""
        parsed_data = {
            "business_context": "User authentication feature",
            "code_change_summary": "Added JWT authentication",
            "business_code_impact": "Enhanced security",
            "suggested_test_cases": ["Test login", "Test logout"],
            "risk_complexity": "Medium complexity",
            "reviewer_guidance": "Focus on security validation"
        }
        
        result = gemini_service._create_summary_object(
            parsed_data=parsed_data,
            pr_data=mock_pr_data,
            jira_data=None
        )
        
        assert isinstance(result, PRSummary)
        assert result.business_context == "User authentication feature"
        assert result.github_pr_url == "https://github.com/owner/repo/pull/123"
        assert result.jira_ticket_id is None
        
    def test_create_pr_summary_with_jira_data(self, gemini_service, mock_pr_data, mock_jira_data):
        """Test PRSummary creation with Jira data."""
        parsed_data = {
            "business_context": "User authentication feature",
            "code_change_summary": "Added JWT authentication", 
            "business_code_impact": "Enhanced security",
            "suggested_test_cases": ["Test login"],
            "risk_complexity": "Medium",
            "reviewer_guidance": "Focus on security"
        }
        
        result = gemini_service._create_summary_object(
            parsed_data=parsed_data,
            pr_data=mock_pr_data,
            jira_data=mock_jira_data
        )
        
        assert result.jira_ticket_id == "PROJ-456"
        
    def test_validate_parsed_data_complete(self, gemini_service):
        """Test validation of complete parsed data."""
        complete_data = {
            "business_context": "User authentication feature",
            "code_change_summary": "Added JWT authentication",
            "business_code_impact": "Enhanced security", 
            "suggested_test_cases": ["Test login", "Test logout"],
            "risk_complexity": "Medium complexity",
            "reviewer_guidance": "Focus on security validation"
        }
        
        # Should not raise exception for complete data
        gemini_service._validate_parsed_data(complete_data)
        
    def test_validate_parsed_data_missing_fields(self, gemini_service):
        """Test validation of incomplete parsed data."""
        incomplete_data = {
            "business_context": "User authentication feature",
            "code_change_summary": "Added JWT authentication"
            # Missing required fields
        }
        
        with pytest.raises(Exception):
            gemini_service._validate_parsed_data(incomplete_data)
            
    def test_generate_summary_id(self, gemini_service):
        """Test generation of unique summary IDs."""
        id1 = gemini_service._generate_summary_id()
        id2 = gemini_service._generate_summary_id()
        
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert id1 != id2  # IDs should be unique
        assert id1.startswith("summary-")
        
    @patch('src.services.gemini.genai.GenerativeModel')
    async def test_call_gemini_api_success(self, mock_model_class, gemini_service):
        """Test successful Gemini API call."""
        # Mock the Gemini API
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '{"business_context": "test"}'
        
        mock_model_class.return_value = mock_model
        mock_model.generate_content.return_value = mock_response
        
        prompt = "Generate a summary for this PR"
        result = await gemini_service._call_gemini_api(prompt)
        
        assert result == '{"business_context": "test"}'
        mock_model.generate_content.assert_called_once_with(prompt)
        
    @patch('src.services.gemini.genai.GenerativeModel')
    async def test_call_gemini_api_error(self, mock_model_class, gemini_service):
        """Test Gemini API error handling."""
        # Mock API to raise exception
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        mock_model.generate_content.side_effect = Exception("API Error")
        
        prompt = "Generate a summary"
        
        with pytest.raises(Exception) as exc_info:
            await gemini_service._call_gemini_api(prompt)
            
        assert "API Error" in str(exc_info.value)
        
    def test_format_test_cases(self, gemini_service):
        """Test formatting of test cases into list format."""
        # Test cases might come as string or list
        test_cases_string = "Test login functionality, Test logout, Verify token expiration"
        result = gemini_service._format_test_cases(test_cases_string)
        
        assert isinstance(result, list)
        assert len(result) >= 2
        
        # Test cases already as list
        test_cases_list = ["Test login", "Test logout", "Test tokens"]
        result = gemini_service._format_test_cases(test_cases_list)
        
        assert isinstance(result, list)
        assert len(result) == 3
        
    async def test_generate_summary_performance_tracking(self, gemini_service, mock_pr_data):
        """Test that performance timing is tracked."""
        result = await gemini_service.generate_summary(pr_data=mock_pr_data)
        
        assert isinstance(result.processing_time_ms, int)
        assert result.processing_time_ms >= 0
        
    async def test_generate_summary_error_handling(self, gemini_service):
        """Test error handling in summary generation."""
        # Invalid PR data should be handled gracefully
        invalid_pr_data = {"invalid": "data"}
        
        with pytest.raises(Exception):
            await gemini_service.generate_summary(pr_data=invalid_pr_data)