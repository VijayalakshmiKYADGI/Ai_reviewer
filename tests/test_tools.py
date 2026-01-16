"""
Tests for static analysis tools.
Verifies integration with external tools and Pydantic models.
"""

import pytest
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
from data.models import ReviewFinding

# Path to test code directory
TEST_CODE_DIR = Path("tests/test-code")
FLAWED_FILE = TEST_CODE_DIR / "flawed_quality.py"
VULNERABLE_FILE = TEST_CODE_DIR / "vulnerable_security.py"
SLOW_FILE = TEST_CODE_DIR / "slow_performance.py"
DIFF_FILE = TEST_CODE_DIR / "sample_pr.diff"

def test_tree_sitter_parser():
    """Test AST parsing with TreeSitter."""
    parser = TreeSitterParser()
    
    with open(FLAWED_FILE, "r") as f:
        code = f.read()
        
    blocks = parser.parse_code(code, "flawed_quality.py")
    
    # Should find at least 1 function and 1 class
    assert len(blocks) >= 2
    types = [b.type for b in blocks]
    assert "function_definition" in types
    assert "class_definition" in types
    
    # Check specific block
    func = next(b for b in blocks if b.type == "function_definition" and b.name == "calculate")
    assert func.start_line == 1
    assert "return a+b" in func.content

def test_pylint_tool():
    """Test Pylint integration."""
    tool = PylintTool()
    
    with open(FLAWED_FILE, "r") as f:
        code = f.read()
        
    findings = tool.analyze(code, "flawed_quality.py")
    
    assert len(findings) > 0
    
    # Check for specific issues we know exist in the file
    # C0103: Argument name "a" doesn't conform to snake_case
    # C0114: Missing module docstring
    # C0116: Missing function or method docstring
    
    codes = [f.issue_description[:5] for f in findings]
    
    # Check if we caught some common issues 
    # Note: Pylint output might vary based on version/config, but flawed.py has many issues
    assert any("C0103" in c or "C0114" in c or "C0116" in c for c in codes)
    
    # Verify model structure
    first = findings[0]
    assert isinstance(first, ReviewFinding)
    assert first.agent_name == "quality"

def test_bandit_tool():
    """Test Bandit security scanning."""
    tool = BanditTool()
    
    with open(VULNERABLE_FILE, "r") as f:
        code = f.read()
        
    findings = tool.scan(code, "vulnerable_security.py")
    
    assert len(findings) > 0
    
    # Should find hardcoded password (B105)
    descriptions = [f.issue_description for f in findings]
    assert any("B105" in d for d in descriptions)
    
    # Should be high/critical severity
    severities = [f.severity for f in findings]
    assert "CRITICAL" in severities or "HIGH" in severities

def test_radon_tool():
    """Test Radon complexity analysis."""
    tool = RadonTool()
    
    with open(SLOW_FILE, "r") as f:
        code = f.read()
        
    findings = tool.analyze_complexity(code, "slow_performance.py")
    
    assert len(findings) > 0
    
    # Should find high complexity
    # complex_logic function has very high CC
    descriptions = [f.issue_description for f in findings]
    assert any("Cyclomatic complexity" in d for d in descriptions)
    
    # Check severity
    high_findings = [f for f in findings if f.severity == "HIGH"]
    assert len(high_findings) > 0

def test_diff_parser():
    """Test unified diff parsing."""
    parser = DiffParser()
    
    with open(DIFF_FILE, "r") as f:
        diff = f.read()
        
    files = parser.parse_diff(diff)
    
    assert len(files) == 2 # 2 parsed file changes (README deleted might be parsed if content exists)
    # The sample diff has src/main.py modified, test_main.py added, README.md deleted
    # Our parser keeps files with hunks. 
    
    # Check main.py
    main_py = next((f for f in files if "main.py" in f.filename), None)
    assert main_py is not None
    assert main_py.language == "python"
    assert "Hello Universe" in main_py.full_content
    
    # Check new file
    test_py = next((f for f in files if "test_main.py" in f.filename), None)
    assert test_py is not None
    assert "def test_main():" in test_py.full_content

def test_finding_aggregator():
    """Test deduplication and sorting."""
    aggregator = FindingAggregator()
    
    f1 = ReviewFinding(
        severity="HIGH",
        agent_name="security",
        file_path="test.py",
        line_number=10,
        issue_description="SQL Injection",
        category="security"
    )
    
    f2 = ReviewFinding(
        severity="MEDIUM", # Lower severity, same issue
        agent_name="other",
        file_path="test.py",
        line_number=10,
        issue_description="SQL Injection detected",
        category="security"
    )
    
    f3 = ReviewFinding(
        severity="LOW", 
        agent_name="style",
        file_path="test.py",
        line_number=20,
        issue_description="Bad formatting",
        category="style"
    )
    
    aggregated = aggregator.aggregate([f1, f2, f3])
    
    assert len(aggregated) == 2 # f1 and f2 are dups, f3 is unique
    
    # Check priority (f1 kept over f2 because HIGH > MEDIUM)
    assert aggregated[0].severity == "HIGH" 
    assert aggregated[1].severity == "LOW"

def test_integration_pipeline():
    """Test full pipeline simulation."""
    # 1. Parse diff
    diff_parser = DiffParser()
    with open(DIFF_FILE, "r") as f:
        diff_code = f.read()
    files = diff_parser.parse_diff(diff_code)
    
    all_findings = []
    
    # 2. Run analysis on each file
    pylint = PylintTool()
    for file in files:
        if file.language == "python":
            # For this test, we mock the content analysis since diff only has partial content
            # But we can verify the Tool calls work
            findings = pylint.analyze(file.full_content, file.filename)
            all_findings.extend(findings)
            
    # 3. Aggregate
    aggregator = FindingAggregator()
    final_findings = aggregator.aggregate(all_findings)
    
    # Verify result format
    assert isinstance(final_findings, list)

def test_error_handling():
    """Test tools handle malformed input gracefully."""
    pylint = PylintTool()
    findings = pylint.analyze("this is not python code %*&^%", "bad.py")
    assert isinstance(findings, list) # Should return list, possibly empty, not crash
    
    bandit = BanditTool()
    findings = bandit.scan("", "empty.py")
    assert len(findings) == 0

def test_performance_limits():
    """Ensure tools respect timeout/limits."""
    # This is a basic check, real performance testing would be more involved
    pylint = PylintTool()
    
    # Analyze a small file should be fast
    import time
    start = time.time()
    pylint.analyze("print('hello')", "fast.py")
    duration = time.time() - start
    
    assert duration < 5.0 # Should be well under 5s
