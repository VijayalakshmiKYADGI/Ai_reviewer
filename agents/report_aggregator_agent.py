import os
from textwrap import dedent
from crewai import Agent
from .gemini_llm import GeminiLLM
import structlog

logger = structlog.get_logger()

class ReportAggregatorAgent:
    def __init__(self):
        self.llm = GeminiLLM(
            model_name="gemini-1.5-pro",
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
