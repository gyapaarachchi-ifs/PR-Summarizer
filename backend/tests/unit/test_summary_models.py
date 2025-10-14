"""
Unit tests for summary models.

This module tests the validation and behavior of PR summary related models
including SummaryRequest, PRSummary, and related data structures.
"""

import pytest
from datetime import datetime
from typing import List, Optional
from pydantic import ValidationError

from src.models.pr_summary import (
    SummaryRequest,
    PRSummary,
    ProcessingStatus
)


class TestSummaryRequest:
    """Unit tests for SummaryRequest model."""
    
    def test_valid_request_creation(self):
        """Test creating a valid SummaryRequest."""
        request = SummaryRequest(
            github_pr_url="https://github.com/owner/repo/pull/123",
            jira_ticket_id="PROJ-456"
        )
        
        assert request.github_pr_url == "https://github.com/owner/repo/pull/123"
        assert request.jira_ticket_id == "PROJ-456"
        
    def test_request_with_only_github_url(self):
        """Test creating a request with only GitHub URL (Jira optional)."""
        request = SummaryRequest(
            github_pr_url="https://github.com/owner/repo/pull/123"
        )
        
        assert request.github_pr_url == "https://github.com/owner/repo/pull/123"
        assert request.jira_ticket_id is None
        
    def test_request_requires_github_url(self):
        """Test that github_pr_url is required."""
        with pytest.raises(ValidationError) as exc_info:
            SummaryRequest(jira_ticket_id="PROJ-456")
            
        assert "github_pr_url" in str(exc_info.value)
        
    def test_github_url_validation(self):
        """Test GitHub URL format validation."""
        # Valid URLs should work
        valid_urls = [
            "https://github.com/owner/repo/pull/123",
            "https://github.com/my-org/my-repo/pull/456",
            "https://github.com/user123/project_name/pull/1"
        ]
        
        for url in valid_urls:
            request = SummaryRequest(github_pr_url=url)
            assert request.github_pr_url == url
            
    def test_invalid_github_url_validation(self):
        """Test that invalid GitHub URLs are rejected."""
        invalid_urls = [
            "https://gitlab.com/owner/repo/pull/123",
            "https://github.com/owner/repo/issues/123",
            "https://github.com/owner",
            "not-a-url",
            "",
            "https://github.com/owner/repo/pull/",
            "https://github.com/owner/repo/pull/abc"
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationError):
                SummaryRequest(github_pr_url=url)
                
    def test_jira_ticket_id_validation(self):
        """Test Jira ticket ID format validation."""
        # Valid ticket IDs should work
        valid_tickets = [
            "PROJ-123",
            "DEV-456",
            "FEATURE-789",
            "BUG-1"
        ]
        
        for ticket in valid_tickets:
            request = SummaryRequest(
                github_pr_url="https://github.com/owner/repo/pull/123",
                jira_ticket_id=ticket
            )
            assert request.jira_ticket_id == ticket
            
    def test_invalid_jira_ticket_validation(self):
        """Test that invalid Jira ticket IDs are rejected."""
        invalid_tickets = [
            "invalid-format",
            "123-PROJ",
            "PROJ_123",
            "proj-123",
            "PROJ-",
            "-123",
            ""
        ]
        
        for ticket in invalid_tickets:
            with pytest.raises(ValidationError):
                SummaryRequest(
                    github_pr_url="https://github.com/owner/repo/pull/123",
                    jira_ticket_id=ticket
                )
                
    def test_request_serialization(self):
        """Test that SummaryRequest can be serialized to dict/JSON."""
        request = SummaryRequest(
            github_pr_url="https://github.com/owner/repo/pull/123",
            jira_ticket_id="PROJ-456"
        )
        
        data = request.model_dump()
        assert data["github_pr_url"] == "https://github.com/owner/repo/pull/123"
        assert data["jira_ticket_id"] == "PROJ-456"
        
    def test_request_from_dict(self):
        """Test creating SummaryRequest from dictionary."""
        data = {
            "github_pr_url": "https://github.com/owner/repo/pull/123",
            "jira_ticket_id": "PROJ-456"
        }
        
        request = SummaryRequest(**data)
        assert request.github_pr_url == data["github_pr_url"]
        assert request.jira_ticket_id == data["jira_ticket_id"]


class TestPRSummary:
    """Unit tests for PRSummary model."""
    
    def test_valid_summary_creation(self):
        """Test creating a valid PRSummary."""
        summary = PRSummary(
            id="summary-123",
            github_pr_url="https://github.com/owner/repo/pull/123",
            jira_ticket_id="PROJ-456",
            business_context="Feature implementation",
            code_change_summary="Added authentication",
            business_code_impact="Enhanced security",
            suggested_test_cases=["Test login", "Test logout"],
            risk_complexity="Medium",
            reviewer_guidance="Focus on security",
            status=ProcessingStatus.COMPLETED,
            created_at=datetime.now()
        )
        
        assert summary.id == "summary-123"
        assert summary.github_pr_url == "https://github.com/owner/repo/pull/123"
        assert summary.status == ProcessingStatus.COMPLETED
        assert len(summary.suggested_test_cases) == 2
        
    def test_summary_requires_all_fields(self):
        """Test that all required fields are present."""
        required_fields = [
            "id", "github_pr_url", "business_context",
            "code_change_summary", "business_code_impact",
            "suggested_test_cases", "risk_complexity",
            "reviewer_guidance", "status", "created_at"
        ]
        
        # Create complete valid data
        complete_data = {
            "id": "summary-123",
            "github_pr_url": "https://github.com/owner/repo/pull/123",
            "jira_ticket_id": "PROJ-456",
            "business_context": "Feature implementation",
            "code_change_summary": "Added authentication",
            "business_code_impact": "Enhanced security",
            "suggested_test_cases": ["Test login"],
            "risk_complexity": "Medium",
            "reviewer_guidance": "Focus on security",
            "status": ProcessingStatus.COMPLETED,
            "created_at": datetime.now()
        }
        
        # Test that removing each required field causes validation error
        for field in required_fields:
            if field == "jira_ticket_id":  # This field is optional
                continue
                
            incomplete_data = complete_data.copy()
            del incomplete_data[field]
            
            with pytest.raises(ValidationError) as exc_info:
                PRSummary(**incomplete_data)
                
            assert field in str(exc_info.value)
            
    def test_processing_status_enum(self):
        """Test ProcessingStatus enum values."""
        valid_statuses = [
            ProcessingStatus.PROCESSING,
            ProcessingStatus.COMPLETED,
            ProcessingStatus.FAILED
        ]
        
        for status in valid_statuses:
            summary = PRSummary(
                id="summary-123",
                github_pr_url="https://github.com/owner/repo/pull/123",
                business_context="Feature implementation",
                code_change_summary="Added authentication",
                business_code_impact="Enhanced security",
                suggested_test_cases=["Test login"],
                risk_complexity="Medium",
                reviewer_guidance="Focus on security",
                status=status,
                created_at=datetime.now()
            )
            assert summary.status == status
            
    def test_suggested_test_cases_is_list(self):
        """Test that suggested_test_cases is properly typed as list."""
        summary = PRSummary(
            id="summary-123",
            github_pr_url="https://github.com/owner/repo/pull/123",
            business_context="Feature implementation",
            code_change_summary="Added authentication",
            business_code_impact="Enhanced security",
            suggested_test_cases=["Test 1", "Test 2", "Test 3"],
            risk_complexity="Medium",
            reviewer_guidance="Focus on security",
            status=ProcessingStatus.COMPLETED,
            created_at=datetime.now()
        )
        
        assert isinstance(summary.suggested_test_cases, list)
        assert len(summary.suggested_test_cases) == 3
        assert all(isinstance(test, str) for test in summary.suggested_test_cases)
        
    def test_summary_serialization(self):
        """Test that PRSummary can be serialized to dict/JSON."""
        now = datetime.now()
        summary = PRSummary(
            id="summary-123",
            github_pr_url="https://github.com/owner/repo/pull/123",
            jira_ticket_id="PROJ-456",
            business_context="Feature implementation",
            code_change_summary="Added authentication",
            business_code_impact="Enhanced security",
            suggested_test_cases=["Test login"],
            risk_complexity="Medium",
            reviewer_guidance="Focus on security",
            status=ProcessingStatus.COMPLETED,
            created_at=now
        )
        
        data = summary.model_dump()
        assert data["id"] == "summary-123"
        assert data["status"] == "completed"  # Enum serialized as string
        assert isinstance(data["suggested_test_cases"], list)
        
    def test_optional_fields(self):
        """Test handling of optional fields."""
        # jira_ticket_id and processing_time_ms are optional
        summary = PRSummary(
            id="summary-123",
            github_pr_url="https://github.com/owner/repo/pull/123",
            business_context="Feature implementation",
            code_change_summary="Added authentication",
            business_code_impact="Enhanced security",
            suggested_test_cases=["Test login"],
            risk_complexity="Medium",
            reviewer_guidance="Focus on security",
            status=ProcessingStatus.COMPLETED,
            created_at=datetime.now()
        )
        
        assert summary.jira_ticket_id is None
        assert summary.processing_time_ms is None
        
    def test_processing_time_validation(self):
        """Test that processing_time_ms must be positive if provided."""
        # Valid positive processing time should work
        summary = PRSummary(
            id="summary-123",
            github_pr_url="https://github.com/owner/repo/pull/123",
            business_context="Feature implementation",
            code_change_summary="Added authentication",
            business_code_impact="Enhanced security",
            suggested_test_cases=["Test login"],
            risk_complexity="Medium",
            reviewer_guidance="Focus on security",
            status=ProcessingStatus.COMPLETED,
            created_at=datetime.now(),
            processing_time_ms=15000
        )
        
        assert summary.processing_time_ms == 15000