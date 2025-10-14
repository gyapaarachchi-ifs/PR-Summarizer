#!/usr/bin/env python3
"""Quick test for GitHub API access to WorkWave PR."""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')
from services.github import GitHubService

async def test_workwave_pr():
    """Test access to the specific WorkWave PR."""
    print("🔍 Testing access to https://github.com/WorkWave/NGP/pull/5696")
    
    service = GitHubService()
    
    try:
        # Test with a working public PR
        print("  Testing with working public PR...")
        result = await service.get_pr_details('https://github.com/octocat/Hello-World/pull/1')
        print(f"✅ PUBLIC PR WORKS! Title: {result['title']}")
        print(f"   Author: {result['author']}")
        print(f"   State: {result['state']}")
        print(f"   Files changed: {result['files_changed']}")
        
        # Now test the PestPac PR
        print("\n  Testing WorkWave PestPac PR...")
        result = await service.get_pr_details('https://github.com/WorkWave/PestPac/pull/12114')
        print(f"✅ SUCCESS! PR Title: {result['title']}")
        print(f"   Author: {result['author']}")
        print(f"   State: {result['state']}")
        print(f"   Repository: {result['repository']}")
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("   This could be due to:")
        print("   - Private repository (token lacks access)")
        print("   - Invalid PR number")
        print("   - Network issues")
        return False

if __name__ == "__main__":
    asyncio.run(test_workwave_pr())