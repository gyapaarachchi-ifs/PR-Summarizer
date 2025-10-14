"""Test utilities and helpers for PR Summarizer tests.

This module provides common testing utilities, data generators, and
assertion helpers to support TDD implementation across user stories.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock


class TestDataGenerator:
    """Generate realistic test data for various scenarios."""
    
    @staticmethod
    def github_pr_data(
        number: int = 123,
        title: str = "Add authentication system",
        additions: int = 100,
        deletions: int = 20,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate GitHub PR data for testing."""
        base_data = {
            "number": number,
            "title": title,
            "body": f"This PR implements {title.lower()}",
            "user": {"login": "developer"},
            "head": {"sha": f"abc{number}"},
            "base": {"ref": "main"},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "additions": additions,
            "deletions": deletions,
            "changed_files": max(1, (additions + deletions) // 50),
            "commits": max(1, (additions + deletions) // 100),
            "comments": 0,
            "review_comments": 0,
            "state": "open",
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def jira_issue_data(
        key: str = "PROJ-123",
        summary: str = "Implement authentication",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate Jira issue data for testing."""
        base_data = {
            "key": key,
            "fields": {
                "summary": summary,
                "description": f"Implement {summary.lower()} with security best practices",
                "status": {"name": "In Progress"},
                "priority": {"name": "High"},
                "assignee": {"displayName": "John Developer"},
                "reporter": {"displayName": "Jane Manager"},
                "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000+0000"),
                "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000+0000"),
                "issuetype": {"name": "Story"},
                "components": [{"name": "Backend"}, {"name": "Security"}],
                "labels": ["authentication", "security"],
                "customfield_10002": 8,  # Story points
            }
        }
        if kwargs:
            base_data["fields"].update(kwargs)
        return base_data
    
    @staticmethod
    def summary_request_data(
        pr_url: str = "https://github.com/owner/repo/pull/123",
        jira_ticket: str = "PROJ-123",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate summary request data for testing."""
        base_data = {
            "pr_url": pr_url,
            "jira_ticket": jira_ticket,
            "confluence_pages": [],
            "google_docs": [],
            "additional_context": ""
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def expected_summary_data(
        summary: str = "Test PR summary",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate expected summary response data."""
        base_data = {
            "summary": summary,
            "changes": ["Added authentication system", "Updated security middleware"],
            "impact": "Medium - affects user authentication flow",
            "testing_recommendations": [
                "Test token validation",
                "Verify role-based access control"
            ],
            "documentation_notes": "Update API documentation with auth requirements",
            "dependencies": ["PyJWT library", "Redis for session storage"],
            "metadata": {
                "pr_number": 123,
                "jira_key": "PROJ-123",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "confidence_score": 0.95
            }
        }
        base_data.update(kwargs)
        return base_data


class MockServiceBuilder:
    """Build configured mock services for testing."""
    
    @staticmethod
    def github_service(pr_data: Optional[Dict] = None) -> AsyncMock:
        """Create a mocked GitHub service."""
        mock = AsyncMock()
        mock.get_pull_request.return_value = pr_data or TestDataGenerator.github_pr_data()
        mock.get_pr_files.return_value = [
            {"filename": "src/auth.py", "status": "added", "additions": 50, "deletions": 0}
        ]
        mock.get_pr_commits.return_value = [
            {"sha": "abc123", "message": "Add authentication", "author": "developer"}
        ]
        return mock
    
    @staticmethod
    def jira_service(issue_data: Optional[Dict] = None) -> AsyncMock:
        """Create a mocked Jira service."""
        mock = AsyncMock()
        mock.get_issue.return_value = issue_data or TestDataGenerator.jira_issue_data()
        return mock
    
    @staticmethod
    def gemini_service(summary_data: Optional[Dict] = None) -> AsyncMock:
        """Create a mocked Gemini AI service."""
        mock = AsyncMock()
        mock.generate_summary.return_value = summary_data or TestDataGenerator.expected_summary_data()
        return mock


class TestAssertions:
    """Custom assertion helpers for PR Summarizer tests."""
    
    @staticmethod
    def assert_valid_summary_structure(response_data: Dict[str, Any]):
        """Assert that response has valid summary structure."""
        required_fields = {
            "summary", "changes", "impact", "testing_recommendations",
            "documentation_notes", "dependencies", "metadata"
        }
        
        assert isinstance(response_data, dict), "Response must be a dictionary"
        
        # Check required fields exist
        missing_fields = required_fields - set(response_data.keys())
        assert not missing_fields, f"Missing required fields: {missing_fields}"
        
        # Validate field types
        assert isinstance(response_data["summary"], str), "Summary must be string"
        assert isinstance(response_data["changes"], list), "Changes must be list"
        assert isinstance(response_data["impact"], str), "Impact must be string"
        assert isinstance(response_data["testing_recommendations"], list), "Testing recommendations must be list"
        assert isinstance(response_data["documentation_notes"], str), "Documentation notes must be string"
        assert isinstance(response_data["dependencies"], list), "Dependencies must be list"
        assert isinstance(response_data["metadata"], dict), "Metadata must be dict"
        
        # Validate metadata structure
        metadata = response_data["metadata"]
        assert "generated_at" in metadata, "Metadata must include generated_at"
        assert "confidence_score" in metadata, "Metadata must include confidence_score"
        
        # Validate confidence score range
        confidence = metadata["confidence_score"]
        assert isinstance(confidence, (int, float)), "Confidence score must be numeric"
        assert 0 <= confidence <= 1, "Confidence score must be between 0 and 1"
    
    @staticmethod
    def assert_http_success(response, expected_status: int = 200):
        """Assert HTTP response indicates success."""
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        if response.headers.get("content-type", "").startswith("application/json"):
            # Should be valid JSON
            try:
                response.json()
            except json.JSONDecodeError:
                assert False, "Response should be valid JSON"
    
    @staticmethod
    def assert_http_error(response, expected_status: int):
        """Assert HTTP response indicates expected error."""
        assert response.status_code == expected_status, (
            f"Expected error status {expected_status}, got {response.status_code}"
        )
        
        # Should have error details
        if response.headers.get("content-type", "").startswith("application/json"):
            error_data = response.json()
            assert "detail" in error_data or "message" in error_data, (
                "Error response should include detail or message"
            )


class FileTestHelper:
    """Helper for file-based testing operations."""
    
    @staticmethod
    def create_temp_config(config_data: Dict[str, Any]) -> str:
        """Create temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            return f.name
    
    @staticmethod
    def create_test_file(content: str, suffix: str = '.txt') -> str:
        """Create temporary test file with content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            return f.name


# Test markers and categories
TEST_CATEGORIES = {
    "unit": "Fast, isolated component tests",
    "integration": "Multi-component interaction tests", 
    "contract": "API interface validation tests",
    "e2e": "Complete user workflow tests",
    "performance": "Speed and scalability tests"
}

USER_STORIES = {
    "us1": "Basic PR Summary Generation",
    "us2": "Multi-Source Context Integration", 
    "us3": "Advanced Review Guidance"
}

SERVICE_TYPES = {
    "github": "GitHub API integration",
    "jira": "Jira API integration",
    "gemini": "Gemini AI service",
    "confluence": "Confluence API integration",
    "gdocs": "Google Docs API integration"
}


def print_test_info():
    """Print information about available test categories and markers."""
    print("\n📋 PR Summarizer Test Framework")
    print("=" * 50)
    
    print("\n🏷️  Test Categories:")
    for category, description in TEST_CATEGORIES.items():
        print(f"  • {category}: {description}")
    
    print("\n📖 User Stories:")
    for story, description in USER_STORIES.items():
        print(f"  • {story}: {description}")
    
    print("\n🔧 Service Types:")
    for service, description in SERVICE_TYPES.items():
        print(f"  • {service}: {description}")
    
    print("\n🚀 Example Commands:")
    print("  pytest -m unit                    # Run unit tests")
    print("  pytest -m 'integration and us1'   # Integration tests for US1")
    print("  pytest -m github                  # Tests requiring GitHub service")
    print("  pytest -v --tb=short             # Verbose with short traceback")
    print("  pytest --cov=src --cov-report=html # Coverage report")


if __name__ == "__main__":
    print_test_info()