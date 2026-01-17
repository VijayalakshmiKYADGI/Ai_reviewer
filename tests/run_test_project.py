"""
Local E2E Test Script for Sample Test Project

This script helps verify the test project setup locally before pushing to a real remote.
It simulates the workflow of cloning, branching, and pushing.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

TEST_PROJECT_SRC = Path("tests/test-project")
TEST_REPO_NAME = "my-test-app-local"
TEST_REPO_DIR = Path(f"temp_{TEST_REPO_NAME}")

def setup_local_test_repo():
    """Create a temporary git repo from the test project files."""
    print(f"Creating local test repo in {TEST_REPO_DIR}...")
    
    if TEST_REPO_DIR.exists():
        shutil.rmtree(TEST_REPO_DIR)
    
    # Copy files
    shutil.copytree(TEST_PROJECT_SRC, TEST_REPO_DIR)
    
    # Init git
    subprocess.run(["git", "init"], cwd=TEST_REPO_DIR, check=True)
    subprocess.run(["git", "add", "."], cwd=TEST_REPO_DIR, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=TEST_REPO_DIR, check=True)
    
    print("Local repo created successfully.")

def simulate_branch_push(branch_name: str, flawed_file: str):
    """Simulate creating a feature branch and pushing changes."""
    print(f"\nSimulating push for {branch_name}...")
    
    # Create branch
    subprocess.run(["git", "checkout", "-b", branch_name], cwd=TEST_REPO_DIR, check=True)
    
    # Modify file slightly to ensure change
    with open(TEST_REPO_DIR / flawed_file, "a") as f:
        f.write("\n# Trigger change\n")
        
    subprocess.run(["git", "add", flawed_file], cwd=TEST_REPO_DIR, check=True)
    subprocess.run(["git", "commit", "-m", f"Modify {flawed_file}"], cwd=TEST_REPO_DIR, check=True)
    
    print(f"Branch {branch_name} ready (simulated push).")
    
    # Return to main
    subprocess.run(["git", "checkout", "main"], cwd=TEST_REPO_DIR, check=True)

def cleanup():
    """Remove temp repo."""
    if TEST_REPO_DIR.exists():
        # Handle windows file lock on git folder
        # Simple attempt, ignore errors if locked
        shutil.rmtree(TEST_REPO_DIR, ignore_errors=True)
        print("\nCleanup complete.")

if __name__ == "__main__":
    try:
        setup_local_test_repo()
        
        # Simulate different workflow triggers
        simulate_branch_push("test-quality", "flawed_quality.py")
        simulate_branch_push("test-security", "vulnerable_security.py")
        simulate_branch_push("test-performance", "slow_performance.py")
        
        print("\n✅ Local project structure verification successful.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    finally:
        cleanup()
