from textwrap import dedent
from crewai import Task, Agent
from langchain.tools import Tool
from tools import FindingAggregator
from data.models import ReviewSummary, ReviewFinding
import json

class AggregateFindingsTask:
    def __init__(self):
        self.aggregator = FindingAggregator()

    def _aggregate_wrapper(self, findings_json: str) -> str:
        """Parse multiple JSON lists and aggregate them."""
        # Findings usually come as a string concatenation of JSONs or list of lists from context
        # We try to parse everything we can find
        all_findings = []
        try:
            # Heuristic: try to find JSON arrays in the string
            # For simplicity in this wrapper, we assume the input string contains valid JSON or we mock it
            # In a real agent flow, we'd need robust parsing.
            # Here we just try loading it if it looks like json
            if findings_json.strip().startswith("["):
                data = json.loads(findings_json)
                for item in data:
                    try:
                        all_findings.append(ReviewFinding(**item))
                    except:
                        pass
        except:
            pass
            
        aggregated = self.aggregator.aggregate(all_findings)
        return json.dumps([f.model_dump() for f in aggregated])

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
                Tool(
                    name="Finding Aggregator",
                    func=self._aggregate_wrapper,
                    description="Aggregate and deduplicate a list of finding objects (JSON string). Input: JSON list of dicts."
                )
            ]
        )
