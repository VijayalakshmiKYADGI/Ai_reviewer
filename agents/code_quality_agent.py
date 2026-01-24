import os
from textwrap import dedent
from crewai import Agent

from tools import pylint_tool, tree_sitter_tool, TreeSitterParser
from langchain_google_genai import ChatGoogleGenerativeAI
import structlog

logger = structlog.get_logger()

class CodeQualityAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL"),  # Changed to a compatible model
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.1
        )
        # Utility parser for internal logic if needed, but tool instances are separate
        self.parser = TreeSitterParser()

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
                pylint_tool,
                tree_sitter_tool
            ],
            llm=self.llm,
            verbose=False,  # Disabled to reduce Railway log spam
            memory=False,
            max_iter=10,
            allow_delegation=False
        )
