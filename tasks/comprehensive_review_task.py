from textwrap import dedent
from crewai import Task, Agent
from typing import List
from data.models import ReviewFinding, ComprehensiveReviewAnalysis
import os

class ComprehensiveReviewTask:
    def create(self, agent: Agent, context_tasks: list[Task], diff_content: str = "") -> Task:
        # Read review mode from environment
        review_mode = os.getenv("REVIEW_MODE", "changes_only")
        
        # Build description based on mode
        if review_mode == "changes_only":
            diff_instructions = """
                **CRITICAL: DIFF-AWARE REVIEW (Changes Only Mode)**
                - You are reviewing a DIFF, not a complete file.
                - The diff shows lines with prefixes: `-` (removed), `+` (added/modified), ` ` (unchanged context).
                - **ONLY create findings for lines that start with `+` (newly added or modified lines).**
                - **IGNORE all context lines** (lines that don't start with `+` or `-`), even if they contain issues.
                - **IGNORE removed lines** (lines starting with `-`).
                - **LINE NUMBERING**: You MUST calculate the line number from the hunk headers (`@@ -old,count +new,count @@`). 
                  - The `+new` number is the start of the new file's line count for that hunk.
                  - Each line in the hunk (including ` ` and `+`) increments the new line counter.
                  - `-` lines do NOT increment the new line counter.
                  - **CRITICAL**: If your calculated line number does not correspond to a `+` line in the diff, do NOT report it as an inline finding.
            """
        else:  # full_file mode
            diff_instructions = """
                **FULL FILE REVIEW MODE**
                - You are reviewing the ENTIRE file content, including both changed and unchanged lines.
                - Mark each finding with the line number from the NEW version of the file.
                - Use hunk headers (`@@ -old,count +new,count @@`) to synchronize your line counting.
                - The formatting task will later separate changed vs unchanged line findings for proper posting.
            """
        
        return Task(
            description=dedent(f"""\
                Perform a deep, multi-dimensional technical review of the code changes identified in the previous step.
                
                {diff_instructions}

                DIFF CONTENT:
                {diff_content}
                
                Your analysis MUST cover:
                1. QUALITY: PEP8, naming, readability, docstrings, and general best practices.
                2. PERFORMANCE: Algorithmic complexity, unnecessary loops, resource usage, and efficiency.
                3. SECURITY: Sensitive data leaks (secrets/keys), SQL injection, unsafe functions, and OWASP risks.
                4. ARCHITECTURE: SOLID principles, design patterns, separation of concerns, and maintainability.
                
                PROCESS:
                - Identify the exact line number for each finding in the changed file.
                - For each issue, you MUST provide exactly these fields:
                    - `file_path`: (string) The path to the file.
                    - `line_number`: (integer) The line number in the NEW version of the file.
                    - `severity`: (string) ONE OF: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'.
                    - `category`: (string) e.g., 'SECURITY', 'QUALITY'.
                    - `issue_description`: (string) A clear explanation of the problem.
                    - `agent_name`: (string) Set this to 'Lead Software Engineer'.
                - **TOTAL LIMIT**: You MUST report a maximum of 20 findings total. If you find more than 20, only report the 20 most critical/complex ones.
                - **STRICT UNIQUENESS**: Each `line_number` MUST appear only ONCE in the list. If a single line has multiple issues, merge all details into one `issue_description`. 
                - **NO DUPLICATION**: Do not repeat the same finding or very similar findings.
                - Focus on impactful findings. Don't nitpick.
                - Wrap your response in the 'findings' key.
            """),
            expected_output="A single JSON object with a 'findings' key. DO NOT repeat the JSON. DO NOT include any text outside the JSON block.",
            agent=agent,
            context=context_tasks,
            output_pydantic=ComprehensiveReviewAnalysis
        )
