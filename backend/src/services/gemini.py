"""Gemini AI service for generating PR summaries."""

import os
import json
from typing import Dict, Any, Optional
import google.generativeai as genai
from datetime import datetime, timezone
from src.models.pr_summary import PRSummary, ProcessingStatus


class GeminiServiceError(Exception):
    """Base exception for Gemini service errors."""
    pass


class GeminiService:
    """Service for Gemini AI operations."""
    
    def __init__(self, api_key: str = None, model_name: str = "models/gemini-2.0-flash"):
        """Initialize Gemini service."""
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise GeminiServiceError("Google API key is required. Set GOOGLE_API_KEY environment variable.")
        
        self.model_name = model_name
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        
    async def generate_summary(
        self,
        pr_data: Dict[str, Any],
        jira_data: Dict[str, Any] = None,
        confluence_data: Dict[str, Any] = None,
        options: Dict[str, Any] = None
    ) -> PRSummary:
        """Generate PR summary using Gemini AI."""
        try:
            # Build comprehensive prompt from PR data
            prompt = self._build_analysis_prompt(pr_data, jira_data, confluence_data)
            
            # Generate content using Gemini
            response = self.model.generate_content(prompt)
            
            # Parse the AI response
            summary_data = self._parse_ai_response(response.text)
            
            return PRSummary(
                id=f"summary-{int(datetime.now(timezone.utc).timestamp())}",
                request_id=options.get('request_id', f"req-{int(datetime.now(timezone.utc).timestamp())}") if options else f"req-{int(datetime.now(timezone.utc).timestamp())}",
                github_pr_url=options.get('github_pr_url', pr_data.get("url", pr_data.get("html_url", ""))),
                jira_ticket_id=jira_data.get("key") if jira_data else None,
                business_context=summary_data.get("business_context", "Business context analysis from PR changes"),
                code_change_summary=summary_data.get("code_change_summary", f"Technical analysis of {pr_data.get('files_changed', 0)} files changed"),
                business_code_impact=summary_data.get("business_code_impact", "Impact analysis based on code modifications"),
                suggested_test_cases=summary_data.get("suggested_test_cases", ["Test core functionality", "Test edge cases", "Test error handling"]),
                risk_complexity=summary_data.get("risk_complexity", "Medium complexity - requires standard review"),
                reviewer_guidance=summary_data.get("reviewer_guidance", "Standard code review focusing on logic and security"),
                status=ProcessingStatus.COMPLETED,
                created_at=datetime.now(timezone.utc),
                processing_time_ms=int((datetime.now(timezone.utc).timestamp() - datetime.now(timezone.utc).timestamp()) * 1000)
            )
            
        except Exception as e:
            raise GeminiServiceError(f"Failed to generate AI summary: {str(e)}")
    
    def _build_analysis_prompt(self, pr_data: Dict[str, Any], jira_data: Dict[str, Any] = None, confluence_data: Dict[str, Any] = None) -> str:
        """Build comprehensive analysis prompt for Gemini."""
        
        prompt_parts = [
            "You are an expert code reviewer and technical analyst. Analyze the following Pull Request and provide a comprehensive summary.",
            "",
            "## Pull Request Information:",
            f"Title: {pr_data.get('title', 'N/A')}",
            f"Description: {pr_data.get('body', 'No description provided')}",
            f"Files Changed: {pr_data.get('files_changed', 0)}",
            f"Lines Added: {pr_data.get('additions', 0)}",
            f"Lines Deleted: {pr_data.get('deletions', 0)}",
            f"Repository: {pr_data.get('repository', 'N/A')}",
            f"Branch: {pr_data.get('head_branch', 'N/A')} → {pr_data.get('base_branch', 'N/A')}",
        ]
        
        # Add file changes if available
        if pr_data.get('changed_files'):
            prompt_parts.extend([
                "",
                "## Changed Files:",
            ])
            for file in pr_data['changed_files'][:10]:  # Limit to first 10 files
                prompt_parts.append(f"- {file['filename']} ({file['status']}: +{file['additions']} -{file['deletions']})")
                if file.get('patch'):
                    prompt_parts.append(f"  Code changes preview: {file['patch'][:200]}...")
        
        # Add commit information
        if pr_data.get('commits'):
            prompt_parts.extend([
                "",
                "## Recent Commits:",
            ])
            for commit in pr_data['commits'][-5:]:  # Last 5 commits
                prompt_parts.append(f"- {commit['sha'][:8]}: {commit['message'][:100]} (by {commit['author']})")
        
        # Add Jira context if available
        if jira_data:
            prompt_parts.extend([
                "",
                "## Related Jira Ticket:",
                f"Key: {jira_data.get('key', 'N/A')}",
                f"Summary: {jira_data.get('summary', 'N/A')}",
                f"Description: {jira_data.get('description', 'N/A')[:500]}...",
            ])
        
        prompt_parts.extend([
            "",
            "Please provide a detailed analysis in the following JSON format:",
            "{",
            '  "business_context": "Detailed explanation of the business purpose and value of these changes",',
            '  "code_change_summary": "Technical summary of what was modified, added, or removed",',
            '  "business_code_impact": "Analysis of how code changes affect business functionality and user experience",',
            '  "suggested_test_cases": ["Specific test case 1", "Specific test case 2", "Specific test case 3"],',
            '  "risk_complexity": "Assessment of complexity level and potential risks with specific concerns",',
            '  "reviewer_guidance": "Specific areas reviewers should focus on during code review"',
            "}",
            "",
            "Make sure your response is valid JSON and provide specific, actionable insights based on the actual code changes."
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and extract structured data."""
        try:
            # Try to extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback if no JSON found
                return self._create_fallback_summary(response_text)
                
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return self._create_fallback_summary(response_text)
    
    def _create_fallback_summary(self, raw_text: str) -> Dict[str, Any]:
        """Create fallback summary when JSON parsing fails."""
        return {
            "business_context": f"AI Analysis: {raw_text[:200]}...",
            "code_change_summary": "Technical analysis generated by AI (see full response for details)",
            "business_code_impact": "Business impact analysis completed by AI",
            "suggested_test_cases": ["Test main functionality", "Test edge cases", "Test error handling"],
            "risk_complexity": "Standard complexity - AI analysis completed",
            "reviewer_guidance": f"AI Recommendation: {raw_text[-200:]}"
        }