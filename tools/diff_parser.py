"""
Parser for GitHub PR unified diffs.
Extracts changed files and code hunks.
"""

from dataclasses import dataclass, field
import re
from typing import List, Optional
import structlog
from crewai.agent import BaseTool
import json

logger = structlog.get_logger()

@dataclass
class ChangedFile:
    filename: str
    hunks: List[str] = field(default_factory=list)
    added_lines: List[int] = field(default_factory=list)
    removed_lines: List[int] = field(default_factory=list)
    language: str = "python"
    
    @property
    def full_content(self) -> str:
        """Combine hunks into rough content representation."""
        return "\n".join(self.hunks)

class DiffParser:
    """Parses unified diff format strings."""
    
    def parse_diff(self, diff_content: str) -> List[ChangedFile]:
        """
        Parse a unified diff string into ChangedFile objects.
        
        Args:
            diff_content: String containing unified diff
            
        Returns:
            List of ChangedFile objects
        """
        if not diff_content.strip():
            return []
            
        files = []
        current_file = None
        current_hunk = []
        
        # Regex for diff header
        # diff --git a/path/to/file b/path/to/file
        file_header_re = re.compile(r'^diff --git a/(.*) b/(.*)')
        
        lines = diff_content.splitlines()
        
        for line in lines:
            # Check for new file header
            header_match = file_header_re.match(line)
            if header_match:
                # Save previous file if exists
                if current_file:
                    if current_hunk:
                        current_file.hunks.append("\n".join(current_hunk))
                    files.append(current_file)
                
                # Start new file
                filename = header_match.group(2) # Get 'b' path (new version)
                current_file = ChangedFile(
                    filename=filename,
                    language=self._detect_language(filename)
                )
                current_hunk = []
                continue
                
            # Skip file metadata lines
            if line.startswith('index') or line.startswith('new file') or \
               line.startswith('deleted file') or line.startswith('---') or \
               line.startswith('+++'):
                continue
                
            # Check for binary files
            if line.startswith('Binary files'):
                current_file = None
                continue
                
            if current_file:
                # Store content in current hunk
                current_hunk.append(line)
                
                # Track changed lines (approximate)
                if line.startswith('+') and not line.startswith('+++'):
                    # We'd need hunk header parsing @@ -x,y +a,b @@ for exact line numbers
                    # For now just storing content is sufficient for analysis
                    pass
        
        # Save last file
        if current_file:
            if current_hunk:
                current_file.hunks.append("\n".join(current_hunk))
            files.append(current_file)
            
        # Filter deleted files (no hunks) or non-text files
        valid_files = [f for f in files if f.hunks]
        
        logger.info("diff_parsed", file_count=len(valid_files))
        return valid_files

    def _detect_language(self, filename: str) -> str:
        """Simple extension-based language detection."""
        if filename.endswith('.py'):
            return "python"
        elif filename.endswith('.js') or filename.endswith('.ts'):
            return "javascript"
        elif filename.endswith('.md'):
            return "markdown"
        return "unknown"
    
    def get_changed_lines(self, diff_content: str, target_file: str) -> set[int]:
        """
        Extract line numbers that were added or modified in the diff for a specific file.
        
        Args:
            diff_content: The full diff content
            target_file: The file path to extract changed lines for
            
        Returns:
            Set of line numbers (in the NEW version of the file) that were added/modified
        """
        changed_lines = set()
        in_target_file = False
        current_new_line = 0
        
        lines = diff_content.splitlines()
        
        for line in lines:
            # Check if we're entering the target file's diff
            if line.startswith('diff --git') and target_file in line:
                in_target_file = True
                current_new_line = 0
                continue
            
            # Check if we're leaving the target file (entering another file)
            if in_target_file and line.startswith('diff --git') and target_file not in line:
                in_target_file = False
                continue
            
            if not in_target_file:
                continue
            
            # Parse hunk header to get starting line number
            # Format: @@ -old_start,old_count +new_start,new_count @@
            if line.startswith('@@'):
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_new_line = int(match.group(1))
                continue
            
            # Skip metadata lines
            if line.startswith('---') or line.startswith('+++') or \
               line.startswith('index') or line.startswith('new file') or \
               line.startswith('deleted file'):
                continue
            
            # Track added/modified lines (lines starting with +)
            if line.startswith('+') and current_new_line > 0:
                changed_lines.add(current_new_line)
                current_new_line += 1
            # Context lines and removed lines also increment the line counter
            elif line.startswith(' ') and current_new_line > 0:
                current_new_line += 1
            # Removed lines don't increment new line counter
            elif line.startswith('-'):
                pass
        
        logger.info("changed_lines_extracted", file=target_file, count=len(changed_lines))
        return changed_lines

class DiffParsingTool(BaseTool):
    name: str = "Diff Parsing"
    description: str = "Parse PR diff to basic file stats. Input is diff string."

    def _run(self, diff: str) -> str:
        parser = DiffParser()
        files = parser.parse_diff(diff)
        # Convert to serializable dicts
        result = []
        for f in files:
            result.append({
                "filename": f.filename,
                "language": f.language,
                "hunks_count": len(f.hunks),
                "full_content": f.full_content
            })
        return json.dumps(result)
