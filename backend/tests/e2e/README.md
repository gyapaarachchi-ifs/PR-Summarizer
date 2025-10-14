# End-to-End Tests

E2E tests validate complete user workflows from UI to backend.

## Purpose
- Test complete user journeys
- Validate frontend-backend integration
- Test cross-browser compatibility
- Verify deployment readiness

## Test Structure
```
test_pr_summary_workflow.py    # Complete PR summary generation workflow
test_user_authentication.py    # User login and authentication flow
test_error_scenarios.py        # Error handling across the stack
```

## Running E2E Tests
```bash
# Run all e2e tests
pytest -m e2e

# Run with browser automation (when implemented)
pytest -m e2e --browser=chrome
```

## What to Test
- User registration and login
- PR summary request workflow
- Error message display
- Loading states and UX
- Data persistence
- Session management

## Prerequisites
- Running backend server
- Running frontend server
- Test database populated
- External service mocks configured

## Test Environment
- Use staging/test environment
- Reset data between tests
- Monitor performance metrics
- Capture screenshots on failure

## TDD Approach
1. Define user acceptance criteria
2. Write E2E test scenarios
3. Implement features to pass tests
4. Validate complete user experience