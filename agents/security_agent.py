import os
from textwrap import dedent
from crewai import Agent
from langchain_core.tools import Tool

from tools import BanditTool, TreeSitterParser
from langchain_google_genai import ChatGoogleGenerativeAI
import structlog

logger = structlog.get_logger()

class SecurityAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.1
        )
        self.bandit = BanditTool()
        self.parser = TreeSitterParser()

    def _scan_wrapper(self, code: str) -> str:
        findings = self.bandit.scan(code, "analyzed_file.py")
        return str([f.model_dump() for f in findings])

    def _parse_wrapper(self, code: str) -> str:
        blocks = self.parser.parse_code(code, "analyzed_file.py")
        return str([str(b) for b in blocks])

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
                Tool(
                    name="Bandit Security Scan",
                    func=self._scan_wrapper,
                    description="Run Bandit security scanner to find vulnerabilities like hardcoded secrets. Input is python code string."
                ),
                Tool(
                    name="Code Structure Analysis",
                    func=self._parse_wrapper,
                    description="Analyze code structure. Input is python code string."
                )
            ],
            llm=self.llm,
            verbose=False,  # Disabled to reduce Railway log spam
            memory=True,
            max_iter=2,
            allow_delegation=False
        )
