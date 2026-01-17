"""
GitHubClient - Authenticated GitHub API client

Handles:
- Personal Access Token authentication
- Rate limiting with exponential backoff
- Error handling and retries
- Future GitHub App support
"""

import os
import time
from typing import Optional, Dict, Any
from github import Github, GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository
import httpx
from dotenv import load_dotenv

load_dotenv()


class GitHubClient:
    """Authenticated GitHub API client with rate limiting and error handling."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client with authentication.
        
        Args:
            token: GitHub Personal Access Token. If None, reads from GITHUB_TOKEN env var.
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token not found. Set GITHUB_TOKEN environment variable "
                "or pass token to GitHubClient constructor."
            )
        
        # Initialize PyGithub client
        self.github = Github(self.token)
        
        # Async HTTP client for additional API calls
        self.http_client = httpx.AsyncClient(
            headers={
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            },
            timeout=30.0
        )
        
    def _handle_rate_limit(self, retry_count: int = 0, max_retries: int = 3):
        """
        Handle rate limiting with exponential backoff.
        
        Args:
            retry_count: Current retry attempt
            max_retries: Maximum number of retries
        """
        if retry_count >= max_retries:
            raise Exception(f"Max retries ({max_retries}) exceeded for rate limiting")
        
        # Exponential backoff: 2^retry_count seconds
        wait_time = 2 ** retry_count
        print(f"Rate limit hit. Waiting {wait_time}s before retry {retry_count + 1}/{max_retries}...")
        time.sleep(wait_time)
    
    def get_repo(self, owner: str, repo: str) -> Repository:
        """
        Get repository object.
        
        Args:
            owner: Repository owner (username or org)
            repo: Repository name
            
        Returns:
            Repository object
            
        Raises:
            GithubException: If repo not found or access denied
        """
        retry_count = 0
        while retry_count < 3:
            try:
                return self.github.get_repo(f"{owner}/{repo}")
            except GithubException as e:
                if e.status == 429:  # Rate limit
                    self._handle_rate_limit(retry_count)
                    retry_count += 1
                elif e.status == 404:
                    raise ValueError(f"Repository {owner}/{repo} not found")
                elif e.status == 403:
                    raise ValueError(f"Access denied to {owner}/{repo}. Check token permissions.")
                else:
                    raise
        
        raise Exception("Failed to get repository after retries")
    
    def get_pr(self, owner: str, repo: str, pr_number: int) -> PullRequest:
        """
        Get pull request object.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            PullRequest object
            
        Raises:
            GithubException: If PR not found
        """
        retry_count = 0
        while retry_count < 3:
            try:
                repository = self.get_repo(owner, repo)
                return repository.get_pull(pr_number)
            except GithubException as e:
                if e.status == 429:
                    self._handle_rate_limit(retry_count)
                    retry_count += 1
                elif e.status == 404:
                    raise ValueError(f"PR #{pr_number} not found in {owner}/{repo}")
                else:
                    raise
        
        raise Exception("Failed to get PR after retries")
    
    async def get_pr_data(self, repo: str, pr_number: int) -> Dict[str, Any]:
        """
        Fetch PR metadata via REST API.
        
        Args:
            repo: Full repo name (owner/repo)
            pr_number: PR number
            
        Returns:
            Dict with PR data
        """
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
        
        retry_count = 0
        while retry_count < 3:
            try:
                response = await self.http_client.get(url)
                
                if response.status_code == 429:
                    self._handle_rate_limit(retry_count)
                    retry_count += 1
                    continue
                
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ValueError(f"PR #{pr_number} not found in {repo}")
                elif e.response.status_code == 403:
                    raise ValueError(f"Access denied. Check token permissions.")
                else:
                    raise
        
        raise Exception("Failed to get PR data after retries")
    
    async def create_review(
        self,
        repo: str,
        pr_number: int,
        body: str,
        event: str,
        comments: list[Dict[str, Any]]
    ) -> str:
        """
        Create a PR review with inline comments.
        
        Args:
            repo: Full repo name (owner/repo)
            pr_number: PR number
            body: Review summary comment
            event: Review event (COMMENT, APPROVE, REQUEST_CHANGES)
            comments: List of inline comments with path, position, body
            
        Returns:
            Review ID
        """
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
        
        payload = {
            "body": body,
            "event": event,
            "comments": comments
        }
        
        retry_count = 0
        while retry_count < 3:
            try:
                response = await self.http_client.post(url, json=payload)
                
                if response.status_code == 429:
                    self._handle_rate_limit(retry_count)
                    retry_count += 1
                    continue
                
                response.raise_for_status()
                result = response.json()
                return str(result.get("id", ""))
            
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 422:
                    raise ValueError(f"Invalid review data: {e.response.text}")
                else:
                    raise
        
        raise Exception("Failed to create review after retries")
    
    async def get_installation_token(self, installation_id: int) -> str:
        """
        Get installation access token for GitHub App (Phase 10).
        
        Args:
            installation_id: GitHub App installation ID
            
        Returns:
            Installation access token
            
        Note:
            This is a placeholder for Phase 10 GitHub App integration.
            Currently raises NotImplementedError.
        """
        raise NotImplementedError(
            "GitHub App authentication will be implemented in Phase 10. "
            "Currently using Personal Access Token authentication."
        )
    
    def check_rate_limit(self) -> Dict[str, int]:
        """
        Check current rate limit status.
        
        Returns:
            Dict with remaining, limit, and reset timestamp
        """
        rate_limit = self.github.get_rate_limit()
        return {
            "remaining": rate_limit.core.remaining,
            "limit": rate_limit.core.limit,
            "reset": int(rate_limit.core.reset.timestamp())
        }
    
    async def close(self):
        """Close async HTTP client."""
        await self.http_client.aclose()
