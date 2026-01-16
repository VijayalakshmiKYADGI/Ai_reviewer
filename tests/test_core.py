"""
Tests for Core Crew execution.
Verifies assembly, execution, and integration of the full pipeline.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from core import ReviewCrew, execute_review_pipeline, ReviewConfig
from data.models import ReviewInput
from tasks.format_comments_task import GitHubReview

@pytest.fixture
def mock_review_input():
    return ReviewInput(
        repo_name="test-repo",
        pr_number=1,
        pr_url="https://github.com/test/repo/pull/1",
        diff_content="diff",
        files_changed=["file1.py"]
    )

@pytest.fixture
def no_memory_config():
    return ReviewConfig(enable_memory=False, verbose=False)

def test_review_crew_assembly(no_memory_config):
    """Test that Crew assembles agents and tasks correctly."""
    crew = ReviewCrew(config=no_memory_config)
    crew.assemble("diff", {"repo_name": "test", "pr_number": 1})
    
    # Check 5 agents
    assert len(crew.crew.agents) == 5
    # Check 7 tasks
    assert len(crew.crew.tasks) == 7

def test_config_pass_through():
    """Test config is respected."""
    cfg = ReviewConfig(verbose=False, max_execution_time=100, enable_memory=False)
    crew = ReviewCrew(cfg)
    # Just check local config attribute
    assert crew.config.max_execution_time == 100

@patch("crewai.Crew.kickoff")
def test_kickoff_execution(mock_crew_kickoff, mock_review_input, no_memory_config):
    """Test execution flow."""
    # Mock return
    mock_result = GitHubReview(
        inline_comments=[], 
        summary_comment="Good", 
        review_state="APPROVED"
    )
    mock_crew_kickoff.return_value = mock_result
    
    crew = ReviewCrew(config=no_memory_config)
    res = crew.kickoff(mock_review_input)
    assert res == mock_result
    assert mock_crew_kickoff.called

@patch("core.execution.save_review_start")
@patch("core.execution.save_full_review_results")
@patch("core.execution.ReviewCrew")
def test_full_pipeline_execution(
    mock_crew_cls, mock_save_results, mock_save_start, mock_review_input
):
    """Test the async wrapper pipeline."""
    # We use manual asyncio.run
    
    mock_save_start.return_value = 123
    
    mock_crew_instance = MagicMock()
    mock_crew_cls.return_value = mock_crew_instance
    
    expected_result = GitHubReview(
        inline_comments=[], 
        summary_comment="Done", 
        review_state="COMMENTED"
    )
    mock_crew_instance.kickoff.return_value = expected_result
    
    # Run
    async def run():
        return await execute_review_pipeline(mock_review_input, config=ReviewConfig(enable_memory=False))
        
    res = asyncio.run(run())
    
    assert res == expected_result
    mock_save_start.assert_called_once()
    mock_save_results.assert_called_once()
    assert mock_save_results.call_args[1]['review_id'] == 123

def test_error_recovery(no_memory_config):
    """Test error handling in kickoff."""
    crew = ReviewCrew(config=no_memory_config)
    # If no assembly called (and assemble is called inside kickoff with valid input)
    # But if checking internal error:
    with pytest.raises(Exception):
         # Pass invalid input that causes crash in assemble or kickoff
         crew.kickoff(None)

