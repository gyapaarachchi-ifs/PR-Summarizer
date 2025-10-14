"""
Request models for PR summary API.

This module defines the request models used by the PR summary generation
endpoints, including validation rules and data structures.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class SummaryRequest(BaseModel):
    """
    Request model for PR summary generation.
    
    This model validates and structures the input data required
    to generate a PR summary from GitHub and optional Jira sources.
    """
    
    github_pr_url: str = Field(
        ...,
        description="GitHub pull request URL",
        example="https://github.com/owner/repo/pull/123",
        min_length=1,
        max_length=500
    )
    
    jira_ticket_id: Optional[str] = Field(
        None,
        description="Optional Jira ticket ID for business context",
        example="PROJ-456",
        max_length=50
    )
    
    @field_validator('github_pr_url')
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        """Validate GitHub PR URL format."""
        if not v:
            raise ValueError("GitHub PR URL is required")
            
        # GitHub PR URL pattern: https://github.com/owner/repo/pull/number
        pattern = r"^https://github\.com/[^/]+/[^/]+/pull/\d+$"
        
        if not re.match(pattern, v):
            raise ValueError(f"Invalid GitHub PR URL format: {v}")
            
        return v
    
    @field_validator('jira_ticket_id')
    @classmethod
    def validate_jira_ticket_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate Jira ticket ID format if provided."""
        if v is None:
            return v
            
        if not v.strip():
            return None
            
        # Jira ticket pattern: PROJECT-123 (uppercase letters/numbers, dash, numbers)
        pattern = r"^[A-Z]+[A-Z0-9]*-\d+$"
        
        if not re.match(pattern, v):
            raise ValueError(f"Invalid Jira ticket ID format: {v}")
            
        return v
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "github_pr_url": "https://github.com/owner/repo/pull/123",
                "jira_ticket_id": "PROJ-456"
            }
        }


class SummaryRequestWithOptions(SummaryRequest):
    """
    Extended request model with additional options for summary generation.
    
    This model includes optional parameters to customize the summary
    generation process and output format.
    """
    
    focus_areas: Optional[list[str]] = Field(
        None,
        description="Specific areas to focus on in the summary",
        example=["security", "performance", "testing"],
        max_length=10
    )
    
    detail_level: Optional[str] = Field(
        "medium",
        description="Level of detail for the summary",
        pattern="^(low|medium|high)$"
    )
    
    include_code_examples: Optional[bool] = Field(
        False,
        description="Whether to include code examples in the summary"
    )
    
    confluence_page_ids: Optional[list[str]] = Field(
        None,
        description="Optional Confluence page IDs for additional context",
        max_length=5
    )
    
    @field_validator('focus_areas')
    @classmethod
    def validate_focus_areas(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate focus areas list."""
        if v is None:
            return v
            
        if len(v) > 10:
            raise ValueError("Maximum 10 focus areas allowed")
            
        # Validate each focus area
        valid_areas = [
            "security", "performance", "testing", "documentation",
            "architecture", "ui/ux", "database", "api", "integration",
            "deployment", "monitoring", "accessibility"
        ]
        
        for area in v:
            if not isinstance(area, str):
                raise ValueError("Focus areas must be strings")
            if area.lower() not in valid_areas:
                raise ValueError(f"Invalid focus area: {area}")
                
        return [area.lower() for area in v]
    
    @field_validator('confluence_page_ids')
    @classmethod
    def validate_confluence_page_ids(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate Confluence page IDs."""
        if v is None:
            return v
            
        if len(v) > 5:
            raise ValueError("Maximum 5 Confluence page IDs allowed")
            
        for page_id in v:
            if not isinstance(page_id, str):
                raise ValueError("Confluence page IDs must be strings")
            if not page_id.strip():
                raise ValueError("Confluence page IDs cannot be empty")
                
        return v


class BulkSummaryRequest(BaseModel):
    """
    Request model for generating multiple PR summaries in bulk.
    
    This model allows processing multiple PRs in a single request
    for improved efficiency and batch operations.
    """
    
    pr_requests: list[SummaryRequest] = Field(
        ...,
        description="List of PR summary requests to process",
        min_length=1,
        max_length=50
    )
    
    parallel_processing: Optional[bool] = Field(
        True,
        description="Whether to process requests in parallel"
    )
    
    @field_validator('pr_requests')
    @classmethod
    def validate_pr_requests(cls, v: list[SummaryRequest]) -> list[SummaryRequest]:
        """Validate the list of PR requests."""
        if len(v) > 50:
            raise ValueError("Maximum 50 PR requests allowed per bulk operation")
            
        # Check for duplicate GitHub URLs
        urls = [req.github_pr_url for req in v]
        if len(set(urls)) != len(urls):
            raise ValueError("Duplicate GitHub PR URLs not allowed in bulk request")
            
        return v


# Request validation utilities
def validate_request_data(data: dict) -> SummaryRequest:
    """
    Validate raw request data and return a SummaryRequest instance.
    
    Args:
        data: Raw request data dictionary
        
    Returns:
        Validated SummaryRequest instance
        
    Raises:
        ValueError: If validation fails
    """
    try:
        return SummaryRequest(**data)
    except Exception as e:
        raise ValueError(f"Request validation failed: {str(e)}")


def extract_github_info(github_url: str) -> tuple[str, str, int]:
    """
    Extract owner, repository, and PR number from GitHub URL.
    
    Args:
        github_url: GitHub PR URL
        
    Returns:
        Tuple of (owner, repo, pr_number)
        
    Raises:
        ValueError: If URL format is invalid
    """
    pattern = r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)$"
    match = re.match(pattern, github_url)
    
    if not match:
        raise ValueError(f"Invalid GitHub PR URL format: {github_url}")
        
    owner, repo, pr_number = match.groups()
    return owner, repo, int(pr_number)


def normalize_jira_ticket_id(ticket_id: Optional[str]) -> Optional[str]:
    """
    Normalize Jira ticket ID format.
    
    Args:
        ticket_id: Raw Jira ticket ID
        
    Returns:
        Normalized ticket ID or None
    """
    if not ticket_id or not ticket_id.strip():
        return None
        
    # Convert to uppercase and validate format
    normalized = ticket_id.strip().upper()
    
    # Validate format
    pattern = r"^[A-Z]+[A-Z0-9]*-\d+$"
    if not re.match(pattern, normalized):
        raise ValueError(f"Invalid Jira ticket ID format: {ticket_id}")
        
    return normalized