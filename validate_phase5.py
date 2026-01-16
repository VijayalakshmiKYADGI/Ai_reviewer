"""
Phase 5 validation script.
Verifies Task creation and Graph orchestration.
"""

import sys
from tasks import TaskGraph, ParseCodeTask
from agents import AgentRegistry
from crewai import Task

def validate_phase5():
    print("=" * 60)
    print("PHASE 5 VALIDATION")
    print("=" * 60)
    
    errors = []
    
    try:
        registry = AgentRegistry()
        agents = {
            "code_quality": registry.get_agent_by_name("code_quality"),
            "performance": registry.get_agent_by_name("performance"),
            "security": registry.get_agent_by_name("security"),
            "architecture": registry.get_agent_by_name("architecture"),
            "report_aggregator": registry.get_agent_by_name("report_aggregator")
        }
    except Exception as e:
        print(f"FAILED to load agents: {e}")
        sys.exit(1)

    # [CHECK 1] ParseCodeTask
    print("\n[CHECK 1] ParseCodeTask parameters...")
    try:
        task = ParseCodeTask().create(agents["code_quality"], "diff", {})
        if "Diff Parsing" in [t.name for t in task.tools]:
             print("  [OK] Valid task with Diff Parsing tool")
        else:
            errors.append("ParseCodeTask missing Diff Parsing tool")
            print("  [FAIL] Missing tool")
    except Exception as e:
        errors.append(f"ParseCodeTask failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 2] Task Graph Sequence
    print("\n[CHECK 2] Task Graph Sequence...")
    try:
        graph = TaskGraph()
        tasks = graph.get_task_sequence(agents, "diff", {})
        if len(tasks) == 7:
            print("  [OK] Generated 7 tasks")
            
            # Check types/names implies correctness
            # 0: Parse
            # 1-4: Analysis
            # 5: Agg
            # 6: Format
            
            if "Aggregate" in tasks[5].description and "GitHub" in tasks[6].description:
                 print("  [OK] Task order seems correct")
            else:
                 errors.append("Task order invalid")
                 print("  [FAIL] Task order invalid")
        else:
            errors.append(f"Generated {len(tasks)} tasks (expected 7)")
            print(f"  [FAIL] Count {len(tasks)}")
    except Exception as e:
        errors.append(f"TaskGraph failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 3] Output Types
    print("\n[CHECK 3] Output Models...")
    try:
        from tasks.format_comments_task import GitHubReview
        if GitHubReview.__name__ == "GitHubReview":
            print("  [OK] GitHubReview model available")
    except Exception as e:
        errors.append(f"Model check failed: {e}")
        print(f"  [FAIL] {e}")

    print("\n" + "=" * 60)
    if errors:
        print("PHASE 5 [FAIL] VALIDATION FAILED")
        sys.exit(1)
    else:
        print("PHASE 5 [SUCCESS] VALIDATED")
        print("Task pipeline ready.")
    print("=" * 60)

if __name__ == "__main__":
    validate_phase5()
