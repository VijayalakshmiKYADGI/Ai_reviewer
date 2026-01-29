from textwrap import dedent
from crewai import Task, Agent
from data.models import GitHubReview
import os

class FormatCommentsTask:
    def create(self, agent: Agent, context_tasks: list[Task], diff_content: str = "", files_changed: list[str] = []) -> Task:
        review_mode = os.getenv("REVIEW_MODE", "changes_only")
        
        if review_mode == "full_file":
            mode_instructions = """
                **FULL FILE MODE - SEPARATE FINDINGS**:
                - You will receive findings for BOTH changed and unchanged lines.
                - Separate them into two lists:
                  1. `inline_comments`: Findings on lines that were ADDED/MODIFIED (part of the diff)
                  2. `pre_existing_findings`: Findings on lines that were NOT changed (context lines)
                - To determine which lines were changed, look at the diff format:
                  - Lines starting with `+` (not `+++`) are changed lines
                  - Lines starting with ` ` (space) or not in the diff are unchanged
                - **FILTER**: Only include MEDIUM, HIGH, or CRITICAL severity in both lists.
                - LOW severity findings go in summary_comment only.
            """
        else:  # changes_only
            mode_instructions = """
                **CHANGES ONLY MODE**:
                - All findings are already for changed lines only.
                - Put all MEDIUM+ findings in `inline_comments`.
                - Leave `pre_existing_findings` empty.
                - **FILTER**: Only include MEDIUM, HIGH, or CRITICAL severity in inline_comments.
                - LOW severity findings go in summary_comment only.
            """
        
        return Task(
            description=dedent(f"""\
                Format findings into a GitHub PR review JSON. 
                
                {mode_instructions}
                
                STEPS:
                1. Map findings from the previous task context.
                2. Each comment MUST have: `file_path`, `line_number` (integer), and `comment`.
                3. Create 'summary_comment' (Brief overview of main issues, mention count of LOW findings if any).
                4. Set 'review_state' (REQUEST_CHANGES if MEDIUM+ findings exist, else COMMENTED).
            """),
            expected_output='A structured GitHub PR review.',
            agent=agent,
            context=context_tasks,
            output_pydantic=GitHubReview
        )
