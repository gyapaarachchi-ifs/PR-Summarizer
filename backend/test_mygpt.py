#!/usr/bin/env python3
"""Test complete PR analysis with MyGPT PR."""

import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')
from services.summary_service import SummaryOrchestrationService
from models.request import SummaryRequest

async def test_mygpt_pr():
    """Test complete analysis of MyGPT PR."""
    print("🚀 Testing complete AI-powered PR analysis")
    print("🔍 PR: https://github.com/yapaarachchi/MyGPT/pull/1")
    print("=" * 60)
    
    try:
        # Initialize the orchestration service
        service = SummaryOrchestrationService()
        
        # Create request object
        request = SummaryRequest(github_pr_url="https://github.com/yapaarachchi/MyGPT/pull/1")
        
        # Generate complete summary
        result = await service.generate_summary(request)
        
        print("✅ SUCCESS! Complete AI-powered analysis generated!")
        print("\n📊 SUMMARY:")
        print(result.code_change_summary)
        
        print(f"\n📈 STATS:")
        print(f"  - Summary ID: {result.id}")
        print(f"  - Status: {result.status}")
        print(f"  - GitHub URL: {result.github_pr_url}")
        print(f"  - Business Context: {len(result.business_context)} chars")
        print(f"  - Risk Level: {result.risk_complexity}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mygpt_pr())
    if success:
        print("\n🎉 Your PR Summarizer is working perfectly!")
        print("🔥 Real AI-powered analysis complete - no more mocks!")
    else:
        print("\n💡 Check the error above for troubleshooting.")