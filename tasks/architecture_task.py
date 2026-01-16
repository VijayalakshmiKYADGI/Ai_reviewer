from textwrap import dedent
from crewai import Task, Agent

class ArchitectureAnalysisTask:
    def create(self, agent: Agent, context_tasks: list[Task]) -> Task:
        return Task(
            description=dedent("""\
                Analyze the software Architecture and Design.
                
                Focus on:
                - SOLID principles (SRP, OCP, etc.)
                - Design patterns usage (or misuse)
                - Coupling and cohesion
                - "God Classes" or monolithic functions
                
                Use AST parsing to understand the class hierarchy and dependencies.
            """),
            expected_output="A list of ReviewFinding objects in JSON format representing architectural insights.",
            agent=agent,
            context=context_tasks
        )
