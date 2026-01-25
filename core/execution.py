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
        raw_result = crew_runner.kickoff(review_input)
        
        # 3. Robust Result Handling
        # Handle CrewAI results which can be string, dict, or CrewOutput object
        result_data = {}
        
        # Extract string content from various possibilities
        str_content = ""
        if hasattr(raw_result, 'raw'): # CrewOutput object
            str_content = raw_result.raw
        elif isinstance(raw_result, str):
            str_content = raw_result
        else:
            str_content = str(raw_result)

        # Cleanup JSON wrapper if present (```json ... ```)
        if "```json" in str_content:
            str_content = str_content.split("```json")[1].split("```")[0].strip()
        elif "```" in str_content:
            str_content = str_content.split("```")[1].split("```")[0].strip()
            
        try:
            result_data = json.loads(str_content)
        except Exception:
            logger.warning("failed_to_parse_json_result", raw=str_content[:200])
            result_data = {
                "inline_comments": [],
                "summary_comment": str_content,
                "review_state": "COMMENTED"
            }

        # Convert to GitHubReview object (manually or via model_validate)
        if isinstance(result_data, dict):
            # Ensure required fields exist for the UI/Commenter
            inline_comments = result_data.get("inline_comments", [])
            # Fix case where LLM might return dicts with wrong keys
            fixed_comments = []
            for c in inline_comments:
                fixed_comments.append({
                    "file_path": c.get("file_path", c.get("path", "README.md")),
                    "line_number": str(c.get("line_number", c.get("line", "1"))),
                    "comment": c.get("comment", c.get("body", "No comment provided"))
                })
            
            result = GitHubReview(
                inline_comments=fixed_comments,
                summary_comment=result_data.get("summary_comment", "Review completed."),
                review_state=result_data.get("review_state", "COMMENTED")
            )
        else:
            result = GitHubReview(
                inline_comments=[],
                summary_comment=str(result_data),
                review_state="COMMENTED"
            )

        # 4. DB Save Results
        execution_time = time.time() - start_time
        save_full_review_results(
            review_id=review_id,
            github_review=result,
            agent_outputs=[], # Simplified for now
            execution_time=execution_time
        )
        
        logger.info("pipeline_completed", execution_time=execution_time)
        return result
        
    except Exception as e:
        logger.error("pipeline_failed", error=str(e))
        # Logic to update DB with failure status could go here
        raise e
