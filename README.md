# PR Summarizer

> **AI-Powered Pull Request Analysis and Summarization Tool**  
> *A Proof of Concept for SpecKit*  
> **🤖 Entirely Built by AI using VS Code, GitHub Copilot & Claude Sonnet 4**

## 🎯 Purpose

PR Summarizer is an intelligent tool that automatically analyzes GitHub pull requests and generates comprehensive summaries using AI. This project serves as a **Proof of Concept for SpecKit**, demonstrating how AI can streamline code review processes and improve development team productivity.

### 🚀 AI-Generated Architecture
This entire project structure, codebase, and documentation was **created by AI** using:
- **VS Code** as the development environment
- **GitHub Copilot** for code generation and suggestions  
- **Claude Sonnet 4** for architectural decisions and comprehensive development

This showcases the power of AI-assisted development in creating production-ready applications from concept to completion.

### Key Features

- 🤖 **AI-Powered Analysis** - Uses Google Gemini 2.0 Flash for intelligent code analysis
- 🔗 **GitHub Integration** - Real-time pull request data extraction via GitHub API
- 📊 **Comprehensive Insights** - Business context, technical analysis, and risk assessment
- 🎯 **Reviewer Guidance** - Automated suggestions for code reviewers
- 🚀 **Fast Processing** - Complete analysis in ~8 seconds
- 🔧 **Extensible Architecture** - Ready for Jira and Confluence integration

## 🏗️ Technical Architecture

### Backend (FastAPI + Python)
```
backend/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── models/                 # Pydantic data models
│   │   ├── context.py         # Integration context models
│   │   ├── pr_summary.py      # PR summary response models
│   │   └── request.py         # API request models
│   ├── services/              # Core business logic
│   │   ├── github.py          # GitHub API integration
│   │   ├── gemini.py          # Google Gemini AI service
│   │   └── summary_service.py # Orchestration service
│   ├── routers/               # API route handlers
│   │   └── summary.py         # Summary generation endpoints
│   └── utils/                 # Utilities and helpers
├── tests/                     # Test suites
└── requirements.txt           # Python dependencies
```

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── components/            # React components
│   ├── pages/                 # Application pages
│   ├── services/              # API client services
│   └── types/                 # TypeScript type definitions
├── public/                    # Static assets
└── package.json              # Node.js dependencies
```

### Key Technologies

- **Backend**: FastAPI, Python 3.11+, Google Generative AI SDK, PyGithub, httpx
- **Frontend**: React, TypeScript, Tailwind CSS
- **AI**: Google Gemini 2.0 Flash
- **APIs**: GitHub REST API v3
- **Authentication**: GitHub Personal Access Tokens

## 🚀 Local Setup

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Git
- GitHub Personal Access Token
- Google AI API Key

### 1. Clone Repository

```bash
git clone https://github.com/gyapaarachchi-ifs/PR_Summarizer.git
cd PR_Summarizer
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment configuration
cp .env.example .env
```

### 3. Configure Environment Variables

Edit `backend/.env` with your API credentials:

```env
# GitHub Configuration (REQUIRED)
GITHUB_TOKEN="your_github_personal_access_token"

# Google Gemini AI Configuration (REQUIRED)  
GOOGLE_API_KEY="your_google_ai_api_key"

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### Getting API Keys

**GitHub Token:**
1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Create a "Classic" personal access token
3. Select scopes: `repo`, `read:org` (for private repositories)

**Google AI API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the generated key

### 4. Start Backend Server

```bash
# From backend directory
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### 5. Frontend Setup (Optional)

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Start development server
npm start
```

The frontend will be available at `http://localhost:3000`

## 📝 API Usage

### Generate PR Summary

**Endpoint:** `POST /api/v1/summary/generate`

**Request Body:**
```json
{
  "github_pr_url": "https://github.com/owner/repo/pull/123",
  "jira_ticket_id": "PROJ-456"  // Optional
}
```

**Response:**
```json
{
  "id": "summary-1760433064",
  "github_pr_url": "https://github.com/owner/repo/pull/123",
  "business_context": "This PR implements user authentication...",
  "code_change_summary": "Added OAuth integration with 3 new components...",
  "business_code_impact": "Enhances security and user experience...",
  "suggested_test_cases": [
    "Test OAuth login flow",
    "Test token expiration handling",
    "Test error scenarios"
  ],
  "risk_complexity": "Medium complexity - requires security review",
  "reviewer_guidance": "Focus on authentication logic and security patterns",
  "status": "completed",
  "created_at": "2025-10-14T14:41:04Z"
}
```

### Health Check

**Endpoint:** `GET /health`

Returns API health status and version information.

## 🧪 Testing

### Test with Your Own PR

```bash
# From backend directory
cd backend

# Test with a public PR
python -c "
import asyncio
import sys
sys.path.append('src')
from services.summary_service import SummaryOrchestrationService
from models.request import SummaryRequest

async def test():
    service = SummaryOrchestrationService()
    request = SummaryRequest(github_pr_url='https://github.com/your-username/your-repo/pull/1')
    result = await service.generate_summary(request)
    print(f'Summary: {result.code_change_summary}')

asyncio.run(test())
"
```

### Run Test Suite

```bash
# Backend tests
cd backend
pytest

# Frontend tests  
cd frontend
npm test
```

## 🔧 Development

### Project Structure Principles

- **Separation of Concerns**: Clear separation between data models, business logic, and API layers
- **Dependency Injection**: Services are loosely coupled and easily testable
- **Error Handling**: Comprehensive error handling with structured logging
- **Type Safety**: Full TypeScript support in frontend, Pydantic models in backend
- **Async/Await**: Non-blocking operations for optimal performance

### Adding New Features

1. **New AI Service**: Implement in `src/services/` with proper error handling
2. **New Data Source**: Add integration context in `src/models/context.py`
3. **New API Endpoint**: Create router in `src/routers/` and register in `main.py`
4. **New Frontend Component**: Add to `frontend/src/components/` with TypeScript types

## 🌟 Current Capabilities

- ✅ **Real GitHub API Integration** - Fetches PR data, files, commits, and metadata
- ✅ **Google Gemini AI Analysis** - Intelligent code analysis and summary generation
- ✅ **Structured Output** - Consistent JSON responses with business and technical insights
- ✅ **Error Handling** - Comprehensive error handling and logging
- ✅ **Performance Optimized** - Fast processing with async operations
- ✅ **Production Ready** - Environment configuration and security best practices

## 🚧 Planned Features (Future User Stories)

- 🔄 **Jira Integration** - Link PR analysis with Jira tickets
- 📚 **Confluence Integration** - Enhanced business context from documentation
- 🎨 **Frontend UI** - React-based web interface for easy PR analysis
- 📊 **Analytics Dashboard** - Team productivity and code quality metrics
- 🔔 **Webhook Integration** - Automatic analysis on PR creation/updates
- 💾 **Caching Layer** - Redis-based caching for improved performance
- 🔐 **Authentication** - User management and access control
- 📈 **Historical Analysis** - Track code quality trends over time

## � AI Development Showcase

This project demonstrates the capabilities of modern AI-assisted development:

### Development Stack
- **Primary IDE**: VS Code with AI extensions
- **Code Generation**: GitHub Copilot for intelligent code completion
- **Architectural Planning**: Claude Sonnet 4 for system design and implementation
- **End-to-End Development**: Complete project built through AI collaboration

### AI Development Highlights
- ✅ **Project Architecture** - Full FastAPI + React structure designed by AI
- ✅ **Code Implementation** - All services, models, and utilities generated with AI assistance
- ✅ **Integration Logic** - GitHub API and Google Gemini AI integration crafted by AI
- ✅ **Error Handling** - Comprehensive error handling patterns implemented by AI
- ✅ **Documentation** - This entire README and code documentation created by AI
- ✅ **Testing & Debugging** - AI-guided debugging and validation processes

### Development Workflow
1. **Conceptual Design** - AI analyzed requirements and proposed technical architecture
2. **Iterative Development** - AI generated code, identified issues, and refined implementation
3. **Integration Testing** - AI debugged service integrations and data flow
4. **Documentation** - AI created comprehensive project documentation
5. **Production Readiness** - AI ensured best practices and deployment preparation

This project serves as a testament to the productivity gains possible when human creativity meets AI-powered development tools.

## �🤝 Contributing

This is a Proof of Concept for SpecKit. For contributions or questions:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

[Add your license information here]

## 🎯 SpecKit Integration

This project demonstrates core capabilities that will be integrated into SpecKit:

- **AI-Powered Code Analysis**
- **Multi-Source Data Integration** 
- **Automated Documentation Generation**
- **Developer Productivity Enhancement**

The architecture and patterns established here will inform the design of SpecKit's comprehensive development toolkit.

---

**Built with ❤️ as a SpecKit Proof of Concept**