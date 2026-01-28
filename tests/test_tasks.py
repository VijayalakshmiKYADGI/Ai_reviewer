"""
Tests for CrewAI tasks.
Verifies task creation, dependency chaining, and context passing.
"""

import pytest
from crewai import Task, Agent
from agents import AgentRegistry
from tasks import (
    ParseCodeTask, ComprehensiveReviewTask, FormatCommentsTask, TaskGraph
)

@pytest.fixture
def agents():
    registry = AgentRegistry()
    # Return mapping needed for TaskGraph
    return {
        "comprehensive": registry.get_agent_by_name("comprehensive"),
        "report_aggregator": registry.get_agent_by_name("report_aggregator")
    }

def test_parse_code_task(agents):
    """Test ParseCodeTask creation."""
    task = ParseCodeTask().create(
        agent=agents["comprehensive"],
        diff_content="diff content",
        pr_details={"repo_name": "test", "pr_number": 1}
    )
    assert isinstance(task, Task)

def test_comprehensive_review_task(agents):
    """Test ComprehensiveReviewTask creation."""
    task = ComprehensiveReviewTask().create(
        agent=agents["comprehensive"],
        context_tasks=[]
    )
    assert isinstance(task, Task)
    assert "QUALITY" in task.description
    assert "SECURITY" in task.description

def test_format_comments_task(agents):
    """Test FormatCommentsTask creation."""
    task = FormatCommentsTask().create(
        agent=agents["report_aggregator"],
        context_tasks=[]
    )
    assert task.output_pydantic is not None

def test_task_graph_sequence(agents):
    """Test TaskGraph sequence generation (Consolidated to 3 tasks)."""
    graph = TaskGraph()
    tasks = graph.get_task_sequence(
        agents=agents,
        diff_content="diff",
        pr_details={"repo_name": "test", "pr_number": 1}
    )
    
    # New sequence: Parse -> Comprehensive -> Format
    assert len(tasks) == 3
    
    # Check order/context
    assert tasks[1] in tasks[2].context # Format depends on Comprehensive
    assert tasks[0] in tasks[1].context # Comprehensive depends on Parse
