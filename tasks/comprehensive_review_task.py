from textwrap import dedent
from crewai import Task, Agent
from typing import List
from data.models import ReviewFinding, ComprehensiveReviewAnalysis

class ComprehensiveReviewTask:
    def create(self, agent: Agent, context_tasks: list[Task]) -> Task:
        return Task(
            description=dedent("""\
                Perform a deep, multi-dimensional technical review of the code changes identified in the previous step.
                
                Your analysis MUST cover:
                1. QUALITY: PEP8, naming, readability, docstrings, and general best practices.
                2. PERFORMANCE: Algorithmic complexity, unnecessary loops, resource usage, and efficiency.
                3. SECURITY: Sensitive data leaks (secrets/keys), SQL injection, unsafe functions, and OWASP risks.
                4. ARCHITECTURE: SOLID principles, design patterns, separation of concerns, and maintainability.
                
                PROCESS:
                - Identify the exact line number for each finding in the changed file.
                - For each issue, you MUST provide exactly these fields:
                    - `file_path`: (string) The path to the file.
                    - `line_number`: (integer) The line number.
                    - `severity`: (string) ONE OF: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'.
                    - `category`: (string) e.g., 'SECURITY', 'QUALITY'.
                    - `issue_description`: (string) A clear explanation of the problem.
                    - `agent_name`: (string) Set this to 'Lead Software Engineer'.
                - Focus on impactful findings. Don't nitpick.
                - Wrap your response in the 'findings' key.
            """),
            expected_output="A JSON object with a 'findings' key containing the list of issues.",
            agent=agent,
            context=context_tasks,
            output_pydantic=ComprehensiveReviewAnalysis
        )
