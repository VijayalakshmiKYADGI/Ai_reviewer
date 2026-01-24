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
