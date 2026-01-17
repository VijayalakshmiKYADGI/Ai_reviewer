"""
E2E Verification Tests for Sample Test Project

Verifies:
- Test project structure and file existence
- Intentional flaws are detectable (static analysis)
- GitHub workflow validity
"""

import os
import yaml
import pytest
from pathlib import Path
import ast

TEST_PROJECT_DIR = Path(__file__).parent / "test-project"


def test_test_project_structure():
    """Verify all required files exist."""
    required_files = [
        "flawed_quality.py",
        "vulnerable_security.py",
        "slow_performance.py",
        "poor_architecture.py",
        "README.md",
        ".gitignore",
        "requirements.txt"
    ]
    
    for filename in required_files:
        assert (TEST_PROJECT_DIR / filename).exists(), f"Missing {filename}"
        
    required_workflows = [
        ".github/workflows/test-pr-quality.yml",
        ".github/workflows/test-pr-security.yml",
        ".github/workflows/test-pr-performance.yml",
        ".github/workflows/test-pr-architecture.yml"
    ]
    
    for workflow in required_workflows:
        assert (TEST_PROJECT_DIR / workflow).exists(), f"Missing {workflow}"


def test_github_actions_valid():
    """Verify GitHub Action YAML files are valid."""
    workflow_dir = TEST_PROJECT_DIR / ".github/workflows"
    
    for workflow_file in workflow_dir.glob("*.yml"):
        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
            
        assert content is not None
        assert "name" in content
        # PyYAML 1.1 parses 'on' as boolean True
        assert "on" in content or True in content
        assert "jobs" in content
        assert "trigger-review" in content["jobs"]


def test_flawed_quality_issues():
    """Verify flawed_quality.py contains basic syntax issues detectable by AST."""
    file_path = TEST_PROJECT_DIR / "flawed_quality.py"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Just ensure it parses as Python, even if flawed
    tree = ast.parse(content)
    assert tree is not None
    
    # Check for specific flawed token 'messy_function'
    assert "messy_function" in content
    assert "process_users" in content


def test_vulnerable_security_issues():
    """Verify vulnerable_security.py contains hardcoded secrets pattern."""
    file_path = TEST_PROJECT_DIR / "vulnerable_security.py"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    assert "password" in content
    assert "sk-" in content  # API key prefix
    assert "cursor.execute(f" in content  # SQLi pattern


def test_slow_performance_complexity():
    """Verify slow_performance.py contains nested loops."""
    file_path = TEST_PROJECT_DIR / "slow_performance.py"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check for nested loops
    assert content.count("for ") >= 2
    assert "time.sleep" in content


def test_poor_architecture_structure():
    """Verify poor_architecture.py contains God Class indicators."""
    file_path = TEST_PROJECT_DIR / "poor_architecture.py"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    assert "class GlobalSystem" in content
    assert "def add_user" in content
    assert "def connect_db" in content
    assert "def render_page" in content
    
    # Verify mixed responsibilities in one file
    assert "db" in content.lower()
    assert "ui" in content.lower()


def test_workflow_trigger_branches():
    """Verify workflows trigger on correct branches."""
    # Helper to get 'on' section regardless of parsing
    def get_on_section(yaml_content):
        if "on" in yaml_content:
            return yaml_content["on"]
        if True in yaml_content:
            return yaml_content[True]
        return {}

    # Quality
    with open(TEST_PROJECT_DIR / ".github/workflows/test-pr-quality.yml") as f:
        q_yaml = yaml.safe_load(f)
        on_section = get_on_section(q_yaml)
        assert "test-quality" in on_section["push"]["branches"]
        
    # Security
    with open(TEST_PROJECT_DIR / ".github/workflows/test-pr-security.yml") as f:
        s_yaml = yaml.safe_load(f)
        on_section = get_on_section(s_yaml)
        assert "test-security" in on_section["push"]["branches"]



def test_helper_script_exists():
    """Verify the run_test_project.py script exists."""
    script_path = TEST_PROJECT_DIR.parent / "run_test_project.py"
    assert script_path.exists()
