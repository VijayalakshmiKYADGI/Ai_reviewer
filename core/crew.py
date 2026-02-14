from typing import List, Optional
import structlog
from crewai import Crew, Process
from agents.agent_registry import AgentRegistry
from tasks.task_graph import TaskGraph
from data.models import ReviewInput, GitHubReview
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
            max_retries=1,
            max_output_tokens=8192
        )

        # 1. Get Agents (Passing shared LLM)
        agents = {
            "comprehensive": self.registry.get_agent_by_name("comprehensive", llm=shared_llm),
            "report_aggregator": self.registry.get_agent_by_name("report_aggregator", llm=shared_llm)
        }
        
        # 2. Get Tasks
        tasks = self.graph.get_task_sequence(
            agents=agents,
            diff_content=diff_content,
            pr_details=pr_details
        )
        
        # 3. Create Crew
        self.crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=self.config.verbose,
            memory=False, # FORCED FALSE to avoid OPENAI_API_KEY requirement
            max_rpm=10
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
                 logger.info("crew_result_extracted_pydantic", model=type(result.pydantic).__name__)
                 return result.pydantic
            
            if isinstance(result, GitHubReview):
                logger.info("crew_result_direct_model")
                return result

            # If it's a TaskOutput but for some reason pydantic is None, 
            # try to parse the raw string as a fallback
            if hasattr(result, "raw") and result.raw:
                try:
                    import json
                    logger.info("crew_result_parsing_raw")
                    data = json.loads(result.raw)
                    return GitHubReview(**data)
                except:
                    logger.warning("crew_result_parse_failed")
                    pass

            return result 

        except Exception as e:
            logger.error("crew_kickoff_failed", error=str(e))
            # Return the error as a string to allow execute_review_pipeline to use emergency extraction
            return f"ERROR_DURING_KICKOFF: {str(e)}"
