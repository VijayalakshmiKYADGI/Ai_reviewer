"""
GitHub API Integration Module

Provides production-ready GitHub client for:
- Fetching PR data and diffs
- Posting inline code review comments
- Mock data for testing without API calls
"""

from .client import GitHubClient
from .pr_fetcher import PRFetcher, PRData, FileChange
from .commenter import GitHubCommenter
from .mocks import MockPRData

__all__ = [
    "GitHubClient",
    "PRFetcher",
    "PRData",
    "FileChange",
    "GitHubCommenter",
    "MockPRData",
]
