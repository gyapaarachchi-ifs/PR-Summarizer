"""Tests for input validation utilities."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.utils.validators import (
    validate_pr_number,
    validate_repository_identifier,
    validate_github_url,
    validate_api_key,
    validate_pagination_params,
    validate_file_path,
    PRNumberValidator,
    RepositoryValidator,
    GitHubURLValidator,
    APIKeyValidator,
    PaginationValidator,
    FilePathValidator,
)
from src.utils.exceptions import ValidationError


class TestPRNumberValidator:
    """Test PR number validation."""

    def test_valid_pr_numbers(self):
        """Test validation of valid PR numbers."""
        valid_numbers = [1, 123, 9999, "1", "123", "9999"]
        
        for number in valid_numbers:
            result = validate_pr_number(number)
            assert isinstance(result, int)
            assert result > 0

    def test_invalid_pr_numbers(self):
        """Test validation of invalid PR numbers."""
        invalid_numbers = [0, -1, "0", "-1", "abc", "", None, 0.5, "123.5"]
        
        for number in invalid_numbers:
            with pytest.raises(ValidationError) as exc_info:
                validate_pr_number(number)
            
            assert "PR number" in str(exc_info.value)

    def test_pr_number_validator_class(self):
        """Test PRNumberValidator class."""
        validator = PRNumberValidator()
        
        # Valid cases
        assert validator.validate(123) == 123
        assert validator.validate("456") == 456
        
        # Invalid cases
        with pytest.raises(ValidationError):
            validator.validate(-1)
        
        with pytest.raises(ValidationError):
            validator.validate("invalid")

    def test_pr_number_edge_cases(self):
        """Test PR number validation edge cases."""
        # Very large numbers should be valid
        large_number = 999999999
        result = validate_pr_number(large_number)
        assert result == large_number
        
        # String with leading zeros
        result = validate_pr_number("0123")
        assert result == 123


class TestRepositoryValidator:
    """Test repository identifier validation."""

    def test_valid_repository_identifiers(self):
        """Test validation of valid repository identifiers."""
        valid_repos = [
            "owner/repo",
            "github-user/my-project",
            "org123/repo_name",
            "user/repo-with-dashes",
            "a/b",  # Minimum length
        ]
        
        for repo in valid_repos:
            result = validate_repository_identifier(repo)
            assert result == repo

    def test_invalid_repository_identifiers(self):
        """Test validation of invalid repository identifiers."""
        invalid_repos = [
            "owner",  # Missing repo name
            "/repo",  # Missing owner
            "owner/",  # Missing repo name
            "",  # Empty string
            "owner/repo/extra",  # Too many parts
            "owner with spaces/repo",  # Spaces in owner
            "owner/repo with spaces",  # Spaces in repo
            None,  # None value
        ]
        
        for repo in invalid_repos:
            with pytest.raises(ValidationError) as exc_info:
                validate_repository_identifier(repo)
            
            assert "repository identifier" in str(exc_info.value).lower()

    def test_repository_validator_class(self):
        """Test RepositoryValidator class."""
        validator = RepositoryValidator()
        
        # Valid case
        result = validator.validate("owner/repo")
        assert result == "owner/repo"
        
        # Invalid case
        with pytest.raises(ValidationError):
            validator.validate("invalid-format")

    def test_repository_case_sensitivity(self):
        """Test repository validation case sensitivity."""
        # GitHub is case-insensitive but preserves case
        mixed_case = "MyOrg/MyRepo"
        result = validate_repository_identifier(mixed_case)
        assert result == mixed_case


class TestGitHubURLValidator:
    """Test GitHub URL validation."""

    def test_valid_github_urls(self):
        """Test validation of valid GitHub URLs."""
        valid_urls = [
            "https://github.com/owner/repo",
            "https://github.com/owner/repo/",
            "https://github.com/owner/repo.git",
            "https://github.com/owner/repo/pulls/123",
            "https://github.com/owner/repo/issues/456",
            "https://api.github.com/repos/owner/repo",
        ]
        
        for url in valid_urls:
            result = validate_github_url(url)
            assert result == url

    def test_invalid_github_urls(self):
        """Test validation of invalid GitHub URLs."""
        invalid_urls = [
            "http://github.com/owner/repo",  # Not HTTPS
            "https://gitlab.com/owner/repo",  # Not GitHub
            "https://github.com",  # No repo
            "not-a-url",  # Invalid URL format
            "",  # Empty string
            None,  # None value
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationError) as exc_info:
                validate_github_url(url)
            
            assert "github url" in str(exc_info.value).lower()

    def test_github_url_validator_class(self):
        """Test GitHubURLValidator class."""
        validator = GitHubURLValidator()
        
        # Valid case
        url = "https://github.com/owner/repo"
        result = validator.validate(url)
        assert result == url
        
        # Invalid case
        with pytest.raises(ValidationError):
            validator.validate("https://example.com")


class TestAPIKeyValidator:
    """Test API key validation."""

    def test_valid_api_keys(self):
        """Test validation of valid API keys."""
        valid_keys = [
            "ghp_1234567890abcdef1234567890abcdef12345678",  # GitHub personal access token
            "sk-1234567890abcdef1234567890abcdef",  # OpenAI style key
            "AIzaSyD1234567890abcdef1234567890abcdef",  # Google API key style
            "xoxb-1234567890-1234567890-abcdef1234567890",  # Slack bot token style
            "a" * 20,  # Minimum length
            "a" * 100,  # Long key
        ]
        
        for key in valid_keys:
            result = validate_api_key(key)
            assert result == key

    def test_invalid_api_keys(self):
        """Test validation of invalid API keys."""
        invalid_keys = [
            "",  # Empty string
            "short",  # Too short
            "a" * 10,  # Too short
            None,  # None value
            "   ",  # Only spaces
            "key with spaces",  # Contains spaces
        ]
        
        for key in invalid_keys:
            with pytest.raises(ValidationError) as exc_info:
                validate_api_key(key)
            
            assert "api key" in str(exc_info.value).lower()

    def test_api_key_validator_class(self):
        """Test APIKeyValidator class."""
        validator = APIKeyValidator()
        
        # Valid case
        key = "valid-api-key-1234567890"
        result = validator.validate(key)
        assert result == key
        
        # Invalid case
        with pytest.raises(ValidationError):
            validator.validate("short")

    def test_api_key_sanitization(self):
        """Test API key sanitization in error messages."""
        validator = APIKeyValidator()
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("secret-key-123")
        
        # Error message should not contain the actual key
        error_message = str(exc_info.value)
        assert "secret-key-123" not in error_message


class TestPaginationValidator:
    """Test pagination parameters validation."""

    def test_valid_pagination_params(self):
        """Test validation of valid pagination parameters."""
        valid_params = [
            {"page": 1, "size": 10},
            {"page": 1, "size": 100},
            {"page": 10, "size": 50},
            {"page": "1", "size": "10"},  # String numbers
        ]
        
        for params in valid_params:
            result = validate_pagination_params(params)
            assert isinstance(result["page"], int)
            assert isinstance(result["size"], int)
            assert result["page"] >= 1
            assert 1 <= result["size"] <= 100

    def test_invalid_pagination_params(self):
        """Test validation of invalid pagination parameters."""
        invalid_params = [
            {"page": 0, "size": 10},  # Page zero
            {"page": -1, "size": 10},  # Negative page
            {"page": 1, "size": 0},  # Size zero
            {"page": 1, "size": 101},  # Size too large
            {"page": "invalid", "size": 10},  # Invalid page
            {"page": 1, "size": "invalid"},  # Invalid size
            {"page": 1},  # Missing size
            {"size": 10},  # Missing page
            {},  # Empty params
        ]
        
        for params in invalid_params:
            with pytest.raises(ValidationError) as exc_info:
                validate_pagination_params(params)
            
            assert "pagination" in str(exc_info.value).lower()

    def test_pagination_validator_class(self):
        """Test PaginationValidator class."""
        validator = PaginationValidator()
        
        # Valid case
        params = {"page": 2, "size": 25}
        result = validator.validate(params)
        assert result["page"] == 2
        assert result["size"] == 25
        
        # Invalid case
        with pytest.raises(ValidationError):
            validator.validate({"page": 0, "size": 10})

    def test_pagination_defaults(self):
        """Test pagination with default values."""
        # Test that validator can provide defaults
        validator = PaginationValidator(default_page=1, default_size=20)
        
        # Should be able to validate partial params with defaults
        result = validator.validate_with_defaults({})
        assert result["page"] == 1
        assert result["size"] == 20


class TestFilePathValidator:
    """Test file path validation."""

    def test_valid_file_paths(self):
        """Test validation of valid file paths."""
        valid_paths = [
            "src/main.py",
            "docs/README.md",
            "tests/test_example.py",
            "package.json",
            "folder/subfolder/file.txt",
            ".gitignore",
            "path/with-dashes/file_name.ext",
        ]
        
        for path in valid_paths:
            result = validate_file_path(path)
            assert result == path

    def test_invalid_file_paths(self):
        """Test validation of invalid file paths."""
        invalid_paths = [
            "",  # Empty string
            "/absolute/path",  # Absolute path
            "C:\\windows\\path",  # Windows absolute path
            "../parent/file",  # Parent directory
            "./current/file",  # Current directory prefix
            "path//double/slash",  # Double slashes
            "path\\backslash",  # Backslashes
            None,  # None value
        ]
        
        for path in invalid_paths:
            with pytest.raises(ValidationError) as exc_info:
                validate_file_path(path)
            
            assert "file path" in str(exc_info.value).lower()

    def test_file_path_validator_class(self):
        """Test FilePathValidator class."""
        validator = FilePathValidator()
        
        # Valid case
        path = "src/utils/helpers.py"
        result = validator.validate(path)
        assert result == path
        
        # Invalid case
        with pytest.raises(ValidationError):
            validator.validate("../invalid/path")

    def test_file_path_security(self):
        """Test file path validation for security concerns."""
        # Paths that could be security risks
        risky_paths = [
            "../../etc/passwd",
            "..\\windows\\system32",
            "/.ssh/id_rsa",
            "~/.bashrc",
        ]
        
        for path in risky_paths:
            with pytest.raises(ValidationError):
                validate_file_path(path)


class TestCombinedValidation:
    """Test combined validation scenarios."""

    def test_multiple_validators(self):
        """Test using multiple validators together."""
        # Validate PR request data
        pr_number = validate_pr_number("123")
        repository = validate_repository_identifier("owner/repo")
        
        assert pr_number == 123
        assert repository == "owner/repo"

    def test_validation_error_details(self):
        """Test that validation errors include helpful details."""
        with pytest.raises(ValidationError) as exc_info:
            validate_pr_number("invalid")
        
        error = exc_info.value
        assert error.details is not None
        assert "field" in error.details
        assert "value" in error.details

    def test_validator_inheritance(self):
        """Test that all validators inherit from base validator."""
        validators = [
            PRNumberValidator(),
            RepositoryValidator(),
            GitHubURLValidator(),
            APIKeyValidator(),
            PaginationValidator(),
            FilePathValidator(),
        ]
        
        for validator in validators:
            # All validators should have validate method
            assert hasattr(validator, 'validate')
            assert callable(validator.validate)