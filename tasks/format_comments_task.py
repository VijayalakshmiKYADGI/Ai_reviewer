from textwrap import dedent
from crewai import Task, Agent
from typing import List, Literal, Optional, Dict, Union
from pydantic import BaseModel, Field

class InlineComment(BaseModel):
    file_path: Optional[str] = Field(None, description="Path to the file being reviewed")
    line_number: Optional[Union[int, str]] = Field(None, description="Line number in the file")
    comment: str = Field(..., description="The review comment text")

class GitHubReview(BaseModel):
    inline_comments: List[InlineComment] = Field(default_factory=list, description="List of inline comments")
    summary_comment: str = Field(..., description="Overall summary of the review")
    review_state: str = Field(..., description="Review state: APPROVED, REQUEST_CHANGES, or COMMENTED")

class FormatCommentsTask:
    def create(self, agent: Agent, context_tasks: list[Task]) -> Task:
        return Task(
            description=dedent("""\
                Format the aggregated findings into a GitHub Pull Request review.
                
                STEPS:
                1. Create inline_comments for specific lines of code.
                2. Create a high-level summary_comment.
                3. Determine review_state:
                   - REQUESTED_CHANGES if any CRITICAL/HIGH issues and return that state.
                   - COMMENTED if only MEDIUM/LOW issues.
                   - APPROVED if no findings.
                   
                IMPORTANT:
                - EVERY comment must have 'file_path', 'line_number', and 'comment'.
                - If a path is unknown, use 'README.md' or the main file found in context.
                - 'line_number' MUST be an integer or a string.
                - Format the result as valid JSON.
            """),
            expected_output=dedent("""\
                A JSON object with exactly this structure:
                {
                  "inline_comments": [
                    {"file_path": "string", "line_number": 1, "comment": "string"}
                  ],
                  "summary_comment": "string",
                  "review_state": "APPROVED|REQUEST_CHANGES|COMMENTED"
                }
            """),
            agent=agent,
            context=context_tasks
        )
