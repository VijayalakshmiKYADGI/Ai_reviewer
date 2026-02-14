"""
GitHubCommenter - Post senior-dev-style inline comments to GitHub PRs

Formats and posts code review comments with severity indicators.
"""

from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime
from data.models import GitHubReview, InlineComment
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
    
    def _format_summary(self, github_review: GitHubReview) -> str:
        """Format the high-level summary for the review."""
        review_state = getattr(github_review, "review_state", "COMMENTED")
        status_emoji = "✅" if review_state == "APPROVED" else "⚠️"
        if review_state == "REQUESTED_CHANGES":
            status_emoji = "❌"
            
        summary_text = getattr(github_review, "summary_comment", "Review completed check findings below.")
        return f"## 🤖 AI Code Review Summary {status_emoji}\n\n{summary_text}\n\n---\n*Sent by CrewAI Lead Engineer*"

    def _format_comment(self, comment: Any) -> Dict[str, Any]:
        """Format an individual inline comment for the GitHub API."""
        # Handle both object and dict access for robustness
        def safe_get(obj, attr, default=""):
            if isinstance(obj, dict):
                val = obj.get(attr)
            else:
                val = getattr(obj, attr, None)
            
            # If value is None, try aliases
            if val is None:
                if attr == "file_path": val = safe_get(obj, "path", None)
                if attr == "path": val = safe_get(obj, "file_path", None)
                if attr == "line_number": val = safe_get(obj, "line", None)
                if attr == "line": val = safe_get(obj, "line_number", None)
                if attr == "comment": val = safe_get(obj, "body", None)
                if attr == "body": val = safe_get(obj, "comment", None)
                
            return val if val is not None else default

        body = safe_get(comment, "comment", safe_get(comment, "body", ""))
        # Add severity prefix if not present
        formatted_body = self._format_comment_body({"body": body})
        
        path = safe_get(comment, "file_path", safe_get(comment, "path", "unknown"))
        line = safe_get(comment, "line_number", safe_get(comment, "line", 0))
        
        return {
            "path": str(path) if path else "unknown",
            "line": int(line) if line else 1,
            "body": formatted_body
        }

    async def post_review(
        self,
        repo_full_name: str,
        pr_number: int,
        github_review: GitHubReview,
        valid_paths: Optional[List[str]] = None,
        event: str = "COMMENT",
        diff_content: str = ""
    ) -> str:
        """
        Post a complete code review to GitHub PR.
        
        Args:
            repo_full_name: Full repo name (owner/repo)
            pr_number: PR number
            github_review: GitHubReview object from CrewAI pipeline
            valid_paths: List of allowed file paths
            event: GitHub review event (COMMENT, REQUEST_CHANGES, APPROVE)
            diff_content: Raw diff content for line validation
            
        Returns:
            Review ID
        """
        # 1. Setup line validation if diff is provided
        from tools.diff_parser import DiffParser
        parser = DiffParser()
        changed_lines_cache = {}

        # 2. Format the summary (we'll append validation warnings here if any)
        summary_base = self._format_summary(github_review)
        mislocated_findings = []
        
        # 3. Format inline comments
        formatted_comments = []
        for comment in github_review.inline_comments:
            path = getattr(comment, "file_path", getattr(comment, "path", ""))
            line = getattr(comment, "line_number", getattr(comment, "line", 0))
            
            # Filter comments for files that actually exist in the diff
            if valid_paths is not None and path not in valid_paths:
                print(f"⚠️ Skipping comment for invalid path: {path}")
                mislocated_findings.append(comment)
                continue
            
            # Line validation if diff available
            if diff_content:
                if path not in changed_lines_cache:
                    changed_lines_cache[path] = parser.get_changed_lines(diff_content, path)
                
                valid_lines = changed_lines_cache[path]
                if int(line) not in valid_lines:
                    print(f"⚠️ Line {line} not in diff for {path}. Moving to summary.")
                    mislocated_findings.append(comment)
                    continue
                
            formatted_comment = self._format_comment(comment)
            # Add 'side' parameter for newer GitHub API compliance
            formatted_comment["side"] = "RIGHT"
            formatted_comments.append(formatted_comment)
        
        # 4. Handle mislocated findings (add to summary)
        if mislocated_findings:
            summary_base += "\n\n### 📋 Additional Findings (General/Context)\n"
            for f in mislocated_findings:
                path = getattr(f, "file_path", getattr(f, "path", "unknown"))
                line = getattr(f, "line_number", getattr(f, "line", "?"))
                body = getattr(f, "comment", getattr(f, "body", ""))
                summary_base += f"- **{path}:L{line}**: {body}\n"

        # 5. Post review via GitHub API
        try:
            # Determine correct event (override 'COMMENT' if results are critical)
            if github_review.review_state == "REQUESTED_CHANGES":
                event = "REQUEST_CHANGES"
            elif github_review.review_state == "APPROVED":
                event = "APPROVE"

            review_id = await self.client.create_review(
                repo=repo_full_name,
                pr_number=pr_number,
                body=summary_base,
                event=event,
                comments=formatted_comments
            )
            
            print(f"✅ Posted review to {repo_full_name}#{pr_number} (Review ID: {review_id})")
            
            # 6. Post pre-existing findings as a separate comment (if any)
            if github_review.pre_existing_findings:
                await self._post_pre_existing_findings(repo_full_name, pr_number, github_review.pre_existing_findings)
            
            return str(review_id)
        
        except Exception as e:
            # Handle 422 "line not in diff" errors by falling back to PR comment
            error_str = str(e)
            if "422" in error_str or "Unprocessable Entity" in error_str:
                print(f"⚠️ Inline comments failed (422) even after validation. Reason: {error_str}")
                print(f"⚠️ Falling back to single PR comment.")
                return await self._post_as_pr_comment(repo_full_name, pr_number, github_review)
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
            # Safe access helper
            def safe_val(obj, attr, default):
                if isinstance(obj, dict): return obj.get(attr, default)
                return getattr(obj, attr, default)

            path = safe_val(comment, "file_path", safe_val(comment, "path", "unknown"))
            line = safe_val(comment, "line_number", safe_val(comment, "line", 1))
            body = safe_val(comment, "comment", safe_val(comment, "body", ""))
            
            formatted_body = self._format_comment_body({"body": body})
            
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
    
    async def _post_pre_existing_findings(
        self,
        repo_full_name: str,
        pr_number: int,
        findings: List[InlineComment]
    ) -> str:
        """
        Post pre-existing findings as a separate PR comment.
        
        Args:
            repo_full_name: Full repo name (owner/repo)
            pr_number: PR number
            findings: List of findings on unchanged lines
            
        Returns:
            Comment ID
        """
        if not findings:
            return ""
        
        # Build comment body
        comment_body = "## 📋 Pre-existing Issues Found\n\n"
        comment_body += f"While reviewing this PR, I also noticed **{len(findings)} existing issue(s)** in the files you modified:\n\n"
        
        for i, finding in enumerate(findings, 1):
            def safe_val(obj, attr, default):
                if isinstance(obj, dict): return obj.get(attr, default)
                return getattr(obj, attr, default)

            path = safe_val(finding, "file_path", safe_val(finding, "path", "unknown"))
            line = safe_val(finding, "line_number", safe_val(finding, "line", 1))
            body = safe_val(finding, "comment", safe_val(finding, "body", ""))
            
            comment_body += f"{i}. **`{path}:L{line}`**\n   {body}\n\n"
        
        comment_body += "---\n"
        comment_body += "> 💡 **Note**: These issues existed before this PR and are not blocking approval. "
        comment_body += "However, consider addressing them in a follow-up PR to improve overall code quality.\n"
        
        # Post as issue comment
        comment_id = await self.client.create_issue_comment(
            repo=repo_full_name,
            pr_number=pr_number,
            body=comment_body
        )
        
        print(f"📋 Posted {len(findings)} pre-existing findings to {repo_full_name}#{pr_number} (Comment ID: {comment_id})")
        return str(comment_id)
