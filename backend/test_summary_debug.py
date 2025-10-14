#!/usr/bin/env python3
"""Test summary service with detailed debugging."""

import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')

async def test_summary_service_debug():
    """Test summary service with debugging."""
    print("🔍 Testing summary service with debugging")
    
    try:
        from services.summary_service import SummaryOrchestrationService
        from models.request import SummaryRequest
        
        # Create service and request
        service = SummaryOrchestrationService()
        request = SummaryRequest(github_pr_url="https://github.com/yapaarachchi/MyGPT/pull/1")
        
        print("✅ Service and request created")
        
        # Let's manually test each step
        print("🔍 Step 1: Testing GitHub service directly...")
        github_service = service.github_service
        pr_data = await github_service.get_pr_details(request.github_pr_url)
        print(f"✅ GitHub service works: {pr_data['title'][:30]}...")
        
        print("🔍 Step 2: Testing context creation...")
        from models.context import create_github_context, SourceMetadata, DataSource
        
        # Create metadata
        metadata = SourceMetadata(
            source=DataSource.GITHUB,
            retrieved_at="2025-10-14T14:30:00Z",
            cache_hit=False,
            response_time_ms=100
        )
        
        # This might be where the issue is - let's see what create_github_context expects
        print(f"   PR data keys: {list(pr_data.keys())}")
        
        try:
            github_context = create_github_context(pr_data, metadata)
            print(f"✅ Context created: {github_context.title[:30]}...")
        except Exception as e:
            print(f"❌ Context creation failed: {str(e)}")
            return False
        
        print("🔍 Step 3: Testing full summary generation...")
        result = await service.generate_summary(request)
        print(f"✅ Summary generated successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_summary_service_debug())