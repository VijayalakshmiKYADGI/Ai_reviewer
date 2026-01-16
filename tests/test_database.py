"""
Pytest tests for database layer functionality.
Tests schema creation, CRUD operations, and Pydantic validation.
"""

import os
import sqlite3
import pytest
from datetime import datetime
from pathlib import Path
from pydantic import ValidationError

from data import (
    init_database,
    save_review,
    save_findings,
    get_review_by_id,
    update_review_status,
    get_db_connection,
    ReviewFinding,
    AgentOutput,
    ReviewSummary,
    ReviewInput
)


@pytest.fixture
def test_db():
    """Create a clean test database for each test."""
    # Use in-memory database for tests
    os.environ["DATABASE_URL"] = "sqlite:///tests/test_reviews.db"
    
    # Remove existing test db
    test_db_path = Path("tests/test_reviews.db")
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Initialize fresh database
    init_database()
    
    yield
    
    # Cleanup
    if test_db_path.exists():
        test_db_path.unlink()


def test_database_init(test_db):
    """Test that database initialization creates all required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check that 3 tables exist
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('reviews', 'findings', 'agent_outputs')
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    assert len(tables) == 3
    assert "reviews" in tables
    assert "findings" in tables
    assert "agent_outputs" in tables
    
    # Verify reviews table schema
    cursor.execute("PRAGMA table_info(reviews)")
    columns = {row[1] for row in cursor.fetchall()}
    
    expected_columns = {
        "review_id", "repo_name", "pr_number", "pr_url", "status",
        "total_findings", "severity_high", "severity_medium", "severity_low",
        "execution_time_seconds", "total_cost_usd", "created_at", "completed_at"
    }
    
    assert expected_columns.issubset(columns)
    
    conn.close()


def test_save_and_retrieve_review(test_db):
    """Test saving a review and retrieving it with all findings."""
    # Create mock review with findings
    findings = [
        ReviewFinding(
            severity="HIGH",
            agent_name="security",
            file_path="src/auth.py",
            line_number=42,
            code_block="password = request.args.get('pwd')",
            issue_description="Password transmitted in URL parameters",
            fix_suggestion="Use POST with encrypted body",
            category="security"
        ),
        ReviewFinding(
            severity="MEDIUM",
            agent_name="quality",
            file_path="src/utils.py",
            line_number=15,
            issue_description="Function complexity exceeds threshold",
            fix_suggestion="Refactor into smaller functions",
            category="style"
        ),
        ReviewFinding(
            severity="LOW",
            agent_name="performance",
            file_path="src/db.py",
            line_number=88,
            issue_description="N+1 query detected in loop",
            fix_suggestion="Use batch query or eager loading",
            category="performance"
        )
    ]
    
    agent_output = AgentOutput(
        agent_name="security",
        findings=findings,
        execution_time=12.5,
        tokens_used=1500
    )
    
    review = ReviewSummary(
        repo_name="testorg/testrepo",
        pr_number=123,
        pr_url="https://github.com/testorg/testrepo/pull/123",
        status="completed",
        agent_outputs=[agent_output],
        execution_time=45.2,
        total_cost=0.0234
    )
    
    # Save review
    review_id = save_review(review)
    assert review_id > 0
    
    # Save findings
    save_findings(review_id, findings)
    
    # Retrieve review
    retrieved = get_review_by_id(review_id)
    
    assert retrieved is not None
    assert retrieved.review_id == review_id
    assert retrieved.repo_name == "testorg/testrepo"
    assert retrieved.pr_number == 123
    assert retrieved.status == "completed"
    assert retrieved.total_findings == 3
    assert retrieved.severity_counts["HIGH"] == 1
    assert retrieved.severity_counts["MEDIUM"] == 1
    assert retrieved.severity_counts["LOW"] == 1


def test_pydantic_validation():
    """Test Pydantic model validation rules."""
    # Test invalid severity
    with pytest.raises(ValidationError):
        ReviewFinding(
            severity="INVALID",  # Should fail
            agent_name="security",
            file_path="test.py",
            issue_description="Test issue description here",
            category="security"
        )
    
    # Test negative pr_number
    with pytest.raises(ValidationError):
        ReviewSummary(
            repo_name="test/repo",
            pr_number=-1,  # Should fail (must be > 0)
            pr_url="https://github.com/test/repo/pull/1",
            status="pending"
        )
    
    # Test empty diff_content
    with pytest.raises(ValidationError):
        ReviewInput(
            repo_name="test/repo",
            pr_number=1,
            pr_url="https://github.com/test/repo/pull/1",
            diff_content="",  # Should fail (cannot be empty)
            files_changed=["test.py"]
        )
    
    # Test valid ReviewInput
    valid_input = ReviewInput(
        repo_name="test/repo",
        pr_number=1,
        pr_url="https://github.com/test/repo/pull/1",
        diff_content="diff --git a/test.py b/test.py\n+new line",
        files_changed=["test.py"]
    )
    assert valid_input.language == "python"  # Default value


def test_severity_counts_computed(test_db):
    """Test that severity_counts computed property works correctly."""
    findings = [
        ReviewFinding(
            severity="CRITICAL",
            agent_name="security",
            file_path="test1.py",
            issue_description="Critical security vulnerability detected",
            category="security"
        ),
        ReviewFinding(
            severity="HIGH",
            agent_name="security",
            file_path="test2.py",
            issue_description="High severity issue found",
            category="security"
        ),
        ReviewFinding(
            severity="HIGH",
            agent_name="quality",
            file_path="test3.py",
            issue_description="Another high severity issue",
            category="quality"
        ),
        ReviewFinding(
            severity="MEDIUM",
            agent_name="performance",
            file_path="test4.py",
            issue_description="Medium severity performance issue",
            category="performance"
        ),
        ReviewFinding(
            severity="LOW",
            agent_name="quality",
            file_path="test5.py",
            issue_description="Low severity style issue",
            category="style"
        )
    ]
    
    agent_output = AgentOutput(
        agent_name="multi",
        findings=findings,
        execution_time=10.0
    )
    
    review = ReviewSummary(
        repo_name="test/repo",
        pr_number=456,
        pr_url="https://github.com/test/repo/pull/456",
        status="completed",
        agent_outputs=[agent_output]
    )
    
    counts = review.severity_counts
    
    assert counts["CRITICAL"] == 1
    assert counts["HIGH"] == 2
    assert counts["MEDIUM"] == 1
    assert counts["LOW"] == 1
    assert review.total_findings == 5


def test_database_cascade_delete(test_db):
    """Test that deleting a review cascades to findings and agent_outputs."""
    # Create and save review with findings
    finding = ReviewFinding(
        severity="HIGH",
        agent_name="security",
        file_path="test.py",
        line_number=10,
        issue_description="Test security issue for cascade delete",
        category="security"
    )
    
    review = ReviewSummary(
        repo_name="cascade/test",
        pr_number=999,
        pr_url="https://github.com/cascade/test/pull/999",
        status="completed",
        agent_outputs=[AgentOutput(
            agent_name="security",
            findings=[finding],
            execution_time=5.0
        )]
    )
    
    review_id = save_review(review)
    save_findings(review_id, [finding])
    
    # Verify data exists
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM findings WHERE review_id = ?", (review_id,))
    assert cursor.fetchone()[0] == 1
    
    # Delete review
    cursor.execute("DELETE FROM reviews WHERE review_id = ?", (review_id,))
    conn.commit()
    
    # Verify findings were cascade deleted
    cursor.execute("SELECT COUNT(*) FROM findings WHERE review_id = ?", (review_id,))
    assert cursor.fetchone()[0] == 0
    
    conn.close()


def test_update_review_status(test_db):
    """Test updating review status and completion time."""
    review = ReviewSummary(
        repo_name="status/test",
        pr_number=111,
        pr_url="https://github.com/status/test/pull/111",
        status="pending"
    )
    
    review_id = save_review(review)
    
    # Update to running
    update_review_status(review_id, "running")
    
    retrieved = get_review_by_id(review_id)
    assert retrieved.status == "running"
    assert retrieved.completed_at is None
    
    # Update to completed with timestamp
    completed_time = datetime.utcnow()
    update_review_status(review_id, "completed", completed_time)
    
    retrieved = get_review_by_id(review_id)
    assert retrieved.status == "completed"
    assert retrieved.completed_at is not None
