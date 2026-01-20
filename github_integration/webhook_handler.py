"""
WebhookHandler - Process GitHub PR webhook events

Handles real-time PR events from GitHub webhooks:
- pull_request.opened → Full review
- pull_request.synchronize → Incremental review
- pull_request.reopened → Full review
"""

import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from .pr_fetcher import PRFetcher, PRData
from .commenter import GitHubCommenter
from .client import GitHubClient
from tasks.format_comments_task import GitHubReview
from data.models import ReviewInput

logger = structlog.get_logger()


class WebhookHandler:
    """Process GitHub webhook events and trigger code reviews."""
    
    def __init__(self):
        """Initialize webhook handler with GitHub clients."""
        self.client = GitHubClient()
        self.pr_fetcher = PRFetcher(self.client)
        self.commenter = GitHubCommenter(self.client)
    
    async def process_pr_event(
        self,
        payload: Dict[str, Any],
        delivery_id: str
    ) -> Dict[str, Any]:
        """
        Process a pull request webhook event.
        
        Args:
            payload: GitHub webhook payload
            delivery_id: X-GitHub-Delivery header value
            
        Returns:
            Dict with processing results
            
        Raises:
            Exception: If processing fails
        """
        try:
            # Extract event details
            action = payload.get("action", "")
            pr_data = payload.get("pull_request", {})
            repo_data = payload.get("repository", {})
            
            repo_full_name = repo_data.get("full_name", "")
            pr_number = pr_data.get("number", 0)
            
            logger.info(
                "processing_pr_event",
                action=action,
                repo=repo_full_name,
                pr_number=pr_number,
                delivery_id=delivery_id
            )
            
            # Route to appropriate handler
            if action == "opened":
                return await self.handle_opened(payload, delivery_id)
            elif action == "synchronize":
                return await self.handle_synchronize(payload, delivery_id)
            elif action == "reopened":
                return await self.handle_reopened(payload, delivery_id)
            else:
                logger.info(
                    "unsupported_action",
                    action=action,
                    repo=repo_full_name,
                    pr_number=pr_number
                )
                return {
                    "status": "ignored",
                    "action": action,
                    "reason": "Unsupported action"
                }
        
        except Exception as e:
            logger.error(
                "webhook_processing_failed",
                error=str(e),
                delivery_id=delivery_id,
                exc_info=True
            )
            
            # Try to post error comment on PR
            try:
                await self._post_error_comment(payload, str(e))
            except Exception as comment_error:
                logger.error(
                    "failed_to_post_error_comment",
                    error=str(comment_error)
                )
            
            raise
    
    async def handle_opened(
        self,
        payload: Dict[str, Any],
        delivery_id: str
    ) -> Dict[str, Any]:
        """
        Handle pull_request.opened event - Full review.
        
        Args:
            payload: GitHub webhook payload
            delivery_id: Delivery ID
            
        Returns:
            Processing results
        """
        logger.info("handling_pr_opened", delivery_id=delivery_id)
        
        # Extract PR details
        pr_data = payload.get("pull_request", {})
        repo_data = payload.get("repository", {})
        
        repo_full_name = repo_data.get("full_name", "")
        pr_number = pr_data.get("number", 0)
        
        # Fetch full PR data
        pr_info = await self.pr_fetcher.get_full_pr_data(repo_full_name, pr_number)
        
        # Execute review pipeline
        review_result = await self._execute_review_pipeline(pr_info, delivery_id)
        
        # Post review to GitHub
        if review_result:
            review_id = await self.commenter.post_review(
                repo_full_name,
                pr_number,
                review_result
            )
            
            return {
                "status": "completed",
                "action": "opened",
                "review_id": review_id,
                "repo": repo_full_name,
                "pr_number": pr_number
            }
        
        return {
            "status": "failed",
            "action": "opened",
            "reason": "Review pipeline returned no results"
        }
    
    async def handle_synchronize(
        self,
        payload: Dict[str, Any],
        delivery_id: str
    ) -> Dict[str, Any]:
        """
        Handle pull_request.synchronize event - Incremental review.
        
        For Phase 9, we perform full review. Phase 10+ will implement
        incremental review of only new commits.
        
        Args:
            payload: GitHub webhook payload
            delivery_id: Delivery ID
            
        Returns:
            Processing results
        """
        logger.info("handling_pr_synchronize", delivery_id=delivery_id)
        
        # For now, perform full review (same as opened)
        # TODO Phase 10: Implement incremental review
        return await self.handle_opened(payload, delivery_id)
    
    async def handle_reopened(
        self,
        payload: Dict[str, Any],
        delivery_id: str
    ) -> Dict[str, Any]:
        """
        Handle pull_request.reopened event - Full review.
        
        Args:
            payload: GitHub webhook payload
            delivery_id: Delivery ID
            
        Returns:
            Processing results
        """
        logger.info("handling_pr_reopened", delivery_id=delivery_id)
        
        # Perform full review (same as opened)
        return await self.handle_opened(payload, delivery_id)
    
    async def _execute_review_pipeline(
        self,
        pr_data: PRData,
        delivery_id: str
    ) -> Optional[GitHubReview]:
        """
        Execute the CrewAI review pipeline.
        
        Args:
            pr_data: PR data to review
            delivery_id: Delivery ID for tracking
            
        Returns:
            GitHubReview object or None if failed
        """
        try:
            # Import here to avoid circular dependencies
            from core.crew import ReviewCrew
            from core.execution import execute_review_pipeline
            
            logger.info(
                "executing_review_pipeline",
                repo=pr_data.repo_name,
                pr_number=pr_data.pr_number,
                delivery_id=delivery_id
            )
            
            # Create review input
            review_input = {
                "repo_name": pr_data.repo_name,
                "pr_number": pr_data.pr_number,
                "diff_content": pr_data.full_diff,
                "files_changed": [f.filename for f in pr_data.files_changed]
            }
            
            # Execute CrewAI pipeline (Phase 15: Production)
            # Create ReviewInput for the pipeline
            review_input = ReviewInput(
                repo_name=pr_data.repo_name,
                pr_number=pr_data.pr_number,
                pr_url=f"https://github.com/{pr_data.repo_name}/pull/{pr_data.pr_number}",
                diff_content=pr_data.full_diff,
                files_changed=[f.filename for f in pr_data.files_changed]
            )
            
            logger.info(
                "executing_crewai_pipeline",
                repo=pr_data.repo_name,
                pr_number=pr_data.pr_number,
                files_count=len(pr_data.files_changed)
            )
            
            # Execute the full CrewAI review pipeline
            result = await execute_review_pipeline(review_input)
            
            logger.info(
                "crewai_pipeline_completed",
                repo=pr_data.repo_name,
                pr_number=pr_data.pr_number,
                findings_count=len(result.inline_comments) if result else 0
            )
            
            return result
        
        except Exception as e:
            logger.error(
                "review_pipeline_failed",
                error=str(e),
                delivery_id=delivery_id,
                exc_info=True
            )
            return None
    
    async def _post_error_comment(
        self,
        payload: Dict[str, Any],
        error_message: str
    ):
        """
        Post error comment on PR when review fails.
        
        Args:
            payload: GitHub webhook payload
            error_message: Error message to post
        """
        pr_data = payload.get("pull_request", {})
        repo_data = payload.get("repository", {})
        
        repo_full_name = repo_data.get("full_name", "")
        pr_number = pr_data.get("number", 0)
        
        error_review = GitHubReview(
            inline_comments=[],
            summary_comment=f"""## ❌ Code Review Failed

An error occurred while processing this PR:

```
{error_message}
```

Please check the logs or contact the administrator.
""",
            review_state="COMMENTED"
        )
        
        await self.commenter.post_review(
            repo_full_name,
            pr_number,
            error_review
        )
