"""
Pylint wrapper for static code analysis.
Detects style issues, bugs, and quality problems.
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

class PylintTool(BaseTool):
    name: str = "Pylint Analysis"
    description: str = "Run Pylint on python code to find style issues and errors. Input should be the python code string."

    def _run(self, code: str) -> str:
        """
        Run pylint on code string.
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
            # Run pylint
            result = subprocess.run(
                ["pylint", "--output-format=json", "--score=no", tmp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    
                    for item in data[:10]: # Limit 10 findings
                        msg_id = item.get("message-id", "")
                        severity = "LOW"
                        category = "style"
                        
                        if msg_id.startswith("E") or msg_id.startswith("F"):
                            severity = "HIGH"
                            category = "correctness"
                        elif msg_id.startswith("W"):
                            severity = "MEDIUM"
                            category = "correctness"
                        elif msg_id == "R0903": 
                            severity = "LOW"
                            category = "design"
                        elif msg_id == "C0415":
                            severity = "MEDIUM"
                            category = "style"
                        elif msg_id.startswith("C"):
                            severity = "LOW"
                            category = "style"
                        elif msg_id.startswith("R"):
                            severity = "LOW"
                            category = "design"
                        
                        findings.append(ReviewFinding(
                            severity=severity,
                            agent_name="quality",
                            file_path=filename,
                            line_number=item.get("line"),
                            code_block=None, 
                            issue_description=f"{msg_id}: {item.get('message')}",
                            fix_suggestion=None,
                            category=category
                        ))
                except json.JSONDecodeError:
                    logger.warning("pylint_json_error", output=result.stdout)
                    
            logger.info("pylint_scan_complete", filename=filename, count=len(findings))
            return str([f.model_dump() for f in findings])
            
        except subprocess.TimeoutExpired:
            logger.error("pylint_timeout", filename=filename)
            return "[]"
        except Exception as e:
            logger.error("pylint_error", filename=filename, error=str(e))
            return "[]"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
