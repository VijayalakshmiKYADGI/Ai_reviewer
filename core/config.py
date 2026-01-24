from dataclasses import dataclass

@dataclass
class ReviewConfig:
    """Configuration for the Review Crew execution."""
    max_execution_time: int = 300  # seconds
    max_findings_per_file: int = 20
    max_total_findings: int = 100
    enable_memory: bool = False
    verbose: bool = True
    temperature: float = 0.1
    early_termination_threshold: int = 3  # Stop if CRITICAL findings > threshold (optional logic)
