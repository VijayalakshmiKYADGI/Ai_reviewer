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
                Format findings into a GitHub PR review JSON. 
                
                STEPS:
                1. Create 'inline_comments' (file_path, line_number, comment).
                2. Create 'summary_comment' (Brief overview of main issues).
                3. Set 'review_state' (REQUESTED_CHANGES if findings exist, else APPROVED).
                   
                FORBIDDEN:
                - Do NOT include markdown code blocks (```json).
                - Do NOT include any text outside the JSON object.
                - Keep the summary_comment brief.
            """),
            expected_output='A raw string containing only a JSON object: {"inline_comments": [...], "summary_comment": "...", "review_state": "..."}',
            agent=agent,
            context=context_tasks
        )
