"""
Core summary orchestration service.

This service coordinates the integration of GitHub, Jira, Confluence, and AI services
to generate comprehensive PR summaries with proper error handling and performance tracking.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4

from src.models.context import (
    IntegrationContext, 
    GitHubPRContext, 
    JiraTicketContext,
    SourceMetadata, 
    DataSource,
    create_github_context,
    create_jira_context
)
from src.models.pr_summary import PRSummary, ProcessingStatus
from src.models.request import SummaryRequest, extract_github_info, normalize_jira_ticket_id
from src.services.github import GitHubService, GitHubValidationError
from src.services.jira import JiraService, JiraValidationError
from src.services.gemini import GeminiService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SummaryOrchestrationError(Exception):
    """Base exception for summary orchestration errors."""
    pass


class DataRetrievalError(SummaryOrchestrationError):
    """Exception raised when data retrieval from external services fails."""
    pass


class SummaryGenerationError(SummaryOrchestrationError):
    """Exception raised when AI summary generation fails."""
    pass


class SummaryOrchestrationService:
    """
    Core orchestration service for PR summary generation.
    
    This service coordinates multiple data sources and AI processing
    to create comprehensive, context-rich PR summaries.
    """
    
    def __init__(
        self,
        github_service: Optional[GitHubService] = None,
        jira_service: Optional[JiraService] = None,
        gemini_service: Optional[GeminiService] = None
    ):
        """
        Initialize the orchestration service.
        
        Args:
            github_service: GitHub integration service
            jira_service: Jira integration service  
            gemini_service: AI summary generation service
        """
        self.github_service = github_service or GitHubService()
        self.jira_service = jira_service or JiraService()
        self.gemini_service = gemini_service or GeminiService()
        
        # Performance tracking
        self.performance_metrics = {}
        
    async def generate_summary(
        self, 
        request: SummaryRequest,
        options: Optional[Dict[str, Any]] = None
    ) -> PRSummary:
        """
        Generate a comprehensive PR summary from the given request.
        
        Args:
            request: Summary generation request
            options: Optional configuration parameters
            
        Returns:
            Generated PR summary
            
        Raises:
            SummaryOrchestrationError: If summary generation fails
        """
        start_time = time.time()
        integration_id = str(uuid4())
        
        logger.info(
            "Starting summary generation",
            extra={
                "integration_id": integration_id,
                "github_pr_url": request.github_pr_url,
                "jira_ticket_id": request.jira_ticket_id
            }
        )
        
        try:
            # Step 1: Build integration context
            context = await self._build_integration_context(request, integration_id)
            
            # Step 2: Prepare options with original URL
            enhanced_options = options.copy() if options else {}
            enhanced_options['github_pr_url'] = request.github_pr_url
            
            # Step 3: Generate AI summary using integrated context
            summary = await self._generate_ai_summary(context, enhanced_options)
            
            # Step 3: Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            summary.processing_time_ms = processing_time
            
            logger.info(
                "Summary generation completed successfully",
                extra={
                    "integration_id": integration_id,
                    "summary_id": summary.id,
                    "processing_time_ms": processing_time,
                    "completeness_score": context.completeness_score
                }
            )
            
            return summary
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            
            logger.error(
                "Summary generation failed",
                extra={
                    "integration_id": integration_id,
                    "error": str(e),
                    "processing_time_ms": processing_time
                }
            )
            
            # Re-raise with context
            if isinstance(e, (GitHubValidationError, JiraValidationError)):
                raise e
            elif isinstance(e, SummaryOrchestrationError):
                raise e
            else:
                raise SummaryOrchestrationError(f"Summary generation failed: {str(e)}")
    
    async def _build_integration_context(
        self, 
        request: SummaryRequest, 
        integration_id: str
    ) -> IntegrationContext:
        """
        Build comprehensive integration context from multiple sources.
        
        Args:
            request: Summary request
            integration_id: Unique integration identifier
            
        Returns:
            Integration context with all available data
        """
        logger.info(
            "Building integration context",
            extra={"integration_id": integration_id}
        )
        
        # Prepare data retrieval tasks
        tasks = {}
        
        # Always retrieve GitHub data (required)
        tasks['github'] = self._retrieve_github_data(request.github_pr_url)
        
        # Conditionally retrieve Jira data
        if request.jira_ticket_id:
            normalized_ticket_id = normalize_jira_ticket_id(request.jira_ticket_id)
            if normalized_ticket_id:
                tasks['jira'] = self._retrieve_jira_data(normalized_ticket_id)
        
        # Execute data retrieval tasks concurrently
        results = await self._execute_concurrent_tasks(tasks)
        
        # Build context from results
        context = IntegrationContext(
            integration_id=integration_id,
            github=results['github']['data'],
            jira=results.get('jira', {}).get('data'),
            created_at=datetime.now()
        )
        
        # Calculate data quality scores
        context.completeness_score = context.calculate_completeness_score()
        context.confidence_score = self._calculate_confidence_score(context, results)
        
        logger.info(
            "Integration context built successfully",
            extra={
                "integration_id": integration_id,
                "available_sources": [s.value for s in context.get_available_sources()],
                "completeness_score": context.completeness_score,
                "confidence_score": context.confidence_score
            }
        )
        
        return context
    
    async def _retrieve_github_data(self, github_url: str) -> Dict[str, Any]:
        """Retrieve GitHub PR data with error handling and metadata tracking."""
        start_time = time.time()
        
        try:
            # Validate URL and extract information
            owner, repo, pr_number = extract_github_info(github_url)
            
            logger.debug(
                "Retrieving GitHub data",
                extra={
                    "github_url": github_url,
                    "owner": owner,
                    "repo": repo,
                    "pr_number": pr_number
                }
            )
            
            # Retrieve PR data
            pr_data = await self.github_service.get_pr_details(github_url)
            
            # Create metadata
            response_time = int((time.time() - start_time) * 1000)
            metadata = SourceMetadata(
                source=DataSource.GITHUB,
                retrieved_at=datetime.now(),
                response_time_ms=response_time,
                cache_hit=False  # TODO: Implement caching
            )
            
            # Create structured context
            github_context = create_github_context(pr_data, metadata)
            
            return {
                'success': True,
                'data': github_context,
                'metadata': metadata,
                'response_time_ms': response_time
            }
            
        except GitHubValidationError:
            raise  # Re-raise validation errors as-is
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            
            logger.error(
                "GitHub data retrieval failed",
                extra={
                    "github_url": github_url,
                    "error": str(e),
                    "response_time_ms": response_time
                }
            )
            
            raise DataRetrievalError(f"GitHub data retrieval failed: {str(e)}")
    
    async def _retrieve_jira_data(self, ticket_id: str) -> Dict[str, Any]:
        """Retrieve Jira ticket data with error handling and metadata tracking."""
        start_time = time.time()
        
        try:
            logger.debug(
                "Retrieving Jira data",
                extra={"ticket_id": ticket_id}
            )
            
            # Retrieve ticket data
            ticket_data = await self.jira_service.get_ticket_details(ticket_id)
            
            # Create metadata
            response_time = int((time.time() - start_time) * 1000)
            metadata = SourceMetadata(
                source=DataSource.JIRA,
                retrieved_at=datetime.now(),
                response_time_ms=response_time,
                cache_hit=False  # TODO: Implement caching
            )
            
            # Create structured context
            jira_context = create_jira_context(ticket_data, metadata)
            
            return {
                'success': True,
                'data': jira_context,
                'metadata': metadata,
                'response_time_ms': response_time
            }
            
        except JiraValidationError:
            raise  # Re-raise validation errors as-is
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            
            logger.error(
                "Jira data retrieval failed",
                extra={
                    "ticket_id": ticket_id,
                    "error": str(e),
                    "response_time_ms": response_time
                }
            )
            
            raise DataRetrievalError(f"Jira data retrieval failed: {str(e)}")
    
    async def _execute_concurrent_tasks(
        self, 
        tasks: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Execute multiple data retrieval tasks concurrently with error isolation.
        
        Args:
            tasks: Dictionary of task names to coroutines
            
        Returns:
            Dictionary of results with error handling
        """
        results = {}
        
        # Execute tasks concurrently
        task_results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True
        )
        
        # Process results
        for task_name, result in zip(tasks.keys(), task_results):
            if isinstance(result, Exception):
                # Handle task failure
                if task_name == 'github':
                    # GitHub is required - re-raise the error
                    raise result
                else:
                    # Optional tasks - log error but continue
                    logger.warning(
                        f"{task_name.title()} data retrieval failed",
                        extra={
                            "task": task_name,
                            "error": str(result)
                        }
                    )
                    results[task_name] = {
                        'success': False,
                        'error': str(result)
                    }
            else:
                results[task_name] = result
        
        return results
    
    async def _generate_ai_summary(
        self, 
        context: IntegrationContext, 
        options: Optional[Dict[str, Any]] = None
    ) -> PRSummary:
        """
        Generate AI-powered summary from integration context.
        
        Args:
            context: Integration context with all source data
            options: Optional generation parameters
            
        Returns:
            Generated PR summary
        """
        logger.info(
            "Generating AI summary",
            extra={
                "integration_id": context.integration_id,
                "available_sources": [s.value for s in context.get_available_sources()]
            }
        )
        
        try:
            # Prepare data for AI service
            pr_data = self._prepare_pr_data_for_ai(context.github)
            jira_data = self._prepare_jira_data_for_ai(context.jira) if context.jira else None
            confluence_data = None  # TODO: Implement Confluence integration
            
            # Generate summary using AI service
            summary = await self.gemini_service.generate_summary(
                pr_data=pr_data,
                jira_data=jira_data,
                confluence_data=confluence_data,
                options=options
            )
            
            logger.info(
                "AI summary generated successfully",
                extra={
                    "integration_id": context.integration_id,
                    "summary_id": summary.id
                }
            )
            
            return summary
            
        except Exception as e:
            logger.error(
                "AI summary generation failed",
                extra={
                    "integration_id": context.integration_id,
                    "error": str(e)
                }
            )
            
            raise SummaryGenerationError(f"AI summary generation failed: {str(e)}")
    
    def _prepare_pr_data_for_ai(self, github_context: GitHubPRContext) -> Dict[str, Any]:
        """Convert GitHubPRContext to format expected by AI service."""
        return {
            "number": github_context.pr_number,
            "title": github_context.title,
            "body": github_context.description or "",
            "state": github_context.state,
            "user": {"login": github_context.author},
            "additions": github_context.additions,
            "deletions": github_context.deletions,
            "changed_files": github_context.file_changes,  # Use detailed file changes
            "commits": github_context.commit_details,    # Use detailed commit info
            "html_url": github_context.html_url,
            "created_at": github_context.created_at.isoformat(),
            "head": {"ref": github_context.head_branch},
            "base": {"ref": github_context.base_branch},
            "labels": github_context.labels,
            "comments": github_context.comments,
            "review_comments": github_context.review_comments
        }
    
    def _prepare_jira_data_for_ai(self, jira_context: JiraTicketContext) -> Dict[str, Any]:
        """Convert JiraTicketContext to format expected by AI service."""
        return {
            "key": jira_context.key,
            "summary": jira_context.summary,
            "description": jira_context.description or "",
            "status": jira_context.status,
            "priority": jira_context.priority,
            "issue_type": jira_context.issue_type,
            "project": {
                "key": jira_context.project_key,
                "name": jira_context.project_name
            },
            "components": jira_context.components,
            "labels": jira_context.labels,
            "assignee": jira_context.assignee,
            "reporter": jira_context.reporter
        }
    
    def _calculate_confidence_score(
        self, 
        context: IntegrationContext, 
        results: Dict[str, Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence score based on data quality and retrieval success.
        
        Args:
            context: Integration context
            results: Data retrieval results
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.5
        
        # GitHub data quality
        github_result = results.get('github', {})
        if github_result.get('success', False):
            base_confidence += 0.3
            
            # Bonus for rich PR data
            if context.github.description and len(context.github.description) > 100:
                base_confidence += 0.1
            if context.github.review_comments > 0:
                base_confidence += 0.1
        
        # Jira data quality
        jira_result = results.get('jira', {})
        if jira_result.get('success', False):
            base_confidence += 0.2
        
        # Response time penalty
        total_response_time = sum(
            result.get('response_time_ms', 0) 
            for result in results.values() 
            if result.get('success', False)
        )
        if total_response_time > 5000:  # 5 seconds
            base_confidence -= 0.1
        
        return max(0.0, min(1.0, base_confidence))
    
    async def get_summary_status(self, summary_id: str) -> Dict[str, Any]:
        """
        Get the status of a summary generation process.
        
        Args:
            summary_id: Summary identifier
            
        Returns:
            Status information
        """
        # TODO: Implement status tracking with database
        return {
            "id": summary_id,
            "status": ProcessingStatus.COMPLETED,
            "progress": 100,
            "message": "Summary generation completed"
        }
    
    async def cancel_summary_generation(self, summary_id: str) -> bool:
        """
        Cancel an in-progress summary generation.
        
        Args:
            summary_id: Summary identifier
            
        Returns:
            True if cancellation was successful
        """
        # TODO: Implement cancellation logic
        logger.info(
            "Summary generation cancellation requested",
            extra={"summary_id": summary_id}
        )
        return True
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the orchestration service."""
        return {
            "total_summaries_generated": len(self.performance_metrics),
            "average_processing_time_ms": sum(
                metrics.get("processing_time_ms", 0) 
                for metrics in self.performance_metrics.values()
            ) / max(len(self.performance_metrics), 1),
            "success_rate": sum(
                1 for metrics in self.performance_metrics.values() 
                if metrics.get("success", False)
            ) / max(len(self.performance_metrics), 1)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all dependent services.
        
        Returns:
            Health status of all services
        """
        try:
            # Check GitHub service
            github_healthy = await self._check_github_health()
            
            # Check Jira service  
            jira_healthy = await self._check_jira_health()
            
            # Check Gemini service
            gemini_healthy = await self._check_gemini_health()
            
            overall_healthy = github_healthy and jira_healthy and gemini_healthy
            
            return {
                "overall": "healthy" if overall_healthy else "unhealthy",
                "services": {
                    "github": "healthy" if github_healthy else "unhealthy",
                    "jira": "healthy" if jira_healthy else "unhealthy",
                    "gemini": "healthy" if gemini_healthy else "unhealthy"
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "overall": "unhealthy",
                "error": str(e),
                "services": {
                    "github": "unknown",
                    "jira": "unknown", 
                    "gemini": "unknown"
                }
            }
    
    async def _check_github_health(self) -> bool:
        """Check GitHub service health."""
        try:
            # Simple health check - verify service is initialized
            return self.github_service is not None
        except Exception:
            return False
    
    async def _check_jira_health(self) -> bool:
        """Check Jira service health."""
        try:
            # Simple health check - verify service is initialized
            return self.jira_service is not None
        except Exception:
            return False
    
    async def _check_gemini_health(self) -> bool:
        """Check Gemini service health."""
        try:
            # Simple health check - verify service is initialized
            return self.gemini_service is not None
        except Exception:
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics for monitoring.
        
        Returns:
            Service metrics data
        """
        return {
            "performance": self.get_performance_metrics(),
            "health": {
                "service_initialized": True,
                "dependencies_count": 3,
                "uptime_seconds": time.time() - getattr(self, '_start_time', time.time())
            }
        }