"""
Phase 4 validation script.
Verifies CrewAI configuration and agent loading.
"""

import sys
import os
from agents import (
    CodeQualityAgent,
    PerformanceAgent,
    SecurityAgent,
    ArchitectureAgent,
    ReportAggregatorAgent,
    AgentRegistry
)
from crewai import Agent, Crew

def validate_phase4():
    print("=" * 60)
    print("PHASE 4 VALIDATION")
    print("=" * 60)
    
    errors = []
    
    # [CHECK 1] CodeQualityAgent Tools
    print("\n[CHECK 1] CodeQualityAgent Configuration...")
    try:
        agent = CodeQualityAgent().create()
        tools = [t.name for t in agent.tools]
        if "Pylint Analysis" in tools and "AST Parsing" in tools:
            print("  [OK] Tools configured correctly")
        else:
            errors.append(f"Missing tools in CodeQualityAgent. Found: {tools}")
            print(f"  [FAIL] Missing tools: {tools}")
    except Exception as e:
        errors.append(f"CodeQualityAgent init failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 2] PerformanceAgent Logic
    print("\n[CHECK 2] PerformanceAgent Logic...")
    try:
        adapter = PerformanceAgent()
        # Test wrapper
        res = adapter._complexity_wrapper("def foo():\n    pass")
        if "[]" in res or "ReviewFinding" in res:
             print("  [OK] Wrapper executed successfully")
        else:
            errors.append("PerformanceAgent wrapper failed to return string list")
            print("  [FAIL] Wrapper output malformed")
    except Exception as e:
        errors.append(f"PerformanceAgent check failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 3] SecurityAgent Logic
    print("\n[CHECK 3] SecurityAgent Logic...")
    try:
        adapter = SecurityAgent()
        # Test wrapper on empty code
        res = adapter._scan_wrapper("")
        if res == "[]":
            print("  [OK] Empty scan handled correctly")
        else:
            errors.append(f"SecurityAgent empty scan returned {res}")
            print("  [FAIL] Empty scan check failed")
    except Exception as e:
        errors.append(f"SecurityAgent check failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 4] ArchitectureAgent Logic
    print("\n[CHECK 4] ArchitectureAgent Logic...")
    try:
        # Just check it creates without error
        agent = ArchitectureAgent().create()
        if agent.role == "Software Architect":
             print("  [OK] Agent created successfully")
    except Exception as e:
        errors.append(f"ArchitectureAgent init failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 5] ReportAggregator
    print("\n[CHECK 5] ReportAggregator Logic...")
    try:
        agent = ReportAggregatorAgent().create()
        if len(agent.tools) == 0:
            print("  [OK] Correctly configured with 0 tools")
        else:
             errors.append("ReportAggregator should have 0 tools")
             print("  [FAIL] Has tools")
    except Exception as e:
        errors.append(f"ReportAggregator init failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 6] AgentRegistry
    print("\n[CHECK 6] AgentRegistry...")
    try:
        reg = AgentRegistry()
        agents = reg.get_all_agents()
        if len(agents) == 5:
            print("  [OK] Registry returns 5 agents")
        else:
            errors.append(f"Registry returned {len(agents)} agents (expected 5)")
            print(f"  [FAIL] Returned {len(agents)}")
    except Exception as e:
        errors.append(f"Registry check failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 7] Crew Assembly
    print("\n[CHECK 7] Crew Assembly...")
    try:
        crew = AgentRegistry().create_crew()
        if isinstance(crew, Crew):
            print("  [OK] Crew created successfully")
    except Exception as e:
        errors.append(f"Crew creation failed: {e}")
        print(f"  [FAIL] {e}")

    print("\n" + "=" * 60)
    if errors:
        print("PHASE 4 [FAIL] VALIDATION FAILED")
        sys.exit(1)
    else:
        print("PHASE 4 [SUCCESS] VALIDATED")
        print("All CrewAI agents ready.")
    print("=" * 60)

if __name__ == "__main__":
    validate_phase4()
