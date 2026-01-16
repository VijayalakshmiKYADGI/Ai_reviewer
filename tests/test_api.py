"""
Tests for FastAPI Backend.
Verifies endpoints, middleware, and logic availability.
"""
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app
from tasks.format_comments_task import GitHubReview

client = TestClient(app)

def test_health_endpoint():
    """Test /health returns 200 and status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "uptime" in data

def test_pr_review_endpoint_queued():
    """Test POST /review/pr returns 202 queued."""
    with patch("api.endpoints.pr_review.save_review_start") as mock_save:
        mock_save.return_value = 1
        
        payload = {
            "repo_name": "test-repo",
            "pr_number": 1,
            "pr_url": "http://github.com/test",
            "diff_content": "diff",
            "files_changed": ["main.py"]
        }
        response = client.post("/review/pr", json=payload)
        
        if response.status_code != 202:
            print(response.json()) # For debug
            
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"
        assert data["review_id"] == 1

def test_file_review_endpoint_sync():
    """Test POST /review/file returns 200 and result."""
    # We mock execution to avoid waiting for LLM
    with patch("api.endpoints.file_review.execute_review_pipeline") as mock_exec:
        # Mock result
        mock_exec.return_value = GitHubReview(
            inline_comments=[], 
            summary_comment="Done", 
            review_state="APPROVED"
        )
        
        files = {'file': ('test.py', 'print("hello")', 'text/x-python')}
        data = {'repo_name': 'test', 'pr_number': '1'}
        
        response = client.post("/review/file", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed"
        assert result["github_review"]["review_state"] == "APPROVED"

def test_cors_headers():
    """Test CORS options."""
    origin = "http://github.com"
    response = client.options("/health", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code == 200
    # Starlette/FastAPI reflects origin when credentials allowed
    assert response.headers["access-control-allow-origin"] in ["*", origin]

def test_rate_limiting():
    """Test rate limiter works."""
    # Run this LAST to avoid side effects
    
    # We make 11 requests.
    for _ in range(11):
        response = client.get("/health")
        
    # The 11th should fail
    assert response.status_code == 429
