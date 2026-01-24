import os
from textwrap import dedent
from crewai import Agent

from tools import PylintTool, TreeSitterTool, TreeSitterParser
from langchain_google_genai import ChatGoogleGenerativeAI
import structlog

logger = structlog.get_logger()

class CodeQualityAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL"),
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.1,
            max_retries=1
        )
        # Utility parser for internal logic if needed, but tool instances are separate
        self.parser = TreeSitterParser()

    def create(self) -> Agent:
        return Agent(
            role="Lead Software Engineer",
            goal="Identify code quality, performance, security and architecture issues in Python code",
            backstory=dedent("""\
                You are a senior technical lead with deep expertise in all aspects of Python development.
                You are strictly PEP8 compliant, security-conscious, and performance-driven.
                You use tools to analyze code and provide comprehensive feedback."""),
            tools=[
                PylintTool(),
                RadonTool(),
                BanditTool(),
                TreeSitterTool()
            ],
            llm=self.llm,
            verbose=False,
            memory=False,
            max_iter=10,
            max_rpm=1,
            allow_delegation=False
        )
