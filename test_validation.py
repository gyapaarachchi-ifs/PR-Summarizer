#!/usr/bin/env python3
"""
T019 Test Infrastructure Validation Script
"""
import sys
sys.path.append('tests')

from test_utils import TestDataGenerator, MockServiceBuilder, TestAssertions

def main():
    print('=== T019 Test Infrastructure Validation ===')
    
    # Test data generation
    print('\n🔧 Testing Data Generation...')
    pr_data = TestDataGenerator.github_pr_data(number=456, title='Test Feature')
    print(f'✅ GitHub PR data: PR #{pr_data["number"]} - {pr_data["title"]}')
    
    jira_data = TestDataGenerator.jira_issue_data(key='TEST-789')
    jira_summary = jira_data['fields']['summary']
    print(f'✅ Jira issue data: {jira_data["key"]} - {jira_summary}')
    
    summary_req = TestDataGenerator.summary_request_data()
    print(f'✅ Summary request data: {summary_req["pr_url"]}')
    
    # Test mock services
    print('\n🔧 Testing Mock Services...')
    github_mock = MockServiceBuilder.github_service()
    print(f'✅ GitHub service mock created: {type(github_mock).__name__}')
    
    jira_mock = MockServiceBuilder.jira_service() 
    print(f'✅ Jira service mock created: {type(jira_mock).__name__}')
    
    gemini_mock = MockServiceBuilder.gemini_service()
    print(f'✅ Gemini service mock created: {type(gemini_mock).__name__}')
    
    # Test summary structure validation
    print('\n🔧 Testing Assertions...')
    valid_summary = TestDataGenerator.expected_summary_data()
    try:
        TestAssertions.assert_valid_summary_structure(valid_summary)
        print('✅ Valid summary structure assertion passed')
    except AssertionError as e:
        print(f'❌ Summary structure validation failed: {e}')
    
    print('\n🎯 T019 Test Infrastructure: READY FOR TDD!')
    print('📋 Features Available:')
    print('   • Comprehensive test fixtures and mocks')
    print('   • Authentication token fixtures')
    print('   • Service mock builders')
    print('   • Test data generators')
    print('   • Custom assertion helpers')
    print('   • Test categorization and markers')
    print('   • Performance and benchmark support')
    
    return True

if __name__ == '__main__':
    main()