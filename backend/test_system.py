#!/usr/bin/env python3
"""Test script to verify the PR Summarizer system works end-to-end."""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
backend_path = Path(__file__).parent
src_path = backend_path / "src"
sys.path.insert(0, str(src_path))

from services.github import GitHubService
from services.gemini import GeminiService


async def test_github_service():
    """Test GitHub service with a real public PR."""
    print("🔍 Testing GitHub service...")
    
    github_service = GitHubService()
    
    # Test with a known public PR
    test_pr_url = "https://github.com/python/cpython/pull/90000"  # This should exist or be close
    
    try:
        pr_data = await github_service.get_pr_data(test_pr_url)
        print(f"✅ GitHub service working! PR title: {pr_data['title'][:50]}...")
        return pr_data
    except Exception as e:
        print(f"❌ GitHub service error: {e}")
        return None


async def test_gemini_service(pr_data):
    """Test Gemini AI service."""
    print("🤖 Testing Gemini AI service...")
    
    if not pr_data:
        print("❌ Cannot test Gemini without PR data")
        return None
    
    gemini_service = GeminiService()
    
    try:
        summary = await gemini_service.generate_summary(pr_data)
        print(f"✅ Gemini AI working! Summary generated: {len(summary.get('summary', ''))} characters")
        return summary
    except Exception as e:
        print(f"❌ Gemini AI error: {e}")
        return None


async def main():
    """Run the test suite."""
    print("🚀 Starting PR Summarizer End-to-End Test")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment")
        return False
    
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        return False
    
    print("✅ Environment variables loaded")
    
    # Test GitHub service
    pr_data = await test_github_service()
    if not pr_data:
        return False
    
    # Test Gemini service
    summary = await test_gemini_service(pr_data)
    if not summary:
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All services working correctly!")
    print("✅ Your PR Summarizer system is ready to use!")
    return True


if __name__ == "__main__":
    asyncio.run(main())