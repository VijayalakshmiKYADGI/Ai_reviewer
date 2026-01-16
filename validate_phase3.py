"""
Phase 3 validation script.
Verifies static analysis tools functionality.
"""

import sys
import os
from pathlib import Path
from tools import (
    TreeSitterParser,
    PylintTool,
    BanditTool,
    RadonTool,
    DiffParser,
    FindingAggregator
)

def validate_phase3():
    print("=" * 60)
    print("PHASE 3 VALIDATION")
    print("=" * 60)
    
    errors = []
    test_dir = Path("tests/test-code")
    
    # [CHECK 1] TreeSitter
    print("\n[CHECK 1] TreeSitter Parser...")
    try:
        parser = TreeSitterParser()
        with open(test_dir / "flawed_quality.py", "r") as f:
            code = f.read()
        blocks = parser.parse_code(code, "flawed.py")
        if len(blocks) >= 2:
            print(f"  [OK] Extracted {len(blocks)} code blocks")
        else:
            errors.append(f"TreeSitter found only {len(blocks)} blocks (expected >= 2)")
            print(f"  [FAIL] Found {len(blocks)} blocks")
    except Exception as e:
        errors.append(f"TreeSitter failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 2] Pylint
    print("\n[CHECK 2] Pylint Analysis...")
    try:
        tool = PylintTool()
        with open(test_dir / "flawed_quality.py", "r") as f:
            code = f.read()
        findings = tool.analyze(code, "flawed.py")
        if len(findings) >= 5:
            print(f"  [OK] Found {len(findings)} style issues")
            print(f"       Sample: {findings[0].issue_description[:50]}...")
        else:
            errors.append(f"Pylint found only {len(findings)} issues (expected >= 5)")
            print(f"  [FAIL] Found only {len(findings)} issues")
    except Exception as e:
        errors.append(f"Pylint failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 3] Bandit
    print("\n[CHECK 3] Bandit Security Scan...")
    try:
        tool = BanditTool()
        with open(test_dir / "vulnerable_security.py", "r") as f:
            code = f.read()
        findings = tool.scan(code, "vuln.py")
        
        has_critical = any(f.severity == "CRITICAL" for f in findings)
        if len(findings) >= 2 and has_critical:
            print(f"  [OK] Found {len(findings)} security issues (CRITICAL confirmed)")
        else:
            errors.append(f"Bandit validation failed (count={len(findings)}, critical={has_critical})")
            print(f"  [FAIL] Count: {len(findings)}, Critical: {has_critical}")
    except Exception as e:
        errors.append(f"Bandit failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 4] Radon
    print("\n[CHECK 4] Radon Complexity...")
    try:
        tool = RadonTool()
        with open(test_dir / "slow_performance.py", "r") as f:
            code = f.read()
        findings = tool.analyze_complexity(code, "slow.py")
        
        if len(findings) >= 1:
            print(f"  [OK] Found {len(findings)} complexity issues")
        else:
            errors.append("Radon found no complexity issues")
            print("  [FAIL] No issues found")
    except Exception as e:
        errors.append(f"Radon failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 5] Diff Parser
    print("\n[CHECK 5] Diff Parsing...")
    try:
        parser = DiffParser()
        with open(test_dir / "sample_pr.diff", "r") as f:
            diff = f.read()
        files = parser.parse_diff(diff)
        
        if len(files) >= 2:
            print(f"  [OK] Parsed {len(files)} changed files")
        else:
            errors.append(f"DiffParser found {len(files)} files (expected >= 2)")
            print(f"  [FAIL] Found {len(files)} files")
    except Exception as e:
        errors.append(f"DiffParser failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 6] Aggregation
    print("\n[CHECK 6] Findings Aggregation...")
    try:
        agg = FindingAggregator()
        # Create dummy findings
        from data.models import ReviewFinding
        f1 = ReviewFinding(severity="HIGH", agent_name="test", file_path="a", issue_description="Duplicate finding description", category="test")
        f2 = ReviewFinding(severity="LOW", agent_name="test", file_path="a", issue_description="Duplicate finding description", category="test")
        
        res = agg.aggregate([f1, f2])
        if len(res) == 1 and res[0].severity == "HIGH":
            print("  [OK] Deduplication and prioritization worked")
        else:
            errors.append("Aggregation logic failed")
            print("  [FAIL] Aggregation failed")
    except Exception as e:
        errors.append(f"Aggregator failed: {e}")
        print(f"  [FAIL] {e}")

    print("\n" + "=" * 60)
    if errors:
        print("PHASE 3 [FAIL] VALIDATION FAILED")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("PHASE 3 [SUCCESS] VALIDATED")
        print("All static analysis tools are functional.")
    print("=" * 60)

if __name__ == "__main__":
    validate_phase3()
