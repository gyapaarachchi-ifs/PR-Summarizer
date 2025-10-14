"""Tests for health check system.

Test coverage for health check endpoints and components including
database connectivity, external services, and system metrics.
"""

import json
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from fastapi.testclient import TestClient

from src.main import create_application
from src.utils.health import HealthCheck, HealthStatus, ComponentStatus


class TestHealthCheckEndpoints:
    """Test health check HTTP endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        test_app = create_application()
        self.client = TestClient(test_app)
    
    def test_basic_health_endpoint(self):
        """Test basic /health endpoint."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "pr-summarizer"
        assert data["version"] == "1.0.0"
        assert "environment" in data
        assert "timestamp" in data
        
        # Validate timestamp format (ISO 8601)
        import datetime
        timestamp = datetime.datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        assert timestamp is not None
    
    def test_liveness_probe_endpoint(self):
        """Test /health/live endpoint."""
        response = self.client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "alive"
        assert data["service"] == "pr-summarizer"
        assert "timestamp" in data
    
    def test_readiness_probe_endpoint(self):
        """Test /health/ready endpoint."""
        response = self.client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] in ["ready", "not_ready"]
        assert data["service"] == "pr-summarizer"
        assert "timestamp" in data
        assert "checks" in data
        assert "database" in data["checks"]
    
    def test_comprehensive_health_endpoint(self):
        """Test /health/comprehensive endpoint."""
        response = self.client.get("/health/comprehensive")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate overall structure
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert data["service"] == "pr-summarizer"
        assert data["version"] == "1.0.0"
        assert "environment" in data
        assert "timestamp" in data
        assert "duration_ms" in data
        assert "components" in data
        
        # Validate components structure
        components = data["components"]
        assert "database" in components
        assert "external_services" in components
        assert "system" in components
        
        # Validate database component
        db_component = components["database"]
        assert "status" in db_component
        assert db_component["status"] in ["up", "down", "degraded"]
        assert "response_time_ms" in db_component
        
        # Validate external services component
        ext_component = components["external_services"]
        assert "status" in ext_component
        assert "services" in ext_component
        
        # Validate system component
        sys_component = components["system"]
        assert "status" in sys_component
        if sys_component["status"] != "down":  # Only check metrics if not down
            assert "metrics" in sys_component


class TestHealthCheckService:
    """Test HealthCheck service class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.health_check = HealthCheck()
    
    @pytest.mark.asyncio
    async def test_database_check_success(self):
        """Test successful database health check."""
        result = await self.health_check.check_database()
        
        assert "status" in result
        assert result["status"] in ["up", "down", "degraded"]
        assert "response_time_ms" in result
        assert "details" in result
        
        if result["status"] == "up":
            assert result["details"]["connected"] is True
            assert "table_count" in result["details"]
    
    @pytest.mark.asyncio
    async def test_external_services_check(self):
        """Test external services health check."""
        result = await self.health_check.check_external_services()
        
        assert "status" in result
        assert result["status"] in ["up", "down", "degraded"]
        assert "services" in result
        
        services = result["services"]
        assert "github" in services
        assert "google_ai" in services
        
        # Check GitHub service structure
        github = services["github"]
        assert "status" in github
        assert "response_time_ms" in github
        assert "details" in github
    
    def test_system_metrics_check(self):
        """Test system metrics health check."""
        result = self.health_check.check_system_metrics()
        
        assert "status" in result
        assert result["status"] in ["up", "down", "degraded"]
        
        if result["status"] != "down":
            assert "metrics" in result
            metrics = result["metrics"]
            assert "cpu_percent" in metrics
            assert "memory" in metrics
            assert "disk" in metrics
            assert "platform" in metrics
            assert "python_version" in metrics
            
            # Validate memory structure
            memory = metrics["memory"]
            assert "total" in memory
            assert "available" in memory
            assert "percent" in memory
            assert "used" in memory
            assert "free" in memory
            
            # Validate disk structure
            disk = metrics["disk"]
            assert "total" in disk
            assert "used" in disk
            assert "free" in disk
            assert "percent" in disk
    
    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self):
        """Test comprehensive health check."""
        result = await self.health_check.comprehensive_health_check()
        
        # Validate overall structure
        assert "status" in result
        assert result["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in result
        assert "service" in result
        assert "version" in result
        assert "environment" in result
        assert "duration_ms" in result
        assert "components" in result
        
        # Validate components
        components = result["components"]
        assert "database" in components
        assert "external_services" in components
        assert "system" in components
        
        # Validate timestamp format
        import datetime
        timestamp = datetime.datetime.fromisoformat(result["timestamp"])
        assert timestamp is not None
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_github_api_check_success(self, mock_client_class):
        """Test successful GitHub API health check."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        mock_client_class.return_value = mock_client
        
        result = await self.health_check._check_github_api()
        
        assert result["status"] == ComponentStatus.UP
        assert "response_time_ms" in result
        assert result["details"]["status_code"] == 200
        assert result["details"]["endpoint"] == "https://api.github.com/zen"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_github_api_check_failure(self, mock_client_class):
        """Test GitHub API health check failure."""
        # Mock timeout exception
        import httpx
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        mock_client_class.return_value = mock_client
        
        result = await self.health_check._check_github_api()
        
        assert result["status"] == ComponentStatus.DOWN
        assert "response_time_ms" in result
        assert "error" in result["details"]
        assert "timeout" in result["details"]["error"].lower()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_system_metrics_degraded_status(self, mock_disk, mock_memory, mock_cpu):
        """Test system metrics with degraded status."""
        # Mock high resource usage
        mock_cpu.return_value = 95.0
        
        mock_memory_obj = MagicMock()
        mock_memory_obj.total = 1000000000
        mock_memory_obj.available = 50000000
        mock_memory_obj.percent = 95.0
        mock_memory_obj.used = 950000000
        mock_memory_obj.free = 50000000
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = MagicMock()
        mock_disk_obj.total = 1000000000
        mock_disk_obj.used = 950000000
        mock_disk_obj.free = 50000000
        mock_disk.return_value = mock_disk_obj
        
        result = self.health_check.check_system_metrics()
        
        assert result["status"] == ComponentStatus.DEGRADED  # CPU = 95% should be DEGRADED
        assert result["metrics"]["cpu_percent"] == 95.0
        assert result["metrics"]["memory"]["percent"] == 95.0
    
    def test_mask_database_url(self):
        """Test database URL masking functionality."""
        # Mock database config with URL
        mock_config = MagicMock()
        mock_config.database = MagicMock()
        mock_config.database.database_url = 'postgresql://user:password@host:5432/db'
        
        with patch.object(self.health_check, 'config', mock_config):
            masked = self.health_check._mask_database_url()
            assert "password" not in masked
            assert "user:***@host:5432/db" in masked
        
        # Test with exception handling (no database config)
        mock_config_no_db = MagicMock()
        mock_config_no_db.database = None
        
        with patch.object(self.health_check, 'config', mock_config_no_db):
            masked = self.health_check._mask_database_url()
            assert masked == "***masked***"


class TestHealthCheckIntegration:
    """Integration tests for health check system."""
    
    def test_health_endpoints_with_correlation_ids(self):
        """Test that health endpoints include correlation IDs."""
        test_app = create_application()
        client = TestClient(test_app)
        
        # Test each health endpoint
        endpoints = ["/health", "/health/live", "/health/ready", "/health/comprehensive"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert "x-correlation-id" in response.headers
            
            # Each request should get a unique correlation ID
            correlation_id = response.headers["x-correlation-id"]
            assert len(correlation_id) == 36  # UUID length
    
    def test_health_endpoints_response_times(self):
        """Test that health endpoints respond within reasonable time limits."""
        test_app = create_application()
        client = TestClient(test_app)
        
        import time
        
        # Test lightweight endpoints (should be very fast)
        fast_endpoints = ["/health", "/health/live"]
        for endpoint in fast_endpoints:
            start = time.time()
            response = client.get(endpoint)
            duration = time.time() - start
            
            assert response.status_code == 200
            assert duration < 1.0  # Should complete in under 1 second
        
        # Test more comprehensive endpoints (may take longer but still reasonable)
        comprehensive_endpoints = ["/health/ready", "/health/comprehensive"]
        for endpoint in comprehensive_endpoints:
            start = time.time()
            response = client.get(endpoint)
            duration = time.time() - start
            
            assert response.status_code == 200
            assert duration < 10.0  # Should complete in under 10 seconds
    
    def test_concurrent_health_checks(self):
        """Test that health checks work correctly under concurrent load."""
        import threading
        import time
        
        test_app = create_application()
        client = TestClient(test_app)
        
        results = []
        
        def make_request(endpoint):
            try:
                response = client.get(endpoint)
                results.append(response.status_code)
            except Exception as e:
                results.append(500)  # Mark as failure
        
        # Create multiple threads to test concurrent access
        threads = []
        endpoints = ["/health", "/health/live", "/health", "/health/live"]
        
        for endpoint in endpoints:
            thread = threading.Thread(target=make_request, args=(endpoint,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == len(endpoints)
        assert all(status == 200 for status in results)