from typing import List, Dict
from crewai import Agent, Crew, Process

from .code_quality_agent import CodeQualityAgent
from .performance_agent import PerformanceAgent
from .security_agent import SecurityAgent
from .architecture_agent import ArchitectureAgent
from .report_aggregator_agent import ReportAggregatorAgent

class AgentRegistry:
    """Registry to manage and retrieve CrewAI agents."""
    
    def __init__(self):
        self._agents = {
            "code_quality": CodeQualityAgent(),
            "performance": PerformanceAgent(),
            "security": SecurityAgent(),
            "architecture": ArchitectureAgent(),
            "report_aggregator": ReportAggregatorAgent()
        }

    def get_all_agents(self) -> List[Agent]:
        """Return list of all initialized CrewAI agents."""
        return [adapter.create() for adapter in self._agents.values()]

    def get_agent_by_name(self, name: str, llm=None) -> Agent:
        """Get a specific agent instance by name."""
        if name not in self._agents:
            raise ValueError(f"Agent '{name}' not found. Available: {list(self._agents.keys())}")
        
        agent_adapter = self._agents[name]
        if llm:
            agent_adapter.llm = llm
            
        return agent_adapter.create()

    def create_crew(self) -> Crew:
        """Create a default crew with all agents configured."""
        agents = self.get_all_agents()
        # Note: Crew usually needs tasks to be useful. 
        # This returns a crew structure ready to accept tasks.
        return Crew(
            agents=agents,
            process=Process.sequential,
            verbose=True
        )
