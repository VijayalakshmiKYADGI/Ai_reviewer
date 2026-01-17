"""
GitHubClient - Authenticated GitHub API client

Handles:
- Personal Access Token authentication (Phase 8)
- GitHub App JWT + Installation tokens (Phase 10)
- Rate limiting with exponential backoff
- Error handling and retries
"""

import os
import time
from typing import Optional, Dict, Any, Literal
from github import Github, GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository
import httpx
from dotenv import load_dotenv
import structlog

load_dotenv()

logger = structlog.get_logger()


class GitHubClient:
    """Authenticated GitHub API client with dual-mode authentication and rate limiting."""
    
    def __init__(
        self,
        auth_mode: Literal["token", "app"] = "token",
        token: Optional[str] = None
    ):
        """
        Initialize GitHub client with authentication.
        
        Args:
            auth_mode: Authentication mode - "token" for PAT, "app" for GitHub App
            token: GitHub Personal Access Token (for "token" mode). If None, reads from env.
        """
        self.auth_mode = auth_mode
        self.token = None
        self.app_auth = None
        self.installation_manager = None
        
        if auth_mode == "token":
            # Personal Access Token mode (Phase 8)
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
            
            logger.info("github_client_initialized", auth_mode="token")
        
        elif auth_mode == "app":
            # GitHub App mode (Phase 10)
            try:
                from .app_auth import GitHubAppAuth
                from .installation import InstallationManager
                from config.app_config import GitHubAppConfig
                
                # Load config
                config = GitHubAppConfig.from_env()
                
                # Initialize App auth
                self.app_auth = GitHubAppAuth(
                    app_id=config.app_id,
                    private_key_path=config.private_key_path
                )
                
                # Initialize installation manager
                self.installation_manager = InstallationManager()
                
                # HTTP client (will be updated with installation token per request)
                self.http_client = httpx.AsyncClient(
                    headers={"Accept": "application/vnd.github.v3+json"},
                    timeout=30.0
                )
                
                # PyGithub client will be initialized with installation token
                self.github = None
                
                logger.info("github_client_initialized", auth_mode="app", app_id=config.app_id)
            
            except Exception as e:
                logger.error("app_auth_failed", error=str(e))
                
                # Fallback to token mode
                logger.warning("falling_back_to_token_auth")
                self.auth_mode = "token"
                self.token = os.getenv("GITHUB_TOKEN")
                
                if not self.token:
                    raise ValueError(
                        f"GitHub App authentication failed: {e}. "
                        "Fallback to token mode also failed (no GITHUB_TOKEN)."
                    )
                
                self.github = Github(self.token)
                self.http_client = httpx.AsyncClient(
                    headers={
                        "Authorization": f"token {self.token}",
                        "Accept": "application/vnd.github.v3+json"
                    },
                    timeout=30.0
                )
        
        else:
            raise ValueError(f"Invalid auth_mode: {auth_mode}. Must be 'token' or 'app'.")
    
    async def get_access_token(self, repo_full_name: Optional[str] = None) -> str:
        """
        Get access token for API requests.
        
        Args:
            repo_full_name: Full repository name (owner/repo) - required for app mode
            
        Returns:
            Access token (PAT or installation token)
        """
        if self.auth_mode == "token":
            return self.token
        
        elif self.auth_mode == "app":
            # Get installation ID for repo
            if not repo_full_name:
                raise ValueError("repo_full_name required for app mode")
            
            installation_id = await self.installation_manager.get_installation_id(repo_full_name)
            
            if not installation_id:
                raise ValueError(f"No installation found for {repo_full_name}")
            
            # Get installation token
            installation_token = await self.app_auth.get_installation_token(installation_id)
            
            return installation_token
        
        return ""

        
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
