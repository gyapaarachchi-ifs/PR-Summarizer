"""Test User Story 1: Basic PR Summary Generation.

Tests the core functionality of accepting GitHub PR URL and Jira ticket ID,
fetching data from both sources, and generating structured AI-powered summaries.

Acceptance Scenarios:
1. Given valid GitHub PR URL and Jira ticket ID, when generating summary,
   then system displays structured summary with all six sections populated
2. Given valid inputs, when AI processing completes, then summary appears 
   as readable text within 30 seconds
3. Given PR with code changes, when summary is generated, then Code Change
   Summary section accurately describes modified files
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.main import create_application
from src.models.pr_summary import (
    SummaryRequest, 
    PRSummary, 
    SummarySection,
    ProcessingStatus
)


class TestUS1BasicPRSummaryGeneration:
    """Test User Story 1: Basic PR Summary Generation."""
    
    @pytest.fixture
    def test_client(self):
        """Create test client for API endpoints."""
        app = create_application()
        return TestClient(app)
    
    @pytest.fixture
    def valid_summary_request(self):
        """Valid PR summary request data."""
        return {
            "github_pr_url": "https://github.com/owner/repo/pull/123",
            "jira_ticket_id": "PROJ-456"
        }
    
    @pytest.fixture
    def mock_github_pr_data(self):
        """Mock GitHub PR data."""
        return {
            "number": 123,
            "title": "Add user authentication feature",
            "body": "Implements JWT-based authentication with role-based access control",
            "state": "open",
            "commits": 5,
            "additions": 234,
            "deletions": 12,
            "changed_files": 8,
            "files": [
                {
                    "filename": "src/auth/jwt.py",
                    "status": "added",
                    "additions": 89,
                    "deletions": 0,
                    "patch": "@@ -0,0 +1,89 @@\n+class JWTManager:\n+    def create_token..."
                },
                {
                    "filename": "src/models/user.py", 
                    "status": "modified",
                    "additions": 45,
                    "deletions": 12,
                    "patch": "@@ -15,7 +15,7 @@\n class User(BaseModel):\n+    role: UserRole"
                }
            ],
            "user": {"login": "developer"},
            "created_at": "2025-10-13T10:00:00Z",
            "updated_at": "2025-10-13T11:00:00Z"
        }
    
    @pytest.fixture 
    def mock_jira_ticket_data(self):
        """Mock Jira ticket data."""
        return {
            "key": "PROJ-456",
            "fields": {
                "summary": "Implement user authentication system",
                "description": "As a user, I want secure login functionality so that my data is protected",
                "issuetype": {"name": "Story"},
                "priority": {"name": "High"},
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "John Developer"},
                "created": "2025-10-10T09:00:00.000+0000",
                "updated": "2025-10-13T08:00:00.000+0000"
            }
        }
    
    @pytest.fixture
    def expected_summary_structure(self):
        """Expected structure of generated summary."""
        return {
            "business_context": str,
            "code_change_summary": str, 
            "business_code_impact": str,
            "suggested_test_cases": list,
            "risk_complexity": str,
            "reviewer_guidance": str
        }

    @pytest.mark.us1
    @pytest.mark.integration
    async def test_summary_generation_with_valid_inputs(
        self, 
        test_client, 
        valid_summary_request,
        mock_github_pr_data,
        mock_jira_ticket_data
    ):
        """
        US1 Acceptance Scenario 1:
        Given valid GitHub PR URL and Jira ticket ID,
        When generating summary,
        Then system displays structured summary with all six sections populated.
        """
        # Arrange: Mock external service calls
        with patch('src.services.github.GitHubService.get_pr_details', new_callable=AsyncMock) as mock_github, \
             patch('src.services.jira.JiraService.get_ticket_details', new_callable=AsyncMock) as mock_jira, \
             patch('src.services.gemini.GeminiService.generate_summary', new_callable=AsyncMock) as mock_gemini:
            
            mock_github.return_value = mock_github_pr_data
            mock_jira.return_value = mock_jira_ticket_data
            mock_gemini.return_value = PRSummary(
                id="summary-123",
                request_id="req-456", 
                github_pr_url=valid_summary_request["github_pr_url"],
                jira_ticket_id=valid_summary_request["jira_ticket_id"],
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
            
            # Act: Make API request to generate summary
            response = test_client.post("/api/v1/summaries", json=valid_summary_request)
            
            # Assert: Verify response structure and content
            assert response.status_code == 201
            summary_data = response.json()
            
            # Verify all six required sections are present and populated
            assert "business_context" in summary_data
            assert "code_change_summary" in summary_data  
            assert "business_code_impact" in summary_data
            assert "suggested_test_cases" in summary_data
            assert "risk_complexity" in summary_data
            assert "reviewer_guidance" in summary_data
            
            # Verify content is meaningful (not empty)
            assert len(summary_data["business_context"]) > 0
            assert len(summary_data["code_change_summary"]) > 0
            assert len(summary_data["suggested_test_cases"]) > 0
            
            # Verify external services were called correctly
            mock_github.assert_called_once_with("https://github.com/owner/repo/pull/123")
            mock_jira.assert_called_once_with("PROJ-456")
            mock_gemini.assert_called_once()

    @pytest.mark.us1
    @pytest.mark.performance
    async def test_summary_generation_completes_within_30_seconds(
        self,
        test_client,
        valid_summary_request,
        mock_github_pr_data,
        mock_jira_ticket_data
    ):
        """
        US1 Acceptance Scenario 2:
        Given valid inputs,
        When AI processing completes,
        Then summary appears as readable text within 30 seconds.
        """
        import time
        
        # Arrange: Mock services with realistic timing
        with patch('src.services.github.GitHubService.get_pr_details', new_callable=AsyncMock) as mock_github, \
             patch('src.services.jira.JiraService.get_ticket_details', new_callable=AsyncMock) as mock_jira, \
             patch('src.services.gemini.GeminiService.generate_summary', new_callable=AsyncMock) as mock_gemini:
            
            mock_github.return_value = mock_github_pr_data
            mock_jira.return_value = mock_jira_ticket_data
            mock_gemini.return_value = PRSummary(
                id="summary-123",
                request_id="req-456",
                github_pr_url=valid_summary_request["github_pr_url"],
                jira_ticket_id=valid_summary_request["jira_ticket_id"], 
                business_context="Authentication feature",
                code_change_summary="JWT implementation added",
                business_code_impact="Security enhancement",
                suggested_test_cases=["Login test", "Security test"],
                risk_complexity="Medium risk",
                reviewer_guidance="Review security patterns",
                status=ProcessingStatus.COMPLETED,
                created_at=datetime.now(),
                processing_time_ms=25000  # 25 seconds - within limit
            )
            
            # Act: Measure processing time
            start_time = time.time()
            response = test_client.post("/api/v1/summaries", json=valid_summary_request)
            end_time = time.time()
            
            # Assert: Verify timing and response
            assert response.status_code == 201
            processing_time = end_time - start_time
            assert processing_time < 30.0, f"Processing took {processing_time:.2f} seconds, expected < 30"
            
            # Verify processing time is reported correctly
            summary_data = response.json()
            assert "processing_time_ms" in summary_data
            assert summary_data["processing_time_ms"] <= 30000

    @pytest.mark.us1
    @pytest.mark.unit
    async def test_code_change_summary_accurately_describes_files(
        self,
        test_client,
        valid_summary_request,
        mock_github_pr_data,
        mock_jira_ticket_data
    ):
        """
        US1 Acceptance Scenario 3:
        Given PR with associated code changes,
        When summary is generated,
        Then Code Change Summary section accurately describes modified files.
        """
        # Arrange: Mock services with specific file changes
        with patch('src.services.github.GitHubService.get_pr_details', new_callable=AsyncMock) as mock_github, \
             patch('src.services.jira.JiraService.get_ticket_details', new_callable=AsyncMock) as mock_jira, \
             patch('src.services.gemini.GeminiService.generate_summary', new_callable=AsyncMock) as mock_gemini:
            
            mock_github.return_value = mock_github_pr_data
            mock_jira.return_value = mock_jira_ticket_data
            
            # Configure Gemini to return summary that reflects the file changes
            def generate_summary_with_files(*args, **kwargs):
                # Simulate AI analyzing the file changes
                files_info = mock_github_pr_data["files"]
                code_summary = f"Modified {len(files_info)} files: "
                code_summary += ", ".join([f["filename"] for f in files_info])
                code_summary += f". Added {mock_github_pr_data['additions']} lines, deleted {mock_github_pr_data['deletions']} lines."
                
                return PRSummary(
                    id="summary-123",
                    request_id="req-456",
                    github_pr_url=valid_summary_request["github_pr_url"],
                    jira_ticket_id=valid_summary_request["jira_ticket_id"],
                    business_context="Authentication feature implementation",
                    code_change_summary=code_summary,
                    business_code_impact="Security improvements", 
                    suggested_test_cases=["Authentication tests"],
                    risk_complexity="Medium",
                    reviewer_guidance="Focus on security",
                    status=ProcessingStatus.COMPLETED,
                    created_at=datetime.now(),
                    processing_time_ms=20000
                )
            
            mock_gemini.side_effect = generate_summary_with_files
            
            # Act: Generate summary
            response = test_client.post("/api/v1/summaries", json=valid_summary_request)
            
            # Assert: Verify code change summary accuracy
            assert response.status_code == 201
            summary_data = response.json()
            
            code_summary = summary_data["code_change_summary"]
            
            # Verify file names are mentioned
            assert "src/auth/jwt.py" in code_summary
            assert "src/models/user.py" in code_summary
            
            # Verify statistics are included  
            assert "234" in code_summary  # additions
            assert "12" in code_summary   # deletions
            assert "2" in code_summary or "files" in code_summary.lower()

    @pytest.mark.us1
    @pytest.mark.error_handling
    async def test_invalid_github_url_returns_validation_error(self, test_client):
        """Test validation of GitHub PR URL format."""
        # Arrange: Invalid GitHub URL
        invalid_request = {
            "github_pr_url": "https://invalid-url.com/not-github",
            "jira_ticket_id": "PROJ-456"
        }
        
        # Act: Attempt to create summary
        response = test_client.post("/api/v1/summaries", json=invalid_request)
        
        # Assert: Validation error
        assert response.status_code == 422
        error_data = response.json()
        assert "github_pr_url" in str(error_data)

    @pytest.mark.us1
    @pytest.mark.error_handling  
    async def test_invalid_jira_ticket_id_returns_validation_error(self, test_client):
        """Test validation of Jira ticket ID format."""
        # Arrange: Invalid Jira ticket ID
        invalid_request = {
            "github_pr_url": "https://github.com/owner/repo/pull/123",
            "jira_ticket_id": "invalid-ticket-format"
        }
        
        # Act: Attempt to create summary
        response = test_client.post("/api/v1/summaries", json=invalid_request)
        
        # Assert: Validation error
        assert response.status_code == 422
        error_data = response.json()
        assert "jira_ticket_id" in str(error_data)

    @pytest.mark.us1
    @pytest.mark.error_handling
    async def test_github_service_unavailable_returns_error(
        self,
        test_client,
        valid_summary_request
    ):
        """Test handling of GitHub service being unavailable."""
        # Arrange: Mock GitHub service failure
        with patch('src.services.github.GitHubService.get_pr_details', new_callable=AsyncMock) as mock_github:
            mock_github.side_effect = Exception("GitHub API unavailable")
            
            # Act: Attempt to generate summary
            response = test_client.post("/api/v1/summaries", json=valid_summary_request)
            
            # Assert: Appropriate error response
            assert response.status_code in [500, 503]
            error_data = response.json()
            assert "error" in error_data or "detail" in error_data

    @pytest.mark.us1
    @pytest.mark.error_handling
    async def test_jira_service_unavailable_returns_error(
        self,
        test_client,
        valid_summary_request,
        mock_github_pr_data
    ):
        """Test handling of Jira service being unavailable."""
        # Arrange: Mock Jira service failure
        with patch('src.services.github.GitHubService.get_pr_details', new_callable=AsyncMock) as mock_github, \
             patch('src.services.jira.JiraService.get_ticket_details', new_callable=AsyncMock) as mock_jira:
            
            mock_github.return_value = mock_github_pr_data
            mock_jira.side_effect = Exception("Jira API unavailable")
            
            # Act: Attempt to generate summary
            response = test_client.post("/api/v1/summaries", json=valid_summary_request)
            
            # Assert: Appropriate error response
            assert response.status_code in [500, 503]
            error_data = response.json()
            assert "error" in error_data or "detail" in error_data