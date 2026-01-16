"""
Phase 6 validation script.
Verifies Core Crew assembly and CLI structure.
"""
import sys
import asyncio
from core import ReviewCrew, execute_review_pipeline, ReviewConfig
from core.cli import run_local_review
from data.models import ReviewInput

def validate_phase6():
    print("=" * 60)
    print("PHASE 6 VALIDATION")
    print("=" * 60)
    
    errors = []
    
    # [CHECK 1] ReviewCrew Assembly
    print("\n[CHECK 1] ReviewCrew Assembly...")
    try:
        crew = ReviewCrew()
        crew.assemble("diff", {"repo_name": "t", "pr_number": 1})
        if len(crew.crew.agents) == 5 and len(crew.crew.tasks) == 7:
            print("  [OK] Crew assembled 5 agents and 7 tasks")
        else:
            errors.append("Invalid agent/task count")
            print(f"  [FAIL] Agents: {len(crew.crew.agents)}, Tasks: {len(crew.crew.tasks)}")
    except Exception as e:
        errors.append(f"Assembly failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 2] CLI Import and Config
    print("\n[CHECK 2] CLI & Pipeline components...")
    try:
        if callable(run_local_review) and callable(execute_review_pipeline):
            print("  [OK] CLI and Pipeline functions available")
        else:
            errors.append("Missing core functions")
            print("  [FAIL] Missing functions")
    except Exception as e:
         errors.append(f"Check failed: {e}")
         print(f"  [FAIL] {e}")

    # [CHECK 3] Config defaults
    print("\n[CHECK 3] Config defaults...")
    try:
        cfg = ReviewConfig()
        if cfg.max_execution_time == 300:
             print("  [OK] Config defaults correct")
        else:
             errors.append("Config defaults wrong")
             print("  [FAIL] Defaults wrong")
    except Exception as e:
        errors.append(f"Config check failed: {e}")
        print(f"  [FAIL] {e}")

    print("\n" + "=" * 60)
    if errors:
        print("PHASE 6 [FAIL] VALIDATION FAILED")
        sys.exit(1)
    else:
        print("PHASE 6 [SUCCESS] VALIDATED")
        print("Core pipeline ready for Backend.")
    print("=" * 60)

if __name__ == "__main__":
    validate_phase6()
