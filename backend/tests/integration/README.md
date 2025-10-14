# Integration Tests

Integration tests validate interactions between multiple components.

## Purpose
- Test service-to-service communication
- Validate external API integrations
- Test database interactions
- Verify end-to-end workflows

## Test Structure
```
test_summary_flow.py       # End-to-end summary generation (US1)
test_multi_source.py       # Multi-source data integration (US2)
test_advanced_guidance.py  # Advanced guidance generation (US3)
test_auth_flow.py         # Authentication integration tests
```

## Running Integration Tests
```bash
# Run all integration tests
pytest -m integration

# Run specific user story tests
pytest -m "integration and us1"
pytest -m "integration and us2"
pytest -m "integration and us3"
```

## What to Test
- Data flow between services
- External API error handling
- Service dependency management
- Configuration loading
- Database transactions
- Cache interactions

## Test Data
- Use realistic test data
- Mock external services when needed
- Test both success and failure scenarios
- Verify data transformation accuracy

## TDD Approach
1. Write integration test FIRST (should fail)
2. Implement service integrations
3. Verify complete workflow functionality