"""Configuration for pytest test framework.

Provides comprehensive test fixtures and utilities for TDD implementation
of user stories including authentication, external service mocking, and
test data management.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any, Optional

import pytest
from fastapi.testclient import TestClient


# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def test_app():
    """Create FastAPI application for testing."""
    from main import create_application
    return create_application()


@pytest.fixture
def client(test_app):
    """Create a test client for the FastAPI application."""
    return TestClient(test_app)


@pytest.fixture
def authenticated_client(client, admin_token):
    """Create an authenticated test client with admin token."""
    client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return client


@pytest.fixture
def admin_token(client):
    """Get an admin authentication token for testing."""
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    # Fallback for tests that don't need real authentication
    return "test-admin-token"


@pytest.fixture
def user_token(client):
    """Get a regular user authentication token for testing."""
    # Create a test user first
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    })
    
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    # Fallback for tests that don't need real authentication
    return "test-user-token"


@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture."""
    return {
        "testing": True,
        "github_token": "test-token",
        "gemini_api_key": "test-key",
        "redis_url": "redis://localhost:6379/1",  # Test DB
    }


@pytest.fixture
def mock_github_pr():
    """Mock GitHub PR data for testing."""
    return {
        "number": 123,
        "title": "Add new feature",
        "body": "This PR adds a new feature to the application.",
        "user": {"login": "developer"},
        "head": {"sha": "abc123"},
        "base": {"ref": "main"},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "additions": 50,
        "deletions": 10,
        "changed_files": 3,
        "commits": 2,
        "comments": 1,
        "review_comments": 2,
        "state": "open",
    }


@pytest.fixture
def mock_pr_files():
    """Mock PR file changes for testing."""
    return [
        {
            "filename": "src/models/user.py",
            "status": "added",
            "additions": 30,
            "deletions": 0,
            "patch": "@@ -0,0 +1,30 @@\n+class User:\n+    def __init__(self, name):\n+        self.name = name"
        },
        {
            "filename": "src/api/users.py",
            "status": "modified",
            "additions": 15,
            "deletions": 5,
            "patch": "@@ -10,5 +10,15 @@\n def get_user():\n-    return None\n+    return User('test')"
        },
        {
            "filename": "tests/test_users.py",
            "status": "added",
            "additions": 5,
            "deletions": 5,
            "patch": "@@ -0,0 +1,5 @@\n+def test_user_creation():\n+    user = User('test')\n+    assert user.name == 'test'"
        }
    ]


@pytest.fixture
def mock_jira_issue():
    """Mock Jira issue data for testing."""
    return {
        "key": "PROJ-123",
        "fields": {
            "summary": "Implement new user authentication",
            "description": "Add OAuth2 authentication system with role-based access control",
            "status": {"name": "In Progress"},
            "priority": {"name": "High"},
            "assignee": {"displayName": "John Developer"},
            "reporter": {"displayName": "Jane Manager"},
            "created": "2024-01-01T00:00:00.000+0000",
            "updated": "2024-01-01T12:00:00.000+0000",
            "issuetype": {"name": "Story"},
            "components": [{"name": "Authentication"}, {"name": "Security"}],
            "labels": ["security", "oauth", "authentication"],
            "customfield_10001": "Sprint 1",  # Sprint field
            "customfield_10002": 8,  # Story points
        }
    }


@pytest.fixture
def mock_confluence_page():
    """Mock Confluence page data for testing."""
    return {
        "id": "123456",
        "title": "Authentication Architecture",
        "body": {
            "storage": {
                "value": "<h1>OAuth2 Implementation Guide</h1><p>This page describes the OAuth2 authentication flow...</p>",
                "representation": "storage"
            }
        },
        "space": {"key": "PROJ"},
        "version": {"number": 1},
        "created": "2024-01-01T00:00:00.000Z",
        "updated": "2024-01-01T12:00:00.000Z"
    }


@pytest.fixture
def mock_google_doc():
    """Mock Google Docs document data for testing."""
    return {
        "documentId": "doc-123456",
        "title": "API Design Specification",
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "This document outlines the REST API design patterns for authentication endpoints..."
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }


class MockResponse:
    """Mock HTTP response for testing external API calls."""
    
    def __init__(self, json_data: dict, status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
    
    def json(self):
        return self.json_data
    
    @property
    def text(self):
        return str(self.json_data)


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response for testing."""
    return MockResponse({
        "candidates": [{
            "content": {
                "parts": [{
                    "text": "## Summary\nTest PR summary\n\n## Changes\n- Added new feature\n\n## Impact\nLow risk\n\n## Testing\nUnit tests added\n\n## Documentation\nNot updated\n\n## Dependencies\nNone"
                }]
            }
        }]
    })


# Service Mocks for TDD
@pytest.fixture
def mock_github_service():
    """Mock GitHub service for testing."""
    mock = AsyncMock()
    mock.get_pull_request.return_value = {
        "number": 123,
        "title": "Add authentication system",
        "body": "Implement OAuth2 with JWT tokens",
        "user": {"login": "developer"},
        "head": {"sha": "abc123"},
        "base": {"ref": "main"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "additions": 100,
        "deletions": 20,
        "changed_files": 5,
        "commits": 3,
        "comments": 2,
        "review_comments": 1,
        "state": "open",
    }
    mock.get_pr_files.return_value = [
        {"filename": "src/auth.py", "status": "added", "additions": 50, "deletions": 0},
        {"filename": "tests/test_auth.py", "status": "added", "additions": 30, "deletions": 0}
    ]
    mock.get_pr_commits.return_value = [
        {"sha": "abc123", "message": "Add OAuth2 authentication", "author": "developer"}
    ]
    return mock


@pytest.fixture
def mock_jira_service():
    """Mock Jira service for testing."""
    mock = AsyncMock()
    mock.get_issue.return_value = {
        "key": "PROJ-123",
        "summary": "Implement authentication system",
        "description": "Add secure user authentication with role-based access control",
        "status": "In Progress",
        "priority": "High",
        "assignee": "developer@company.com",
        "labels": ["authentication", "security"],
        "components": ["Backend", "Security"],
        "story_points": 8
    }
    return mock


@pytest.fixture
def mock_confluence_service():
    """Mock Confluence service for testing."""
    mock = AsyncMock()
    mock.search_pages.return_value = [
        {
            "id": "123456",
            "title": "Authentication Architecture",
            "content": "OAuth2 implementation guidelines with security best practices...",
            "space": "PROJ",
            "url": "https://company.atlassian.net/wiki/spaces/PROJ/pages/123456"
        }
    ]
    mock.get_page_content.return_value = "Detailed authentication architecture documentation..."
    return mock


@pytest.fixture
def mock_gdocs_service():
    """Mock Google Docs service for testing."""
    mock = AsyncMock()
    mock.get_document.return_value = {
        "documentId": "doc-123456", 
        "title": "API Design Specification",
        "content": "Authentication endpoint specifications and security requirements..."
    }
    return mock


@pytest.fixture
def mock_gemini_service():
    """Mock Gemini AI service for testing."""
    mock = AsyncMock()
    mock.generate_summary.return_value = {
        "summary": "This PR implements OAuth2 authentication with JWT tokens",
        "changes": ["Added authentication middleware", "Implemented JWT token generation"],
        "impact": "Medium - New authentication system affects all endpoints",
        "testing_recommendations": ["Test token validation", "Verify role-based access"],
        "documentation_notes": "Update API documentation with authentication requirements",
        "dependencies": ["PyJWT library added", "Redis for token storage"]
    }
    return mock


# Test Data Factories
@pytest.fixture
def summary_request_data():
    """Factory for creating test summary request data."""
    return {
        "pr_url": "https://github.com/owner/repo/pull/123",
        "jira_ticket": "PROJ-123",
        "confluence_pages": ["https://company.atlassian.net/wiki/spaces/PROJ/pages/123456"],
        "google_docs": ["https://docs.google.com/document/d/doc-123456"],
        "additional_context": "Focus on security implications"
    }


@pytest.fixture 
def expected_summary_structure():
    """Expected structure for PR summary responses."""
    return {
        "summary": str,
        "changes": list,
        "impact": str,
        "testing_recommendations": list,
        "documentation_notes": str,
        "dependencies": list,
        "metadata": {
            "pr_number": int,
            "jira_key": str,
            "generated_at": str,
            "confidence_score": float
        }
    }


# Database and External Service Test Utilities
@pytest.fixture(autouse=True)
def isolate_tests():
    """Ensure test isolation by resetting global state."""
    # Reset any global caches or state before each test
    yield
    # Cleanup after test if needed


@pytest.fixture
def temp_directory(tmp_path):
    """Provide temporary directory for file-based tests."""
    return tmp_path


# Pytest configuration and markers
def pytest_configure(config):
    """Configure pytest with custom markers for TDD workflow."""
    # Test type markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (slower, multiple components)"
    )
    config.addinivalue_line(
        "markers", "contract: mark test as a contract test (API interface validation)"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test (full system)"
    )
    
    # Performance markers
    config.addinivalue_line(
        "markers", "slow: mark test as slow running (>5 seconds)"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance benchmark"
    )
    
    # User story markers
    config.addinivalue_line(
        "markers", "us1: mark test as User Story 1 (Basic PR Summary)"
    )
    config.addinivalue_line(
        "markers", "us2: mark test as User Story 2 (Multi-Source Integration)"
    )
    config.addinivalue_line(
        "markers", "us3: mark test as User Story 3 (Advanced Review Guidance)"
    )
    
    # Service markers
    config.addinivalue_line(
        "markers", "github: mark test as requiring GitHub service"
    )
    config.addinivalue_line(
        "markers", "jira: mark test as requiring Jira service"
    )
    config.addinivalue_line(
        "markers", "gemini: mark test as requiring Gemini AI service"
    )
    config.addinivalue_line(
        "markers", "confluence: mark test as requiring Confluence service"
    )
    config.addinivalue_line(
        "markers", "gdocs: mark test as requiring Google Docs service"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically add markers based on test file paths and names."""
    for item in items:
        # Add markers based on directory structure
        test_path = str(item.fspath)
        
        # Test type markers by directory
        if "unit" in test_path:
            item.add_marker(pytest.mark.unit)
        elif "integration" in test_path:
            item.add_marker(pytest.mark.integration)
        elif "contract" in test_path:
            item.add_marker(pytest.mark.contract)
        elif "e2e" in test_path:
            item.add_marker(pytest.mark.e2e)
        
        # User story markers by filename
        test_name = item.name.lower()
        if "us1" in test_name or "summary" in test_name:
            item.add_marker(pytest.mark.us1)
        if "us2" in test_name or "multi_source" in test_name:
            item.add_marker(pytest.mark.us2)
        if "us3" in test_name or ("advanced" in test_name and "guidance" in test_name):
            item.add_marker(pytest.mark.us3)
        
        # Service markers by filename
        if "github" in test_name:
            item.add_marker(pytest.mark.github)
        if "jira" in test_name:
            item.add_marker(pytest.mark.jira)
        if "gemini" in test_name:
            item.add_marker(pytest.mark.gemini)
        if "confluence" in test_name:
            item.add_marker(pytest.mark.confluence)
        if "gdocs" in test_name or "google_docs" in test_name:
            item.add_marker(pytest.mark.gdocs)
        
        # Performance markers
        if "slow" in test_name or "performance" in test_name:
            item.add_marker(pytest.mark.slow)
        if "benchmark" in test_name:
            item.add_marker(pytest.mark.performance)


# Environment setup for tests
os.environ.update({
    # Core testing configuration
    "TESTING": "true",
    "LOG_LEVEL": "DEBUG",
    "ENVIRONMENT": "test",
    
    # Authentication and security
    "SECRET_KEY": "test-secret-key-for-jwt-signing",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
    
    # External service credentials (test values) - core required variables
    "GITHUB_TOKEN": "test-github-token",  # Required by config
    "GEMINI_API_KEY": "test-gemini-key",  # Required by config
    
    # Additional GitHub config (double underscore format)
    "GITHUB__API_TOKEN": "test-github-token",
    "GITHUB__BASE_URL": "https://api.github.com", 
    "GITHUB__TIMEOUT_SECONDS": "8",
    "GITHUB__MAX_RETRIES": "3",
    
    # Additional Gemini config (double underscore format)
    "GEMINI__MODEL_NAME": "gemini-2.5-pro", 
    "GEMINI__MAX_TOKENS": "1000",
    "GEMINI__TEMPERATURE": "0.3",
    "GEMINI__TIMEOUT_SECONDS": "15",
    
    "JIRA__SERVER_URL": "https://test-company.atlassian.net",
    "JIRA__USERNAME": "test-user@company.com",
    "JIRA__API_TOKEN": "test-jira-token",
    "JIRA__TIMEOUT_SECONDS": "8",
    "JIRA__MAX_RETRIES": "3",
    
    "CONFLUENCE__SERVER_URL": "https://test-company.atlassian.net/wiki",
    "CONFLUENCE__API_TOKEN": "test-confluence-token",
    "CONFLUENCE__TIMEOUT_SECONDS": "10",
    "CONFLUENCE__MAX_SEARCH_RESULTS": "5",
    
    "GOOGLE__CREDENTIALS_FILE_PATH": "test-service-account.json",
    "GOOGLE__DRIVE_SEARCH_TIMEOUT": "10",
    "GOOGLE__DOCS_EXTRACTION_TIMEOUT": "8",
    "GOOGLE__MAX_DOCUMENTS": "3",
    
    # Application settings
    "MAX_CONCURRENT_REQUESTS": "10",
    "REQUEST_TIMEOUT_TOTAL": "30",
    
    # Development settings for testing
    "DEBUG": "true",
    "RELOAD": "false", 
    "HOST": "127.0.0.1",
    "PORT": "8001",  # Different port for testing
    
    # CORS settings for testing
    "ALLOWED_ORIGINS": "http://localhost:3000,http://localhost:3001",
    "ALLOWED_METHODS": "GET,POST,PUT,DELETE,OPTIONS",
    "ALLOWED_HEADERS": "*"
})


# Test execution hooks
def pytest_runtest_setup(item):
    """Setup for each individual test."""
    # Log test execution for debugging
    print(f"\n🧪 Running test: {item.name}")


def pytest_runtest_teardown(item, nextitem):
    """Teardown after each individual test."""
    # Clear any test-specific state
    pass


def pytest_sessionstart(session):
    """Called at the start of the test session."""
    print("\n🚀 Starting PR Summarizer test session...")
    print("📋 Test markers available:")
    print("  • Unit tests: pytest -m unit")
    print("  • Integration tests: pytest -m integration") 
    print("  • Contract tests: pytest -m contract")
    print("  • User Story 1: pytest -m us1")
    print("  • User Story 2: pytest -m us2")
    print("  • User Story 3: pytest -m us3")
    print("  • Service-specific: pytest -m github/jira/gemini")


def pytest_sessionfinish(session, exitstatus):
    """Called at the end of the test session."""
    if exitstatus == 0:
        print("\n✅ All tests passed! Ready for TDD implementation.")
    else:
        print(f"\n❌ Tests failed with exit status: {exitstatus}")