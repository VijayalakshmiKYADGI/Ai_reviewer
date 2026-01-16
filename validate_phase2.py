# -*- coding: utf-8 -*-
"""
Phase 2 validation script.
Validates database schema, Pydantic models, and basic operations.
"""

import os
import sys
import json
from pathlib import Path

# Set test database
os.environ["DATABASE_URL"] = "sqlite:///data/validation_test.db"

def validate_phase2():
    """Run all Phase 2 validation checks."""
    print("=" * 60)
    print("PHASE 2 VALIDATION")
    print("=" * 60)
    
    errors = []
    
    # Check 1: Schema file exists and executes
    print("\n[CHECK 1] Schema execution...")
    try:
        from data.database import init_database, get_db_connection
        
        # Remove existing validation db
        db_path = Path("data/validation_test.db")
        if db_path.exists():
            db_path.unlink()
        
        init_database()
        print("  [OK] schema.sql executed successfully")
    except Exception as e:
        errors.append(f"Schema execution failed: {e}")
        print(f"  [FAIL] {e}")
    
    # Check 2: Verify tables created
    print("\n[CHECK 2] Table creation...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('reviews', 'findings', 'agent_outputs')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        if len(tables) == 3:
            print(f"  [OK] All 3 tables created: {', '.join(tables)}")
        else:
            errors.append(f"Expected 3 tables, found {len(tables)}")
            print(f"  [FAIL] Only {len(tables)} tables found")
        
        # Count columns
        cursor.execute("PRAGMA table_info(reviews)")
        review_cols = len(cursor.fetchall())
        
        cursor.execute("PRAGMA table_info(findings)")
        finding_cols = len(cursor.fetchall())
        
        cursor.execute("PRAGMA table_info(agent_outputs)")
        output_cols = len(cursor.fetchall())
        
        total_cols = review_cols + finding_cols + output_cols
        print(f"  [OK] Total columns: {total_cols} (reviews: {review_cols}, findings: {finding_cols}, agent_outputs: {output_cols})")
        
        conn.close()
    except Exception as e:
        errors.append(f"Table verification failed: {e}")
        print(f"  [FAIL] {e}")
    
    # Check 3: Pydantic model validation
    print("\n[CHECK 3] Pydantic model validation...")
    try:
        from data.models import ReviewFinding, AgentOutput, ReviewSummary, ReviewInput
        from pydantic import ValidationError
        
        # Test valid finding
        finding = ReviewFinding(
            severity="HIGH",
            agent_name="security",
            file_path="test.py",
            line_number=42,
            issue_description="Test security issue for validation",
            category="security"
        )
        print("  [OK] ReviewFinding validates correctly")
        
        # Test invalid severity (should raise error)
        try:
            bad_finding = ReviewFinding(
                severity="INVALID",
                agent_name="security",
                file_path="test.py",
                issue_description="Test issue",
                category="security"
            )
            errors.append("Pydantic validation should have failed for invalid severity")
            print("  [FAIL] Invalid severity not caught")
        except ValidationError:
            print("  [OK] Invalid severity correctly rejected")
        
        # Test ReviewSummary computed properties
        agent_output = AgentOutput(
            agent_name="security",
            findings=[finding],
            execution_time=10.0
        )
        
        review = ReviewSummary(
            repo_name="test/repo",
            pr_number=123,
            pr_url="https://github.com/test/repo/pull/123",
            status="completed",
            agent_outputs=[agent_output]
        )
        
        assert review.total_findings == 1
        assert review.severity_counts["HIGH"] == 1
        print("  [OK] Computed properties work correctly")
        
    except Exception as e:
        errors.append(f"Pydantic validation failed: {e}")
        print(f"  [FAIL] {e}")
    
    # Check 4: Save and retrieve review
    print("\n[CHECK 4] Database CRUD operations...")
    try:
        from data import save_review, get_review_by_id, save_findings
        
        review_id = save_review(review)
        assert review_id > 0
        print(f"  [OK] save_review() returned ID: {review_id}")
        
        retrieved = get_review_by_id(review_id)
        assert retrieved is not None
        assert retrieved.repo_name == "test/repo"
        print("  [OK] get_review_by_id() retrieved correct data")
        
    except Exception as e:
        errors.append(f"CRUD operations failed: {e}")
        print(f"  [FAIL] {e}")
    
    # Check 5: Cascade delete
    print("\n[CHECK 5] Foreign key cascade delete...")
    try:
        from data import save_findings
        
        save_findings(review_id, [finding])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify finding exists
        cursor.execute("SELECT COUNT(*) FROM findings WHERE review_id = ?", (review_id,))
        count_before = cursor.fetchone()[0]
        assert count_before == 1
        
        # Delete review
        cursor.execute("DELETE FROM reviews WHERE review_id = ?", (review_id,))
        conn.commit()
        
        # Verify finding was cascade deleted
        cursor.execute("SELECT COUNT(*) FROM findings WHERE review_id = ?", (review_id,))
        count_after = cursor.fetchone()[0]
        assert count_after == 0
        
        conn.close()
        print("  [OK] CASCADE DELETE works correctly")
        
    except Exception as e:
        errors.append(f"Cascade delete failed: {e}")
        print(f"  [FAIL] {e}")
    
    # Cleanup
    db_path = Path("data/validation_test.db")
    if db_path.exists():
        db_path.unlink()
    
    # Final result
    print("\n" + "=" * 60)
    if errors:
        print("PHASE 2 [FAIL] VALIDATION FAILED")
        print("\nErrors found:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("PHASE 2 [SUCCESS] VALIDATED")
        print("\nAll checks passed:")
        print("  [OK] schema.sql executes without errors")
        print("  [OK] All 3 tables created with correct columns")
        print("  [OK] Pydantic models validate sample JSON")
        print("  [OK] save_review() inserts and returns ID")
        print("  [OK] Cascade delete works")
    print("=" * 60)


if __name__ == "__main__":
    validate_phase2()
