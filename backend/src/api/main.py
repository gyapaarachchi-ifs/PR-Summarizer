"""Main FastAPI application for PR Summarizer.

This module sets up the FastAPI application with all middleware,
error handlers, and route registrations.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from starlette.responses import Response


from src.models.config import get_config
from src.models.error_responses import (
    create_error_response,
    create_validation_error_response,
    ValidationErrorResponse,
    InternalServerErrorResponse,
)
from src.utils.exceptions import PRSummarizerError
from src.utils.logger import configure_logging, get_logger, LogLevel
from src.utils.health import get_health_check


# Global logger instance
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager for startup and shutdown events.
    
    Handles initialization and cleanup of resources like database connections,
    external service clients, and background tasks.
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None during application runtime
    """
    # Startup events
    logger.info("Starting PR Summarizer application")
    
    try:
        # Load configuration
        config = get_config()
        logger.info("Configuration loaded successfully", extra={
            "environment": config.environment,
            "debug": config.debug,
            "host": config.host,
            "port": config.port
        })
        
        # Initialize external service clients
        # TODO: Initialize GitHub client, Gemini client, etc.
        logger.info("External service clients initialized")
        
        # Initialize database connection
        # TODO: Set up database connection pool if enabled
        if config.database:
            logger.info("Database connection initialized")
        
        # Initialize cache connection
        # TODO: Set up Redis connection if enabled
        if config.redis:
            logger.info("Cache connection initialized")
        
        logger.info("Application startup completed successfully")
        
        yield  # Application runtime
        
    except Exception as e:
        logger.error("Application startup failed", extra={
            "error": str(e),
            "type": type(e).__name__
        })
        raise
    
    finally:
        # Shutdown events
        logger.info("Shutting down PR Summarizer application")
        
        try:
            # Close database connections
            # TODO: Clean up database connection pool
            logger.info("Database connections closed")
            
            # Close cache connections
            # TODO: Clean up Redis connection pool
            logger.info("Cache connections closed")
            
            # Close external service clients
            # TODO: Clean up HTTP clients
            logger.info("External service clients closed")
            
            logger.info("Application shutdown completed successfully")
            
        except Exception as e:
            logger.error("Error during application shutdown", extra={
                "error": str(e),
                "type": type(e).__name__
            })


def create_application() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    # Load configuration
    config = get_config()
    
    # Configure logging
    configure_logging(
        level=LogLevel(config.logging.level),
        json_format=config.logging.json_format,
        enable_correlation_id=config.logging.enable_correlation_id
    )
    
    # Create FastAPI application
    app = FastAPI(
        title="PR Summarizer API",
        description="AI-powered pull request analysis and summarization service",
        version="1.0.0",
        docs_url="/docs" if config.debug else None,
        redoc_url="/redoc" if config.debug else None,
        openapi_url="/openapi.json" if config.debug else None,
        lifespan=lifespan,
    )
    
    # Register middleware
    register_cors_middleware(app)
    register_logging_middleware(app)
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Register routes
    register_routes(app)
    
    logger.info("FastAPI application created successfully", extra={
        "title": app.title,
        "version": app.version,
        "debug": config.debug
    })
    
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers for the application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(PRSummarizerError)
    async def pr_summarizer_exception_handler(
        request: Request,
        exc: PRSummarizerError
    ) -> JSONResponse:
        """Handle custom PRSummarizerError exceptions.
        
        Args:
            request: HTTP request that caused the exception
            exc: The PRSummarizerError that was raised
            
        Returns:
            JSON response with error details
        """
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        error_response = create_error_response(
            exc,
            correlation_id=correlation_id,
            path=str(request.url.path),
            method=request.method,
            include_debug=get_config().debug
        )
        
        logger.error("PRSummarizerError occurred", extra={
            "error_code": error_response.error_code,
            "message": error_response.message,
            "path": error_response.path,
            "method": error_response.method,
            "correlation_id": error_response.correlation_id,
            "details": error_response.details
        })
        
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.model_dump(mode='json')
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors.
        
        Args:
            request: HTTP request that caused the validation error
            exc: The validation error that was raised
            
        Returns:
            JSON response with validation error details
        """
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        # Convert Pydantic errors to our format
        errors = []
        for error in exc.errors():
            field_path = '.'.join(str(loc) for loc in error['loc'])
            errors.append({
                'field': field_path,
                'message': error['msg'],
                'code': error['type'],
                'value': error.get('input')
            })
        
        error_response = create_validation_error_response(
            errors,
            correlation_id=correlation_id,
            path=str(request.url.path),
            method=request.method
        )
        
        logger.warning("Validation error occurred", extra={
            "path": error_response.path,
            "method": error_response.method,
            "correlation_id": error_response.correlation_id,
            "error_count": len(errors),
            "errors": errors
        })
        
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.model_dump(mode='json')
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler_override(
        request: Request,
        exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions with consistent error format.
        
        Args:
            request: HTTP request that caused the exception
            exc: The HTTP exception that was raised
            
        Returns:
            JSON response with error details
        """
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        # For standard HTTP errors, use FastAPI's default handler
        # but log the error for monitoring
        logger.warning("HTTP exception occurred", extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url.path),
            "method": request.method,
            "correlation_id": correlation_id
        })
        
        # Call FastAPI's default handler
        return await http_exception_handler(request, exc)
    
    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request,
        exc: ValueError
    ) -> JSONResponse:
        """Handle ValueError exceptions.
        
        Args:
            request: HTTP request that caused the exception
            exc: The ValueError that was raised
            
        Returns:
            JSON response with internal server error
        """
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        error_response = create_error_response(
            exc,
            correlation_id=correlation_id,
            path=str(request.url.path),
            method=request.method,
            include_debug=get_config().debug
        )
        
        logger.error("Unexpected exception occurred", extra={
            "error": str(exc),
            "type": type(exc).__name__,
            "path": error_response.path,
            "method": error_response.method,
            "correlation_id": error_response.correlation_id
        }, exc_info=True)
        
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.model_dump(mode='json')
        )


def register_cors_middleware(app: FastAPI) -> None:
    """Register CORS middleware for the application.
    
    Args:
        app: FastAPI application instance
    """
    config = get_config()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.security.cors_origins,
        allow_credentials=config.security.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
        max_age=3600,  # 1 hour preflight cache
    )
    
    logger.info("CORS middleware registered", extra={
        "allowed_origins": config.security.cors_origins,
        "allow_credentials": config.security.cors_allow_credentials,
        "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    })


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses with correlation IDs."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process HTTP request and response with logging.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response
        """
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Start timing
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = str(request.url.path)
        query_params = dict(request.query_params) if request.query_params else None
        user_agent = request.headers.get("user-agent")
        client_ip = request.client.host if request.client else None
        
        # Log request
        from src.utils.logger import log_api_request
        log_api_request(
            method=method,
            path=path,
            request_id=correlation_id,
            query_params=query_params,
            user_agent=user_agent,
            client_ip=client_ip
        )
        
        # Process request and handle exceptions
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            # Get response size if available
            response_size = None
            if hasattr(response, 'body') and response.body:
                response_size = len(response.body)
            
            # Log successful response
            from src.utils.logger import log_api_response
            log_api_response(
                status_code=response.status_code,
                path=path,
                duration_ms=duration_ms,
                request_id=correlation_id,
                response_size=response_size,
                user_agent=user_agent,
                client_ip=client_ip
            )
            
            return response
            
        except Exception as exc:
            # Calculate duration for failed request
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error response
            from src.utils.logger import log_api_response
            log_api_response(
                status_code=500,
                path=path,
                duration_ms=duration_ms,
                request_id=correlation_id,
                error=str(exc),
                user_agent=user_agent,
                client_ip=client_ip
            )
            
            # Re-raise the exception to be handled by FastAPI
            raise


def register_logging_middleware(app: FastAPI) -> None:
    """Register logging middleware for the application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(LoggingMiddleware)
    
    logger.info("Logging middleware registered", extra={
        "features": [
            "correlation_ids", 
            "request_response_logging", 
            "performance_timing",
            "error_tracking"
        ]
    })


def register_routes(app: FastAPI) -> None:
    """Register API routes for the application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """Basic health check endpoint for monitoring and load balancers.
        
        This is a lightweight endpoint that returns quickly for basic liveness probes.
        
        Returns:
            Dictionary with basic health status and application information
        """
        from datetime import datetime, timezone
        
        config = get_config()
        
        return {
            "status": "healthy",
            "service": "pr-summarizer",
            "version": "1.0.0",
            "environment": config.environment,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @app.get("/health/comprehensive")
    async def comprehensive_health_check() -> Dict[str, Any]:
        """Comprehensive health check endpoint with detailed component status.
        
        This endpoint checks database connectivity, external services, and system metrics.
        Use this for detailed health monitoring and diagnostics.
        
        Returns:
            Dictionary with detailed health status of all components
        """
        health_checker = get_health_check()
        return await health_checker.comprehensive_health_check()
    
    @app.get("/health/ready")
    async def readiness_probe() -> Dict[str, Any]:
        """Readiness probe endpoint for Kubernetes deployments.
        
        This endpoint checks if the application is ready to serve requests
        by verifying critical dependencies like database connectivity.
        
        Returns:
            Dictionary with readiness status
        """
        health_checker = get_health_check()
        
        # Check critical components for readiness
        db_check = await health_checker.check_database()
        
        # App is ready if database is accessible
        is_ready = db_check["status"] == "up"
        
        from datetime import datetime, timezone
        
        return {
            "status": "ready" if is_ready else "not_ready",
            "service": "pr-summarizer",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": db_check
            }
        }
    
    @app.get("/health/live")
    async def liveness_probe() -> Dict[str, Any]:
        """Liveness probe endpoint for Kubernetes deployments.
        
        This endpoint performs minimal checks to determine if the application
        is alive and should not be restarted.
        
        Returns:
            Dictionary with liveness status
        """
        from datetime import datetime, timezone
        
        # Minimal check - just verify the application is responding
        return {
            "status": "alive",
            "service": "pr-summarizer", 
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @app.get("/")
    async def root() -> Dict[str, str]:
        """Root endpoint providing API information.
        
        Returns:
            Dictionary with API welcome message and documentation links
        """
        config = get_config()
        
        response = {
            "message": "Welcome to PR Summarizer API",
            "version": "1.0.0",
            "service": "pr-summarizer"
        }
        
        if config.debug:
            response.update({
                "docs": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json"
            })
        
        return response
    
    # Register authentication routes
    from src.api.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/v1")
    
    # Register summary routes
    from src.api.routers.summary import router as summary_router
    app.include_router(summary_router)
    
    # TODO: Register additional route modules
    # app.include_router(github_router, prefix="/api/v1/github", tags=["GitHub"])
    # app.include_router(summarization_router, prefix="/api/v1/summarize", tags=["Summarization"])
    # app.include_router(jira_router, prefix="/api/v1/jira", tags=["Jira"])
    # app.include_router(confluence_router, prefix="/api/v1/confluence", tags=["Confluence"])


# Create application instance
app = create_application()


# Export the application instance
__all__ = [
    "app",
    "create_application",
    "register_exception_handlers", 
    "register_routes",
]