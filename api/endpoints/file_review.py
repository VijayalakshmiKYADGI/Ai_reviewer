from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.models import ReviewResponse
from data.models import ReviewInput
from core.execution import execute_review_pipeline
from core.config import ReviewConfig
from tools import DiffParser
import asyncio

router = APIRouter()

@router.post("/review/file", response_model=ReviewResponse)
async def review_file(
    file: UploadFile = File(...),
    repo_name: str = Form(...),
    pr_number: int = Form(...)
):
    try:
        content_bytes = await file.read()
        diff_content = content_bytes.decode("utf-8")
        
        # Determine files changed (basic parse)
        # Note: If uploading a raw file (not diff), ParseCodeTask logic needs to handle it.
        # But 'ParseCodeTask' expects a DIFF.
        # If user uploads a single python file, we treat it as a diff?
        # Or wrap it?
        # Spec says "Upload code file -> GitHubReview".
        # If I upload "flawed_quality.py", it is not a diff.
        # Construct a fake diff?
        #   diff --git a/filename.py b/filename.py
        #   new file mode 100644
        #   index 0000000..1234567
        #   --- /dev/null
        #   +++ b/filename.py
        #   @@ -0,0 +1,50 @@
        #   + content...
        
        # Ideally, we should support raw file analysis.
        # But Phase 5 ParseCodeTask uses DiffParser.
        # I will wrap the content in a synthetic diff for compatibility.
        
        filename = file.filename or "uploaded_file.py"
        fake_diff = f"diff --git a/{filename} b/{filename}\nnew file mode 100644\n--- /dev/null\n+++ b/{filename}\n@@ -0,0 +1,1000 @@\n"
        # Prepend + to every line
        fake_lines = ["+" + line for line in diff_content.splitlines()]
        fake_diff += "\n".join(fake_lines)
        
        files_changed = [filename]
        
        review_input = ReviewInput(
            repo_name=repo_name,
            pr_number=pr_number,
            pr_url=f"http://upload/{filename}",
            diff_content=fake_diff,
            files_changed=files_changed
        )
        
        # Execute Sync (Wait)
        result = await execute_review_pipeline(
            review_input, 
            config=ReviewConfig(verbose=True)
        )
        
        return ReviewResponse(
            review_id=0, # In a real system, we'd get ID from execution logic or lookup
            status="completed",
            github_review=result,
            execution_time=0.0 # Placeholder or modify pipeline to return time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
