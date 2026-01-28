from typing import List, Dict
from crewai import Task, Agent

from .parse_code_task import ParseCodeTask
from .quality_task import QualityAnalysisTask
from .performance_task import PerformanceAnalysisTask
from .security_task import SecurityAnalysisTask
from .architecture_task import ArchitectureAnalysisTask
from .aggregate_task import AggregateFindingsTask
from .format_comments_task import FormatCommentsTask
from .comprehensive_review_task import ComprehensiveReviewTask

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
        parse_task = ParseCodeTask().create(
            agent=agents["comprehensive"],
            diff_content=diff_content,
            pr_details=pr_details
        )
        
        # 2. Comprehensive Analysis
        # Combining all experts into one agent and one task to save quota
        comprehensive_task = ComprehensiveReviewTask().create(
            agent=agents["comprehensive"],
            context_tasks=[parse_task]
        )
        
        # 3. Final Formatting and GitHub Review Prep
        fmt_task = FormatCommentsTask().create(
            agent=agents["report_aggregator"],
            context_tasks=[comprehensive_task]
        )
        
        return [
            parse_task,
            comprehensive_task,
            fmt_task
        ]
