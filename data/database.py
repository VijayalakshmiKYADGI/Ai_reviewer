"""
Database operations for code review persistence.
Handles SQLite connections and CRUD operations for reviews, findings, and agent outputs.
"""

import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import structlog

from .models import ReviewSummary, ReviewFinding, AgentOutput

logger = structlog.get_logger()


def get_db_connection() -> sqlite3.Connection:
    """
    Create and return a SQLite database connection.
    
    Returns:
        sqlite3.Connection: Database connection with Row factory enabled
        
    Raises:
        sqlite3.Error: If connection fails
    """
    try:
        db_url = os.getenv("DATABASE_URL", "sqlite:///data/reviews.db")
        # Extract file path from sqlite:/// URL
        db_path = db_url.replace("sqlite:///", "")
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        
        logger.info("database_connected", path=db_path)
        return conn
    except sqlite3.Error as e:
        logger.error("database_connection_failed", error=str(e))
        raise


def init_database() -> None:
    """
    Initialize database by executing schema.sql.
    Creates all tables and indexes.
    
    Raises:
        FileNotFoundError: If schema.sql not found
        sqlite3.Error: If schema execution fails
    """
    try:
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        conn = get_db_connection()
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        
        logger.info("database_initialized", schema=str(schema_path))
        print("[OK] Database initialized successfully")
        
    except FileNotFoundError as e:
        logger.error("schema_file_not_found", error=str(e))
        raise
    except sqlite3.Error as e:
        logger.error("database_init_failed", error=str(e))
        raise


def save_review(review_summary: ReviewSummary) -> int:
    """
    Save a review summary to the database.
    
    Args:
        review_summary: ReviewSummary object to persist
        
    Returns:
        int: The review_id of the inserted record
        
    Raises:
        sqlite3.Error: If insert fails
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        severity_counts = review_summary.severity_counts
        
        cursor.execute("""
            INSERT OR REPLACE INTO reviews (
                repo_name, pr_number, pr_url, status,
                total_findings, severity_high, severity_medium, severity_low,
                execution_time_seconds, total_cost_usd, created_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            review_summary.repo_name,
            review_summary.pr_number,
            review_summary.pr_url,
            review_summary.status,
            review_summary.total_findings,
            severity_counts.get("HIGH", 0) + severity_counts.get("CRITICAL", 0),
            severity_counts.get("MEDIUM", 0),
            severity_counts.get("LOW", 0),
            int(review_summary.execution_time),
            review_summary.total_cost,
            review_summary.created_at.isoformat(),
            review_summary.completed_at.isoformat() if review_summary.completed_at else None
        ))
        
        review_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info("review_saved", review_id=review_id, repo=review_summary.repo_name)
        return review_id
        
    except sqlite3.Error as e:
        logger.error("save_review_failed", error=str(e))
        raise


def save_findings(review_id: int, findings: list[ReviewFinding]) -> None:
    """
    Batch insert findings for a review.
    
    Args:
        review_id: ID of the parent review
        findings: List of ReviewFinding objects
        
    Raises:
        sqlite3.Error: If insert fails
    """
    if not findings:
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        finding_data = [
            (
                review_id,
                finding.agent_name,
                finding.severity,
                finding.file_path,
                finding.line_number,
                finding.code_block,
                finding.issue_description,
                finding.fix_suggestion,
                finding.category
            )
            for finding in findings
        ]
        
        cursor.executemany("""
            INSERT INTO findings (
                review_id, agent_name, severity, file_path, line_number,
                code_block, issue_description, fix_suggestion, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, finding_data)
        
        conn.commit()
        conn.close()
        
        logger.info("findings_saved", review_id=review_id, count=len(findings))
        
    except sqlite3.Error as e:
        logger.error("save_findings_failed", error=str(e), review_id=review_id)
        raise


def save_agent_output(review_id: int, agent_output: AgentOutput) -> None:
    """
    Save agent execution metadata and output.
    
    Args:
        review_id: ID of the parent review
        agent_output: AgentOutput object
        
    Raises:
        sqlite3.Error: If insert fails
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Serialize findings to JSON
        raw_output = json.dumps([f.model_dump() for f in agent_output.findings])
        
        cursor.execute("""
            INSERT INTO agent_outputs (
                review_id, agent_name, execution_time_seconds,
                tokens_used, cost_usd, raw_output, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            review_id,
            agent_output.agent_name,
            int(agent_output.execution_time),
            agent_output.tokens_used,
            0.0,  # Cost calculation to be added later
            raw_output,
            agent_output.error
        ))
        
        conn.commit()
        conn.close()
        
        logger.info("agent_output_saved", review_id=review_id, agent=agent_output.agent_name)
        
    except sqlite3.Error as e:
        logger.error("save_agent_output_failed", error=str(e))
        raise


def get_review_by_id(review_id: int) -> Optional[ReviewSummary]:
    """
    Retrieve a complete review with all findings and agent outputs.
    
    Args:
        review_id: ID of the review to retrieve
        
    Returns:
        ReviewSummary object or None if not found
        
    Raises:
        sqlite3.Error: If query fails
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch review
        cursor.execute("SELECT * FROM reviews WHERE review_id = ?", (review_id,))
        review_row = cursor.fetchone()
        
        if not review_row:
            conn.close()
            return None
        
        # Fetch findings
        cursor.execute("""
            SELECT * FROM findings WHERE review_id = ? ORDER BY severity DESC
        """, (review_id,))
        finding_rows = cursor.fetchall()
        
        # Fetch agent outputs
        cursor.execute("""
            SELECT * FROM agent_outputs WHERE review_id = ?
        """, (review_id,))
        agent_rows = cursor.fetchall()
        
        conn.close()
        
        # Reconstruct ReviewSummary
        findings_by_agent = {}
        for row in finding_rows:
            agent_name = row["agent_name"]
            if agent_name not in findings_by_agent:
                findings_by_agent[agent_name] = []
            
            findings_by_agent[agent_name].append(ReviewFinding(
                severity=row["severity"],
                agent_name=row["agent_name"],
                file_path=row["file_path"],
                line_number=row["line_number"],
                code_block=row["code_block"],
                issue_description=row["issue_description"],
                fix_suggestion=row["fix_suggestion"],
                category=row["category"]
            ))
        
        # Build agent_outputs from agent_outputs table if available
        agent_outputs = []
        agent_outputs_dict = {}
        
        for row in agent_rows:
            agent_outputs_dict[row["agent_name"]] = AgentOutput(
                agent_name=row["agent_name"],
                findings=findings_by_agent.get(row["agent_name"], []),
                execution_time=float(row["execution_time_seconds"] or 0),
                tokens_used=row["tokens_used"],
                error=row["error_message"]
            )
        
        # If no agent_outputs in table but we have findings, create agent_outputs from findings
        if not agent_outputs_dict and findings_by_agent:
            for agent_name, findings in findings_by_agent.items():
                agent_outputs_dict[agent_name] = AgentOutput(
                    agent_name=agent_name,
                    findings=findings,
                    execution_time=0.0,
                    tokens_used=None,
                    error=None
                )
        
        agent_outputs = list(agent_outputs_dict.values())
        
        return ReviewSummary(
            review_id=review_row["review_id"],
            repo_name=review_row["repo_name"],
            pr_number=review_row["pr_number"],
            pr_url=review_row["pr_url"],
            status=review_row["status"],
            agent_outputs=agent_outputs,
            execution_time=float(review_row["execution_time_seconds"] or 0),
            total_cost=float(review_row["total_cost_usd"] or 0),
            created_at=datetime.fromisoformat(review_row["created_at"]),
            completed_at=datetime.fromisoformat(review_row["completed_at"]) if review_row["completed_at"] else None
        )
        
    except sqlite3.Error as e:
        logger.error("get_review_failed", error=str(e), review_id=review_id)
        raise


def update_review_status(review_id: int, status: str, completed_at: Optional[datetime] = None) -> None:
    """
    Update the status of a review.
    
    Args:
        review_id: ID of the review to update
        status: New status value
        completed_at: Optional completion timestamp
        
    Raises:
        sqlite3.Error: If update fails
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE reviews 
            SET status = ?, completed_at = ?
            WHERE review_id = ?
        """, (
            status,
            completed_at.isoformat() if completed_at else None,
            review_id
        ))
        
        conn.commit()
        conn.close()
        
        logger.info("review_status_updated", review_id=review_id, status=status)
        
    except sqlite3.Error as e:
        logger.error("update_status_failed", error=str(e))
        raise


def get_reviews_by_repo(repo_name: str, limit: int = 10) -> list[ReviewSummary]:
    """
    Retrieve recent reviews for a repository.
    
    Args:
        repo_name: Repository name (e.g., "owner/repo")
        limit: Maximum number of reviews to return
        
    Returns:
        List of ReviewSummary objects, ordered by most recent first
        
    Raises:
        sqlite3.Error: If query fails
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT review_id FROM reviews 
            WHERE repo_name = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (repo_name, limit))
        
        review_ids = [row["review_id"] for row in cursor.fetchall()]
        conn.close()
        
        # Fetch complete review data for each ID
        reviews = []
        for review_id in review_ids:
            review = get_review_by_id(review_id)
            if review:
                reviews.append(review)
        
        logger.info("reviews_fetched", repo=repo_name, count=len(reviews))
        return reviews
        
    except sqlite3.Error as e:
        logger.error("get_reviews_failed", error=str(e), repo=repo_name)
        raise
