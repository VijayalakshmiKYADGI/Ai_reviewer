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
        
        # 3. Robust Result Handling (Smart Recovery)
        import json
        import re
        result_data = {}
        str_content = ""
        
        if hasattr(raw_result, 'raw'):
            str_content = raw_result.raw
        else:
            str_content = str(raw_result)

        # 3a. Cleanup: Remove markdown markers and text before/after JSON
        clean_json = str_content
        if "{" in str_content:
            clean_json = "{" + str_content.split("{", 1)[1]
        if "}" in clean_json:
            clean_json = clean_json.rsplit("}", 1)[0] + "}"
            
        try:
            result_data = json.loads(clean_json)
        except Exception:
            # 3b. Emergency Extraction: If JSON is truncated, try Regex for inline comments
            logger.warning("json_parse_failed_trying_regex", raw=str_content[:100])
            
            # Extract common fields using regex in case of truncation
            comments = []
            review_state = "REQUESTED_CHANGES" if "REQUESTED_CHANGES" in str_content else "COMMENTED"
            summary = "Summary could not be fully parsed due to truncation. See individual findings."
            
            # Try to grab anything that looks like "comment": "..."
            raw_comments = re.findall(r'\"comment\"\:\s*\"([^\"]+)\"', str_content)
            raw_paths = re.findall(r'\"file_path\"\:\s*\"([^\"]+)\"', str_content)
            raw_lines = re.findall(r'\"line_number\"\:\s*(\d+|\"[^\"]+\")', str_content)
            
            for i in range(min(len(raw_comments), len(raw_paths))):
                comments.append({
                    "file_path": raw_paths[i],
                    "line_number": raw_lines[i] if i < len(raw_lines) else "1",
                    "comment": raw_comments[i]
                })
            
            result_data = {
                "inline_comments": comments,
                "summary_comment": summary,
                "review_state": review_state
            }

        # 4. Standardize into GitHubReview object
        if isinstance(result_data, dict):
            raw_inline = result_data.get("inline_comments", [])
            fixed_comments = []
            for c in raw_inline:
                if isinstance(c, dict):
                    fixed_comments.append({
                        "file_path": c.get("file_path", "config.py"),
                        "line_number": str(c.get("line_number", "1")).strip('"'),
                        "comment": c.get("comment", "Review finding inside.")
                    })
            
            result = GitHubReview(
                inline_comments=fixed_comments,
                summary_comment=result_data.get("summary_comment", "Review completed."),
                review_state=result_data.get("review_state", "COMMENTED")
            )
        else:
            result = GitHubReview(inline_comments=[], summary_comment=str_content, review_state="COMMENTED")

        # 5. DB Save Results
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
