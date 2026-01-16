import asyncio
from data.models import ReviewInput
from core.execution import execute_review_pipeline
from core.config import ReviewConfig
from tools import DiffParser

def run_local_review(
    diff_path: str, 
    repo_name: str, 
    pr_number: int
) -> None:
    """
    CLI entry point for local testing.
    Reads a diff file and runs the full pipeline.
    """
    print(f"Starting local review for {repo_name} PR #{pr_number}")
    print(f"Reading diff from: {diff_path}")
    
    try:
        with open(diff_path, "r") as f:
            diff_content = f.read()
            
        # Parse files changed for ReviewInput using parser tool to be accurate
        # Or just pass empty list as ParseCodeTask will do the real work
        parser = DiffParser()
        files = parser.parse_diff(diff_content)
        file_names = [f.filename for f in files]
        
        review_input = ReviewInput(
            repo_name=repo_name,
            pr_number=pr_number,
            diff_content=diff_content,
            files_changed=file_names
        )
        
        # Run pipeline (sync wrapper for async function)
        result = asyncio.run(execute_review_pipeline(
            review_input=review_input,
            config=ReviewConfig(verbose=True)
        ))
        
        print("\n" + "="*60)
        print("REVIEW COMPLETE")
        print("="*60)
        print(f"State: {result.review_state}")
        print(f"Summary: {result.summary_comment[:200]}...")
        print(f"\nInline Comments ({len(result.inline_comments)}):")
        for comment in result.inline_comments:
            print(f"- {comment.get('path')}:{comment.get('line')} -> {comment.get('body')[:50]}...")
            
    except Exception as e:
        print(f"\n[ERROR] Review failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Example usage not run by default
    pass
