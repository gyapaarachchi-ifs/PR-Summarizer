#!/usr/bin/env python3
"""Debug GitHub PR response structure."""

import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')
from services.github import GitHubService

async def debug_pr_response():
    """Debug the actual PR response structure."""
    print("🔍 Debugging GitHub PR response structure")
    
    try:
        service = GitHubService()
        result = await service.get_pr_details("https://github.com/yapaarachchi/MyGPT/pull/1")
        
        print("✅ SUCCESS! GitHub service returned data:")
        print("\n📋 PR Data Keys:")
        for key in result.keys():
            print(f"  - {key}: {type(result[key])}")
            
        print(f"\n📊 Key Details:")
        print(f"  Title: {result.get('title', 'N/A')}")
        print(f"  Author: {result.get('author', 'N/A')}")
        print(f"  State: {result.get('state', 'N/A')}")
        print(f"  Files: {result.get('files_changed', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(debug_pr_response())