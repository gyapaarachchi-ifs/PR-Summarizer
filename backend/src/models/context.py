"""
Integration context models for PR summary generation.

This module defines the context models that aggregate data from multiple
sources (GitHub, Jira, Confluence) for comprehensive PR summarization.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class DataSource(str, Enum):
    """Available data sources for PR summary integration."""
    
    GITHUB = "github"
    JIRA = "jira"
    CONFLUENCE = "confluence"
    GOOGLE_DOCS = "google_docs"
    AZURE_DEVOPS = "azure_devops"


class SourceMetadata(BaseModel):
    """Metadata about a data source."""
    
    source: DataSource = Field(..., description="The data source type")
    retrieved_at: datetime = Field(default_factory=datetime.now)
    api_version: Optional[str] = Field(None, description="API version used")
    rate_limit_remaining: Optional[int] = Field(None, description="Remaining API calls")
    cache_hit: bool = Field(False, description="Whether data came from cache")
    response_time_ms: Optional[int] = Field(None, description="API response time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "github",
                "retrieved_at": "2025-01-15T10:30:00Z",
                "api_version": "2022-11-28",
                "rate_limit_remaining": 4500,
                "cache_hit": False,
                "response_time_ms": 850
            }
        }


class GitHubPRContext(BaseModel):
    """GitHub PR context data."""
    
    # Basic PR information
    pr_number: int = Field(..., description="Pull request number")
    title: str = Field(..., description="PR title")
    description: Optional[str] = Field(None, description="PR body/description")
    author: str = Field(..., description="PR author username")
    
    # PR state
    state: str = Field(..., description="PR state (open, closed, merged)")
    draft: bool = Field(False, description="Whether PR is in draft state")
    mergeable: Optional[bool] = Field(None, description="Whether PR is mergeable")
    merged: bool = Field(False, description="Whether PR has been merged")
    
    # Branch information
    head_branch: str = Field(..., description="Source branch name")
    base_branch: str = Field(..., description="Target branch name")
    head_sha: str = Field(..., description="Head commit SHA")
    base_sha: str = Field(..., description="Base commit SHA")
    
    # Code statistics
    additions: int = Field(0, description="Lines added")
    deletions: int = Field(0, description="Lines deleted")
    changed_files: int = Field(0, description="Number of files changed")
    commits: int = Field(0, description="Number of commits")
    
    # File details for AI analysis
    file_changes: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed file changes")
    commit_details: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed commit information")
    
    # Review information
    review_comments: int = Field(0, description="Number of review comments")
    comments: int = Field(0, description="Number of general comments")
    requested_reviewers: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)
    
    # Labels and metadata
    labels: List[str] = Field(default_factory=list)
    milestone: Optional[str] = Field(None, description="Milestone name")
    
    # URLs
    html_url: str = Field(..., description="Web URL to the PR")
    diff_url: str = Field(..., description="URL to diff view")
    
    # Timestamps
    created_at: datetime = Field(..., description="PR creation time")
    updated_at: datetime = Field(..., description="Last update time")
    closed_at: Optional[datetime] = Field(None, description="PR close time")
    merged_at: Optional[datetime] = Field(None, description="PR merge time")
    
    # File changes (summary)
    modified_files: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Summary of modified files with change statistics"
    )
    
    # Source metadata
    metadata: SourceMetadata = Field(..., description="Source retrieval metadata")
    
    @field_validator('state')
    @classmethod
    def validate_state(cls, v: str) -> str:
        """Validate PR state."""
        valid_states = ['open', 'closed', 'merged']
        if v.lower() not in valid_states:
            raise ValueError(f"Invalid PR state: {v}")
        return v.lower()


class JiraTicketContext(BaseModel):
    """Jira ticket context data."""
    
    # Basic ticket information
    key: str = Field(..., description="Jira ticket key (e.g., PROJ-123)")
    summary: str = Field(..., description="Ticket summary/title")
    description: Optional[str] = Field(None, description="Ticket description")
    
    # Status and workflow
    status: str = Field(..., description="Current ticket status")
    status_category: Optional[str] = Field(None, description="Status category (To Do, In Progress, Done)")
    resolution: Optional[str] = Field(None, description="Ticket resolution")
    
    # Classification
    issue_type: str = Field(..., description="Issue type (Story, Bug, Task, etc.)")
    priority: str = Field(..., description="Ticket priority")
    severity: Optional[str] = Field(None, description="Bug severity if applicable")
    
    # Assignment
    assignee: Optional[Dict[str, str]] = Field(None, description="Assigned user info")
    reporter: Optional[Dict[str, str]] = Field(None, description="Reporter user info")
    
    # Project context
    project_key: str = Field(..., description="Project key")
    project_name: str = Field(..., description="Project name")
    
    # Components and labels
    components: List[str] = Field(default_factory=list, description="Ticket components")
    labels: List[str] = Field(default_factory=list, description="Ticket labels")
    fix_versions: List[str] = Field(default_factory=list, description="Fix versions")
    
    # Timestamps
    created_at: datetime = Field(..., description="Ticket creation time")
    updated_at: datetime = Field(..., description="Last update time")
    resolved_at: Optional[datetime] = Field(None, description="Resolution time")
    
    # Custom fields (common ones)
    story_points: Optional[int] = Field(None, description="Story points if applicable")
    epic_link: Optional[str] = Field(None, description="Epic link if applicable")
    sprint: Optional[str] = Field(None, description="Current sprint")
    
    # Source metadata
    metadata: SourceMetadata = Field(..., description="Source retrieval metadata")


class ConfluencePageContext(BaseModel):
    """Confluence page context data."""
    
    # Basic page information
    page_id: str = Field(..., description="Confluence page ID")
    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Page content (text/markdown)")
    
    # Page hierarchy
    space_key: str = Field(..., description="Confluence space key")
    space_name: str = Field(..., description="Confluence space name")
    parent_page_id: Optional[str] = Field(None, description="Parent page ID")
    
    # Metadata
    page_url: str = Field(..., description="Web URL to the page")
    version: int = Field(..., description="Page version number")
    
    # Timestamps
    created_at: datetime = Field(..., description="Page creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    # Author information
    author: Dict[str, str] = Field(..., description="Page author info")
    last_modified_by: Dict[str, str] = Field(..., description="Last modifier info")
    
    # Content metadata
    word_count: Optional[int] = Field(None, description="Approximate word count")
    content_type: str = Field("page", description="Content type")
    
    # Labels and categorization
    labels: List[str] = Field(default_factory=list, description="Page labels")
    
    # Source metadata
    metadata: SourceMetadata = Field(..., description="Source retrieval metadata")


class IntegrationContext(BaseModel):
    """
    Comprehensive context aggregating data from all integrated sources.
    
    This model serves as the central data structure for PR summary generation,
    combining information from GitHub, Jira, Confluence, and other sources.
    """
    
    # Core PR context (always required)
    github: GitHubPRContext = Field(..., description="GitHub PR data")
    
    # Optional additional contexts
    jira: Optional[JiraTicketContext] = Field(None, description="Jira ticket data")
    confluence_pages: List[ConfluencePageContext] = Field(
        default_factory=list,
        description="Related Confluence pages"
    )
    
    # Integration metadata
    integration_id: str = Field(..., description="Unique integration identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Data quality metrics
    completeness_score: float = Field(
        0.0,
        description="Data completeness score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    confidence_score: float = Field(
        0.0,
        description="Data confidence score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    # Processing hints
    focus_areas: List[str] = Field(
        default_factory=list,
        description="Areas to focus on during summary generation"
    )
    excluded_sections: List[str] = Field(
        default_factory=list,
        description="Sections to exclude from summary"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "integration_id": "int-abc123",
                "github": {
                    "pr_number": 123,
                    "title": "Add user authentication",
                    "author": "developer123",
                    "state": "open",
                    "additions": 234,
                    "deletions": 56
                },
                "jira": {
                    "key": "PROJ-456",
                    "summary": "Implement authentication system",
                    "status": "In Progress",
                    "issue_type": "Story"
                },
                "completeness_score": 0.85,
                "confidence_score": 0.92
            }
        }
    
    def get_available_sources(self) -> List[DataSource]:
        """Get list of available data sources in this context."""
        sources = [DataSource.GITHUB]  # GitHub is always available
        
        if self.jira is not None:
            sources.append(DataSource.JIRA)
            
        if self.confluence_pages:
            sources.append(DataSource.CONFLUENCE)
            
        return sources
    
    def calculate_completeness_score(self) -> float:
        """Calculate data completeness score based on available information."""
        score = 0.3  # Base score for GitHub data
        
        # Add points for optional data
        if self.jira is not None:
            score += 0.4
            
        if self.confluence_pages:
            score += 0.2
            
        # Add points for rich GitHub data
        if self.github.description and len(self.github.description) > 50:
            score += 0.1
            
        return min(score, 1.0)
    
    def get_business_context_sources(self) -> List[str]:
        """Get sources that provide business context."""
        sources = []
        
        if self.jira is not None:
            sources.append(f"Jira ticket {self.jira.key}")
            
        if self.confluence_pages:
            for page in self.confluence_pages:
                sources.append(f"Confluence page: {page.title}")
                
        return sources
    
    def get_technical_context_summary(self) -> Dict[str, Any]:
        """Get summary of technical context from GitHub."""
        return {
            "files_changed": self.github.changed_files,
            "lines_added": self.github.additions,
            "lines_deleted": self.github.deletions,
            "commits": self.github.commits,
            "branch": f"{self.github.head_branch} -> {self.github.base_branch}",
            "review_activity": {
                "comments": self.github.comments,
                "review_comments": self.github.review_comments,
                "requested_reviewers": len(self.github.requested_reviewers)
            }
        }


# Context building utilities
def create_github_context(pr_data: Dict[str, Any], metadata: SourceMetadata) -> GitHubPRContext:
    """
    Create GitHubPRContext from raw PR data.
    
    Args:
        pr_data: Raw GitHub PR data
        metadata: Source metadata
        
    Returns:
        GitHubPRContext instance
    """
    return GitHubPRContext(
        pr_number=pr_data["number"],
        title=pr_data["title"],
        description=pr_data.get("body"),
        author=pr_data["author"],  # Use processed field instead of raw API
        state=pr_data["state"],
        draft=pr_data.get("draft", False),
        mergeable=pr_data.get("mergeable"),
        merged=pr_data.get("merged", False),
        head_branch=pr_data["head_branch"],  # Use processed field
        base_branch=pr_data["base_branch"],  # Use processed field
        head_sha=pr_data.get("head_sha"),
        base_sha=pr_data.get("base_sha"),
        additions=pr_data.get("additions", 0),
        deletions=pr_data.get("deletions", 0),
        changed_files=pr_data.get("files_changed", 0),  # This should be the count
        commits=len(pr_data.get("commits", [])),  # Count of commits array
        file_changes=pr_data.get("changed_files", []),  # Detailed file changes
        commit_details=pr_data.get("commits", []),  # Detailed commit info
        review_comments=pr_data.get("review_comments", 0),
        comments=pr_data.get("comments", 0),
        labels=[label["name"] for label in pr_data.get("labels", [])],
        html_url=pr_data["html_url"],
        diff_url=pr_data.get("diff_url", f"{pr_data['html_url']}.diff"),
        created_at=datetime.fromisoformat(pr_data["created_at"].replace("Z", "+00:00")),
        updated_at=datetime.fromisoformat(pr_data["updated_at"].replace("Z", "+00:00")),
        metadata=metadata
    )


def create_jira_context(ticket_data: Dict[str, Any], metadata: SourceMetadata) -> JiraTicketContext:
    """
    Create JiraTicketContext from raw ticket data.
    
    Args:
        ticket_data: Raw Jira ticket data
        metadata: Source metadata
        
    Returns:
        JiraTicketContext instance
    """
    fields = ticket_data.get("fields", {})
    
    return JiraTicketContext(
        key=ticket_data["key"],
        summary=fields.get("summary", ""),
        description=fields.get("description", ""),
        status=fields.get("status", {}).get("name", "Unknown"),
        issue_type=fields.get("issuetype", {}).get("name", "Unknown"),
        priority=fields.get("priority", {}).get("name", "Unknown"),
        project_key=fields.get("project", {}).get("key", ""),
        project_name=fields.get("project", {}).get("name", ""),
        components=[comp.get("name", "") for comp in fields.get("components", [])],
        labels=fields.get("labels", []),
        created_at=datetime.fromisoformat(fields["created"].replace("Z", "+00:00")) if fields.get("created") else datetime.now(),
        updated_at=datetime.fromisoformat(fields["updated"].replace("Z", "+00:00")) if fields.get("updated") else datetime.now(),
        metadata=metadata
    )