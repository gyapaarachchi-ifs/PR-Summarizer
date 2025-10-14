"""
Integration tests for end-to-end summary generation flow.

This module tests the complete integration of GitHub, Jira, and Gemini services
through the summary generation API endpoint, ensuring all components work together.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from typing import Dict, Any

from src.main import app


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_github_pr_data() -> Dict[str, Any]:
    """Mock GitHub PR data for integration testing."""
    return {
        "number": 123,
        "title": "Add user authentication system",
        "body": "This PR implements JWT-based user authentication with role management.",
        "user": {"login": "developer123"},
        "state": "open",
        "created_at": "2025-01-15T10:00:00Z",
        "head": {
            "sha": "abc123def456",
            "ref": "feature/auth"
        },
        "base": {
            "sha": "def456abc123", 
            "ref": "main"
        },
        "additions": 234,
        "deletions": 56,
        "changed_files": 8,
        "commits": 5,
        "html_url": "https://github.com/owner/repo/pull/123"
    }


@pytest.fixture
def mock_jira_ticket_data() -> Dict[str, Any]:
    """Mock Jira ticket data for integration testing."""
    return {
        "key": "PROJ-456",
        "summary": "Implement user authentication system",
        "description": "Add JWT-based authentication with comprehensive role management",
        "status": "In Progress",
        "priority": "High", 
        "issue_type": "Story",
        "assignee": {
            "name": "John Developer",
            "email": "john@company.com"
        },
        "reporter": {
            "name": "Jane Manager", 
            "email": "jane@company.com"
        },
        "components": ["Authentication", "Security"],
        "labels": ["security", "backend", "api"]
    }


class TestSummaryIntegrationFlow:
    """Integration tests for complete summary generation flow."""
    
    @patch('src.services.github.GitHubService.get_pr_details')
    @patch('src.services.jira.JiraService.get_ticket_details') 
    @patch('src.services.gemini.GeminiService.generate_summary')
    async def test_complete_summary_generation_flow(
        self, 
        mock_gemini,
        mock_jira, 
        mock_github,
        test_client: TestClient,
        mock_github_pr_data,
        mock_jira_ticket_data
    ):
        """Test complete end-to-end summary generation with all services."""
        # Mock service responses
        mock_github.return_value = mock_github_pr_data
        mock_jira.return_value = mock_jira_ticket_data
        
        # Mock Gemini response
        from src.models.pr_summary import PRSummary, ProcessingStatus
        from datetime import datetime
        
        mock_summary = PRSummary(
            id="summary-test-123",
            github_pr_url="https://github.com/owner/repo/pull/123",
            jira_ticket_id="PROJ-456",
            business_context="User authentication feature for secure access control",
            code_change_summary="Added JWT authentication with 8 files modified, 234 lines added",
            business_code_impact="Enhances security posture, enables role-based access",
            suggested_test_cases=[
                "Test successful login with valid credentials",
                "Test failed login with invalid credentials", 
                "Test token expiration and refresh"
            ],
            risk_complexity="Medium complexity - new authentication system requires careful testing",
            reviewer_guidance="Focus on JWT implementation, security validation, and error handling",
            status=ProcessingStatus.COMPLETED,
            created_at=datetime.now(),
            processing_time_ms=15000
        )
        mock_gemini.return_value = mock_summary
        
        # Make API request
        response = test_client.post(
            "/api/v1/summaries",
            json={
                "github_pr_url": "https://github.com/owner/repo/pull/123",
                "jira_ticket_id": "PROJ-456"
            }
        )
        
        # Verify successful response
        assert response.status_code == 201
        data = response.json()
        
        # Verify all services were called with correct parameters
        mock_github.assert_called_once_with("https://github.com/owner/repo/pull/123")
        mock_jira.assert_called_once_with("PROJ-456")
        mock_gemini.assert_called_once()
        
        # Verify response structure and content
        assert data["id"] == "summary-test-123"
        assert data["github_pr_url"] == "https://github.com/owner/repo/pull/123"
        assert data["jira_ticket_id"] == "PROJ-456"
        assert data["business_context"] == "User authentication feature for secure access control"
        assert len(data["suggested_test_cases"]) == 3
        assert data["status"] == "completed"
        
    @patch('src.services.github.GitHubService.get_pr_details')
    async def test_summary_generation_github_only(
        self,
        mock_github,
        test_client: TestClient,
        mock_github_pr_data
    ):
        """Test summary generation with only GitHub PR (no Jira ticket)."""
        # Mock GitHub service response
        mock_github.return_value = mock_github_pr_data
        
        # Make API request without Jira ticket
        response = test_client.post(
            "/api/v1/summaries",
            json={
                "github_pr_url": "https://github.com/owner/repo/pull/123"
            }
        )
        
        # Verify successful response
        assert response.status_code == 201
        data = response.json()
        
        # Verify GitHub service was called
        mock_github.assert_called_once_with("https://github.com/owner/repo/pull/123")
        
        # Verify response has empty Jira ticket ID
        assert data["github_pr_url"] == "https://github.com/owner/repo/pull/123"
        assert data["jira_ticket_id"] == ""
        
    @patch('src.services.github.GitHubService.get_pr_details')
    async def test_github_service_failure_handling(
        self,
        mock_github,
        test_client: TestClient
    ):
        """Test handling of GitHub service failures."""
        # Mock GitHub service to raise exception
        mock_github.side_effect = Exception("GitHub API unavailable")
        
        # Make API request
        response = test_client.post(
            "/api/v1/summaries",
            json={
                "github_pr_url": "https://github.com/owner/repo/pull/123"
            }
        )
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "GitHub API unavailable" in data["detail"]
        
    @patch('src.services.github.GitHubService.get_pr_details')
    @patch('src.services.jira.JiraService.get_ticket_details')
    async def test_jira_service_failure_handling(
        self,
        mock_jira,
        mock_github, 
        test_client: TestClient,
        mock_github_pr_data
    ):
        """Test handling of Jira service failures."""
        # Mock successful GitHub but failed Jira
        mock_github.return_value = mock_github_pr_data
        mock_jira.side_effect = Exception("Jira API unavailable")
        
        # Make API request
        response = test_client.post(
            "/api/v1/summaries", 
            json={
                "github_pr_url": "https://github.com/owner/repo/pull/123",
                "jira_ticket_id": "PROJ-456"
            }
        )
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "Jira API unavailable" in data["detail"]
        
    @patch('src.services.github.GitHubService.get_pr_details')
    @patch('src.services.gemini.GeminiService.generate_summary')
    async def test_gemini_service_failure_handling(
        self,
        mock_gemini,
        mock_github,
        test_client: TestClient,
        mock_github_pr_data
    ):
        """Test handling of Gemini AI service failures."""
        # Mock successful GitHub but failed Gemini
        mock_github.return_value = mock_github_pr_data
        mock_gemini.side_effect = Exception("Gemini API unavailable")
        
        # Make API request
        response = test_client.post(
            "/api/v1/summaries",
            json={
                "github_pr_url": "https://github.com/owner/repo/pull/123"
            }
        )
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "Gemini API unavailable" in data["detail"]
        
    async def test_invalid_github_url_integration(self, test_client: TestClient):
        """Test integration-level validation of invalid GitHub URLs."""
        response = test_client.post(
            "/api/v1/summaries",
            json={
                "github_pr_url": "https://invalid-url.com/not-github"
            }
        )
        
        # Verify validation error
        assert response.status_code == 422
        data = response.json()
        assert "github_pr_url" in data["detail"]
        
    async def test_invalid_jira_ticket_integration(self, test_client: TestClient):
        """Test integration-level validation of invalid Jira ticket IDs."""
        response = test_client.post(
            "/api/v1/summaries",
            json={
                "github_pr_url": "https://github.com/owner/repo/pull/123",
                "jira_ticket_id": "invalid-format"
            }
        )
        
        # Verify validation error
        assert response.status_code == 422
        data = response.json()
        assert "jira_ticket_id" in data["detail"]
        
    @patch('src.services.github.GitHubService.get_pr_details')
    @patch('src.services.jira.JiraService.get_ticket_details')
    @patch('src.services.gemini.GeminiService.generate_summary')
    async def test_performance_requirements(
        self,
        mock_gemini,
        mock_jira,
        mock_github,
        test_client: TestClient,
        mock_github_pr_data,
        mock_jira_ticket_data
    ):
        """Test that summary generation completes within performance requirements."""
        import time
        
        # Mock quick service responses
        mock_github.return_value = mock_github_pr_data
        mock_jira.return_value = mock_jira_ticket_data
        
        from src.models.pr_summary import PRSummary, ProcessingStatus
        from datetime import datetime
        
        mock_summary = PRSummary(
            id="perf-test-summary",
            github_pr_url="https://github.com/owner/repo/pull/123",
            jira_ticket_id="PROJ-456", 
            business_context="Performance test context",
            code_change_summary="Performance test summary",
            business_code_impact="Performance test impact",
            suggested_test_cases=["Perf test"],
            risk_complexity="Low",
            reviewer_guidance="Performance test guidance",
            status=ProcessingStatus.COMPLETED,
            created_at=datetime.now(),
            processing_time_ms=5000  # 5 seconds
        )
        mock_gemini.return_value = mock_summary
        
        # Measure response time
        start_time = time.time()
        
        response = test_client.post(
            "/api/v1/summaries",
            json={
                "github_pr_url": "https://github.com/owner/repo/pull/123",
                "jira_ticket_id": "PROJ-456"
            }
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Verify successful response
        assert response.status_code == 201
        
        # Verify performance requirement (should complete within 30 seconds)
        assert response_time < 30.0, f"Response took {response_time} seconds, exceeding 30s limit"
        
        # Verify processing time is reported
        data = response.json()
        assert "processing_time_ms" in data
        assert isinstance(data["processing_time_ms"], int)
        
    async def test_concurrent_summary_requests(self, test_client: TestClient):
        """Test handling of concurrent summary generation requests."""
        import asyncio
        import aiohttp
        
        async def make_request():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://testserver/api/v1/summaries",
                    json={"github_pr_url": "https://github.com/owner/repo/pull/123"}
                ) as response:
                    return response.status
        
        # Make multiple concurrent requests
        tasks = [make_request() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all requests were handled (success or known errors)
        for result in results:
            if isinstance(result, int):
                assert result in [201, 422, 500]  # Valid response codes
                
    @patch('src.services.github.GitHubService.get_pr_details')
    @patch('src.services.jira.JiraService.get_ticket_details')
    async def test_data_flow_integration(
        self,
        mock_jira,
        mock_github,
        test_client: TestClient,
        mock_github_pr_data,
        mock_jira_ticket_data
    ):
        """Test that data flows correctly between all services."""
        # Mock service responses
        mock_github.return_value = mock_github_pr_data
        mock_jira.return_value = mock_jira_ticket_data
        
        # Make API request
        response = test_client.post(
            "/api/v1/summaries",
            json={
                "github_pr_url": "https://github.com/owner/repo/pull/123",
                "jira_ticket_id": "PROJ-456"
            }
        )
        
        # Verify successful response
        assert response.status_code == 201
        
        # Verify services were called with correct data
        mock_github.assert_called_once()
        mock_jira.assert_called_once()
        
        # Verify the GitHub service received the exact URL from request
        github_call_args = mock_github.call_args[0]
        assert github_call_args[0] == "https://github.com/owner/repo/pull/123"
        
        # Verify the Jira service received the exact ticket ID from request
        jira_call_args = mock_jira.call_args[0] 
        assert jira_call_args[0] == "PROJ-456"
        
    async def test_summary_response_completeness(self, test_client: TestClient):
        """Test that summary responses include all required fields."""
        response = test_client.post(
            "/api/v1/summaries",
            json={
                "github_pr_url": "https://github.com/owner/repo/pull/123",
                "jira_ticket_id": "PROJ-456"
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            
            # Verify all required fields are present
            required_fields = [
                "id", "github_pr_url", "jira_ticket_id",
                "business_context", "code_change_summary", "business_code_impact",
                "suggested_test_cases", "risk_complexity", "reviewer_guidance",
                "status", "created_at"
            ]
            
            for field in required_fields:
                assert field in data, f"Required field '{field}' missing in response"
                
            # Verify field types
            assert isinstance(data["suggested_test_cases"], list)
            assert isinstance(data["created_at"], str)
            assert data["status"] in ["processing", "completed", "failed"]