"""
PRFetcher - Extract complete PR data for CrewAI analysis

Fetches PR metadata, changed files, and unified diffs from GitHub API.
Compatible with Phase 3 DiffParser.
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field
from github.PullRequest import PullRequest
from .client import GitHubClient

import logging
import sys

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Check if handler already exists to avoid duplicates
if not logger.handlers:
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # File handler
    file_handler = logging.FileHandler('logs/pr_fetcher.log', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    # Stream handler (optional, but good for immediate feedback if needed, 
    # currently relying on file to keep console clean for the main app)
    # stream_handler = logging.StreamHandler(sys.stdout)
    # logger.addHandler(stream_handler)


class FileChange(BaseModel):
    """Represents a single file changed in a PR."""
    filename: str = Field(description="Path to the file")
    patch: str = Field(description="Unified diff patch for this file")
    language: str = Field(description="Programming language (py, js, java, etc.)")
    additions: int = Field(description="Number of lines added")
    deletions: int = Field(description="Number of lines deleted")
    status: str = Field(description="Change status (added, modified, removed, renamed)")


class PRData(BaseModel):
    """Complete PR data for review analysis."""
    repo_name: str = Field(description="Full repository name (owner/repo)")
    pr_number: int = Field(description="Pull request number")
    pr_url: str = Field(description="GitHub PR URL")
    title: str = Field(description="PR title")
    author: str = Field(description="PR author username")
    files_changed: List[FileChange] = Field(description="List of changed files with diffs")
    full_diff: str = Field(description="Complete unified diff for all files")


class PRFetcher:
    """Fetch and structure PR data from GitHub API."""
    
    def __init__(self, client: Optional[GitHubClient] = None):
        """
        Initialize PR fetcher.
        
        Args:
            client: GitHubClient instance. If None, creates new client.
        """
        self.client = client or GitHubClient()
    
    def _detect_language(self, filename: str) -> str:
        """
        Detect programming language from file extension.
        
        Args:
            filename: File path
            
        Returns:
            Language identifier (py, js, java, etc.) or 'unknown'
        """
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.cs': 'csharp',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.sh': 'bash',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.md': 'markdown',
        }
        
        # Get file extension
        ext = os.path.splitext(filename)[1].lower()
        return extension_map.get(ext, 'unknown')
    
    def _is_binary_file(self, filename: str) -> bool:
        """
        Check if file is binary (should be skipped).
        
        Args:
            filename: File path
            
        Returns:
            True if binary file
        """
        binary_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
            '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z',
            '.exe', '.dll', '.so', '.dylib',
            '.pyc', '.pyo', '.class', '.jar',
            '.woff', '.woff2', '.ttf', '.eot',
            '.mp3', '.mp4', '.avi', '.mov', '.wav',
        }
        
        ext = os.path.splitext(filename)[1].lower()
        return ext in binary_extensions
    
        return False

    def _should_skip_file(self, file_change, max_lines: int = 50000) -> bool:
        """
        Determine if file should be skipped.
        
        Args:
            file_change: GitHub file object
            max_lines: Maximum lines to process
            
        Returns:
            True if file should be skipped
        """
        filename = file_change.filename
        
        # Skip binary files
        if self._is_binary_file(filename):
            logger.info(f"Skipping {filename}: Identified as binary file.")
            return True
        
        # Skip files without patches (e.g., binary files)
        if not hasattr(file_change, 'patch') or not file_change.patch:
            logger.warning(f"Skipping {filename}: No patch data available (possibly binary or LFS).")
            return True
        
        # Skip very large files
        if file_change.changes > max_lines:
            logger.warning(f"Skipping {filename}: too large ({file_change.changes} lines)")
            print(f"Skipping {filename}: too large ({file_change.changes} lines)")
            return True
        
        return False
    
    async def get_full_pr_data(self, repo_full_name: str, pr_number: int) -> PRData:
        """
        Fetch complete PR data for analysis.
        
        Args:
            repo_full_name: Full repo name (owner/repo)
            pr_number: PR number
            
        Returns:
            PRData with all files and diffs
            
        Example:
            >>> fetcher = PRFetcher()
            >>> pr_data = await fetcher.get_full_pr_data("octocat/Hello-World", 1)
            >>> print(f"PR: {pr_data.title}")
            >>> print(f"Files changed: {len(pr_data.files_changed)}")
        """
        # Parse repo name
        parts = repo_full_name.split('/')
        if len(parts) != 2:
            raise ValueError(f"Invalid repo name: {repo_full_name}. Expected format: owner/repo")
        
        owner, repo = parts
        
        # Get PR object
        try:
            pr: PullRequest = self.client.get_pr(owner, repo, pr_number)
        except Exception as e:
            logger.error(f"Failed to fetch PR {repo_full_name}#{pr_number}: {e}")
            raise

        # Extract metadata
        pr_url = pr.html_url
        title = pr.title
        author = pr.user.login
        
        logger.info(f"Fetching PR: {title} by {author} ({pr_url})")

        # Fetch all changed files
        files_changed: List[FileChange] = []
        full_diff_parts: List[str] = []
        
        files = list(pr.get_files())
        logger.info(f"Total files found in PR: {len(files)}")

        for file in files:
            logger.info(f"Processing file: {file.filename} (Status: {file.status}, Additions: {file.additions}, Deletions: {file.deletions})")
            
            # Skip binary/large files
            if self._should_skip_file(file):
                continue
            
            # Detect language
            language = self._detect_language(file.filename)
            
            # Create FileChange object
            file_change = FileChange(
                filename=file.filename,
                patch=file.patch or "",
                language=language,
                additions=file.additions,
                deletions=file.deletions,
                status=file.status
            )
            
            files_changed.append(file_change)
            
            # Add to full diff
            full_diff_parts.append(f"diff --git a/{file.filename} b/{file.filename}")
            full_diff_parts.append(f"--- a/{file.filename}")
            full_diff_parts.append(f"+++ b/{file.filename}")
            full_diff_parts.append(file.patch or "")
            full_diff_parts.append("")  # Empty line between files
        
        logger.info(f"Successfully processed {len(files_changed)}/{len(files)} files.")

        # Combine full diff
        full_diff = "\n".join(full_diff_parts)
        
        # Create PRData
        pr_data = PRData(
            repo_name=repo_full_name,
            pr_number=pr_number,
            pr_url=pr_url,
            title=title,
            author=author,
            files_changed=files_changed,
            full_diff=full_diff
        )
        
        return pr_data
