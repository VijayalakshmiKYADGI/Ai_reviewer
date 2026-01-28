"""
Pydantic models for code review data structures.
Provides validation and serialization for agent outputs and review summaries.
"""

from datetime import datetime, timezone
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ReviewFinding(BaseModel):
    """
    Represents a single code review finding from an agent.
    """
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    agent_name: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_block: Optional[str] = None
    issue_description: str = Field(...)
    fix_suggestion: Optional[str] = None
    category: str
    
    model_config = ConfigDict(from_attributes=True)


class AgentOutput(BaseModel):
    """
    Represents the complete output from a single agent execution.
    
    Example:
        {
            "agent_name": "security",
            "findings": [...],
            "execution_time": 12.5,
            "tokens_used": 1500,
            "error": null
        }
    """
    agent_name: str
    findings: list[ReviewFinding] = Field(default_factory=list)
    execution_time: float
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ReviewSummary(BaseModel):
    """
    Complete summary of a PR review session with all agent outputs.
    
    Example:
        {
            "review_id": 1,
            "repo_name": "myorg/myrepo",
            "pr_number": 123,
            "pr_url": "https://github.com/myorg/myrepo/pull/123",
            "status": "completed",
            "agent_outputs": [...],
            "execution_time": 45.2,
            "total_cost": 0.0234,
            "created_at": "2026-01-16T19:00:00Z",
            "completed_at": "2026-01-16T19:00:45Z"
        }
    """
    review_id: Optional[int] = None
    repo_name: str
    pr_number: int = Field(..., gt=0)
    pr_url: str
    status: Literal["pending", "running", "completed", "failed"]
    agent_outputs: list[AgentOutput] = Field(default_factory=list)
    execution_time: float = 0.0
    total_cost: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @property
    def total_findings(self) -> int:
        """Compute total number of findings across all agents."""
        return sum(len(output.findings) for output in self.agent_outputs)
    
    @property
    def severity_counts(self) -> dict[str, int]:
        """Compute severity distribution across all findings."""
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for output in self.agent_outputs:
            for finding in output.findings:
                counts[finding.severity] += 1
        return counts


class ReviewInput(BaseModel):
    """
    Input data required to start a new code review.
    
    Example:
        {
            "repo_name": "myorg/myrepo",
            "pr_number": 123,
            "pr_url": "https://github.com/myorg/myrepo/pull/123",
            "diff_content": "diff --git a/file.py...",
            "files_changed": ["src/auth.py", "tests/test_auth.py"],
            "language": "python"
        }
    """
    repo_name: str
    pr_number: int = Field(..., gt=0)
    pr_url: str
    diff_content: str
    files_changed: list[str]
    language: str = "python"
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('diff_content')
    @classmethod
    def diff_not_empty(cls, v: str) -> str:
        """Ensure diff content is provided."""
        if not v or not v.strip():
            raise ValueError("diff_content cannot be empty")
        return v

class ComprehensiveReviewAnalysis(BaseModel):
    """Container for the multi-agent consolidated analysis."""
    findings: list[ReviewFinding] = Field(..., description="List of all detected issues")

class InlineComment(BaseModel):
    """Represents a single inline comment on a file."""
    file_path: Optional[str] = Field(None, description="Path to the file being reviewed")
    line_number: Optional[int] = Field(None, description="Line number in the file")
    comment: str = Field(..., description="The review comment text")

class GitHubReview(BaseModel):
    """Represents the final review to be posted to GitHub."""
    inline_comments: list[InlineComment] = Field(default_factory=list, description="List of inline comments")
    summary_comment: str = Field(..., description="Overall summary of the review")
    review_state: str = Field(..., description="Review state: APPROVED, REQUEST_CHANGES, or COMMENTED")
