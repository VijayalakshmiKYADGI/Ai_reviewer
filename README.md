# AI Code Reviewer 🤖

**Auto-scaling, AI-powered Code Review System using Google Gemini 2.0 and CrewAI**

Review Pull Requests automatically with an autonomous agent team. Identify bugs, security vulnerabilities, and performance issues instantly.

🚀 **LIVE DEMO**: `https://code-review-crew.up.railway.app/health`

## 🌟 FREE & OPEN SOURCE PRODUCTION SETUP

Deploy this entire system for **$0/month** using our recommended free stack.

### Quick Start (5 Minutes)

1. **Railway (Free Web Hosting)**
   ```bash
   npm install -g @railway/cli
   railway login && railway up
   ```

2. **Supabase (Free Postgres Database)**
   - Create free project at [supabase.com](https://supabase.com)
   - Run SQL from `deploy/supabase.sql` in their SQL Editor.

3. **Configure Secrets**
   Set `DATABASE_URL`, `GEMINI_API_KEY`, etc. in Railway Dashboard.

4. **GitHub App Webhook**
   Point your App's webhook to your Railway URL.

**COST**: ₹0/month | **USAGE**: Unlimited | **LICENSE**: MIT

---

## Features

- **Phase 1-7**: Complete CrewAI pipeline with FastAPI backend
- **Phase 8**: GitHub API integration for PR fetching and commenting
- Multi-agent code review (security, performance, architecture, testing)
- Real-time PR analysis with inline comments
- Mock data support for testing without GitHub API

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.template` to `.env` and fill in your credentials:
```bash
cp .env.template .env
```

Required environment variables:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `GITHUB_TOKEN`: Personal Access Token with `repo` and `pull_requests` scopes (Phase 8)

### 3. Run Validation
```bash
# Validate Phase 8 GitHub integration
python validate_phase8.py

# Run all tests
pytest tests/test_github.py -v
```

### 4. Start FastAPI Server
```bash
uvicorn api.main:app --reload
```

## GitHub Integration (Phase 8)

The system can now:
- Fetch PR data and diffs from GitHub
- Post inline code review comments
- Set review states (APPROVED, COMMENTED, REQUESTED_CHANGES)

### Usage Example
```python
from github_integration import PRFetcher, GitHubCommenter, MockPRData

# Use mock data for testing
mock_pr = MockPRData.get_sample_pr(123)
print(f"Analyzing PR: {mock_pr.title}")
print(f"Files changed: {len(mock_pr.files_changed)}")

# Or fetch real PR data
fetcher = PRFetcher()
pr_data = await fetcher.get_full_pr_data("owner/repo", 1)
```

## Project Status

✅ Phase 1-7: Complete (CrewAI pipeline + FastAPI)  
✅ Phase 8: Complete (GitHub API integration)  
🔜 Phase 9: Webhook integration  
🔜 Phase 10: GitHub App deployment
h
python -m venv venv
venv\Scripts\activate
```