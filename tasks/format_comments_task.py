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
                2. **FILTER**: Only include findings with severity 'MEDIUM', 'HIGH', or 'CRITICAL' in inline_comments.
                   LOW severity findings should be mentioned in the summary_comment but NOT as inline comments.
                3. Each comment MUST have: `file_path`, `line_number` (integer), and `comment`.
                4. Create 'summary_comment' (Brief overview of main issues, mention count of LOW findings if any).
                5. Set 'review_state' (REQUEST_CHANGES if MEDIUM+ findings exist, else COMMENTED).
            """),
            expected_output='A structured GitHub PR review.',
            agent=agent,
            context=context_tasks,
            output_pydantic=GitHubReview
        )
