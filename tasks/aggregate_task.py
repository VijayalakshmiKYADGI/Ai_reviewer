from textwrap import dedent
from crewai import Task, Agent
from tools import FindingAggregator, finding_aggregator_tool
from data.models import ReviewSummary, ReviewFinding
import json

class AggregateFindingsTask:
    def __init__(self):
        self.aggregator = FindingAggregator()

    def create(self, agent: Agent, context_tasks: list[Task]) -> Task:
        return Task(
            description=dedent("""\
                Aggregate findings from all previous analysis steps.
                
                1. Collect outputs from Quality, Performance, Security, and Architecture tasks.
                2. Deduplicate findings (same issue reported by multiple agents).
                3. Prioritize by severity (CRITICAL > HIGH > MEDIUM > LOW).
                4. Drop low-value noise if total findings > 100.
                
                Return a consolidated summary.
            """),
            expected_output="A specific ReviewSummary object in JSON format.",
            agent=agent,
            context=context_tasks,
            tools=[
                finding_aggregator_tool
            ]
        )
