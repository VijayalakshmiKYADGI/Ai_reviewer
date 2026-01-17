"""
Installation Management

Manages GitHub App installations and repository access.
"""

from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger()


class InstallationManager:
    """
    Manage GitHub App installations.
    
    Handles installation ID lookups and repository access management.
    """
    
    def __init__(self):
        """Initialize installation manager with caching."""
        # In-memory cache: repo_full_name -> installation_id
        self._installation_cache: Dict[str, int] = {}
        
        # Reverse cache: installation_id -> list[repo_full_name]
        self._repos_cache: Dict[int, List[str]] = {}
    
    async def get_installation_id(self, repo_full_name: str) -> Optional[int]:
        """
        Get installation ID for a repository.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            
        Returns:
            Installation ID or None if not found
            
        Example:
            >>> manager = InstallationManager()
            >>> installation_id = await manager.get_installation_id("octocat/Hello-World")
            >>> print(installation_id)
            123456
        """
        # Check cache first
        if repo_full_name in self._installation_cache:
            logger.debug(
                "installation_id_cached",
                repo=repo_full_name,
                installation_id=self._installation_cache[repo_full_name]
            )
            return self._installation_cache[repo_full_name]
        
        # For Phase 10, we use a single installation ID from config
        # Phase 11+ will implement multi-installation support via GitHub API
        from config.app_config import GitHubAppConfig
        
        try:
            config = GitHubAppConfig.from_env()
            if config.installation_id:
                # Cache the mapping
                self._cache_installation(repo_full_name, config.installation_id)
                return config.installation_id
        except Exception as e:
            logger.warning(
                "installation_id_lookup_failed",
                repo=repo_full_name,
                error=str(e)
            )
        
        return None
    
    async def list_repos(self, installation_id: int) -> List[str]:
        """
        List repositories accessible by an installation.
        
        Args:
            installation_id: GitHub App installation ID
            
        Returns:
            List of repository full names
            
        Example:
            >>> manager = InstallationManager()
            >>> repos = await manager.list_repos(123456)
            >>> print(repos)
            ['octocat/Hello-World', 'octocat/Spoon-Knife']
        """
        # Check cache first
        if installation_id in self._repos_cache:
            logger.debug(
                "repos_cached",
                installation_id=installation_id,
                count=len(self._repos_cache[installation_id])
            )
            return self._repos_cache[installation_id]
        
        # For Phase 10, return empty list
        # Phase 11+ will implement via GitHub API
        logger.info(
            "list_repos_not_implemented",
            installation_id=installation_id,
            note="Phase 11 will implement via GitHub API"
        )
        
        return []
    
    def _cache_installation(self, repo_full_name: str, installation_id: int):
        """
        Cache installation ID for a repository.
        
        Args:
            repo_full_name: Full repository name
            installation_id: Installation ID
        """
        self._installation_cache[repo_full_name] = installation_id
        
        # Update reverse cache
        if installation_id not in self._repos_cache:
            self._repos_cache[installation_id] = []
        
        if repo_full_name not in self._repos_cache[installation_id]:
            self._repos_cache[installation_id].append(repo_full_name)
        
        logger.debug(
            "installation_cached",
            repo=repo_full_name,
            installation_id=installation_id
        )
    
    def clear_cache(self):
        """Clear all caches."""
        self._installation_cache.clear()
        self._repos_cache.clear()
        logger.info("installation_cache_cleared")
