import os
from textwrap import dedent
from crewai import Agent

from tools import RadonTool, TreeSitterTool, TreeSitterParser
from langchain_google_genai import ChatGoogleGenerativeAI
import structlog

logger = structlog.get_logger()

class PerformanceAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL"),  # Changed to a compatible model
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.1
        )
        self.parser = TreeSitterParser()

    def create(self) -> Agent:
        return Agent(
            role="Performance Engineer",
            goal="Detect algorithmic inefficiencies, complexity hotspots, and resource waste",
            backstory=dedent("""\
                You are an optimization expert who ensures Python code runs at production scale.
                You look for O(n^2) loops, inefficient list comprehensions, and high cyclomatic complexity.
                You use Radon to measure complexity and your own intuition to spot algorithmic traps."""),
            tools=[
                RadonTool(),
                TreeSitterTool()
            ],
            llm=self.llm,
            verbose=False,  # Disabled to reduce Railway log spam
            memory=False,
            max_iter=10,
            max_rpm=2, 
            allow_delegation=False
        )
