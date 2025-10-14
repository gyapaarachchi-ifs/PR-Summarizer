"""PR Summary API endpoints.

This module provides REST API endpoints for PR summary generation
using GitHub, Jira, and AI services.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import asyncio

from src.models.pr_summary import (
    SummaryRequest, 
    SummaryResponse, 
    SummaryError, 
    PRSummary,
    ProcessingStatus
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["summaries"])


# TDD Implementation with actual service calls
@router.post("/summaries", response_model=Dict[str, Any], status_code=201)
async def create_pr_summary(request_data: Dict[str, Any]):
    """
    Generate a PR summary from GitHub PR URL and optional Jira ticket.
    
    Now implements actual service integration for TDD green phase.
    """
    try:
        logger.info(
            "Creating PR summary",
            extra={
                "github_pr_url": request_data.get("github_pr_url"),
                "jira_ticket_id": request_data.get("jira_ticket_id")
            }
        )
        
        # Validate required fields
        github_pr_url = request_data.get("github_pr_url")
        if not github_pr_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="github_pr_url is required"
            )
        
        # Import and initialize services
        from src.services.github import GitHubService, GitHubValidationError
        from src.services.jira import JiraService, JiraValidationError
        from src.services.gemini import GeminiService
        
        github_service = GitHubService()
        jira_service = JiraService()
        gemini_service = GeminiService()
        
        # Call GitHub service with validation
        try:
            pr_data = await github_service.get_pr_details(github_pr_url)
        except GitHubValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"github_pr_url: {str(e)}"
            )
        
        # Call Jira service if ticket ID provided
        jira_data = None
        jira_ticket_id = request_data.get("jira_ticket_id")
        if jira_ticket_id:
            try:
                jira_data = await jira_service.get_ticket_details(jira_ticket_id)
            except JiraValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"jira_ticket_id: {str(e)}"
                )
        
        # Generate AI summary
        summary = await gemini_service.generate_summary(
            pr_data=pr_data,
            jira_data=jira_data,
            confluence_data=None,
            options={}
        )
        
        # Convert PRSummary to dict response
        response_data = {
            "id": summary.id,
            "github_pr_url": summary.github_pr_url,
            "jira_ticket_id": summary.jira_ticket_id or "",
            "business_context": summary.business_context,
            "code_change_summary": summary.code_change_summary,
            "business_code_impact": summary.business_code_impact,
            "suggested_test_cases": summary.suggested_test_cases,
            "risk_complexity": summary.risk_complexity,
            "reviewer_guidance": summary.reviewer_guidance,
            "status": summary.status.value,
            "created_at": summary.created_at.isoformat(),
            "processing_time_ms": summary.processing_time_ms or 0
        }
        
        logger.info(
            "Successfully created PR summary",
            extra={
                "summary_id": response_data["id"],
                "processing_time": response_data["processing_time_ms"]
            }
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create PR summary",
            extra={
                "error": str(e),
                "github_pr_url": request_data.get("github_pr_url")
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.get("/summaries/{summary_id}", response_model=Dict[str, Any])
async def get_pr_summary(summary_id: str):
    """
    Get an existing PR summary by ID.
    
    Temporary mock implementation for TDD.
    """
    try:
        logger.info(
            "Retrieving PR summary",
            extra={"summary_id": summary_id}
        )
        
        # Mock response - TODO: Replace with actual data retrieval
        mock_response = {
            "id": summary_id,
            "github_pr_url": "https://github.com/owner/repo/pull/123",
            "jira_ticket_id": "PROJ-456",
            "business_context": "User authentication feature for secure access control",
            "code_change_summary": "Added JWT authentication with 8 files modified, 234 lines added",
            "business_code_impact": "Enhances security posture, enables role-based access",
            "suggested_test_cases": [
                "Test successful login with valid credentials",
                "Test failed login with invalid credentials", 
                "Test token expiration and refresh"
            ],
            "risk_complexity": "Medium complexity - new authentication system requires careful testing",
            "reviewer_guidance": "Focus on JWT implementation, security validation, and error handling",
            "status": "completed",
            "created_at": datetime.now().isoformat(),
            "processing_time_ms": 15000
        }
        
        return mock_response
        
    except Exception as e:
        logger.error(
            "Failed to retrieve PR summary",
            extra={
                "error": str(e),
                "summary_id": summary_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve summary: {str(e)}"
        )


@router.get("/summaries", response_model=Dict[str, Any])
async def list_pr_summaries(
    limit: int = 10,
    offset: int = 0,
    status_filter: Optional[str] = None
):
    """
    List PR summaries with pagination.
    
    Temporary mock implementation for TDD.
    """
    try:
        logger.info(
            "Listing PR summaries",
            extra={
                "limit": limit,
                "offset": offset,
                "status_filter": status_filter
            }
        )
        
        # Mock response list - TODO: Replace with actual data query
        mock_summaries = [
            {
                "id": f"summary-{i}",
                "github_pr_url": f"https://github.com/owner/repo/pull/{i}",
                "jira_ticket_id": f"PROJ-{i}",
                "status": "completed",
                "created_at": datetime.now().isoformat(),
                "processing_time_ms": 15000 + (i * 1000)
            }
            for i in range(offset + 1, offset + limit + 1)
        ]
        
        return {
            "summaries": mock_summaries,
            "total": 100,  # Mock total
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(
            "Failed to list PR summaries",
            extra={
                "error": str(e),
                "limit": limit,
                "offset": offset
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list summaries: {str(e)}"
        )