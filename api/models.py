from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from tasks.format_comments_task import GitHubReview

class ReviewRequest(BaseModel):
    repo_name: str
    pr_number: int
    pr_url: Optional[str] = None
    diff_content: Optional[str] = None
    files_changed: Optional[List[str]] = None

class ReviewResponse(BaseModel):
    """Unified response for sync and async reviews."""
    review_id: int
    status: Literal["queued", "processing", "completed", "failed"]
    github_review: Optional[GitHubReview] = None
    execution_time: Optional[float] = None
    total_cost: Optional[float] = 0.0

class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded"]
    database: str
    uptime: float
