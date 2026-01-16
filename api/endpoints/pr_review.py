from fastapi import APIRouter, BackgroundTasks, HTTPException
from api.models import ReviewRequest, ReviewResponse
from data.models import ReviewInput
from core.execution import execute_review_pipeline
from core.config import ReviewConfig
from core.results import save_review_start
import structlog

logger = structlog.get_logger()
router = APIRouter()

async def run_pipeline_task(review_input: ReviewInput):
    """Background task wrapper."""
    try:
        await execute_review_pipeline(review_input, ReviewConfig())
    except Exception as e:
        logger.error("background_task_failed", error=str(e))

@router.post("/review/pr", response_model=ReviewResponse, status_code=202)
async def review_pr(request: ReviewRequest, background_tasks: BackgroundTasks):
    try:
        # Validate input
        if not request.diff_content and not request.repo_name:
             raise HTTPException(status_code=400, detail="Missing diff or repo info")

        # Map to internal input
        # If diff_content is provided directly
        files = request.files_changed or []
        
        review_input = ReviewInput(
            repo_name=request.repo_name,
            pr_number=request.pr_number,
            pr_url=request.pr_url or "",
            diff_content=request.diff_content or "", # If empty, pipeline might fail or fetch? 
            # Our pipeline assumes content is provided.
            files_changed=files
        )
        
        # Start DB record immediately to get ID
        review_id = save_review_start(review_input)
        
        # Queue task
        background_tasks.add_task(run_pipeline_task, review_input)
        
        return ReviewResponse(
            review_id=review_id,
            status="queued",
            github_review=None, # Async
            execution_time=None
        )
        
    except Exception as e:
        logger.error("pr_review_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
