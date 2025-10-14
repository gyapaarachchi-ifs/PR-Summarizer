#!/usr/bin/env python3
"""Debug GitHub API raw response."""

import asyncio
import sys
import httpx
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def debug_raw_github_response():
    """Debug the raw GitHub API response."""
    print("🔍 Debugging raw GitHub API response")
    
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "PR-Summarizer/1.0"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/repos/yapaarachchi/MyGPT/pulls/1",
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ SUCCESS! Raw API response structure:")
                print(f"  - Title: {data.get('title', 'N/A')}")
                print(f"  - State: {data.get('state', 'N/A')}")
                print(f"  - User structure: {type(data.get('user', 'N/A'))}")
                
                if 'user' in data:
                    user_data = data['user']
                    print(f"  - User keys: {list(user_data.keys()) if isinstance(user_data, dict) else 'Not a dict'}")
                    print(f"  - User login: {user_data.get('login', 'N/A') if isinstance(user_data, dict) else 'N/A'}")
                else:
                    print("  - ❌ No 'user' field in response!")
                    print(f"  - Available keys: {list(data.keys())}")
                    
                return True
            else:
                print(f"❌ API Error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(debug_raw_github_response())