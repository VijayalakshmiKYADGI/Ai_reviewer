-- Database schema for Automated Code Review System
-- SQLite schema with 3 core tables

-- Drop existing tables for clean migrations
DROP TABLE IF EXISTS agent_outputs;
DROP TABLE IF EXISTS findings;
DROP TABLE IF EXISTS reviews;

-- Table: reviews
-- Stores metadata for each PR review session
CREATE TABLE reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_name TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    pr_url TEXT,
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    total_findings INTEGER DEFAULT 0,
    severity_high INTEGER DEFAULT 0,
    severity_medium INTEGER DEFAULT 0,
    severity_low INTEGER DEFAULT 0,
    execution_time_seconds INTEGER,
    total_cost_usd DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE(repo_name, pr_number)
);

CREATE INDEX idx_reviews_repo_pr ON reviews(repo_name, pr_number);

-- Table: findings
-- Stores individual code review findings from agents
CREATE TABLE findings (
    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    agent_name TEXT NOT NULL CHECK(agent_name IN ('quality', 'performance', 'security', 'architecture')),
    severity TEXT NOT NULL CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    file_path TEXT NOT NULL,
    line_number INTEGER,
    code_block TEXT,
    issue_description TEXT NOT NULL,
    fix_suggestion TEXT,
    category TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES reviews(review_id) ON DELETE CASCADE
);

CREATE INDEX idx_findings_review_severity ON findings(review_id, severity);

-- Table: agent_outputs
-- Stores execution metadata for each agent run
CREATE TABLE agent_outputs (
    output_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    agent_name TEXT NOT NULL,
    execution_time_seconds INTEGER,
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 4),
    raw_output TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES reviews(review_id) ON DELETE CASCADE
);
