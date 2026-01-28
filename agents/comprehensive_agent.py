import os
from textwrap import dedent
from crewai import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
import structlog

logger = structlog.get_logger()

class ComprehensiveReviewAgent:
    """A generalist agent that performs all aspects of the review in a single session."""
    
    def __init__(self, llm=None):
        self.llm = llm or ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL"),
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.1,
            max_retries=1
        )

    def create(self) -> Agent:
        return Agent(
            role="Lead Software Engineer",
            goal="Perform a complete, multi-dimensional code review in a single pass",
            backstory=dedent("""\
                You are a world-class Lead Software Engineer with expertise in:
                1. Code Quality (PEP8, Readability, Clean Code)
                2. Performance (Complexity, Algorithmic efficiency)
                3. Security (Vulns, Hardcoded secrets, OWASP)
                4. Architecture (SOLID, Design Patterns)
                
                You provide concise, high-impact feedback without unnecessary filler."""),
            tools=[], # We'll provide specialized tools via tasks if needed
            llm=self.llm,
            verbose=True,
            memory=False, # DISABLED - Memory creates extra 'thinking' steps and consumes more calls
            max_iter=3,   # STRICT - Force the agent to finish its analysis quickly
            max_rpm=10,
            allow_delegation=False
        )
