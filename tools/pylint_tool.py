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

class PylintTool:
    """Wrapper around Pylint for static analysis."""
    
    def analyze(self, code: str, filename: str) -> List[ReviewFinding]:
        """
        Run pylint on code string.
        
        Args:
            code: Python source code
            filename: Virtual filename for reporting
            
        Returns:
            List of ReviewFinding objects
        """
        if not code.strip():
            return []
            
        findings = []
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(code)
            tmp_path = tmp.name
            
        try:
            # Run pylint
            # --output-format=json: structured output
            # --score=no: don't print score report
            result = subprocess.run(
                ["pylint", "--output-format=json", "--score=no", tmp_path],
                capture_output=True,
                text=True,
                timeout=5  # 5s timeout
            )
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    
                    for item in data[:10]: # Limit 10 findings
                        # Map Pylint ID to Severity/Category
                        msg_id = item.get("message-id", "")
                        severity = "LOW"
                        category = "style"
                        
                        if msg_id.startswith("E") or msg_id.startswith("F"):
                            severity = "HIGH"
                            category = "correctness"
                        elif msg_id.startswith("W"):
                            severity = "MEDIUM"
                            category = "correctness"
                        elif msg_id == "R0903": # Too few public methods
                            severity = "LOW"
                            category = "design"
                        elif msg_id == "C0415": # Import outside toplevel
                            severity = "MEDIUM"
                            category = "style"
                        elif msg_id.startswith("C"): # Convention (style)
                            severity = "LOW"
                            category = "style"
                        elif msg_id.startswith("R"): # Refactor (design)
                            severity = "LOW"
                            category = "design"
                        
                        findings.append(ReviewFinding(
                            severity=severity,
                            agent_name="quality",
                            file_path=filename,
                            line_number=item.get("line"),
                            code_block=None, # Pylint doesn't give code snippet easily
                            issue_description=f"{msg_id}: {item.get('message')}",
                            fix_suggestion=None,
                            category=category
                        ))
                except json.JSONDecodeError:
                    logger.warning("pylint_json_error", output=result.stdout)
                    
            logger.info("pylint_scan_complete", filename=filename, count=len(findings))
            return findings
            
        except subprocess.TimeoutExpired:
            logger.error("pylint_timeout", filename=filename)
            return []
        except Exception as e:
            logger.error("pylint_error", filename=filename, error=str(e))
            return []
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
