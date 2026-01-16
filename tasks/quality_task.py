from textwrap import dedent
from crewai import Task, Agent
from data.models import ReviewFinding

class QualityAnalysisTask:
    def create(self, agent: Agent, context_tasks: list[Task]) -> Task:
        return Task(
            description=dedent("""\
                Analyze the code files identified in the previous step for Quality issues.
                
                Focus on:
                - PEP8 style violations
                - Naming conventions
                - Code smells (missing docstrings, complex imports)
                - Readability
                
                Use your tools (Pylint, AST) to scan the code.
                For every issue found, check if it's a false positive.
                Return a list of findings.
            """),
            expected_output="A list of ReviewFinding objects in JSON format representing quality issues.",
            agent=agent,
            context=context_tasks,
            tools=[] # Agent usually has the tools (CodeQualityAgent has Pylint/AST)
        )
