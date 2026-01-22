import os
from textwrap import dedent
from crewai import Agent
from langchain.tools import Tool

from tools import TreeSitterParser
from .gemini_llm import GeminiLLM
import structlog

logger = structlog.get_logger()

class ArchitectureAgent:
    def __init__(self):
        self.llm = GeminiLLM(
            model_name="gemini-1.5-pro",
            temperature=0.1
        )
        self.parser = TreeSitterParser()

    def _structure_wrapper(self, code: str) -> str:
        blocks = self.parser.parse_code(code, "analyzed_file.py")
        return str([str(b) for b in blocks])

    def create(self) -> Agent:
        return Agent(
            role="Software Architect",
            goal="Validate design patterns, SOLID principles, and system structure",
            backstory=dedent("""\
                You are a Software Architect who has designed 50+ scalable systems.
                You look for design flaws, tight coupling, SRP violations, and God classes.
                You suggest design patterns (Factory, Observer, etc.) and architectural improvements.
                You rely on code structure analysis to understand class relationships."""),
            tools=[
                Tool(
                    name="Code Structure Analysis",
                    func=self._structure_wrapper,
                    description="Extract classes and functions to analyze hierarchy and coupling. Input is python code string."
                )
            ],
            llm=self.llm,
            verbose=False,  # Disabled to reduce Railway log spam
            memory=False,
            max_iter=2,
            allow_delegation=False
        )
