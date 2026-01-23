"""
Bandit wrapper for security vulnerability scanning.
Detects hardcoded secrets, injection flaws, and unsafe practices.
"""

import json
import subprocess
import tempfile
import os
from typing import List
import structlog

from data.models import ReviewFinding

logger = structlog.get_logger()

from crewai.tools import BaseTool

class BanditTool(BaseTool):
    name: str = "Bandit Security Scan"
    description: str = "Run Bandit security scan on python code. Input: python code string."

    def _run(self, code: str) -> str:
        """
        Run bandit on code string.
        returns: JSON string of findings
        """
        filename = "analyzed_file.py"
        if not code.strip():
            return "[]"
            
        findings = []
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(code)
            tmp_path = tmp.name
            
        try:
            # Run bandit
            result = subprocess.run(
                ["bandit", "-f", "json", "-q", tmp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    results = data.get("results", [])
                    
                    for item in results[:10]: # Limit 10 findings
                        # Map Bandit severity
                        severity_map = {
                            "HIGH": "CRITICAL",
                            "MEDIUM": "HIGH",
                            "LOW": "MEDIUM"
                        }
                        
                        severity = severity_map.get(item.get("issue_severity"), "MEDIUM")
                        
                        findings.append(ReviewFinding(
                            severity=severity,
                            agent_name="security",
                            file_path=filename,
                            line_number=item.get("line_number"),
                            code_block=item.get("code"),
                            issue_description=f"{item.get('test_id')}: {item.get('issue_text')}",
                            fix_suggestion=f"See: {item.get('more_info')}",
                            category="security"
                        ))
                except json.JSONDecodeError:
                    logger.warning("bandit_json_error", output=result.stdout)
                    
            logger.info("bandit_scan_complete", filename=filename, count=len(findings))
            return str([f.model_dump() for f in findings])
            
        except subprocess.TimeoutExpired:
            logger.error("bandit_timeout", filename=filename)
            return "[]"
        except Exception as e:
            logger.error("bandit_error", filename=filename, error=str(e))
            return "[]"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
