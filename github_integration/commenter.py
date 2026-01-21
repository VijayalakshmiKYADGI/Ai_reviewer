"""
GitHubCommenter - Post senior-dev-style inline comments to GitHub PRs

Formats and posts code review comments with severity indicators.
"""

from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime
from tasks.format_comments_task import GitHubReview
from .client import GitHubClient


class GitHubCommenter:
    """Post code review comments to GitHub PRs."""
    
    def __init__(self, client: GitHubClient = None):
        """
        Initialize commenter.
        
        Args:
            client: GitHubClient instance. If None, creates new client.
        """
        self.client = client or GitHubClient()
    
    def _format_comment_body(self, comment: Dict[str, str]) -> str:
        """
        Format comment with severity emoji.
        
        Args:
            comment: Comment dict with 'body' field
            
        Returns:
            Formatted comment with emoji prefix
        """
        body = comment.get("body", "")
        
        # Add severity emoji based on keywords
        if "CRITICAL" in body.upper():
            return f"🔴 {body}"
        elif "HIGH" in body.upper():
            return f"🟡 {body}"
        elif "MEDIUM" in body.upper():
            return f"🟠 {body}"
        elif "LOW" in body.upper():
            return f"🟢 {body}"
        else:
            return f"💡 {body}"
    
    def _convert_line_to_position(
        self,
        file_path: str,
        line_number: int,
        pr_files: List[Any]
    ) -> int:
        """
        Convert absolute line number to diff position.
        
        GitHub API requires 'position' in the diff, not absolute line number.
        This is a simplified implementation - production would parse the diff.
        
        Args:
            file_path: Path to file
            line_number: Absolute line number
            pr_files: List of PR file objects
            
        Returns:
            Diff position (for now, returns line_number as approximation)
        """
        # TODO: Implement proper diff position calculation
        # For Phase 8, we'll use line number as position
        # Phase 9 will implement proper diff parsing
        return line_number
    
    async def post_review(
        self,
        repo_full_name: str,
        pr_number: int,
        github_review: GitHubReview
    ) -> str:
        """
        Post a complete code review to GitHub PR.
        
        Args:
            repo_full_name: Full repo name (owner/repo)
            pr_number: PR number
            github_review: GitHubReview object from CrewAI pipeline
            
        Returns:
            Review ID
            
        Example:
            >>> commenter = GitHubCommenter()
            >>> review = GitHubReview(
            ...     inline_comments=[{"path": "app.py", "line": 42, "body": "Fix this"}],
            ...     summary_comment="Great work!",
            ...     review_state="COMMENTED"
            ... )
            >>> review_id = await commenter.post_review("owner/repo", 1, review)
        """
        # Format inline comments for GitHub API
        formatted_comments = []
        
        for comment in github_review.inline_comments:
            # Extract comment data
            path = comment.get("path", "")
            line = int(comment.get("line", 0))
            body = comment.get("body", "")
            
            if not path or not line or not body:
                print(f"Skipping invalid comment: {comment}")
                continue
            
            # Format comment body with emoji
            formatted_body = self._format_comment_body(comment)
            
    async def post_review(
        self,
        repo_full_name: str,
        pr_number: int,
        github_review: GitHubReview,
        valid_paths: Optional[List[str]] = None,
        event: str = "COMMENT"
    ) -> str:
        """
        Post a review to GitHub.

        Args:
            repo_full_name: Full repo name (owner/repo)
            pr_number: PR number
            github_review: GitHubReview object
            valid_paths: Optional list of valid file paths in the PR diff
            event: Review event type (APPROVE, REQUEST_CHANGES, COMMENT)

        Returns:
            Review ID
        """
        # Format comments
        summary = self._format_summary(github_review)
        formatted_comments = []
        
        for comment in github_review.inline_comments:
            path = comment.get("path")
            # validate path if valid_paths provided
            if valid_paths is not None and path not in valid_paths:
                print(f"⚠️ Skipping comment for invalid path: {path}")
                # Append to summary instead
                summary += f"\n\n**Note on {path}:{comment.get('line')}**: {comment.get('body')}"
                continue
                
            formatted_comments.append(self._format_comment(comment))
        
        # Post review via GitHub API
        try:
            review_id = await self.client.create_review(
                repo=repo_full_name,
                pr_number=pr_number,
                body=summary,
                event=event,
                comments=formatted_comments
            )
            
            print(f"✅ Posted review to {repo_full_name}#{pr_number} (Review ID: {review_id})")
            return review_id
        
        except Exception as e:
            # Handle 422 "line not in diff" errors
            if "422" in str(e) or "Unprocessable Entity" in str(e):
                print(f"⚠️ Inline comments failed (422), falling back to PR comment")
                # Fallback: Post as single PR comment
                return await self._post_as_pr_comment(
                    repo_full_name,
                    pr_number,
                    github_review
                )
            else:
                print(f"❌ Failed to post review: {e}")
                raise
    
    def format_review_preview(self, github_review: GitHubReview) -> str:
        """
        Format review as text preview (for testing without API call).
        
        Args:
            github_review: GitHubReview object
            
        Returns:
            Formatted text preview
        """
        lines = []
        lines.append("=" * 60)
        lines.append("AI CODE REVIEW PREVIEW")
        lines.append("=" * 60)
        lines.append("")
        
        # Summary
        lines.append("SUMMARY:")
        lines.append(github_review.summary_comment)
        lines.append("")
        
        # Review state
        lines.append(f"REVIEW STATE: {github_review.review_state}")
        lines.append("")
        
        # Inline comments
        lines.append(f"INLINE COMMENTS ({len(github_review.inline_comments)}):")
        lines.append("-" * 60)
        
        for i, comment in enumerate(github_review.inline_comments, 1):
            path = comment.get("path", "unknown")
            line = comment.get("line", 0)
            body = comment.get("body", "")
            formatted_body = self._format_comment_body(comment)
            
            lines.append(f"{i}. {path}:L{line}")
            lines.append(f"   {formatted_body}")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    async def _post_as_pr_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        github_review: GitHubReview
    ) -> str:
        """
        Fallback: Post review as single PR comment when inline comments fail.
        
        Used when GitHub API returns 422 (line not in diff).
        
        Args:
            repo_full_name: Full repo name (owner/repo)
            pr_number: PR number
            github_review: GitHubReview object
            
        Returns:
            Comment ID
        """
        # Format all findings as single comment
        comment_body = f"""## 🤖 AI Code Review Summary

{github_review.summary_comment}

### 📋 Findings ({len(github_review.inline_comments)}):

"""
        
        for i, comment in enumerate(github_review.inline_comments, 1):
            path = comment.get("path", "unknown")
            line = comment.get("line", 0)
            body = comment.get("body", "")
            formatted_body = self._format_comment_body(comment)
            
            comment_body += f"{i}. **`{path}:L{line}`** - {formatted_body}\n"
        
        comment_body += "\n---\n*Posted as single comment due to diff position conflicts*\n"
        
        # Post as issue comment
        comment_id = await self.client.create_issue_comment(
            repo=repo_full_name,
            pr_number=pr_number,
            body=comment_body
        )
        
        print(f"✅ Posted fallback comment to {repo_full_name}#{pr_number} (Comment ID: {comment_id})")
        return str(comment_id)
