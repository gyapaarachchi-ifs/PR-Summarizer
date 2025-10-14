"""GitHub service for interacting with GitHub API."""

import os
import re
from typing import Dict, Any, Optional
import asyncio
import httpx
from datetime import datetime


class GitHubServiceError(Exception):
    """Base exception for GitHub service errors."""
    pass


class GitHubValidationError(GitHubServiceError):
    """Exception for GitHub validation errors."""
    pass


class GitHubService:
    """Service for GitHub API operations."""
    
    def __init__(self, token: str = None):
        """Initialize GitHub service."""
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise GitHubServiceError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "PR-Summarizer/1.0"
        }
        
    async def get_pr_details(self, pr_url: str) -> Dict[str, Any]:
        """Get PR details from GitHub API."""
        # Validate URL format first
        if not self._is_valid_github_pr_url(pr_url):
            raise GitHubValidationError(f"Invalid GitHub PR URL format: {pr_url}")
        
        # Extract owner, repo, and PR number from URL
        owner, repo, pr_number = self._extract_pr_info(pr_url)
        
        async with httpx.AsyncClient() as client:
            try:
                # Get PR details
                pr_response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}",
                    headers=self.headers,
                    timeout=30.0
                )
                pr_response.raise_for_status()
                pr_data = pr_response.json()
                
                # Get PR files/diff
                files_response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files",
                    headers=self.headers,
                    timeout=30.0
                )
                files_response.raise_for_status()
                files_data = files_response.json()
                
                # Get commits
                commits_response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/commits",
                    headers=self.headers,
                    timeout=30.0
                )
                commits_response.raise_for_status()
                commits_data = commits_response.json()
                
                # Process and return structured data
                return {
                    "url": pr_url,
                    "number": pr_data["number"],
                    "title": pr_data["title"],
                    "body": pr_data["body"] or "",
                    "state": pr_data["state"],
                    "author": pr_data["user"]["login"],
                    "created_at": pr_data["created_at"],
                    "updated_at": pr_data["updated_at"],
                    "base_branch": pr_data["base"]["ref"],
                    "head_branch": pr_data["head"]["ref"],
                    "head_sha": pr_data["head"]["sha"],
                    "base_sha": pr_data["base"]["sha"],
                    "repository": f"{owner}/{repo}",
                    "files_changed": len(files_data),
                    "additions": pr_data["additions"],
                    "deletions": pr_data["deletions"],
                    "draft": pr_data.get("draft", False),
                    "mergeable": pr_data.get("mergeable"),
                    "merged": pr_data.get("merged", False),
                    "html_url": pr_data["html_url"],
                    "diff_url": pr_data.get("diff_url", f"{pr_data['html_url']}.diff"),
                    "labels": pr_data.get("labels", []),
                    "comments": pr_data.get("comments", 0),
                    "review_comments": pr_data.get("review_comments", 0),
                    "changed_files": [
                        {
                            "filename": file["filename"],
                            "status": file["status"],
                            "additions": file["additions"],
                            "deletions": file["deletions"],
                            "patch": file.get("patch", "")[:1000]  # Limit patch size
                        }
                        for file in files_data[:20]  # Limit number of files
                    ],
                    "commits": [
                        {
                            "sha": commit["sha"],
                            "message": commit["commit"]["message"],
                            "author": commit["commit"]["author"]["name"],
                            "date": commit["commit"]["author"]["date"]
                        }
                        for commit in commits_data[-10:]  # Last 10 commits
                    ]
                }
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise GitHubServiceError(f"PR not found: {pr_url}")
                elif e.response.status_code == 403:
                    raise GitHubServiceError("GitHub API access denied. Check token permissions.")
                else:
                    raise GitHubServiceError(f"GitHub API error: {e.response.status_code}")
            except httpx.RequestError as e:
                raise GitHubServiceError(f"GitHub API request failed: {str(e)}")
    
    def _extract_pr_info(self, pr_url: str) -> tuple[str, str, str]:
        """Extract owner, repo, and PR number from GitHub URL."""
        match = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url.rstrip('/'))
        if not match:
            raise GitHubValidationError(f"Invalid GitHub PR URL format: {pr_url}")
        return match.groups()
    
    def _is_valid_github_pr_url(self, url: str) -> bool:
        """Validate GitHub PR URL format."""
        pattern = r'^https://github\.com/[^/]+/[^/]+/pull/\d+$'
        return bool(re.match(pattern, url))