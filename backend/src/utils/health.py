"""Health check system for PR Summarizer application.

This module provides comprehensive health checking capabilities including
database connectivity, external service health, and system metrics.
"""

import asyncio
import platform
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List

import httpx
import psutil
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.models.config import get_config
from src.database.session import get_database_session
from src.utils.logger import get_logger, log_external_service_call, log_performance_metric


class HealthStatus(str, Enum):
    """Health status enumeration."""
    
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentStatus(str, Enum):
    """Individual component status enumeration."""
    
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"


class HealthCheck:
    """Main health check service."""
    
    def __init__(self):
        self.logger = get_logger("health_check")
        self.config = get_config()
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance.
        
        Returns:
            Dictionary with database health status and metrics
        """
        start_time = time.time()
        
        try:
            async with get_database_session() as session:
                # Test basic connectivity with a simple query
                result = await session.execute(text("SELECT 1"))
                result.fetchone()
                
                # Test more complex query for performance
                perf_result = await session.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
                table_count = perf_result.scalar()
                
                duration_ms = (time.time() - start_time) * 1000
                
                log_performance_metric(
                    operation="database_health_check",
                    duration_ms=duration_ms,
                    success=True,
                    metadata={"table_count": table_count}
                )
                
                return {
                    "status": ComponentStatus.UP,
                    "response_time_ms": round(duration_ms, 2),
                    "details": {
                        "connected": True,
                        "table_count": table_count,
                        "database_url": self._mask_database_url()
                    }
                }
                
        except SQLAlchemyError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            log_performance_metric(
                operation="database_health_check",
                duration_ms=duration_ms,
                success=False,
                error=error_msg
            )
            
            self.logger.error("Database health check failed", error=error_msg)
            
            return {
                "status": ComponentStatus.DOWN,
                "response_time_ms": round(duration_ms, 2),
                "details": {
                    "connected": False,
                    "error": error_msg,
                    "database_url": self._mask_database_url()
                }
            }
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Unexpected error: {str(e)}"
            
            self.logger.error("Database health check failed", error=error_msg)
            
            return {
                "status": ComponentStatus.DOWN,
                "response_time_ms": round(duration_ms, 2),
                "details": {
                    "connected": False,
                    "error": error_msg
                }
            }
    
    async def check_external_services(self) -> Dict[str, Any]:
        """Check external service connectivity (GitHub, Google AI, etc.).
        
        Returns:
            Dictionary with external service health status
        """
        services = {}
        
        # Check GitHub API
        github_status = await self._check_github_api()
        services["github"] = github_status
        
        # Check Google AI API (if configured)
        google_ai_status = await self._check_google_ai_api()
        services["google_ai"] = google_ai_status
        
        # Determine overall external services status
        all_up = all(service["status"] == ComponentStatus.UP for service in services.values())
        any_down = any(service["status"] == ComponentStatus.DOWN for service in services.values())
        
        if all_up:
            overall_status = ComponentStatus.UP
        elif any_down:
            overall_status = ComponentStatus.DEGRADED
        else:
            overall_status = ComponentStatus.DEGRADED
        
        return {
            "status": overall_status,
            "services": services
        }
    
    async def _check_github_api(self) -> Dict[str, Any]:
        """Check GitHub API connectivity.
        
        Returns:
            GitHub API health status
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                # Use GitHub's public API status endpoint
                response = await client.get(
                    "https://api.github.com/zen",
                    timeout=10.0
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    log_external_service_call(
                        service="github",
                        operation="health_check",
                        url="https://api.github.com/zen",
                        status_code=response.status_code,
                        duration_ms=duration_ms
                    )
                    
                    return {
                        "status": ComponentStatus.UP,
                        "response_time_ms": round(duration_ms, 2),
                        "details": {
                            "endpoint": "https://api.github.com/zen",
                            "status_code": response.status_code
                        }
                    }
                else:
                    return {
                        "status": ComponentStatus.DEGRADED,
                        "response_time_ms": round(duration_ms, 2),
                        "details": {
                            "endpoint": "https://api.github.com/zen",
                            "status_code": response.status_code,
                            "error": f"Non-200 response: {response.status_code}"
                        }
                    }
                    
        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = "Request timeout"
            
            log_external_service_call(
                service="github",
                operation="health_check",
                url="https://api.github.com/zen",
                duration_ms=duration_ms,
                error=error_msg
            )
            
            return {
                "status": ComponentStatus.DOWN,
                "response_time_ms": round(duration_ms, 2),
                "details": {
                    "endpoint": "https://api.github.com/zen",
                    "error": error_msg
                }
            }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            log_external_service_call(
                service="github",
                operation="health_check",
                url="https://api.github.com/zen",
                duration_ms=duration_ms,
                error=error_msg
            )
            
            return {
                "status": ComponentStatus.DOWN,
                "response_time_ms": round(duration_ms, 2),
                "details": {
                    "endpoint": "https://api.github.com/zen",
                    "error": error_msg
                }
            }
    
    async def _check_google_ai_api(self) -> Dict[str, Any]:
        """Check Google AI API connectivity.
        
        Returns:
            Google AI API health status
        """
        start_time = time.time()
        
        try:
            # For now, we'll do a basic connectivity check
            # In production, this would use the actual Google AI SDK
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://generativelanguage.googleapis.com",
                    timeout=10.0
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Any response (even 404) indicates the service is reachable
                if response.status_code in [200, 404, 401, 403]:
                    log_external_service_call(
                        service="google_ai",
                        operation="health_check",
                        url="https://generativelanguage.googleapis.com",
                        status_code=response.status_code,
                        duration_ms=duration_ms
                    )
                    
                    return {
                        "status": ComponentStatus.UP,
                        "response_time_ms": round(duration_ms, 2),
                        "details": {
                            "endpoint": "https://generativelanguage.googleapis.com",
                            "status_code": response.status_code,
                            "note": "Basic connectivity check"
                        }
                    }
                else:
                    return {
                        "status": ComponentStatus.DEGRADED,
                        "response_time_ms": round(duration_ms, 2),
                        "details": {
                            "endpoint": "https://generativelanguage.googleapis.com",
                            "status_code": response.status_code,
                            "error": f"Unexpected response: {response.status_code}"
                        }
                    }
                    
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            log_external_service_call(
                service="google_ai",
                operation="health_check",
                url="https://generativelanguage.googleapis.com",
                duration_ms=duration_ms,
                error=error_msg
            )
            
            return {
                "status": ComponentStatus.DOWN,
                "response_time_ms": round(duration_ms, 2),
                "details": {
                    "endpoint": "https://generativelanguage.googleapis.com",
                    "error": error_msg
                }
            }
    
    def check_system_metrics(self) -> Dict[str, Any]:
        """Check system metrics and resource usage.
        
        Returns:
            Dictionary with system health metrics
        """
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_usage = {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            }
            
            # Get disk usage for current directory
            disk = psutil.disk_usage('.')
            disk_usage = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
            
            # Determine status based on resource usage
            status = ComponentStatus.UP
            if cpu_percent > 90 or memory.percent > 90 or disk_usage["percent"] > 90:
                status = ComponentStatus.DEGRADED
            elif cpu_percent > 95 or memory.percent > 95 or disk_usage["percent"] > 95:
                status = ComponentStatus.DOWN
            
            return {
                "status": status,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory": memory_usage,
                    "disk": disk_usage,
                    "platform": platform.platform(),
                    "python_version": platform.python_version()
                }
            }
            
        except Exception as e:
            self.logger.error("System metrics check failed", error=str(e))
            return {
                "status": ComponentStatus.DOWN,
                "error": str(e)
            }
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of all components.
        
        Returns:
            Complete health check report
        """
        start_time = time.time()
        
        # Run all health checks concurrently
        database_check, external_check, system_check = await asyncio.gather(
            self.check_database(),
            self.check_external_services(),
            asyncio.to_thread(self.check_system_metrics),
            return_exceptions=True
        )
        
        # Handle exceptions from concurrent operations
        if isinstance(database_check, Exception):
            database_check = {
                "status": ComponentStatus.DOWN,
                "error": str(database_check)
            }
        
        if isinstance(external_check, Exception):
            external_check = {
                "status": ComponentStatus.DOWN,
                "error": str(external_check)
            }
        
        if isinstance(system_check, Exception):
            system_check = {
                "status": ComponentStatus.DOWN,
                "error": str(system_check)
            }
        
        # Determine overall health status
        component_statuses = [
            database_check["status"],
            external_check["status"],
            system_check["status"]
        ]
        
        if all(status == ComponentStatus.UP for status in component_statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(status == ComponentStatus.DOWN for status in component_statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED
        
        duration_ms = (time.time() - start_time) * 1000
        
        log_performance_metric(
            operation="comprehensive_health_check",
            duration_ms=duration_ms,
            success=overall_status != HealthStatus.UNHEALTHY,
            metadata={"overall_status": overall_status}
        )
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "pr-summarizer",
            "version": "1.0.0",
            "environment": self.config.environment,
            "duration_ms": round(duration_ms, 2),
            "components": {
                "database": database_check,
                "external_services": external_check,
                "system": system_check
            }
        }
    
    def _mask_database_url(self) -> str:
        """Mask sensitive information in database URL.
        
        Returns:
            Masked database URL
        """
        try:
            db_url = str(self.config.database.database_url)
            # Mask password if present
            if "@" in db_url and "://" in db_url:
                scheme, rest = db_url.split("://", 1)
                if "@" in rest:
                    credentials, host_path = rest.split("@", 1)
                    if ":" in credentials:
                        user, _ = credentials.split(":", 1)
                        return f"{scheme}://{user}:***@{host_path}"
                    else:
                        return f"{scheme}://***@{host_path}"
            return db_url
        except Exception:
            return "***masked***"


# Singleton health check instance
_health_check_instance: Optional[HealthCheck] = None


def get_health_check() -> HealthCheck:
    """Get singleton health check instance.
    
    Returns:
        HealthCheck instance
    """
    global _health_check_instance
    if _health_check_instance is None:
        _health_check_instance = HealthCheck()
    return _health_check_instance