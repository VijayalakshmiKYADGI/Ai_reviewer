import os
from textwrap import dedent
from crewai import Agent

from tools import BanditTool, TreeSitterTool, TreeSitterParser
from langchain_google_genai import ChatGoogleGenerativeAI
import structlog

logger = structlog.get_logger()

class SecurityAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", # Changed to a compatible model
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.1
        )
        self.parser = TreeSitterParser()

    def create(self) -> Agent:
        return Agent(
            role="Application Security Engineer",
            goal="Find security vulnerabilities, hardcoded secrets, and injection risks",
            backstory=dedent("""\
                You are a security expert familiar with OWASP Top 10.
                You never let a hardcoded password or SQL injection vulnerability pass.
                You analyze code to ensure it is secure against common attacks.
                You characterize risks as CRITICAL, HIGH, or MEDIUM."""),
            tools=[
                BanditTool(),
                TreeSitterTool()
            ],
            llm=self.llm,
            verbose=False,  # Disabled to reduce Railway log spam
            memory=True,
            max_iter=2,
            allow_delegation=False
        )
