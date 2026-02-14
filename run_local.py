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
    if result.pre_existing_findings:
        print(f"PRE-EXISTING ISSUES: {len(result.pre_existing_findings)}")
    print()

    # --- LOG RESULTS TO FILE ---
    import datetime
    import json
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/review_{timestamp}.txt"
    os.makedirs("logs", exist_ok=True)
    
    with open(log_filename, "w", encoding="utf-8") as f:
        f.write(f"REVIEW REPORT - {timestamp}\n")
        f.write(f"Repo: {repo_name} | PR #{pr_number}\n")
        f.write("="*50 + "\n\n")
        
        f.write(f"STATE: {result.review_state}\n")
        f.write(f"SUMMARY: {result.summary_comment}\n\n")
        
        f.write("--- PROCESSED FILES ---\n")
        for filename in [f.filename for f in pr_info.files_changed]:
            f.write(f"- {filename}\n")
        f.write("\n")
        
        f.write(f"--- FINDINGS ({len(result.inline_comments)}) ---\n")
        for finding in result.inline_comments:
            f.write(f"{finding.file_path}:{finding.line_number}\n")
            f.write(f"Comment: {finding.comment}\n")
            f.write("-" * 20 + "\n")
            
        if result.pre_existing_findings:
            f.write(f"\n--- PRE-EXISTING ISSUES ({len(result.pre_existing_findings)}) ---\n")
            for finding in result.pre_existing_findings:
                f.write(f"{finding.file_path}:{finding.line_number}\n")
                f.write(f"Comment: {finding.comment}\n")
                f.write("-" * 20 + "\n")

    print(f"📄 Detailed review log saved to: {log_filename}")
    
    # --- ALSO CREATE FIXED LOG FILE ---
    fixed_log_path = "logs/log.txt"
    with open(fixed_log_path, "w", encoding="utf-8") as f:
        f.write(f"LATEST REVIEW - {timestamp}\n")
        f.write(f"Repo: {repo_name} | PR #{pr_number}\n")
        f.write("="*50 + "\n\n")
        
        f.write("--- FILES PROCESSED ---\n")
        for filename in [f.filename for f in pr_info.files_changed]:
            f.write(f"- {filename}\n")
        f.write("\n")
        
        f.write(f"STATE: {result.review_state}\n")
        f.write(f"SUMMARY: {result.summary_comment}\n\n")
        
        f.write(f"FINDINGS: {len(result.inline_comments)}\n")
        if result.pre_existing_findings:
            f.write(f"PRE-EXISTING ISSUES: {len(result.pre_existing_findings)}\n")
    
    print(f"📄 Fixed log file updated: {fixed_log_path}")
    
    # 7. Post to GitHub?
    # Clear input buffer on Windows to prevent skipped prompts
    import sys
    import time
    if sys.platform == 'win32':
        try:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
        except:
            pass
    
    # Small delay to ensure buffer is clear
    time.sleep(0.1)
    
    # Prompt with retry logic
    max_attempts = 3
    for attempt in range(max_attempts):
        choice = input("Do you want to post these results to GitHub? (y/n): ").strip().lower()
        
        if choice in ['y', 'n']:
            break
        elif choice == '':
            if attempt < max_attempts - 1:
                print("⚠️ No input detected. Please try again.")
                time.sleep(0.2)
            else:
                print("⚠️ No valid input after 3 attempts. Defaulting to 'n'.")
                choice = 'n'
        else:
            print(f"⚠️ Invalid input '{choice}'. Please enter 'y' or 'n'.")
            if attempt == max_attempts - 1:
                choice = 'n'
    
    if choice == 'y':
        valid_paths = [f.filename for f in pr_info.files_changed]
        await commenter.post_review(repo_name, pr_number, result, valid_paths=valid_paths, diff_content=pr_info.full_diff)
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
