# Quickstart: AI-Powered PR Summarizer

**Feature**: AI-Powered PR Summarizer  
**Version**: 1.0.0  
**Date**: 2025-10-13

## Overview

This guide helps developers quickly set up and validate the AI-powered PR summarizer locally. The system generates comprehensive 6-section summaries by integrating data from GitHub, Jira, Confluence, and Google Docs through Google Gemini LLM.

## Prerequisites

### System Requirements
- Python 3.11 or higher
- Git
- Docker (optional, for containerized setup)
- 8GB RAM minimum (for concurrent processing)
- Internet connection for external API access

### Required Accounts & Access
1. **GitHub**: Personal access token with repo read permissions
2. **Jira**: API token from your Atlassian account
3. **Confluence**: API token (can be same as Jira if using Atlassian Cloud)
4. **Google Cloud**: Service account with Drive and Docs API access
5. **Google AI**: Gemini API key from Google AI Studio

## Quick Setup (15 minutes)

### 1. Clone and Environment Setup

```bash
# Clone the repository
git clone https://github.com/company/pr-summarizer.git
cd pr-summarizer

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt
```

### 2. Configure Environment Variables

Create `.env` file in the repository root:

```bash
# Copy template and edit
cp config/.env.example .env
```

Edit `.env` with your credentials:

```env
# GitHub Configuration
GITHUB__API_TOKEN=ghp_your_github_token_here
GITHUB__BASE_URL=https://api.github.com
GITHUB__TIMEOUT_SECONDS=8

# Jira Configuration  
JIRA__SERVER_URL=https://yourcompany.atlassian.net
JIRA__USERNAME=your.email@company.com
JIRA__API_TOKEN=your_jira_api_token_here
JIRA__TIMEOUT_SECONDS=8

# Confluence Configuration
CONFLUENCE__SERVER_URL=https://yourcompany.atlassian.net/wiki
CONFLUENCE__API_TOKEN=your_confluence_api_token_here
CONFLUENCE__TIMEOUT_SECONDS=10

# Google Services Configuration
GOOGLE__CREDENTIALS_FILE_PATH=config/google-service-account.json
GOOGLE__DRIVE_SEARCH_TIMEOUT=10
GOOGLE__DOCS_EXTRACTION_TIMEOUT=8

# Gemini LLM Configuration
GEMINI__API_KEY=your_gemini_api_key_here
GEMINI__MODEL_NAME=gemini-2.5-pro
GEMINI__TEMPERATURE=0.3
GEMINI__TIMEOUT_SECONDS=15

# Application Settings
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT_TOTAL=30
LOG_LEVEL=INFO
```

### 3. Google Service Account Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Drive API and Google Docs API
4. Create a service account with viewer permissions
5. Download JSON credentials to `config/google-service-account.json`

### 4. Start the Application

```bash
# Start backend API server
cd backend
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start frontend (if available)
cd frontend
npm install
npm start
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## Basic Usage Test

### 1. Health Check

Verify all services are configured correctly:

```bash
curl http://localhost:8000/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "github": "healthy",
    "jira": "healthy", 
    "confluence": "healthy",
    "google_docs": "healthy",
    "gemini": "healthy"
  },
  "timestamp": "2025-10-13T10:30:00Z",
  "uptime_seconds": 120
}
```

### 2. Generate Your First Summary

```bash
curl -X POST http://localhost:8000/v1/summary \
  -H "Content-Type: application/json" \
  -d '{
    "github_pr_url": "https://github.com/your-org/your-repo/pull/123",
    "jira_ticket_id": "PROJ-456"
  }'
```

Expected response structure:
```json
{
  "success": true,
  "data": {
    "request_id": "req_123e4567-e89b-12d3-a456-426614174000",
    "business_context": {
      "title": "Business Context",
      "content": "Description of why this change was made...",
      "word_count": 45
    },
    "code_change_summary": {
      "title": "Code Change Summary", 
      "content": "Technical summary of what was changed...",
      "word_count": 52
    },
    // ... other sections ...
    "total_word_count": 287,
    "sources_used": ["github", "jira", "confluence"],
    "generation_time_seconds": 18.5
  },
  "sources_attempted": 4,
  "sources_successful": 3,
  "partial_failure": true
}
```

### 3. Test Error Handling

```bash
# Test invalid GitHub URL
curl -X POST http://localhost:8000/v1/summary \
  -H "Content-Type: application/json" \
  -d '{
    "github_pr_url": "invalid-url",
    "jira_ticket_id": "PROJ-456"
  }'

# Should return 400 with validation error
```

## Frontend Usage (if available)

1. Open browser to `http://localhost:3000`
2. Enter GitHub PR URL: `https://github.com/your-org/your-repo/pull/123`
3. Enter Jira ticket ID: `PROJ-456`
4. Click "Generate Summary"
5. Wait 15-30 seconds for processing
6. Review the 6-section summary output
7. Use "Copy Summary" button to copy formatted text

## Testing Framework Validation

### Run Unit Tests

```bash
cd backend
pytest tests/unit/ -v --cov=src --cov-report=html
```

Expected: >80% code coverage, all tests passing

### Run Integration Tests

```bash
# Test external service integrations (requires valid credentials)
pytest tests/integration/ -v -s
```

### Run Contract Tests

```bash
# Validate API responses match OpenAPI specification
pytest tests/contract/ -v
```

## Performance Validation

### Load Testing

```bash
# Install load testing tool
pip install locust

# Run load test (10 concurrent users, 2 minute test)
cd backend/tests/load
locust -f locustfile.py --host=http://localhost:8000 -u 10 -r 2 -t 120s --headless
```

Expected results:
- Average response time: <30 seconds
- 95th percentile: <45 seconds  
- Error rate: <5%
- Memory usage: <2GB per request

### Memory Monitoring

```bash
# Monitor memory usage during processing
python backend/scripts/memory_monitor.py --duration=300 --interval=5
```

## Common Issues & Solutions

### 1. Authentication Failures

**Symptoms**: 401 errors, "authentication_failed" responses

**Solutions**:
- Verify API tokens are correctly set in `.env`
- Check token permissions (GitHub repo access, Jira project access)
- Ensure service account has Google Drive/Docs viewer permissions

### 2. Timeout Errors

**Symptoms**: 408 responses, "processing_timeout" errors

**Solutions**:
- Increase timeout values in `.env`
- Check network connectivity to external services
- Reduce concurrent processing load

### 3. Rate Limiting

**Symptoms**: 429 responses, slow processing

**Solutions**:
- Add delays between requests during testing
- Verify API quota limits with service providers
- Implement exponential backoff in production

### 4. Partial Failures

**Symptoms**: Summaries generated but `partial_failure: true`

**Solutions**:
- Check individual service configurations
- Review logs for specific service errors
- Acceptable for degraded operation (system continues with available data)

## Development Workflow

### 1. Code Quality Checks

```bash
# Type checking
mypy backend/src/

# Linting  
flake8 backend/src/

# Code formatting
black backend/src/
```

### 2. Pre-commit Setup

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### 3. Documentation Updates

```bash
# Generate API documentation
cd backend
python scripts/generate_docs.py

# Update OpenAPI spec from code
python scripts/update_openapi.py
```

## Next Steps

### Feature Development
1. Review [tasks.md](tasks.md) for implementation priorities
2. Start with User Story 1 (Basic PR Summary Generation)
3. Follow TDD approach: write tests first, then implement

### Production Deployment
1. Set up CI/CD pipeline with GitHub Actions
2. Configure production environment variables
3. Set up monitoring and alerting
4. Deploy to containerized environment (Docker/Kubernetes)

### Monitoring Setup
1. Configure structured logging aggregation
2. Set up performance metrics collection
3. Create alerting rules for error rates and response times
4. Implement user feedback collection

## Validation Checklist

- [ ] All services return "healthy" in health check
- [ ] Can generate summary with valid GitHub PR and Jira ticket
- [ ] Error handling works for invalid inputs
- [ ] Unit tests pass with >80% coverage
- [ ] Integration tests pass with real API credentials
- [ ] Load testing shows acceptable performance
- [ ] Memory usage stays under 2GB per request
- [ ] Frontend (if available) successfully displays summaries

**Success Criteria**: All checklist items completed indicates system is ready for development and testing of additional features.

## Support

- **Technical Issues**: Check logs in `backend/logs/`
- **API Documentation**: `http://localhost:8000/docs`
- **Configuration Help**: Review `.env.example` and data models
- **Performance Issues**: Use built-in monitoring endpoints at `/v1/health`

This quickstart guide ensures rapid setup validation and provides the foundation for feature development following the constitutional requirements for code quality, testing, and performance.