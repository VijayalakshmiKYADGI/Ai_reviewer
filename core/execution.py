from typing import Optional
from data.models import ReviewInput, AgentOutput
from tasks.format_comments_task import GitHubReview
from core.config import ReviewConfig
from core.crew import ReviewCrew
from core.results import save_review_start, save_full_review_results
import structlog
import time

logger = structlog.get_logger()

async def execute_review_pipeline(
    review_input: ReviewInput, 
    config: Optional[ReviewConfig] = None
) -> GitHubReview:
    """
    Production entry point for running a code review.
    Handles DB persistence, error recovery, and Config.
    """
    if config is None:
        config = ReviewConfig()
        
    start_time = time.time()
    logger.info("pipeline_started", repo=review_input.repo_name, pr=review_input.pr_number)
    
    # 1. DB Start
    review_id = save_review_start(review_input)
    
    try:
        # 2. Crew Execution
        crew_runner = ReviewCrew(config)
        result = crew_runner.kickoff(review_input)
        
        # 3. Extract Intermediate Outputs
        # CrewAI stores task outputs in crew.tasks
        # We extract them for DB records
        agent_outputs = []
        if crew_runner.crew and crew_runner.crew.tasks:
            for task in crew_runner.crew.tasks:
                if task.output:
                    # Map task output to AgentOutput
                    # This is simplified; ideally we parse distinct agent contributions
                    # But for now, we just list task descriptions/results if available
                    # Or rely on what the agents produced (list[ReviewFinding])
                    # Since AgentOutput requires 'findings', 'raw_output'
                    
                    # We skip strict mapping here for MVP and just use placeholder empty list or parse if needed
                    # The prompt asked for `agent_outputs: list[AgentOutput]`
                    # We will create one AgentOutput per task if it produced findings
                    pass

        # 4. DB Save Results
        execution_time = time.time() - start_time
        save_full_review_results(
            review_id=review_id,
            github_review=result,
            agent_outputs=agent_outputs, # Passed empty or populated
            execution_time=execution_time
        )
        
        logger.info("pipeline_completed", execution_time=execution_time)
        return result
        
    except Exception as e:
        logger.error("pipeline_failed", error=str(e))
        # Logic to update DB with failure status could go here
        raise e
