"""
Tests for CrewAI tasks.
Verifies task creation, dependency chaining, and context passing.
"""

import pytest
from crewai import Task, Agent
from agents import AgentRegistry
from tasks import (
    ParseCodeTask, QualityAnalysisTask, PerformanceAnalysisTask, 
    SecurityAnalysisTask, ArchitectureAnalysisTask, 
    AggregateFindingsTask, FormatCommentsTask, TaskGraph
)

@pytest.fixture
def agents():
    registry = AgentRegistry()
    # Return mapping
    return {
        "code_quality": registry.get_agent_by_name("code_quality"),
        "performance": registry.get_agent_by_name("performance"),
        "security": registry.get_agent_by_name("security"),
        "architecture": registry.get_agent_by_name("architecture"),
        "report_aggregator": registry.get_agent_by_name("report_aggregator")
    }

def test_parse_code_task(agents):
    """Test ParseCodeTask creation."""
    task = ParseCodeTask().create(
        agent=agents["code_quality"],
        diff_content="diff content",
        pr_details={"repo_name": "test", "pr_number": 1}
    )
    assert isinstance(task, Task)
    assert "Diff Parsing" in [t.name for t in task.tools]

def test_quality_task(agents):
    """Test QualityTask creation."""
    task = QualityAnalysisTask().create(
        agent=agents["code_quality"],
        context_tasks=[]
    )
    assert isinstance(task, Task)
    assert "PEP8" in task.description

def test_performance_task(agents):
    """Test PerformanceTask creation."""
    task = PerformanceAnalysisTask().create(
        agent=agents["performance"],
        context_tasks=[]
    )
    assert "Radon" in task.description

def test_security_task(agents):
    """Test SecurityTask creation."""
    task = SecurityAnalysisTask().create(
        agent=agents["security"],
        context_tasks=[]
    )
    assert "Bandit" in task.description

def test_architecture_task(agents):
    """Test ArchitectureTask creation."""
    task = ArchitectureAnalysisTask().create(
        agent=agents["architecture"],
        context_tasks=[]
    )
    assert "SOLID" in task.description

def test_aggregate_task(agents):
    """Test AggregateTask creation."""
    task = AggregateFindingsTask().create(
        agent=agents["report_aggregator"],
        context_tasks=[]
    )
    assert "Finding Aggregator" in [t.name for t in task.tools]

def test_format_comments_task(agents):
    """Test FormatCommentsTask creation and model."""
    task = FormatCommentsTask().create(
        agent=agents["report_aggregator"],
        context_tasks=[]
    )
    assert "GitHubReview" in task.description
    assert task.output_pydantic is not None

def test_task_graph_sequence(agents):
    """Test TaskGraph sequence generation."""
    graph = TaskGraph()
    tasks = graph.get_task_sequence(
        agents=agents,
        diff_content="diff",
        pr_details={"repo_name": "test"}
    )
    
    assert len(tasks) == 7
    
    # Check order
    assert isinstance(tasks[0].agent, type(agents["code_quality"])) # Parse
    assert isinstance(tasks[5].agent, type(agents["report_aggregator"])) # Aggregate
    assert isinstance(tasks[6].agent, type(agents["report_aggregator"])) # Format

def test_task_context_passing(agents):
    """Test that tasks are linked via context."""
    graph = TaskGraph()
    tasks = graph.get_task_sequence(agents, "diff", {})
    
    # Format task depends on Aggregate
    fmt_task = tasks[6]
    agg_task = tasks[5]
    
    assert agg_task in fmt_task.context
    
    # Aggregate depends on analysis tasks (indices 1,2,3,4)
    analysis_tasks = tasks[1:5]
    for t in analysis_tasks:
        assert t in agg_task.context
