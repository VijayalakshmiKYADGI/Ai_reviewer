import os
from textwrap import dedent
from crewai import Agent
from langchain.tools import Tool

from tools import RadonTool, TreeSitterParser
from .gemini_llm import GeminiLLM
import structlog

logger = structlog.get_logger()

class PerformanceAgent:
    def __init__(self):
        self.llm = GeminiLLM(
            model_name="gemini-1.5-pro",
            temperature=0.1
        )
        self.radon = RadonTool()
        self.parser = TreeSitterParser()

    def _complexity_wrapper(self, code: str) -> str:
        findings = self.radon.analyze_complexity(code, "analyzed_file.py")
        return str([f.model_dump() for f in findings])

    def _structure_wrapper(self, code: str) -> str:
        blocks = self.parser.parse_code(code, "analyzed_file.py")
        return str([str(b) for b in blocks])

    def create(self) -> Agent:
        return Agent(
            role="Performance Engineer",
            goal="Detect algorithmic inefficiencies, complexity hotspots, and resource waste",
            backstory=dedent("""\
                You are an optimization expert who ensures Python code runs at production scale.
                You look for O(n^2) loops, inefficient list comprehensions, and high cyclomatic complexity.
                You use Radon to measure complexity and your own intuition to spot algorithmic traps."""),
            tools=[
                Tool(
                    name="Radon Complexity Analysis",
                    func=self._complexity_wrapper,
                    description="Calculate Cyclomatic Complexity and Maintainability Index. Input is python code string. Use this to find complex functions."
                ),
                Tool(
                    name="Code Structure Analysis",
                    func=self._structure_wrapper,
                    description="Extract code structure to identify nested loops and class hierarchy. Input is python code string."
                )
            ],
            llm=self.llm,
            verbose=False,  # Disabled to reduce Railway log spam
            memory=True,
            max_iter=3,
            allow_delegation=False
        )
