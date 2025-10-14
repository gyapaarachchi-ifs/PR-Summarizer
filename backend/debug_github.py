#!/usr/bin/env python3
"""Debug GitHub API access."""

import asyncio
import sys
import os
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def debug_github_access():
    """Debug GitHub API access."""
    print("🔍 Debugging GitHub API access")
    
    # Check environment variable
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ No GITHUB_TOKEN found")
        return
    
    print(f"✅ GITHUB_TOKEN found: {token[:10]}...")
    
    # Test API directly
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "PR-Summarizer/1.0"
    }
    
    async with httpx.AsyncClient() as client:
        # Test a very simple known PR first
        test_urls = [
            "https://api.github.com/repos/octocat/Hello-World/pulls/1",
            "https://api.github.com/repos/yapaarachchi/MyGPT/pulls/1"
        ]
        
        for url in test_urls:
            try:
                print(f"\n🔍 Testing: {url}")
                response = await client.get(url, headers=headers, timeout=30.0)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ SUCCESS! Title: {data['title'][:50]}...")
                elif response.status_code == 404:
                    print("   ❌ 404 Not Found - PR doesn't exist or no access")
                elif response.status_code == 403:
                    print("   ❌ 403 Forbidden - Token lacks permissions")
                else:
                    print(f"   ❌ {response.status_code}: {response.text[:100]}...")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_github_access())