import os
from textwrap import dedent
from crewai import Agent
from langchain.tools import Tool

from tools import PylintTool, TreeSitterParser
from .gemini_llm import GeminiLLM
import structlog

logger = structlog.get_logger()

class CodeQualityAgent:
    def __init__(self):
        self.llm = GeminiLLM(
            model_name="gemini-1.5-pro",
            temperature=0.1
        )
        self.pylint = PylintTool()
        self.parser = TreeSitterParser()

    def _analyze_wrapper(self, code: str) -> str:
        """Wrapper for Pylint tool to be used by CrewAI."""
        findings = self.pylint.analyze(code, "analyzed_file.py")
        return str([f.model_dump() for f in findings])

    def _parse_wrapper(self, code: str) -> str:
        """Wrapper for TreeSitter parser."""
        blocks = self.parser.parse_code(code, "analyzed_file.py")
        return str([str(b) for b in blocks])

    def create(self) -> Agent:
        return Agent(
            role="Senior Python Developer",
            goal="Find style violations, naming issues, and code smells in Python code",
            backstory=dedent("""\
                You are a veteran Python developer with 10+ years of experience.
                You are strictly PEP8 compliant and believe that readability counts.
                You job is to read code, analyze it using the provided tools, and report every single style violation.
                You do not tolerate messy imports, bad variable names, or missing docstrings."""),
            tools=[
                Tool(
                    name="Pylint Analysis",
                    func=self._analyze_wrapper,
                    description="Run Pylint on python code to find style issues and errors. Input should be the python code string."
                ),
                Tool(
                    name="AST Parsing",
                    func=self._parse_wrapper,
                    description="Parse Python code into structural blocks (functions, classes) to understand code structure. Input is python code string."
                )
            ],
            llm=self.llm,
            verbose=False,  # Disabled to reduce Railway log spam
            memory=True,
            max_iter=2,
            allow_delegation=False
        )
