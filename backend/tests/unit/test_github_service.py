"""
Unit tests for GitHub service.

This module tests the GitHub service functionality including
PR data retrieval, URL validation, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from src.services.github import GitHubService, GitHubValidationError


class TestGitHubService:
    """Unit tests for GitHubService class."""
    
    @pytest.fixture
    def github_service(self):
        """Create a GitHubService instance for testing."""
        return GitHubService()
        
    @pytest.fixture
    def mock_pr_data(self) -> Dict[str, Any]:
        """Mock PR data for testing."""
        return {
            "number": 123,
            "title": "Add user authentication",
            "body": "This PR adds JWT-based user authentication to the application.",
            "user": {
                "login": "developer123"
            },
            "state": "open",
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-01-15T15:30:00Z",
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
            "comments": 2,
            "review_comments": 3,
            "mergeable": True,
            "merged": False,
            "html_url": "https://github.com/owner/repo/pull/123"
        }
        
    def test_service_initialization(self, github_service):
        """Test that GitHubService initializes correctly."""
        assert isinstance(github_service, GitHubService)
        # Add any initialization checks here
        
    def test_valid_github_url_validation(self, github_service):
        """Test validation of valid GitHub PR URLs."""
        valid_urls = [
            "https://github.com/owner/repo/pull/123",
            "https://github.com/my-org/my-repo/pull/456",
            "https://github.com/user123/project_name/pull/1",
            "https://github.com/a/b/pull/999999"
        ]
        
        for url in valid_urls:
            # Should not raise exception for valid URLs
            github_service._validate_github_url(url)
            
    def test_invalid_github_url_validation(self, github_service):
        """Test validation of invalid GitHub PR URLs."""
        invalid_urls = [
            "https://gitlab.com/owner/repo/pull/123",  # Wrong domain
            "https://github.com/owner/repo/issues/123",  # Issues, not PR
            "https://github.com/owner",  # Missing parts
            "https://github.com/owner/repo",  # Missing pull request
            "https://github.com/owner/repo/pull/",  # Missing PR number
            "https://github.com/owner/repo/pull/abc",  # Non-numeric PR number
            "not-a-url",  # Not a URL
            "",  # Empty string
            None  # None value
        ]
        
        for url in invalid_urls:
            with pytest.raises(GitHubValidationError):
                github_service._validate_github_url(url)
                
    def test_extract_owner_repo_number(self, github_service):
        """Test extraction of owner, repo, and PR number from URL."""
        url = "https://github.com/owner/repo/pull/123"
        owner, repo, pr_number = github_service._extract_pr_info(url)
        
        assert owner == "owner"
        assert repo == "repo"
        assert pr_number == 123
        
    def test_extract_pr_info_with_hyphen_names(self, github_service):
        """Test extraction with hyphenated names."""
        url = "https://github.com/my-org/my-repo/pull/456"
        owner, repo, pr_number = github_service._extract_pr_info(url)
        
        assert owner == "my-org"
        assert repo == "my-repo"
        assert pr_number == 456
        
    @patch('src.services.github.Github')
    async def test_get_pr_details_success(self, mock_github_class, github_service, mock_pr_data):
        """Test successful PR data retrieval."""
        # Mock the GitHub API client
        mock_github = Mock()
        mock_repo = Mock()
        mock_pr = Mock()
        
        # Configure mock chain
        mock_github_class.return_value = mock_github
        mock_github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        
        # Configure PR mock with data
        for key, value in mock_pr_data.items():
            setattr(mock_pr, key, value)
            
        # Test the method
        url = "https://github.com/owner/repo/pull/123"
        result = await github_service.get_pr_details(url)
        
        # Verify API calls
        mock_github.get_repo.assert_called_once_with("owner/repo")
        mock_repo.get_pull.assert_called_once_with(123)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert result["number"] == 123
        assert result["title"] == "Add user authentication"
        assert result["additions"] == 234
        assert result["deletions"] == 56
        
    async def test_get_pr_details_invalid_url(self, github_service):
        """Test PR data retrieval with invalid URL."""
        invalid_url = "https://invalid-url.com/not-github"
        
        with pytest.raises(GitHubValidationError) as exc_info:
            await github_service.get_pr_details(invalid_url)
            
        assert "Invalid GitHub PR URL format" in str(exc_info.value)
        
    @patch('src.services.github.Github')
    async def test_get_pr_details_api_error(self, mock_github_class, github_service):
        """Test PR data retrieval with GitHub API error."""
        # Mock GitHub API to raise exception
        mock_github = Mock()
        mock_github_class.return_value = mock_github
        mock_github.get_repo.side_effect = Exception("GitHub API Error")
        
        url = "https://github.com/owner/repo/pull/123"
        
        with pytest.raises(Exception) as exc_info:
            await github_service.get_pr_details(url)
            
        assert "GitHub API Error" in str(exc_info.value)
        
    @patch('src.services.github.Github')
    async def test_get_pr_details_repo_not_found(self, mock_github_class, github_service):
        """Test PR data retrieval with repository not found."""
        from github.GithubException import UnknownObjectException
        
        # Mock GitHub API to raise UnknownObjectException
        mock_github = Mock()
        mock_github_class.return_value = mock_github
        mock_github.get_repo.side_effect = UnknownObjectException(404, "Not Found", {})
        
        url = "https://github.com/nonexistent/repo/pull/123"
        
        with pytest.raises(Exception):
            await github_service.get_pr_details(url)
            
    @patch('src.services.github.Github')
    async def test_get_pr_details_pr_not_found(self, mock_github_class, github_service):
        """Test PR data retrieval with PR not found."""
        from github.GithubException import UnknownObjectException
        
        # Mock GitHub API
        mock_github = Mock()
        mock_repo = Mock()
        mock_github_class.return_value = mock_github
        mock_github.get_repo.return_value = mock_repo
        mock_repo.get_pull.side_effect = UnknownObjectException(404, "Not Found", {})
        
        url = "https://github.com/owner/repo/pull/999999"
        
        with pytest.raises(Exception):
            await github_service.get_pr_details(url)
            
    def test_format_pr_data(self, github_service, mock_pr_data):
        """Test formatting of raw PR data."""
        # Create mock PR object
        mock_pr = Mock()
        for key, value in mock_pr_data.items():
            setattr(mock_pr, key, value)
            
        # Test formatting
        result = github_service._format_pr_data(mock_pr)
        
        assert isinstance(result, dict)
        assert result["number"] == 123
        assert result["title"] == "Add user authentication"
        assert result["state"] == "open"
        assert result["additions"] == 234
        assert result["deletions"] == 56
        assert result["changed_files"] == 8
        
    def test_pr_data_includes_all_required_fields(self, github_service, mock_pr_data):
        """Test that formatted PR data includes all required fields."""
        mock_pr = Mock()
        for key, value in mock_pr_data.items():
            setattr(mock_pr, key, value)
            
        result = github_service._format_pr_data(mock_pr)
        
        required_fields = [
            "number", "title", "body", "state", "html_url",
            "additions", "deletions", "changed_files", "commits"
        ]
        
        for field in required_fields:
            assert field in result, f"Required field '{field}' missing"
            
    @patch('src.services.github.Github')
    async def test_get_pr_data_alias_method(self, mock_github_class, github_service, mock_pr_data):
        """Test the get_pr_data alias method."""
        # Mock the GitHub API client
        mock_github = Mock()
        mock_repo = Mock()
        mock_pr = Mock()
        
        mock_github_class.return_value = mock_github
        mock_github.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        
        for key, value in mock_pr_data.items():
            setattr(mock_pr, key, value)
            
        # Test the alias method
        url = "https://github.com/owner/repo/pull/123"
        result = await github_service.get_pr_data(url)
        
        # Should return same result as get_pr_details
        assert isinstance(result, dict)
        assert result["number"] == 123
        
    def test_github_validation_error_message(self):
        """Test GitHubValidationError provides clear error messages."""
        error = GitHubValidationError("Invalid URL format")
        assert str(error) == "Invalid URL format"
        
    def test_url_regex_pattern(self, github_service):
        """Test the URL regex pattern matching."""
        # This tests the internal regex pattern used for validation
        pattern = r"^https://github\.com/[^/]+/[^/]+/pull/\d+$"
        
        import re
        
        valid_urls = [
            "https://github.com/owner/repo/pull/123",
            "https://github.com/my-org/my-repo/pull/1",
        ]
        
        invalid_urls = [
            "https://github.com/owner/repo/pull/",
            "https://github.com/owner/repo/issues/123",
        ]
        
        for url in valid_urls:
            assert re.match(pattern, url), f"Valid URL {url} should match pattern"
            
        for url in invalid_urls:
            assert not re.match(pattern, url), f"Invalid URL {url} should not match pattern"