"""
GitHub App Authentication

Implements JWT-based authentication for GitHub Apps with installation token management.
Provides production-ready authentication with enhanced rate limits and security.
"""

import os
import time
import jwt
from datetime import datetime, timedelta
from typing import Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import httpx
import structlog

logger = structlog.get_logger()


class GitHubAppAuth:
    """
    GitHub App authentication with JWT and installation tokens.
    
    Generates RS256-signed JWTs and exchanges them for installation tokens.
    """
    
    def __init__(self, app_id: int, private_key_path: str):
        """
        Initialize GitHub App authentication.
        
        Args:
            app_id: GitHub App ID
            private_key_path: Path to PEM private key file
        """
        self.app_id = app_id
        self.private_key_path = private_key_path
        self.private_key = self._load_private_key()
        
        # HTTP client for installation token requests
        self.http_client = httpx.AsyncClient(
            headers={"Accept": "application/vnd.github+json"},
            timeout=30.0
        )
    
    def _load_private_key(self):
        """
        Load RSA private key from PEM file.
        
        Returns:
            RSA private key object
            
        Raises:
            FileNotFoundError: If private key file not found
            ValueError: If private key format is invalid
        """
        try:
            with open(self.private_key_path, 'rb') as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
            
            logger.info(
                "private_key_loaded",
                path=self.private_key_path
            )
            
            return private_key
        
        except FileNotFoundError:
            logger.error(
                "private_key_not_found",
                path=self.private_key_path
            )
            raise FileNotFoundError(
                f"GitHub App private key not found: {self.private_key_path}"
            )
        
        except Exception as e:
            logger.error(
                "private_key_load_failed",
                path=self.private_key_path,
                error=str(e)
            )
            raise ValueError(f"Failed to load private key: {e}")
    
    def generate_jwt(self) -> str:
        """
        Generate JWT for GitHub App authentication.
        
        JWT is valid for 10 minutes (GitHub requirement).
        
        Returns:
            RS256-signed JWT token
            
        Example:
            >>> auth = GitHubAppAuth(123456, "./private_key.pem")
            >>> jwt_token = auth.generate_jwt()
            >>> print(jwt_token[:20])
            eyJhbGciOiJSUzI1NiI...
        """
        # Current time
        now = int(time.time())
        
        # JWT payload (claims)
        payload = {
            "iat": now,  # Issued at
            "exp": now + (10 * 60),  # Expires in 10 minutes
            "iss": self.app_id  # Issuer (App ID)
        }
        
        # Sign with RS256
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm="RS256"
        )
        
        logger.debug(
            "jwt_generated",
            app_id=self.app_id,
            expires_at=datetime.fromtimestamp(payload["exp"]).isoformat()
        )
        
        return token
    
    async def get_installation_token(self, installation_id: int) -> str:
        """
        Exchange JWT for installation access token.
        
        Installation tokens are valid for 1 hour and provide
        repository-specific access.
        
        Args:
            installation_id: GitHub App installation ID
            
        Returns:
            Installation access token
            
        Raises:
            Exception: If token exchange fails
            
        Example:
            >>> auth = GitHubAppAuth(123456, "./private_key.pem")
            >>> token = await auth.get_installation_token(789012)
            >>> print(token[:20])
            ghs_abc123def456...
        """
        # Generate JWT
        jwt_token = self.generate_jwt()
        
        # Request installation token
        url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json"
        }
        
        try:
            response = await self.http_client.post(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            token = data.get("token", "")
            expires_at = data.get("expires_at", "")
            
            logger.info(
                "installation_token_obtained",
                installation_id=installation_id,
                expires_at=expires_at
            )
            
            return token
        
        except httpx.HTTPStatusError as e:
            logger.error(
                "installation_token_failed",
                installation_id=installation_id,
                status=e.response.status_code,
                error=e.response.text
            )
            raise Exception(f"Failed to get installation token: {e.response.status_code}")
        
        except Exception as e:
            logger.error(
                "installation_token_error",
                installation_id=installation_id,
                error=str(e)
            )
            raise
    
    async def close(self):
        """Close HTTP client."""
        if hasattr(self, 'http_client') and self.http_client:
            await self.http_client.aclose()
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                if hasattr(self, 'http_client'): # Check existence
                    loop.create_task(self.close())
        except:
            pass
