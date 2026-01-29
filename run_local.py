#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from data.models import ReviewInput
from github_integration.pr_fetcher import PRFetcher
from github_integration.client import GitHubClient
from core.execution import execute_review_pipeline
from github_integration.commenter import GitHubCommenter

#python run_local.py "VijayalakshmiKYADGI/test" 1

async def run_local_review(repo_name: str, pr_number: int):
    """Run a full review pipeline locally."""
    # 1. Load environment
    load_dotenv()
    
    if not os.getenv("GITHUB_TOKEN") or not os.getenv("GEMINI_API_KEY"):
        print("❌ ERROR: Missing GITHUB_TOKEN or GEMINI_API_KEY in .env file.")
        return

    print(f"🚀 Starting local review for {repo_name} PR #{pr_number}...")
    
    # 2. Setup Integration
    client = GitHubClient()
    fetcher = PRFetcher(client)
    commenter = GitHubCommenter(client)
    
    # 3. Fetch PR Data
    print("📡 Fetching PR data from GitHub...")
    pr_info = await fetcher.get_full_pr_data(repo_name, pr_number)
    
    # 4. Prepare Input
    review_input = ReviewInput(
        repo_name=repo_name,
        pr_number=pr_number,
        pr_url=f"https://github.com/{repo_name}/pull/{pr_number}",
        diff_content=pr_info.full_diff,
        files_changed=[f.filename for f in pr_info.files_changed]
    )
    
    # 5. Execute Pipeline
    print("🧠 Running AI Review (this may take 5-10 minutes due to throttling)...")
    result = await execute_review_pipeline(review_input)
    
    # 6. Output Results
    print("\n" + "="*50)
    print("✅ REVIEW COMPLETED")
    print("="*50)
    print(f"STATE: {result.review_state}")
    print(f"SUMMARY: {result.summary_comment[:200]}...")
    print(f"FINDINGS: {len(result.inline_comments)}")
    print()
    
    # 7. Post to GitHub?
    # Note: Using synchronous input() here is intentional - it works more reliably
    # on Windows than async alternatives. The brief blocking is acceptable for CLI usage.
    choice = input("Do you want to post these results to GitHub? (y/n): ").strip().lower()
    
    if choice == 'y':
        valid_paths = [f.filename for f in pr_info.files_changed]
        await commenter.post_review(repo_name, pr_number, result, valid_paths=valid_paths)
        print("✨ Posted to GitHub successfully!")
    else:
        print("🚫 Review not posted.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run AI Code Review locally.")
    parser.add_argument("repo", help="Repository name (e.g., owner/repo)")
    parser.add_argument("pr", type=int, help="Pull Request number")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_local_review(args.repo, args.pr))
    except Exception as e:
        print(f"💥 CRASHED: {e}")
        import traceback
        traceback.print_exc()
