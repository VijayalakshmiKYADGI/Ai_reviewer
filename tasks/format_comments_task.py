from textwrap import dedent
from crewai import Task, Agent
from typing import List, Literal, Optional, Dict
from pydantic import BaseModel, Field

# Define Output Model locally to avoid data package edit if restricted, 
# but ideally should be shared.
class GitHubReview(BaseModel):
    inline_comments: List[Dict[str, str]] = Field(description="List of comments with path, line, body")
    summary_comment: str
    review_state: Literal["COMMENTED", "APPROVED", "REQUESTED_CHANGES"]

class FormatCommentsTask:
    def create(self, agent: Agent, context_tasks: list[Task]) -> Task:
        return Task(
            description=dedent("""\
                Format the aggregated findings into a GitHub Pull Request review.
                
                1. Create inline_comments for specific lines of code.
                2. Create a high-level summary_comment.
                3. Determine review_state:
                   - REQUESTED_CHANGES if any CRITICAL/HIGH issues.
                   - COMMENTED if only MEDIUM/LOW issues.
                   - APPROVED if no findings.
                   
                Format exactly as the GitHubReview schema.
            """),
            expected_output="A GitHubReview JSON object with inline_comments, summary_comment, and review_state.",
            agent=agent,
            context=context_tasks,
            output_pydantic=GitHubReview # Force Pydantic output if supported by version
        )
