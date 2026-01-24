from typing import List, Dict
from crewai import Task, Agent

from .parse_code_task import ParseCodeTask
from .quality_task import QualityAnalysisTask
from .performance_task import PerformanceAnalysisTask
from .security_task import SecurityAnalysisTask
from .architecture_task import ArchitectureAnalysisTask
from .aggregate_task import AggregateFindingsTask
from .format_comments_task import FormatCommentsTask

class TaskGraph:
    """Manages the dependency chain of review tasks."""
    
    def get_task_sequence(self, agents: Dict[str, Agent], diff_content: str, pr_details: Dict) -> List[Task]:
        """
        Create the full chain of tasks instantiated with provided agents.
        
        Args:
            agents: Dict mapping role/key to Agent instance. 
                   Expected keys: code_quality, performance, security, architecture, report_aggregator
            diff_content: PR diff string
            pr_details: Dict with repo_name, pr_number logic
            
        Returns:
            List of instantiated Task objects in sequential order
        """
        
        # 1. Parse (Input)
        # Assign to Code Quality Agent as it's the most generic "Code Reader" or dedicated system agent
        # The prompt implied "Agent: None (system task)", but CrewAI requires an agent.
        # We assign to code_quality agent but ensure it focuses on parsing.
        parse_task = ParseCodeTask().create(
            agent=agents["code_quality"],
            diff_content=diff_content,
            pr_details=pr_details
        )
        
        # 2. Sequential Analysis using a Single Generalist Agent
        # Combining experts into one agent severely reduces coordination overhead and 429 risks.
        general_agent = agents["code_quality"]
        
        quality_task = QualityAnalysisTask().create(
            agent=general_agent,
            context_tasks=[parse_task]
        )
        
        perf_task = PerformanceAnalysisTask().create(
            agent=general_agent,
            context_tasks=[parse_task]
        )
        
        sec_task = SecurityAnalysisTask().create(
            agent=general_agent,
            context_tasks=[parse_task]
        )
        
        arch_task = ArchitectureAnalysisTask().create(
            agent=general_agent,
            context_tasks=[parse_task]
        )
        
        # 3. Aggregation and Formatting
        agg_task = AggregateFindingsTask().create(
            agent=agents["report_aggregator"],
            context_tasks=[quality_task, perf_task, sec_task, arch_task]
        )
        
        fmt_task = FormatCommentsTask().create(
            agent=agents["report_aggregator"],
            context_tasks=[agg_task]
        )
        
        return [
            parse_task,
            quality_task,
            perf_task,
            sec_task,
            arch_task,
            agg_task,
            fmt_task
        ]
