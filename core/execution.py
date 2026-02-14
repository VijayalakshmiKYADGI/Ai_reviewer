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
        try:
            raw_result = crew_runner.kickoff(review_input)
        except Exception as e:
            logger.warning("kickoff_crashed_externally", error=str(e))
            raw_result = f"CRITICAL_SYSTEM_ERROR: {str(e)}"
        
        # 3. Robust Result Handling
        final_review: GitHubReview
        if isinstance(raw_result, GitHubReview):
            final_review = raw_result
        else:
            # Fallback for when kickoff returns a string/dict (e.g. on minor parsing issues)
            import json
            import re
            
            str_content = str(raw_result.raw) if hasattr(raw_result, 'raw') else str(raw_result)
            
            # 1. Isolate the FIRST JSON object if multiple exist (handles duplication)
            clean_json = str_content.strip()
            
            # Remove markdown code fences if present
            if "```" in clean_json:
                # Find first occurrence of a JSON block
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', clean_json, re.DOTALL)
                if json_match:
                    clean_json = json_match.group(1)
                else:
                    # Fallback to simple fence removal
                    clean_json = re.sub(r'^```(?:json)?\s*', '', clean_json)
                    clean_json = re.sub(r'\s*```\s*$', '', clean_json)
            
            # Find the first balanced JSON object boundaries
            if "{" in clean_json and "}" in clean_json:
                stack = []
                start_ptr = clean_json.find("{")
                for i in range(start_ptr, len(clean_json)):
                    if clean_json[i] == "{":
                        stack.append(i)
                    elif clean_json[i] == "}":
                        stack.pop()
                        if not stack:
                            clean_json = clean_json[start_ptr:i+1]
                            break
                
            # Check if we have valid content before attempting parse
            if not clean_json or not clean_json.strip():
                logger.error("json_extraction_empty", raw_preview=str_content[:100])
                final_review = GitHubReview(
                    inline_comments=[],
                    summary_comment="Review extraction failed - no valid JSON output.",
                    review_state="COMMENTED"
                )
            else:
                try:
                    result_data = json.loads(clean_json)
                    final_review = GitHubReview(**result_data)
                except (json.JSONDecodeError, Exception) as je:
                    logger.error("json_parse_failed", error=str(je), raw_preview=clean_json[:200])
                    # Emergency extraction - regex based to capture real line numbers
                    comments = []
                    # Improved regex to find objects with file_path, line_number, and comment
                    # Handles various quoting styles and spacing
                    blocks = re.findall(r'\{(?:[^{}]|(?R))*\}', str_content, re.DOTALL)
                    
                    # If regex-recursion is not supported, use a simpler approach
                    # Look for things that look like InlineComment dicts
                    pattern = r'[\'"]file_path[\'"]\s*:\s*[\'"]([^\'"]+)[\'"].*?[\'"]line_number[\'"]\s*:\s*(\d+).*?[\'"]comment[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]'
                    matches = re.findall(pattern, str_content, re.DOTALL)
                    
                    for path, line, msg in matches:
                        comments.append({
                            "file_path": path,
                            "line_number": int(line),
                            "comment": msg
                        })
                    
                    # Also try to find summary_comment and review_state
                    summary_match = re.search(r'[\'"]summary_comment[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]', str_content, re.DOTALL)
                    state_match = re.search(r'[\'"]review_state[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]', str_content)
                    
                    final_review = GitHubReview(
                        inline_comments=comments,
                        summary_comment=summary_match.group(1) if summary_match else "Parsed via emergency extraction due to JSON error.",
                        review_state=state_match.group(1) if state_match else "REQUESTED_CHANGES" if comments else "COMMENTED"
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
