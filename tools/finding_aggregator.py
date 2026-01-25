"""
Aggregator for deduplicating and prioritizing findings.
"""

from typing import List, Dict
import structlog
from data.models import ReviewFinding, ReviewSummary
from crewai.agent import BaseTool
import json

logger = structlog.get_logger()

class FindingAggregator:
    """Aggregates, deduplicates, and sorts findings from multiple tools."""
    
    SEVERITY_WEIGHTS = {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1
    }
    
    def aggregate(self, findings: List[ReviewFinding]) -> List[ReviewFinding]:
        """
        Deduplicate and sort findings.
        
        Args:
            findings: Raw list of findings from all tools
            
        Returns:
            Sorted and filtered list of unique findings
        """
        if not findings:
            return []
            
        # Deduplicate based on unique key
        unique_findings = {}
        
        for f in findings:
            # Create a signature for the finding
            # Group by file, line, and category. Ignore agent_name and description for deduplication
            # This ensures if multiple tools report "style issue" at line 10, we only keep the highest severity one
            key = f"{f.file_path}:{f.line_number}:{f.category}"
            
            if key not in unique_findings:
                unique_findings[key] = f
            else:
                # If duplicate, keep higher severity
                existing = unique_findings[key]
                if self.SEVERITY_WEIGHTS[f.severity] > self.SEVERITY_WEIGHTS[existing.severity]:
                    unique_findings[key] = f
        
        results = list(unique_findings.values())
        
        # Sort by severity (descending) then line number
        results.sort(key=lambda x: (
            -self.SEVERITY_WEIGHTS.get(x.severity, 0),
            x.file_path,
            x.line_number or 0
        ))
        
        # Soft limit per file (20) and total (100)
        final_results = results[:100]
        
        logger.info("findings_aggregated", 
                   raw_count=len(findings), 
                   unique_count=len(final_results))
                   
        return final_results
        
    def get_severity_stats(self, findings: List[ReviewFinding]) -> Dict[str, int]:
        """Calculate stats for aggregated findings."""
        stats = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in findings:
            if f.severity in stats:
                stats[f.severity] += 1
        return stats

class FindingAggregatorTool(BaseTool):
    name: str = "Finding Aggregator"
    description: str = "Aggregate and deduplicate a list of finding objects (JSON string). Input: JSON list of dicts."

    def _run(self, findings_json: str) -> str:
        aggregator = FindingAggregator()
        all_findings = []
        
        # Cleanup input string (sometimes LLMs wrap tool inputs)
        raw_input = findings_json.strip()
        if raw_input.startswith("```json"):
            raw_input = raw_input.split("```json")[1].split("```")[0].strip()
        elif raw_input.startswith("```"):
            raw_input = raw_input.split("```")[1].split("```")[0].strip()
            
        try:
            data = json.loads(raw_input)
            # Handle both Single Dict results and List results
            items = data if isinstance(data, list) else [data]
            
            for item in items:
                # Handle nested containers (like 'findings': [...])
                if isinstance(item, dict) and "findings" in item:
                    item_list = item["findings"] if isinstance(item["findings"], list) else [item["findings"]]
                    for sub_item in item_list:
                        try:
                            all_findings.append(ReviewFinding(**sub_item))
                        except:
                            continue
                    continue

                try:
                    all_findings.append(ReviewFinding(**item))
                except:
                    # Try to map common aliases
                    mapped = {
                        "severity": item.get("severity", item.get("finding_type", "MEDIUM")),
                        "agent_name": item.get("agent_name", "lead_engineer"),
                        "file_path": item.get("file_path", "config.py"),
                        "line_number": int(item.get("line_number", 1)) if item.get("line_number") else 1,
                        "category": item.get("category", "performance"),
                        "issue_description": item.get("issue_description", item.get("message", "No description")),
                        "fix_suggestion": item.get("fix_suggestion", "Please review this code block."),
                        "code_block": item.get("code_block")
                    }
                    try:
                        all_findings.append(ReviewFinding(**mapped))
                    except:
                        continue
        except Exception as e:
            logger.error("aggregator_json_failed", error=str(e), raw=raw_input[:100])
            
        aggregated = aggregator.aggregate(all_findings)
        return json.dumps([f.model_dump() for f in aggregated])
