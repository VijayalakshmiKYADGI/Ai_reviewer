"""
Radon wrapper for cyclomatic complexity and maintainability metrics.
"""

import subprocess
import tempfile
import os
import json # Used for error handling logic mainly
from typing import List
import structlog

from data.models import ReviewFinding

logger = structlog.get_logger()

from crewai.tools import BaseTool

class RadonTool(BaseTool):
    name: str = "Radon Complexity Analysis"
    description: str = "Run Radon on python code to measure complexity. Input: python code string."

    def _run(self, code: str) -> str:
        """
        Run radon cc on code.
        returns: JSON string of findings
        """
        filename = "analyzed_file.py"
        if not code.strip():
            return "[]"
            
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(code)
            tmp_path = tmp.name
            
        try:
            # 1. Cyclomatic Complexity (radon cc -j)
            cc_process = subprocess.run(
                ["radon", "cc", "-j", tmp_path],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if cc_process.stdout:
                try:
                    data = json.loads(cc_process.stdout)
                    
                    file_blocks = data.get(tmp_path, [])
                    for block in file_blocks:
                        cc = block.get("complexity", 0)
                        
                        # Thresholds
                        if cc > 15:
                            severity = "HIGH"
                            desc = f"Cyclomatic complexity {cc} (very high) in {block.get('type')} '{block.get('name')}'"
                        elif cc >= 10:
                            severity = "MEDIUM"
                            desc = f"Cyclomatic complexity {cc} (high) in {block.get('type')} '{block.get('name')}'"
                        else:
                            continue 
                            
                        findings.append(ReviewFinding(
                            severity=severity,
                            agent_name="performance",
                            file_path=filename,
                            line_number=block.get("lineno"),
                            code_block=None,
                            issue_description=desc,
                            fix_suggestion="Refactor to reduce complexity (split function/class)",
                            category="performance"
                        ))
                except json.JSONDecodeError:
                    pass

            # 2. Maintainability Index (radon mi -j)
            mi_process = subprocess.run(
                ["radon", "mi", "-j", tmp_path],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if mi_process.stdout:
                try:
                    data = json.loads(mi_process.stdout)
                    metrics = data.get(tmp_path, {})
                    mi = metrics.get("mi", 100)
                    
                    if mi < 30:
                        findings.append(ReviewFinding(
                            severity="HIGH",
                            agent_name="architecture",
                            file_path=filename,
                            line_number=1,
                            code_block=None,
                            issue_description=f"Maintainability Index {mi:.1f} is critically low",
                            fix_suggestion="Refactor entire module to improve maintainability",
                            category="design"
                        ))
                except json.JSONDecodeError:
                    pass
                    
            logger.info("radon_scan_complete", filename=filename, count=len(findings))
            return str([f.model_dump() for f in findings])
            
        except Exception as e:
            logger.error("radon_error", filename=filename, error=str(e))
            return "[]"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
