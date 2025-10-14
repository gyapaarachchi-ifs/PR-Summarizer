#!/usr/bin/env python3
"""Minimal test to isolate the GitHub service issue."""

import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')

async def test_github_step_by_step():
    """Test GitHub service step by step to find the issue."""
    print("🔍 Step-by-step GitHub service test")
    
    try:
        # Import and initialize
        from services.github import GitHubService
        print("✅ Step 1: GitHub service imported")
        
        service = GitHubService()
        print("✅ Step 2: GitHub service initialized")
        
        # Test the URL parsing
        url = "https://github.com/yapaarachchi/MyGPT/pull/1"
        owner, repo, pr_number = service._extract_pr_info(url)
        print(f"✅ Step 3: URL parsed - {owner}/{repo}#{pr_number}")
        
        # Try the actual API call with try/catch around the specific line
        import httpx
        import os
        
        token = os.getenv("GITHUB_TOKEN")
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "PR-Summarizer/1.0"
        }
        
        async with httpx.AsyncClient() as client:
            print("✅ Step 4: Making API call...")
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=headers,
                timeout=30.0
            )
            print(f"✅ Step 5: API response received - {response.status_code}")
            
            pr_data = response.json()
            print("✅ Step 6: JSON parsed")
            
            # Test the specific line that's failing
            try:
                author = pr_data["user"]["login"]
                print(f"✅ Step 7: Author extracted - {author}")
            except KeyError as e:
                print(f"❌ Step 7 FAILED: KeyError accessing {e}")
                print(f"   Available keys: {list(pr_data.keys())}")
                if 'user' in pr_data:
                    print(f"   User keys: {list(pr_data['user'].keys())}")
                return False
                
            # Now try the full service call
            print("✅ Step 8: Testing full service call...")
            result = await service.get_pr_details(url)
            print(f"✅ Step 9: Full service success - {result['title'][:30]}...")
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR at step: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_github_step_by_step())