from textwrap import dedent
from crewai import Task, Agent

class SecurityAnalysisTask:
    def create(self, agent: Agent, context_tasks: list[Task]) -> Task:
        return Task(
            description=dedent("""\
                Scan the code for Security Vulnerabilities.
                
                Focus on:
                - Hardcoded secrets/passwords (CRITICAL)
                - SQL Injection risks
                - Unsafe input handling
                - Common CVE patterns
                
                Use Bandit to scan the code.
                If CRITICAL issues are found, highlight them prominently.
            """),
            expected_output="A list of ReviewFinding objects in JSON format representing security risks.",
            agent=agent,
            context=context_tasks
        )
