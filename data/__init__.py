"""
Data layer package for code review persistence.
Exports database functions and Pydantic models.
"""

from .database import (
    init_database,
    save_review,
    save_findings,
    save_agent_output,
    get_review_by_id,
    update_review_status,
    get_reviews_by_repo,
    get_db_connection
)

from .models import (
    ReviewFinding,
    AgentOutput,
    ReviewSummary,
    ReviewInput
)

__all__ = [
    # Database functions
    "init_database",
    "save_review",
    "save_findings",
    "save_agent_output",
    "get_review_by_id",
    "update_review_status",
    "get_reviews_by_repo",
    "get_db_connection",
    
    # Pydantic models
    "ReviewFinding",
    "AgentOutput",
    "ReviewSummary",
    "ReviewInput",
]
