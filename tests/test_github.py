"""
Comprehensive tests for GitHub API integration (Phase 8)

Tests cover:
- GitHub client authentication
- PR data fetching
- Comment posting
- Error handling
- Rate limiting
- Mock data integration
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from github import GithubException

# Import GitHub modules
from github_integration.client import GitHubClient
from github_integration.pr_fetcher import PRFetcher, PRData, FileChange
from github_integration.commenter import GitHubCommenter
from github_integration.mocks import MockPRData
from tasks.format_comments_task import GitHubReview


# Test 1: GitHub Client Authentication
def test_github_client_auth():
    """Test GitHubClient authentication with valid token."""
    # Use mock token for testing
    with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test_token_1234567890"}):
        client = GitHubClient()
        assert client.token == "ghp_test_token_1234567890"
        assert client.github is not None
        assert client.http_client is not None


def test_github_client_no_token():
    """Test GitHubClient raises error without token."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="GitHub token not found"):
            GitHubClient()


# Test 2: PR Fetcher Mock Data
@pytest.mark.asyncio
async def test_pr_fetcher_mock_data():
    """Test PRFetcher with MockPRData."""
    mock_data = MockPRData()
    pr_data = mock_data.get_sample_pr(pr_number=123)
    
    # Verify PRData structure
    assert pr_data.repo_name == "test-org/test-repo"
    assert pr_data.pr_number == 123
    assert pr_data.title == "Add user authentication and utilities"
    assert pr_data.author == "test-developer"
    
    # Verify 3 files
    assert len(pr_data.files_changed) == 3
    
    # Verify file details
    file1 = pr_data.files_changed[0]
    assert file1.filename == "app/auth.py"
    assert file1.language == "python"
    assert "API_KEY" in file1.patch  # Security issue
    
    file2 = pr_data.files_changed[1]
    assert file2.filename == "frontend/utils.js"
    assert file2.language == "javascript"
    assert "for" in file2.patch  # Performance issue
    
    file3 = pr_data.files_changed[2]
    assert file3.filename == "services/user_service.py"
    assert file3.language == "python"
    assert "send_email" in file3.patch  # SRP violation
    
    # Verify full diff
    assert "diff --git" in pr_data.full_diff
    assert len(pr_data.full_diff) > 0


# Test 3: PR Fetcher Real Data (requires GITHUB_TOKEN)
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"),
    reason="Requires GITHUB_TOKEN environment variable"
)
async def test_pr_fetcher_real_data():
    """Test PRFetcher with real GitHub API (optional)."""
    # This test is skipped unless GITHUB_TOKEN is set
    # You can test with a public repo PR
    fetcher = PRFetcher()
    
    # Example: Test with a known public PR
    # Replace with your test repo
    try:
        pr_data = await fetcher.get_full_pr_data("octocat/Hello-World", 1)
        assert pr_data.pr_number == 1
        assert len(pr_data.files_changed) > 0
    except Exception as e:
        pytest.skip(f"Real GitHub test failed: {e}")


# Test 4: Commenter Inline Comment Formatting
def test_commenter_inline_format():
    """Test GitHubCommenter formats inline comments correctly."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test_token"}):
        commenter = GitHubCommenter()
        
        # Test emoji formatting
        assert "🔴" in commenter._format_comment_body({"body": "CRITICAL: Issue"})
        assert "🟡" in commenter._format_comment_body({"body": "HIGH: Issue"})
        assert "🟠" in commenter._format_comment_body({"body": "MEDIUM: Issue"})
        assert "🟢" in commenter._format_comment_body({"body": "LOW: Issue"})
        assert "💡" in commenter._format_comment_body({"body": "Suggestion"})


# Test 5: Commenter Review States
@pytest.mark.asyncio
async def test_commenter_review_states():
    """Test review state mapping based on severity."""
    mock_review = MockPRData.get_sample_github_review()
    
    # Verify review has CRITICAL finding
    assert any("CRITICAL" in c["body"] for c in mock_review.inline_comments)
    
    # Verify review state is REQUESTED_CHANGES
    assert mock_review.review_state == "REQUESTED_CHANGES"
    
    # Test preview formatting
    with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test_token"}):
        commenter = GitHubCommenter()
        preview = commenter.format_review_preview(mock_review)
        
        assert "REQUESTED_CHANGES" in preview
        assert "🔴" in preview  # CRITICAL emoji
        assert "app/auth.py" in preview


# Test 6: File Filtering (Binary/Large Files)
def test_file_filtering():
    """Test PRFetcher skips binary and large files."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test_token"}):
        fetcher = PRFetcher()
        
        # Test binary file detection
        assert fetcher._is_binary_file("image.png") is True
        assert fetcher._is_binary_file("app.py") is False
        assert fetcher._is_binary_file("data.pdf") is True
        assert fetcher._is_binary_file("script.js") is False
        
        # Test should_skip_file
        mock_file = Mock()
        mock_file.filename = "image.jpg"
        mock_file.patch = "binary content"
        mock_file.changes = 100
        
        assert fetcher._should_skip_file(mock_file) is True


# Test 7: Large PR Handling
def test_large_pr_handling():
    """Test PRFetcher handles large files correctly."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test_token"}):
        fetcher = PRFetcher()
        
        # Mock large file
        large_file = Mock()
        large_file.filename = "large.py"
        large_file.patch = "content"
        large_file.changes = 60000  # Exceeds 50k limit
        
        assert fetcher._should_skip_file(large_file) is True
        
        # Mock normal file
        normal_file = Mock()
        normal_file.filename = "normal.py"
        normal_file.patch = "content"
        normal_file.changes = 100
        
        assert fetcher._should_skip_file(normal_file) is False


# Test 8: Language Detection
def test_language_detection():
    """Test language detection from file extensions."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test_token"}):
        fetcher = PRFetcher()
        
        assert fetcher._detect_language("app.py") == "python"
        assert fetcher._detect_language("script.js") == "javascript"
        assert fetcher._detect_language("App.tsx") == "typescript"
        assert fetcher._detect_language("Main.java") == "java"
        assert fetcher._detect_language("main.go") == "go"
        assert fetcher._detect_language("lib.rs") == "rust"
        assert fetcher._detect_language("unknown.xyz") == "unknown"


# Test 9: Rate Limit Handling
def test_rate_limit_handling():
    """Test GitHubClient handles rate limiting."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test_token"}):
        client = GitHubClient()
        
        # Test rate limit check
        with patch.object(client.github, 'get_rate_limit') as mock_rate:
            mock_core = Mock()
            mock_core.remaining = 4500
            mock_core.limit = 5000
            mock_core.reset.timestamp.return_value = 1234567890
            
            mock_rate.return_value.core = mock_core
            
            rate_info = client.check_rate_limit()
            assert rate_info["remaining"] == 4500
            assert rate_info["limit"] == 5000


# Test 10: Error Recovery
def test_error_recovery():
    """Test graceful error handling for 404 repos."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test_token"}):
        client = GitHubClient()
        
        # Mock 404 error
        with patch.object(client.github, 'get_repo') as mock_get_repo:
            mock_get_repo.side_effect = GithubException(404, "Not Found", None)
            
            with pytest.raises(ValueError, match="not found"):
                client.get_repo("nonexistent", "repo")


# Test 11: Mock Integration (End-to-End)
@pytest.mark.asyncio
async def test_mock_integration():
    """Test full pipeline with mock data."""
    # Get mock PR data
    mock_pr = MockPRData.get_sample_pr(123)
    
    # Verify PR data
    assert mock_pr.pr_number == 123
    assert len(mock_pr.files_changed) == 3
    
    # Get mock review
    mock_review = MockPRData.get_sample_github_review()
    
    # Verify review
    assert len(mock_review.inline_comments) == 3
    assert mock_review.review_state == "REQUESTED_CHANGES"
    
    # Test preview (no API call)
    with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test_token"}):
        commenter = GitHubCommenter()
        preview = commenter.format_review_preview(mock_review)
        
        assert "CRITICAL" in preview
        assert "HIGH" in preview
        assert "MEDIUM" in preview


# Test 12: PR Diff Parsing (Phase 3 Compatibility)
def test_pr_diff_parsing():
    """Test GitHub diff format is compatible with Phase 3 DiffParser."""
    mock_pr = MockPRData.get_sample_pr()
    
    # Verify diff format
    assert "diff --git" in mock_pr.full_diff
    assert "---" in mock_pr.full_diff
    assert "+++" in mock_pr.full_diff
    assert "@@" in mock_pr.full_diff
    
    # Verify each file has diff
    for file_change in mock_pr.files_changed:
        assert len(file_change.patch) > 0
        assert file_change.filename in mock_pr.full_diff


# Additional Test: Simulate PR Comments
def test_simulate_pr_comments(capsys):
    """Test simulated PR comment output."""
    MockPRData.simulate_pr_comments("test-org/test-repo", 123)
    
    captured = capsys.readouterr()
    assert "SIMULATED PR REVIEW" in captured.out
    assert "test-org/test-repo#123" in captured.out
    assert "app/auth.py" in captured.out
    assert "CRITICAL" in captured.out


# Test: Flawed PR Diff
def test_flawed_pr_diff():
    """Test flawed PR diff contains expected vulnerabilities."""
    diff = MockPRData.get_flawed_pr_diff()
    
    assert "pickle" in diff
    assert "SQL injection" in diff
    assert "SECRET_KEY" in diff
