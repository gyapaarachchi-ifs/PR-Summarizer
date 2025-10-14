"""Main FastAPI application for PR Summarizer.

This module sets up the FastAPI application with all middleware,
error handlers, and route registrations.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any
from dotenv import load_dotenv
import os

from fastapi import FastAPI, Request, HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Load environment variables
load_dotenv()

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple configuration for development
class DevConfig:
    environment = "development"
    debug = True
    host = "0.0.0.0"
    port = 8000
    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]
    cors_allow_credentials = True

config = DevConfig()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager for startup and shutdown events."""
    # Startup events
    logger.info("Starting PR Summarizer application")
    
    try:
        logger.info("Configuration loaded successfully")
        logger.info("Application startup completed successfully")
        
        yield  # Application runtime
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    finally:
        # Shutdown events
        logger.info("Shutting down PR Summarizer application")
        logger.info("Application shutdown completed successfully")

def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
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
    
    # Register CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=config.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
        max_age=3600,  # 1 hour preflight cache
    )
    
    logger.info("CORS middleware registered")
    
    # Basic exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = []
        for error in exc.errors():
            field_path = '.'.join(str(loc) for loc in error['loc'])
            errors.append({
                'field': field_path,
                'message': error['msg'],
                'code': error['type'],
                'value': error.get('input')
            })
        
        logger.warning(f"Validation error: {errors}")
        
        return JSONResponse(
            status_code=400,
            content={
                "error": "Validation Error",
                "message": "Invalid input data",
                "errors": errors,
                "timestamp": time.time()
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler_override(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions with consistent error format."""
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
        return await http_exception_handler(request, exc)
    
    # Register routes
    register_routes(app)
    
    logger.info("FastAPI application created successfully")
    return app

def register_routes(app: FastAPI) -> None:
    """Register API routes for the application."""
    
    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """Basic health check endpoint for monitoring and load balancers."""
        from datetime import datetime, timezone
        
        return {
            "status": "healthy",
            "service": "pr-summarizer",
            "version": "1.0.0",
            "environment": config.environment,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @app.get("/")
    async def root() -> Dict[str, str]:
        """Root endpoint providing API information."""
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
    
    # Register summary routes
    try:
        from src.api.routers.summary import router as summary_router
        app.include_router(summary_router)
        logger.info("Summary routes registered successfully")
    except ImportError as e:
        logger.warning(f"Could not import summary router: {e}")
        logger.info("Summary router not available - check service dependencies")
    
    # Add a simple test endpoint
    @app.get("/test")
    async def test_endpoint() -> Dict[str, str]:
        """Simple test endpoint."""
        return {"message": "Backend is running successfully!", "status": "ok"}
    
    # Real summary endpoints are now handled by the summary router

# Create application instance
app = create_application()

# Export the application instance
__all__ = ["app", "create_application"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.host, port=config.port, reload=config.debug)
