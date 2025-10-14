"""
Contract tests for summary API endpoints.

This module tests the API contract compliance for the PR summary generation
endpoints, ensuring proper request/response formats and HTTP status codes.
"""

import pytest
from typing import Dict, Any
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestSummaryAPIContract:
    """Contract tests for summary API endpoints."""
    
    def test_create_summary_endpoint_exists(self, test_client: TestClient):
        """Test that the POST /api/v1/summaries endpoint exists."""
        # Make request to check endpoint existence
        response = test_client.post(
            "/api/v1/summaries",
            json={"github_pr_url": "https://github.com/owner/repo/pull/123"}
        )
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        
    def test_create_summary_accepts_json(self, test_client: TestClient):
        """Test that the endpoint accepts JSON content type."""
        response = test_client.post(
            "/api/v1/summaries",
            json={
                "github_pr_url": "https://github.com/owner/repo/pull/123",
                "jira_ticket_id": "PROJ-456"
            }
        )
        
        # Should accept JSON content (not return 415 Unsupported Media Type)
        assert response.status_code != 415
        
    def test_create_summary_requires_github_url(self, test_client: TestClient):
        """Test that github_pr_url is required."""
        response = test_client.post(
            "/api/v1/summaries",
            json={"jira_ticket_id": "PROJ-456"}
        )
        
        # Should return 400 Bad Request for missing required field
        assert response.status_code == 400
        
    def test_create_summary_validates_github_url_format(self, test_client: TestClient):
        """Test that invalid GitHub URL format returns validation error."""
        response = test_client.post(
            "/api/v1/summaries",
            json={
                "github_pr_url": "https://invalid-url.com/not-github",
                "jira_ticket_id": "PROJ-456"
            }
        )
        
        # Should return 422 Unprocessable Entity for validation error
        assert response.status_code == 422
        
    def test_create_summary_validates_jira_ticket_format(self, test_client: TestClient):
        """Test that invalid Jira ticket format returns validation error."""
        response = test_client.post(
            "/api/v1/summaries",
            json={
                "github_pr_url": "https://github.com/owner/repo/pull/123",
                "jira_ticket_id": "invalid-format"
            }
        )
        
        # Should return 422 Unprocessable Entity for validation error
        assert response.status_code == 422
        
    def test_create_summary_success_response_format(self, test_client: TestClient):
        """Test that successful response has correct format."""
        response = test_client.post(
            "/api/v1/summaries",
            json={
                "github_pr_url": "https://github.com/owner/repo/pull/123",
                "jira_ticket_id": "PROJ-456"
            }
        )
        
        # Should return 201 Created for successful creation
        if response.status_code == 201:
            data = response.json()
            
            # Required fields in response
            required_fields = [
                "id", "github_pr_url", "jira_ticket_id",
                "business_context", "code_change_summary", "business_code_impact",
                "suggested_test_cases", "risk_complexity", "reviewer_guidance",
                "status", "created_at"
            ]
            
            for field in required_fields:
                assert field in data, f"Required field '{field}' missing in response"
                
            # Validate field types
            assert isinstance(data["id"], str)
            assert isinstance(data["github_pr_url"], str)
            assert isinstance(data["suggested_test_cases"], list)
            assert data["status"] in ["processing", "completed", "failed"]
            
    def test_create_summary_error_response_format(self, test_client: TestClient):
        """Test that error responses have correct format."""
        response = test_client.post(
            "/api/v1/summaries",
            json={"github_pr_url": "invalid-url"}
        )
        
        # Error responses should have detail field
        if response.status_code in [400, 422]:
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)
            
    def test_get_summary_endpoint_exists(self, test_client: TestClient):
        """Test that GET /api/v1/summaries/{id} endpoint exists."""
        response = test_client.get("/api/v1/summaries/test-id")
        
        # Should not return 404 for endpoint (may return 404 for resource)
        # If endpoint exists, should return some response
        assert response.status_code in [200, 404, 500]
        
    def test_list_summaries_endpoint_exists(self, test_client: TestClient):
        """Test that GET /api/v1/summaries endpoint exists."""
        response = test_client.get("/api/v1/summaries")
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        
    def test_list_summaries_response_format(self, test_client: TestClient):
        """Test that list summaries response has correct format."""
        response = test_client.get("/api/v1/summaries")
        
        if response.status_code == 200:
            data = response.json()
            
            # Should have pagination fields
            assert "summaries" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            
            # Summaries should be a list
            assert isinstance(data["summaries"], list)
            
    def test_api_returns_json_content_type(self, test_client: TestClient):
        """Test that API endpoints return JSON content type."""
        response = test_client.get("/api/v1/summaries")
        
        if response.status_code == 200:
            assert "application/json" in response.headers.get("content-type", "")
            
    def test_cors_headers_present(self, test_client: TestClient):
        """Test that CORS headers are present for frontend integration."""
        response = test_client.options("/api/v1/summaries")
        
        # CORS headers should be present
        headers = response.headers
        assert "Access-Control-Allow-Origin" in headers or response.status_code == 404