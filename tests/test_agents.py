"""
Tests for CrewAI agents.
Verifies agent configuration, tool assignment, and basic functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
from crewai import Agent, Crew

from agents import (
    CodeQualityAgent,
    PerformanceAgent,
    SecurityAgent,
    ArchitectureAgent,
    ReportAggregatorAgent,
    AgentRegistry
)

def test_agent_registry():
    """Test retrieving agents from registry."""
    registry = AgentRegistry()
    agents = registry.get_all_agents()
    
    assert len(agents) == 5
    assert all(isinstance(a, Agent) for a in agents)
    
    # Check specific retrieval
    security = registry.get_agent_by_name("security")
    assert security.role == "Application Security Engineer"

def test_code_quality_agent():
    """Test CodeQualityAgent configuration."""
    agent_adapter = CodeQualityAgent()
    agent = agent_adapter.create()
    
    assert agent.role == "Senior Python Developer"
    assert len(agent.tools) == 2
    tool_names = [t.name for t in agent.tools]
    assert "Pylint Analysis" in tool_names
    assert "AST Parsing" in tool_names

def test_performance_agent():
    """Test PerformanceAgent configuration."""
    agent_adapter = PerformanceAgent()
    agent = agent_adapter.create()
    
    assert agent.role == "Performance Engineer"
    assert len(agent.tools) == 2
    assert "Radon Complexity Analysis" in [t.name for t in agent.tools]

def test_security_agent():
    """Test SecurityAgent configuration."""
    agent_adapter = SecurityAgent()
    agent = agent_adapter.create()
    
    assert agent.role == "Application Security Engineer"
    assert "Bandit Security Scan" in [t.name for t in agent.tools]

def test_architecture_agent():
    """Test ArchitectureAgent configuration."""
    agent_adapter = ArchitectureAgent()
    agent = agent_adapter.create()
    
    assert agent.role == "Software Architect"
    # Arch agent only has parser
    assert len(agent.tools) == 1
    assert "Code Structure Analysis" in [t.name for t in agent.tools]

def test_report_aggregator_agent():
    """Test ReportAggregatorAgent configuration."""
    agent_adapter = ReportAggregatorAgent()
    agent = agent_adapter.create()
    
    assert agent.role == "Technical Report Writer"
    assert len(agent.tools) == 0 # Pure reasoning

def test_agent_llm_config():
    """Test LLM configuration for agents."""
    agent = CodeQualityAgent().create()
    
    # Check if LLM is set and is our custom wrapper
    assert agent.llm is not None
    # We can check the model name directly on our wrapper
    if hasattr(agent.llm, "model_name"):
        assert agent.llm.model_name == "gemini-1.5-pro"
    else:
        # Fallback if wrapped differently
        assert "gemini" in str(agent.llm).lower()
    
def test_agent_memory():
    """Verify memory/delegation setting."""
    agent = SecurityAgent().create()
    # Memory attribute isn't always exposed in Agent V2, check delegation instead which is
    assert agent.allow_delegation is False

def test_crew_assembly():
    """Test putting agents into a Crew."""
    registry = AgentRegistry()
    crew = registry.create_crew()
    
    assert isinstance(crew, Crew)
    assert len(crew.agents) == 5

def test_tool_execution():
    """Use tool directly via agent wrapper to verify it runs."""
    agent_adapter = CodeQualityAgent()
    
    # Call the wrapper method directly
    code = "def foo(): pass"
    result = agent_adapter._analyze_wrapper(code)
    
    # Should get a string representation of list
    assert isinstance(result, str)
    assert "[" in result

def test_error_handling_in_tool():
    """Test wrapper handles empty/bad input."""
    agent_adapter = SecurityAgent()
    result = agent_adapter._scan_wrapper("")
    assert result == "[]" # Empty list

def test_agent_iteration_limit():
    """Verify iteration limits."""
    perf_agent = PerformanceAgent().create()
    assert perf_agent.max_iter == 3
    
    sec_agent = SecurityAgent().create()
    assert sec_agent.max_iter == 2
