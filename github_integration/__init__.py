"""
GitHub API Integration Module

Provides production-ready GitHub client for:
- Fetching PR data and diffs
- Posting inline code review comments
- Mock data for testing without API calls
- Webhook event handling (Phase 9)
"""

from .client import GitHubClient
from .pr_fetcher import PRFetcher, PRData, FileChange
from .commenter import GitHubCommenter
from .mocks import MockPRData
from .webhook_handler import WebhookHandler
from .signature import verify_webhook_signature, generate_webhook_signature

__all__ = [
    "GitHubClient",
    "PRFetcher",
    "PRData",
    "FileChange",
    "GitHubCommenter",
    "MockPRData",
    "WebhookHandler",
    "verify_webhook_signature",
    "generate_webhook_signature",
]
