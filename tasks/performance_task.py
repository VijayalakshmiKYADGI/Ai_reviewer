from textwrap import dedent
from crewai import Task, Agent

class PerformanceAnalysisTask:
    def create(self, agent: Agent, context_tasks: list[Task]) -> Task:
        return Task(
            description=dedent("""\
                Analyze the code for Performance and Complexity issues.
                
                Focus on:
                - High cyclomatic complexity (>10)
                - Nested loops (O(n^2) or worse)
                - Inefficient list comprehensions
                - Resource leaks
                
                Use Radon to measure complexity.
                Review the code structure for algorithmic traps.
            """),
            expected_output="A list of ReviewFinding objects in JSON format representing performance bottlenecks.",
            agent=agent,
            context=context_tasks
        )
