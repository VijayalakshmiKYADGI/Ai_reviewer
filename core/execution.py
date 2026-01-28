from typing import Optional
from data.models import ReviewInput, AgentOutput, GitHubReview
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
        final_review: GitHubReview
        if isinstance(raw_result, GitHubReview):
            final_review = raw_result
        else:
            # Fallback for when kickoff returns a string/dict (e.g. on minor parsing issues)
            import json
            import re
            
            str_content = str(raw_result.raw) if hasattr(raw_result, 'raw') else str(raw_result)
            
            # Cleanup: Remove markdown markers
            clean_json = str_content
            if "{" in str_content:
                clean_json = "{" + str_content.split("{", 1)[1]
            if "}" in clean_json:
                clean_json = clean_json.rsplit("}", 1)[0] + "}"
                
            try:
                result_data = json.loads(clean_json)
                final_review = GitHubReview(**result_data)
            except Exception:
                logger.warning("json_parse_failed_emergency_regex", raw=str_content[:50])
                # Minimal emergency extraction
                comments = []
                # Greedy match for comment-like patterns in non-JSON text
                raw_comments = re.findall(r'comment[\':]\s*[\'"]?([^\'"]+)[\'"]?', str_content)
                raw_paths = re.findall(r'file_path[\':]\s*[\'"]?([^\'"]+)[\'"]?', str_content)
                
                for i in range(min(len(raw_comments), len(raw_paths))):
                    comments.append({
                        "file_path": raw_paths[i],
                        "line_number": "1", # Default fallback
                        "comment": raw_comments[i]
                    })
                
                final_review = GitHubReview(
                    inline_comments=comments,
                    summary_comment="Parsed via emergency extraction.",
                    review_state="REQUESTED_CHANGES" if comments else "COMMENTED"
                )

        # 4. DB Save Results
        execution_time = time.time() - start_time
        
        # Extract agent findings if available to populate DB correctly
        agent_outputs = []
        if hasattr(crew_runner.crew, 'tasks_output'):
            # Task 1 is ComprehensiveReviewTask in the sequence [Parse, Comprehensive, Format]
            # Actually index 1 is ComprehensiveReviewTask
            for task_out in crew_runner.crew.tasks_output:
                if task_out.description and "multi-dimensional" in task_out.description:
                    if hasattr(task_out, 'pydantic') and task_out.pydantic:
                        from data.models import AgentOutput
                        findings = getattr(task_out.pydantic, 'findings', [])
                        agent_outputs.append(AgentOutput(
                            agent_name="Lead Software Engineer",
                            findings=findings,
                            execution_time=0.0 # Unknown for individual task
                        ))

        save_full_review_results(
            review_id=review_id,
            github_review=final_review,
            agent_outputs=agent_outputs,
            execution_time=execution_time
        )
        
        logger.info("pipeline_completed", execution_time=execution_time, findings_count=len(final_review.inline_comments))
        return final_review
        
    except Exception as e:
        logger.error("pipeline_failed", error=str(e))
        # Logic to update DB with failure status could go here
        raise e
