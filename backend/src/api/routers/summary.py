"""
Summary API router for PR Summarizer application.
Task: T033 - Implement summary API endpoints

This module provides RESTful endpoints for generating PR summaries
with proper error handling, validation, and response formatting.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from src.models.request import SummaryRequest
from src.models.pr_summary import PRSummary, ProcessingStatus
from src.services.summary_service import SummaryOrchestrationService
from src.services.github import GitHubService
from src.services.jira import JiraService
from src.services.gemini import GeminiService

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/summary",
    tags=["summary"],
    responses={404: {"description": "Not found"}},
)

# Global service instance (in production, use dependency injection)
summary_service = None

def get_summary_service() -> SummaryOrchestrationService:
    """Dependency injection for summary service."""
    global summary_service
    if summary_service is None:
        try:
            github_service = GitHubService()
            jira_service = JiraService()
            gemini_service = GeminiService()
            summary_service = SummaryOrchestrationService(
                github_service=github_service,
                jira_service=jira_service,
                gemini_service=gemini_service
            )
        except Exception as e:
            logger.error(f"Failed to initialize summary service: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Service Configuration Error",
                    "message": f"Failed to initialize services: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    return summary_service

@router.post(
    "/generate",
    response_model=PRSummary,
    status_code=200,
    summary="Generate PR Summary",
    description="Generate a comprehensive summary for a pull request with optional Jira integration"
)
async def generate_summary(
    request: SummaryRequest,
    summary_service: SummaryOrchestrationService = Depends(get_summary_service)
) -> PRSummary:
    """
    Generate a comprehensive PR summary.
    
    Args:
        request: Summary request containing GitHub PR URL and optional Jira ticket
        summary_service: Injected summary orchestration service
        
    Returns:
        PRSummary: Generated summary with status and metadata
        
    Raises:
        HTTPException: For validation errors or service failures
    """
    try:
        logger.info(f"Generating summary for PR: {request.github_pr_url}")
        
        # Generate summary using orchestration service
        summary = await summary_service.generate_summary(request)
        
        logger.info(f"Summary generated successfully for PR: {request.github_pr_url}")
        return summary
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Validation Error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except ConnectionError as e:
        logger.error(f"Service connection error: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail={
                "error": "Service Unavailable",
                "message": "Unable to connect to external services",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except TimeoutError as e:
        logger.error(f"Service timeout: {str(e)}")
        raise HTTPException(
            status_code=504,
            detail={
                "error": "Request Timeout",
                "message": "Summary generation timed out",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.post(
    "/generate-async",
    response_model=Dict[str, str],
    status_code=202,
    summary="Generate PR Summary Asynchronously",
    description="Start asynchronous PR summary generation and return task ID"
)
async def generate_summary_async(
    request: SummaryRequest,
    background_tasks: BackgroundTasks,
    summary_service: SummaryOrchestrationService = Depends(get_summary_service)
) -> Dict[str, str]:
    """
    Start asynchronous PR summary generation.
    
    Args:
        request: Summary request containing GitHub PR URL and optional Jira ticket
        background_tasks: FastAPI background tasks
        summary_service: Injected summary orchestration service
        
    Returns:
        Dict with task_id for checking status later
        
    Raises:
        HTTPException: For validation errors
    """
    try:
        # Generate unique task ID
        task_id = f"summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(request.github_pr_url) % 10000}"
        
        # Add task to background processing
        background_tasks.add_task(
            _process_summary_async,
            task_id,
            request,
            summary_service
        )
        
        logger.info(f"Started async summary generation with task ID: {task_id}")
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Summary generation started"
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Validation Error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

async def _process_summary_async(
    task_id: str,
    request: SummaryRequest,
    summary_service: SummaryOrchestrationService
) -> None:
    """
    Process summary generation in background.
    
    Args:
        task_id: Unique task identifier
        request: Summary request
        summary_service: Summary orchestration service
    """
    try:
        logger.info(f"Processing async task: {task_id}")
        
        summary = await summary_service.generate_summary(request)
        
        # In production, store result in cache/database for retrieval
        logger.info(f"Async task completed: {task_id}")
        
    except Exception as e:
        logger.error(f"Async task failed {task_id}: {str(e)}")

@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Health Check",
    description="Check the health status of summary service and dependencies"
)
async def health_check(
    summary_service: SummaryOrchestrationService = Depends(get_summary_service)
) -> Dict[str, Any]:
    """
    Perform health check on summary service and dependencies.
    
    Args:
        summary_service: Injected summary orchestration service
        
    Returns:
        Health status information
    """
    try:
        # Check service health
        health_status = await summary_service.health_check()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": health_status,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "version": "1.0.0"
        }

@router.get(
    "/metrics",
    response_model=Dict[str, Any],
    summary="Service Metrics",
    description="Get performance metrics for summary service"
)
async def get_metrics(
    summary_service: SummaryOrchestrationService = Depends(get_summary_service)
) -> Dict[str, Any]:
    """
    Get service performance metrics.
    
    Args:
        summary_service: Injected summary orchestration service
        
    Returns:
        Performance metrics data
    """
    try:
        metrics = summary_service.get_metrics()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "status": "active"
        }
        
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Metrics Unavailable",
                "message": "Unable to retrieve service metrics",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Note: Exception handlers are registered on the main FastAPI app instance
# Router-level exception handlers are handled in the endpoint functions directly