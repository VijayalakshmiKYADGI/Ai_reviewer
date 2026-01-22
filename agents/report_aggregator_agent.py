import os
from textwrap import dedent
from crewai import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
import structlog

logger = structlog.get_logger()

class ReportAggregatorAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.3
        )

    def create(self) -> Agent:
        return Agent(
            role="Technical Report Writer",
            goal="Compile findings from all agents into a structured, helpful GitHub review",
            backstory=dedent("""\
                You are a technical writer who specializes in creating clear, actionable code reviews.
                You take raw findings from various experts (Security, Performance, Quality) and maintain a helpful tone.
                You prioritize critical issues and group minor ones.
                You formats the output as a professional GitHub Pull Request review."""),
            tools=[], # Pure reasoning agent
            llm=self.llm,
            verbose=False,  # Disabled to reduce Railway log spam
            memory=False,
            max_iter=2,
            allow_delegation=False
        )
