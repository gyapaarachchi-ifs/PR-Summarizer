"""Configuration models for PR Summarizer application.

This module defines Pydantic models for application configuration,
supporting loading from environment variables and validation.
"""

import os
from typing import List, Optional
from urllib.parse import quote_plus

from pydantic import BaseModel, Field

from src.utils.exceptions import ConfigurationError


class GitHubConfig(BaseModel):
    """GitHub API configuration."""
    
    token: str = Field(..., description="GitHub personal access token")
    base_url: str = Field(default="https://api.github.com", description="GitHub API base URL")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")


class GeminiConfig(BaseModel):
    """Google Gemini API configuration."""
    
    api_key: str = Field(..., description="Google Gemini API key")
    model: str = Field(default="gemini-1.5-pro", description="Gemini model name")
    temperature: float = Field(default=0.3, description="Generation temperature")
    max_tokens: int = Field(default=8192, description="Maximum tokens to generate")
    timeout: float = Field(default=60.0, description="Request timeout in seconds")


class JiraConfig(BaseModel):
    """Jira API configuration."""
    
    enabled: bool = Field(default=False, description="Whether Jira integration is enabled")
    url: Optional[str] = Field(default=None, description="Jira instance URL")
    email: Optional[str] = Field(default=None, description="Jira user email")
    api_token: Optional[str] = Field(default=None, description="Jira API token")


class ConfluenceConfig(BaseModel):
    """Confluence API configuration."""
    
    enabled: bool = Field(default=False, description="Whether Confluence integration is enabled")
    url: Optional[str] = Field(default=None, description="Confluence instance URL")
    email: Optional[str] = Field(default=None, description="Confluence user email")
    api_token: Optional[str] = Field(default=None, description="Confluence API token")


class RedisConfig(BaseModel):
    """Redis cache configuration."""
    
    url: Optional[str] = Field(default=None, description="Redis connection URL")
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    ssl: bool = Field(default=False, description="Use SSL connection")
    connection_pool_size: int = Field(default=10, description="Connection pool size")


class DatabaseConfig(BaseModel):
    """Database configuration."""
    
    url: Optional[str] = Field(default=None, description="Database connection URL")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Maximum pool overflow")


class SecurityConfig(BaseModel):
    """Security and authentication configuration."""
    
    secret_key: str = Field(..., description="Secret key for JWT signing")
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Token expiration in minutes")
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"], description="CORS allowed origins")
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    level: str = Field(default="INFO", description="Log level")
    json_format: bool = Field(default=False, description="Use JSON log format")
    enable_correlation_id: bool = Field(default=True, description="Enable correlation ID tracking")
    log_file: Optional[str] = Field(default=None, description="Log file path")


class ApplicationConfig(BaseModel):
    """Main application configuration."""
    
    # Application settings
    environment: str = Field(default="production", description="Application environment")
    debug: bool = Field(default=False, description="Debug mode")
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Service configurations
    github: GitHubConfig = Field(..., description="GitHub API configuration")
    gemini: GeminiConfig = Field(..., description="Gemini API configuration")
    jira: Optional[JiraConfig] = Field(default=None, description="Jira API configuration")
    confluence: Optional[ConfluenceConfig] = Field(default=None, description="Confluence API configuration")
    redis: Optional[RedisConfig] = Field(default=None, description="Redis cache configuration")
    database: Optional[DatabaseConfig] = Field(default=None, description="Database configuration")
    
    # Core configurations
    security: SecurityConfig = Field(..., description="Security configuration")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")


# Global configuration instance
_config: Optional[ApplicationConfig] = None


def load_config() -> ApplicationConfig:
    """Load application configuration from environment variables.
    
    Returns:
        Loaded and validated application configuration
        
    Raises:
        ConfigurationError: If configuration is invalid or missing required values
    """
    try:
        # Required environment variables
        github_token = os.getenv("GITHUB_TOKEN")
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        secret_key = os.getenv("SECRET_KEY")
        
        if not github_token:
            raise ConfigurationError(
                "GITHUB_TOKEN environment variable is required",
                details={"missing_env_var": "GITHUB_TOKEN"}
            )
        
        if not gemini_api_key:
            raise ConfigurationError(
                "GEMINI_API_KEY environment variable is required",
                details={"missing_env_var": "GEMINI_API_KEY"}
            )
        
        if not secret_key:
            raise ConfigurationError(
                "SECRET_KEY environment variable is required",
                details={"missing_env_var": "SECRET_KEY"}
            )
        
        # Build configuration
        config = ApplicationConfig(
            environment=os.getenv("ENVIRONMENT", "production"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "8000")),
            github=GitHubConfig(token=github_token),
            gemini=GeminiConfig(api_key=gemini_api_key),
            security=SecurityConfig(secret_key=secret_key),
            logging=LoggingConfig()
        )
        
        return config
        
    except Exception as e:
        if isinstance(e, ConfigurationError):
            raise
        
        raise ConfigurationError(
            f"Failed to load configuration: {str(e)}",
            details={"error": str(e), "type": type(e).__name__}
        )


def get_config() -> ApplicationConfig:
    """Get the global application configuration instance.
    
    Returns:
        Application configuration (loads from environment on first call)
        
    Raises:
        ConfigurationError: If configuration loading fails
    """
    global _config
    
    if _config is None:
        _config = load_config()
    
    return _config


# Export all configuration classes and functions
__all__ = [
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