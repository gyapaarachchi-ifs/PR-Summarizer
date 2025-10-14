"""Tests for configuration models.

Test coverage for all configuration models and environment variable loading.
"""

import os
import pytest
from unittest.mock import patch

from src.models.config import (
    GitHubConfig,
    GeminiConfig,
    JiraConfig,
    ConfluenceConfig,
    RedisConfig,
    DatabaseConfig,
    SecurityConfig,
    LoggingConfig,
    ApplicationConfig,
    load_config,
    get_config,
)
from src.utils.exceptions import ConfigurationError


class TestGitHubConfig:
    """Test GitHub configuration model."""
    
    def test_github_config_creation(self):
        """Test creating GitHub config with required fields."""
        config = GitHubConfig(token="ghp_test123")
        
        assert config.token == "ghp_test123"
        assert config.base_url == "https://api.github.com"
        assert config.timeout == 30.0
        assert config.max_retries == 3
    
    def test_github_config_custom_values(self):
        """Test creating GitHub config with custom values."""
        config = GitHubConfig(
            token="ghp_custom456",
            base_url="https://github.enterprise.com/api/v3",
            timeout=60.0,
            max_retries=5
        )
        
        assert config.token == "ghp_custom456"
        assert config.base_url == "https://github.enterprise.com/api/v3"
        assert config.timeout == 60.0
        assert config.max_retries == 5


class TestGeminiConfig:
    """Test Gemini configuration model."""
    
    def test_gemini_config_creation(self):
        """Test creating Gemini config with required fields."""
        config = GeminiConfig(api_key="AIzaSyTest123")
        
        assert config.api_key == "AIzaSyTest123"
        assert config.model == "gemini-1.5-pro"
        assert config.temperature == 0.3
        assert config.max_tokens == 8192
        assert config.timeout == 60.0
    
    def test_gemini_config_custom_values(self):
        """Test creating Gemini config with custom values."""
        config = GeminiConfig(
            api_key="AIzaSyCustom456",
            model="gemini-1.5-flash",
            temperature=0.7,
            max_tokens=4096,
            timeout=30.0
        )
        
        assert config.api_key == "AIzaSyCustom456"
        assert config.model == "gemini-1.5-flash"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.timeout == 30.0


class TestJiraConfig:
    """Test Jira configuration model."""
    
    def test_jira_config_disabled(self):
        """Test creating disabled Jira config."""
        config = JiraConfig()
        
        assert config.enabled is False
        assert config.url is None
        assert config.email is None
        assert config.api_token is None
    
    def test_jira_config_enabled(self):
        """Test creating enabled Jira config."""
        config = JiraConfig(
            enabled=True,
            url="https://company.atlassian.net",
            email="test@company.com",
            api_token="jira_token_123"
        )
        
        assert config.enabled is True
        assert config.url == "https://company.atlassian.net"
        assert config.email == "test@company.com"
        assert config.api_token == "jira_token_123"


class TestConfluenceConfig:
    """Test Confluence configuration model."""
    
    def test_confluence_config_disabled(self):
        """Test creating disabled Confluence config."""
        config = ConfluenceConfig()
        
        assert config.enabled is False
        assert config.url is None
        assert config.email is None
        assert config.api_token is None
    
    def test_confluence_config_enabled(self):
        """Test creating enabled Confluence config."""
        config = ConfluenceConfig(
            enabled=True,
            url="https://company.atlassian.net/wiki",
            email="test@company.com",
            api_token="confluence_token_123"
        )
        
        assert config.enabled is True
        assert config.url == "https://company.atlassian.net/wiki"
        assert config.email == "test@company.com"
        assert config.api_token == "confluence_token_123"


class TestRedisConfig:
    """Test Redis configuration model."""
    
    def test_redis_config_defaults(self):
        """Test creating Redis config with defaults."""
        config = RedisConfig()
        
        assert config.url is None
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert config.ssl is False
        assert config.connection_pool_size == 10
    
    def test_redis_config_custom(self):
        """Test creating Redis config with custom values."""
        config = RedisConfig(
            url="redis://user:pass@redis.example.com:6380/1",
            host="redis.example.com",
            port=6380,
            db=1,
            password="secret",
            ssl=True,
            connection_pool_size=20
        )
        
        assert config.url == "redis://user:pass@redis.example.com:6380/1"
        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.db == 1
        assert config.password == "secret"
        assert config.ssl is True
        assert config.connection_pool_size == 20


class TestDatabaseConfig:
    """Test Database configuration model."""
    
    def test_database_config_creation(self):
        """Test creating database config."""
        config = DatabaseConfig(
            database="testdb",
            username="testuser",
            password="testpass"
        )
        
        assert config.url is None
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "testdb"
        assert config.username == "testuser"
        assert config.password == "testpass"
        assert config.pool_size == 5
        assert config.max_overflow == 10
    
    def test_database_config_custom(self):
        """Test creating database config with custom values."""
        config = DatabaseConfig(
            url="postgresql://user:pass@db.example.com:5433/mydb",
            host="db.example.com",
            port=5433,
            database="mydb",
            username="user",
            password="pass",
            pool_size=10,
            max_overflow=20
        )
        
        assert config.url == "postgresql://user:pass@db.example.com:5433/mydb"
        assert config.host == "db.example.com"
        assert config.port == 5433
        assert config.database == "mydb"
        assert config.username == "user"
        assert config.password == "pass"
        assert config.pool_size == 10
        assert config.max_overflow == 20


class TestSecurityConfig:
    """Test Security configuration model."""
    
    def test_security_config_creation(self):
        """Test creating security config."""
        config = SecurityConfig(secret_key="test_secret_key_32_characters_long")
        
        assert config.secret_key == "test_secret_key_32_characters_long"
        assert config.algorithm == "HS256"
        assert config.access_token_expire_minutes == 30
        assert config.cors_origins == ["http://localhost:3000"]
        assert config.cors_allow_credentials is True
    
    def test_security_config_custom(self):
        """Test creating security config with custom values."""
        config = SecurityConfig(
            secret_key="custom_secret_key_with_more_than_32_chars",
            algorithm="HS512",
            access_token_expire_minutes=60,
            cors_origins=["http://localhost:8080", "https://app.example.com"],
            cors_allow_credentials=False
        )
        
        assert config.secret_key == "custom_secret_key_with_more_than_32_chars"
        assert config.algorithm == "HS512"
        assert config.access_token_expire_minutes == 60
        assert config.cors_origins == ["http://localhost:8080", "https://app.example.com"]
        assert config.cors_allow_credentials is False


class TestLoggingConfig:
    """Test Logging configuration model."""
    
    def test_logging_config_defaults(self):
        """Test creating logging config with defaults."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.json_format is False
        assert config.enable_correlation_id is True
        assert config.log_file is None
    
    def test_logging_config_custom(self):
        """Test creating logging config with custom values."""
        config = LoggingConfig(
            level="DEBUG",
            json_format=True,
            enable_correlation_id=False,
            log_file="/var/log/app.log"
        )
        
        assert config.level == "DEBUG"
        assert config.json_format is True
        assert config.enable_correlation_id is False
        assert config.log_file == "/var/log/app.log"


class TestApplicationConfig:
    """Test Application configuration model."""
    
    def test_application_config_creation(self):
        """Test creating application config with required fields."""
        github_config = GitHubConfig(token="ghp_test123")
        gemini_config = GeminiConfig(api_key="AIzaSyTest123")
        security_config = SecurityConfig(secret_key="test_secret_key_32_characters_long")
        
        config = ApplicationConfig(
            github=github_config,
            gemini=gemini_config,
            security=security_config
        )
        
        assert config.environment == "production"
        assert config.debug is False
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.github == github_config
        assert config.gemini == gemini_config
        assert config.security == security_config
        assert isinstance(config.logging, LoggingConfig)
    
    def test_application_config_with_optional_services(self):
        """Test creating application config with optional services."""
        github_config = GitHubConfig(token="ghp_test123")
        gemini_config = GeminiConfig(api_key="AIzaSyTest123")
        security_config = SecurityConfig(secret_key="test_secret_key_32_characters_long")
        jira_config = JiraConfig(enabled=True, url="https://test.atlassian.net", email="test@test.com", api_token="token")
        redis_config = RedisConfig(host="redis.example.com")
        
        config = ApplicationConfig(
            github=github_config,
            gemini=gemini_config,
            security=security_config,
            jira=jira_config,
            redis=redis_config
        )
        
        assert config.jira == jira_config
        assert config.redis == redis_config
        assert config.confluence is None
        assert config.database is None


class TestConfigLoader:
    """Test configuration loading from environment variables."""
    
    @patch.dict(os.environ, {
        'GITHUB_TOKEN': 'ghp_test_token',
        'GEMINI_API_KEY': 'AIzaSy_test_key',
        'SECRET_KEY': 'test_secret_key_with_more_than_32_chars'
    }, clear=True)
    def test_load_config_minimal(self):
        """Test loading config with minimal required environment variables."""
        config = load_config()
        
        assert config.github.token == "ghp_test_token"
        assert config.gemini.api_key == "AIzaSy_test_key"
        assert config.security.secret_key == "test_secret_key_with_more_than_32_chars"
        assert config.environment == "production"
        assert config.debug is False
    
    @patch.dict(os.environ, {
        'GITHUB_TOKEN': 'ghp_test_token',
        'GEMINI_API_KEY': 'AIzaSy_test_key',
        'SECRET_KEY': 'test_secret_key_with_more_than_32_chars',
        'ENVIRONMENT': 'development',
        'DEBUG': 'true',
        'HOST': '0.0.0.0',
        'PORT': '9000'
    }, clear=True)
    def test_load_config_custom_app_settings(self):
        """Test loading config with custom application settings."""
        config = load_config()
        
        assert config.environment == "development"
        assert config.debug is True
        assert config.host == "0.0.0.0"
        assert config.port == 9000
    
    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'AIzaSy_test_key',
        'SECRET_KEY': 'test_secret_key_with_more_than_32_chars'
    }, clear=True)
    def test_load_config_missing_github_token(self):
        """Test loading config fails when GitHub token is missing."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_config()
        
        assert "GITHUB_TOKEN environment variable is required" in str(exc_info.value)
        assert exc_info.value.details["missing_env_var"] == "GITHUB_TOKEN"
    
    @patch.dict(os.environ, {
        'GITHUB_TOKEN': 'ghp_test_token',
        'SECRET_KEY': 'test_secret_key_with_more_than_32_chars'
    }, clear=True)
    def test_load_config_missing_gemini_key(self):
        """Test loading config fails when Gemini API key is missing."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_config()
        
        assert "GEMINI_API_KEY environment variable is required" in str(exc_info.value)
        assert exc_info.value.details["missing_env_var"] == "GEMINI_API_KEY"
    
    @patch.dict(os.environ, {
        'GITHUB_TOKEN': 'ghp_test_token',
        'GEMINI_API_KEY': 'AIzaSy_test_key'
    }, clear=True)
    def test_load_config_missing_secret_key(self):
        """Test loading config fails when secret key is missing."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_config()
        
        assert "SECRET_KEY environment variable is required" in str(exc_info.value)
        assert exc_info.value.details["missing_env_var"] == "SECRET_KEY"
    
    @patch.dict(os.environ, {
        'GITHUB_TOKEN': 'ghp_test_token',
        'GEMINI_API_KEY': 'AIzaSy_test_key',
        'SECRET_KEY': 'test_secret_key_with_more_than_32_chars'
    }, clear=True)
    def test_get_config_singleton(self):
        """Test get_config returns same instance on multiple calls."""
        # Clear any existing config
        import src.models.config
        src.models.config._config = None
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
        assert config1.github.token == "ghp_test_token"
    
    def test_config_exports(self):
        """Test that all expected classes and functions are exported."""
        from src.models import config
        
        expected_exports = [
            "GitHubConfig",
            "GeminiConfig",
            "JiraConfig", 
            "ConfluenceConfig",
            "RedisConfig",
            "DatabaseConfig",
            "SecurityConfig",
            "LoggingConfig",
            "ApplicationConfig",
            "load_config",
            "get_config",
        ]
        
        for export in expected_exports:
            assert hasattr(config, export), f"Missing export: {export}"