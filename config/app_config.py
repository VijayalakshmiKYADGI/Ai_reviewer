"""
GitHub App Configuration

Manages GitHub App settings and environment variable loading.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class GitHubAppConfig:
    """GitHub App configuration."""
    
    app_id: int
    private_key_path: str
    webhook_secret: str
    installation_id: Optional[int] = None
    webhook_url: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "GitHubAppConfig":
        """
        Load GitHub App configuration from environment variables.
        
        Returns:
            GitHubAppConfig instance
            
        Raises:
            ValueError: If required environment variables are missing
            
        Example:
            >>> config = GitHubAppConfig.from_env()
            >>> print(config.app_id)
            123456
        """
        app_id_str = os.getenv("GITHUB_APP_ID")
        if not app_id_str:
            raise ValueError("GITHUB_APP_ID environment variable not set")
        
        try:
            app_id = int(app_id_str)
        except ValueError:
            raise ValueError(f"Invalid GITHUB_APP_ID: {app_id_str}")
        
        private_key_path = os.getenv(
            "GITHUB_PRIVATE_KEY_PATH",
            "./github_private_key.pem"
        )
        
        webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
        
        # Optional installation ID
        installation_id_str = os.getenv("GITHUB_INSTALLATION_ID")
        installation_id = None
        if installation_id_str:
            try:
                # Handle URL format: https://github.com/settings/installations/104539256
                if "installations/" in installation_id_str:
                    installation_id = int(installation_id_str.split("/")[-1])
                else:
                    installation_id = int(installation_id_str)
            except ValueError:
                pass  # Leave as None if invalid
        
        webhook_url = os.getenv("GITHUB_WEBHOOK_URL")
        
        return cls(
            app_id=app_id,
            private_key_path=private_key_path,
            webhook_secret=webhook_secret,
            installation_id=installation_id,
            webhook_url=webhook_url
        )
    
    def validate(self) -> bool:
        """
        Validate configuration completeness.
        
        Returns:
            True if configuration is valid
        """
        if not self.app_id:
            return False
        
        if not self.private_key_path:
            return False
        
        # Check if private key file exists
        if not os.path.exists(self.private_key_path):
            return False
        
        return True
    
    def is_complete(self) -> bool:
        """
        Check if all optional fields are set.
        
        Returns:
            True if all fields are set
        """
        return all([
            self.app_id,
            self.private_key_path,
            self.webhook_secret,
            self.installation_id,
            self.webhook_url
        ])


# Phase 15: Production Configuration
ENABLE_CREWAI_PIPELINE = os.getenv("ENABLE_CREWAI_PIPELINE", "true").lower() == "true"
MAX_FINDINGS_PER_PR = int(os.getenv("MAX_FINDINGS_PER_PR", "20"))
