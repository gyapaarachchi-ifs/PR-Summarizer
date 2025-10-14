"""PR Summary data models.

This module defines the core data models for PR summary functionality,
including request/response models, summary sections, and processing status.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class ProcessingStatus(str, Enum):
    """Processing status for PR summary generation."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SummarySection(BaseModel):
    """A section within a PR summary."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Code Changes",
                "content": "This PR introduces new authentication middleware...",
                "priority": "high",
                "source": "github",
                "metadata": {"file_count": 5, "lines_changed": 120}
            }
        }
    )
    
    title: str = Field(
        ...,
        description="Section title",
        min_length=1,
        max_length=200
    )
    content: str = Field(
        ...,
        description="Section content",
        min_length=1
    )
    priority: str = Field(
        default="medium",
        description="Section priority (high, medium, low)",
        pattern="^(high|medium|low)$"
    )
    source: str = Field(
        ...,
        description="Data source for this section (github, jira, confluence, etc.)",
        min_length=1,
        max_length=50
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the section"
    )


class PRSummary(BaseModel):
    """Complete PR summary matching test expectations."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "summary-123",
                "request_id": "req-456",
                "github_pr_url": "https://github.com/owner/repo/pull/123",
                "jira_ticket_id": "PROJ-456",
                "business_context": "User authentication feature for secure access control",
                "code_change_summary": "Added JWT authentication with 8 files modified, 234 lines added",
                "business_code_impact": "Enhances security posture, enables role-based access",
                "suggested_test_cases": ["Test successful login", "Test failed login"],
                "risk_complexity": "Medium complexity - requires careful testing",
                "reviewer_guidance": "Focus on JWT implementation and security validation",
                "status": "completed",
                "created_at": "2024-01-15T10:30:00Z",
                "processing_time_ms": 15000
            }
        }
    )
    
    # Core identifiers
    id: str = Field(
        ...,
        description="Unique identifier for the summary"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request identifier that initiated this summary"
    )
    
    # Source information
    github_pr_url: str = Field(
        ...,
        description="GitHub PR URL",
        pattern=r"^https://github\.com/[^/]+/[^/]+/pull/\d+$"
    )
    jira_ticket_id: Optional[str] = Field(
        default=None,
        description="Associated Jira ticket ID"
    )
    
    # Summary content (the six required sections)
    business_context: str = Field(
        ...,
        description="Business context and purpose of the PR",
        min_length=1
    )
    code_change_summary: str = Field(
        ...,
        description="Technical summary of code changes",
        min_length=1
    )
    business_code_impact: str = Field(
        ...,
        description="Impact of code changes on business goals",
        min_length=1
    )
    suggested_test_cases: List[str] = Field(
        default_factory=list,
        description="Suggested test cases for the changes"
    )
    risk_complexity: str = Field(
        ...,
        description="Assessment of risk and complexity",
        min_length=1
    )
    reviewer_guidance: str = Field(
        ...,
        description="Guidance for code reviewers",
        min_length=1
    )
    
    # Processing metadata
    status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        description="Processing status"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp"
    )
    processing_time_ms: Optional[int] = Field(
        default=None,
        description="Time taken to process in milliseconds",
        ge=0
    )
    
    def update_status(self, status: ProcessingStatus) -> None:
        """Update the processing status."""
        self.status = status
    
    def complete_processing(self, processing_time_ms: int) -> None:
        """Mark processing as completed with timing."""
        self.status = ProcessingStatus.COMPLETED
        self.processing_time_ms = processing_time_ms


class SummaryRequest(BaseModel):
    """Request to generate a PR summary."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pr_url": "https://github.com/owner/repo/pull/123",
                "include_jira": True,
                "include_confluence": False,
                "priority": "high",
                "options": {
                    "max_sections": 10,
                    "include_code_diff": True,
                    "ai_model": "gemini-pro"
                }
            }
        }
    )
    
    pr_url: str = Field(
        ...,
        description="GitHub PR URL to summarize",
        pattern=r"^https://github\.com/[^/]+/[^/]+/pull/\d+$"
    )
    include_jira: bool = Field(
        default=True,
        description="Include related Jira ticket information"
    )
    include_confluence: bool = Field(
        default=False,
        description="Include related Confluence documentation"
    )
    priority: str = Field(
        default="medium",
        description="Processing priority (high, medium, low)",
        pattern="^(high|medium|low)$"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional processing options"
    )
    
    def get_pr_number(self) -> int:
        """Extract PR number from URL."""
        return int(self.pr_url.split("/")[-1])
    
    def get_repo_info(self) -> tuple[str, str]:
        """Extract owner and repo name from URL."""
        parts = self.pr_url.replace("https://github.com/", "").split("/")
        return parts[0], parts[1]


class SummaryResponse(BaseModel):
    """Response for PR summary requests."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "summary": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "pr_url": "https://github.com/owner/repo/pull/123",
                    "title": "Add authentication middleware",
                    "summary": "This PR introduces new authentication middleware...",
                    "sections": [],
                    "status": "completed"
                },
                "message": "Summary generated successfully",
                "processing_time_seconds": 25.5
            }
        }
    )
    
    summary: PRSummary = Field(
        ...,
        description="Generated PR summary"
    )
    message: str = Field(
        default="Summary generated successfully",
        description="Response message"
    )
    processing_time_seconds: Optional[float] = Field(
        default=None,
        description="Processing time",
        ge=0
    )


class SummaryError(BaseModel):
    """Error response for PR summary requests."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "PR not found",
                "details": "GitHub API returned 404 for the specified PR URL",
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )
    
    error: str = Field(
        ...,
        description="Error message",
        min_length=1
    )
    details: Optional[str] = Field(
        default=None,
        description="Detailed error information"
    )
    request_id: Optional[UUID] = Field(
        default=None,
        description="Request identifier for tracking"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )