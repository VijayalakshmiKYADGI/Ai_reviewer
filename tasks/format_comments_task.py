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
                  - Lines starting with `+` (not `+++`) are changed lines.
                  - Lines starting with ` ` (space) or not in the diff are unchanged.
                - **CRITICAL LINE VALIDATION**: Ensure the `line_number` matches the line in the NEW file.
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

                DIFF CONTEXT:
                {diff_content}
                
                STEPS:
                1. Map findings from the previous task context.
                   - The previous task output contains a 'findings' list with ReviewFinding objects.
                   - Each finding has: file_path, line_number, severity, category, issue_description.
                2. Convert ReviewFinding objects to InlineComment format.
                   - Each comment MUST have: `file_path`, `line_number` (integer), and `comment` (the issue_description).
                3. **CRITICAL**: All MEDIUM, HIGH, and CRITICAL severity findings MUST be included in `inline_comments`.
                   - Do NOT skip or filter out any MEDIUM+ findings.
                   - Only LOW severity findings should be summarized in the summary_comment.
                4. **DEDUPLICATION**: If the previous task provided duplicate findings for the same line, MERGE them into a single comment. Ensure each `file_path` + `line_number` combination appears only ONCE in `inline_comments`.
                5. Create 'summary_comment' (Brief overview of main issues, mention count of LOW findings if any).
                6. Set 'review_state' (REQUEST_CHANGES if MEDIUM+ findings exist, else COMMENTED).
            """),
            expected_output='A single structured GitHub PR review JSON object. DO NOT repeat the output. DO NOT include conversational text.',
            agent=agent,
            context=context_tasks,
            output_pydantic=GitHubReview
        )
