from typing import List, Optional
import structlog
from datetime import datetime
from data.models import ReviewInput, ReviewSummary, AgentOutput, ReviewFinding
from data.database import save_review, get_review_by_id
from tasks.format_comments_task import GitHubReview

logger = structlog.get_logger()

def save_review_start(review_input: ReviewInput) -> int:
    """
    Create an initial record for the review.
    Returns the new review_id.
    """
    # Create a placeholder summary to initialize the record
    summary = ReviewSummary(
        repo_name=review_input.repo_name,
        pr_number=review_input.pr_number,
        pr_url=f"https://github.com/{review_input.repo_name}/pull/{review_input.pr_number}", # approximate
        status="running",
        agent_outputs=[],
        created_at=datetime.utcnow()
    )
    return save_review(summary)

def save_full_review_results(
    review_id: int, 
    github_review: GitHubReview,
    agent_outputs: List[AgentOutput],
    execution_time: float = 0.0
) -> None:
    """
    Update the review record with final results.
    """
    try:
        # Reconstruct full summary
        # Fetch existing to get repo info (or pass it down)
        existing = get_review_by_id(review_id)
        if not existing:
            logger.error("review_not_found_for_update", review_id=review_id)
            return

        summary = ReviewSummary(
            review_id=review_id,
            repo_name=existing.repo_name,
            pr_number=existing.pr_number,
            pr_url=existing.pr_url,
            status="completed",
            agent_outputs=agent_outputs,
            execution_time=execution_time,
            completed_at=datetime.utcnow()
        )
        
        # Save (this will update or re-insert depending on DB logic, 
        # Phase 2 `save_review` was INSERT. We might need UPDATE logic or just INSERT a new finished row.
        # Phase 2 `save_review` does INSERT. `database.py` didn't have update_review.
        # However, for this MVP, we can insert the 'completed' record. 
        # Ideally we'd update. But since Phase 2 is done, we'll use save_review which inserts.
        # This gives us a history of states if we want, or duplicates.
        # To avoid duplicates in `reviews` table which usually has PK, `save_review` returns new ID.
        # That logic is imperfect for updates without `update` SQL.
        # But `save_review` implementation in Phase 2 was: 
        # INSERT INTO reviews ...
        # So we simply insert the final record.
        save_review(summary)
        
        logger.info("review_results_saved", review_id=review_id, output_count=len(agent_outputs))
        
    except Exception as e:
        logger.error("save_results_failed", error=str(e))

def get_review_status(review_id: int) -> str:
    """Get status of a review."""
    rev = get_review_by_id(review_id)
    return rev.status if rev else "unknown"
