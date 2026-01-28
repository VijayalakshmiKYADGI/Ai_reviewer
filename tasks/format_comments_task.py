from textwrap import dedent
from crewai import Task, Agent
from data.models import GitHubReview

class FormatCommentsTask:
    def create(self, agent: Agent, context_tasks: list[Task]) -> Task:
        return Task(
            description=dedent("""\
                Format findings into a GitHub PR review JSON. 
                
                STEPS:
                1. Map findings from the previous task context to 'inline_comments'.
                2. Each comment MUST have: `file_path`, `line_number` (integer), and `comment`.
                3. Create 'summary_comment' (Brief overview of main issues).
                4. Set 'review_state' (REQUEST_CHANGES if findings exist, else APPROVED).
            """),
            expected_output='A structured GitHub PR review.',
            agent=agent,
            context=context_tasks,
            output_pydantic=GitHubReview
        )
