# Contract Tests

Contract tests validate API interfaces and ensure backward compatibility.

## Purpose
- Validate API request/response schemas
- Test endpoint availability and behavior
- Ensure API contracts are maintained across versions
- Verify external service integrations

## Test Structure
```
test_summary_api.py     # Summary API contract tests (US1)
test_auth_api.py        # Authentication API contract tests
test_health_api.py      # Health check API contract tests
```

## Running Contract Tests
```bash
# Run all contract tests
pytest -m contract

# Run specific contract tests
pytest tests/contract/test_summary_api.py -v
```

## What to Test
- HTTP status codes
- Response schema validation
- Required vs optional fields
- Error response formats
- Authentication requirements
- Rate limiting behavior

## TDD Approach
1. Write contract test FIRST (should fail)
2. Implement API endpoint to make test pass
3. Refactor while keeping test green