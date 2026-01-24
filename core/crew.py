from typing import List, Optional
import structlog
from crewai import Crew, Process
from agents.agent_registry import AgentRegistry
from tasks.task_graph import TaskGraph
from tasks.format_comments_task import GitHubReview
from data.models import ReviewInput
from core.config import ReviewConfig

logger = structlog.get_logger()

class ReviewCrew:
    """
    Orchestrator for the Code Review Crew.
    Manages Agents, Tasks, and Execution.
    """
    
    def __init__(self, config: Optional[ReviewConfig] = None):
        self.config = config or ReviewConfig()
        self.registry = AgentRegistry()
        self.graph = TaskGraph()
        self.crew: Optional[Crew] = None
        
    def assemble(self, diff_content: str, pr_details: dict):
        """Assemble agents and tasks for a specific review context."""
        
        from langchain_google_genai import ChatGoogleGenerativeAI
        import os
        
        # 0. Shared LLM with global throttling
        # We use a single instance to ensure agents share the same connection/pool
        shared_llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL"),
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.1,
            max_retries=1
        )

        # 1. Get Agents (Passing shared LLM)
        # We instantiate fresh agents for each run in this design, 
        # or reuse registry if agents are stateless (they are mostly).
        # We need mapping for TaskGraph.
        agents = {
            "code_quality": self.registry.get_agent_by_name("code_quality", llm=shared_llm),
            "performance": self.registry.get_agent_by_name("performance", llm=shared_llm),
            "security": self.registry.get_agent_by_name("security", llm=shared_llm),
            "architecture": self.registry.get_agent_by_name("architecture", llm=shared_llm),
            "report_aggregator": self.registry.get_agent_by_name("report_aggregator", llm=shared_llm)
        }
        
        # 2. Get Tasks
        tasks = self.graph.get_task_sequence(
            agents=agents,
            diff_content=diff_content,
            pr_details=pr_details
        )
        
        # 3. Create Crew
        # Use official ChatGoogleGenerativeAI (compatible with CrewAI 0.51.1)
        
        self.crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=self.config.verbose,
            memory=self.config.enable_memory,
            max_rpm=1  # Crew-level reinforcement of the RPM limit
        )
        
    def kickoff(self, review_input: ReviewInput) -> GitHubReview:
        """
        Run the full review pipeline.
        
        Args:
            review_input: Input data including diff and repo details.
            
        Returns:
            GitHubReview object with formatted results.
        """
        try:
            # 1. Assemble
            self.assemble(
                diff_content=review_input.diff_content,
                pr_details={
                    "repo_name": review_input.repo_name,
                    "pr_number": review_input.pr_number
                }
            )
            
            if not self.crew:
                raise ValueError("Crew assembly failed")
                
            # 2. Execute
            # CrewAI kickoff returns the output of the last task.
            # FormatCommentsTask returns GitHubReview (Pydantic or Dict).
            result = self.crew.kickoff()
            
            # CrewAI V0.30+ returns TaskOutput object usually, or raw string if simple.
            # If `output_pydantic` was used in Task, `result` should be that model.
            # We handle potential wrapping.
            
            if hasattr(result, "pydantic") and result.pydantic:
                 return result.pydantic
            
            if hasattr(result, "raw"):
                # Try to parse if raw string
                # Or if result itself is the object (CrewAI sometimes returns the model instance directly)
                pass
            
            # If it's already the model
            if isinstance(result, GitHubReview):
                return result

            # If dict/string, try to coerce (fallback)
            # In Phase 5, FormatCommentsTask uses `output_pydantic=GitHubReview`
            # So CrewAI should return the model instance.
            return result 

        except Exception as e:
            logger.error("crew_kickoff_failed", error=str(e))
            raise e
