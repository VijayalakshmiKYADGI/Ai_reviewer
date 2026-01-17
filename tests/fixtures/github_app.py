"""
Mock GitHub App Data for Testing

Provides mock App IDs, tokens, and authentication for testing without real GitHub App.
"""

from typing import Optional
import time


# Mock GitHub App credentials
MOCK_APP_ID = 123456
MOCK_INSTALLATION_ID = 789012
MOCK_PRIVATE_KEY_PATH = "./tests/fixtures/mock_private_key.pem"

# Mock tokens
MOCK_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE2MDk0NTkyMDAsImV4cCI6MTYwOTQ1OTgwMCwiaXNzIjoxMjM0NTZ9.mock_signature"
MOCK_INSTALLATION_TOKEN = "ghs_mock_installation_token_1234567890abcdef"

# Dynamic Mock Private Key Generation
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def _generate_mock_key():
    """Generate a valid RSA private key for testing."""
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

# Generate on module load
MOCK_PRIVATE_KEY_PEM = _generate_mock_key()



class MockAppAuth:
    """Mock GitHub App authentication for testing."""
    
    def __init__(self, app_id: int = MOCK_APP_ID, private_key_path: str = MOCK_PRIVATE_KEY_PATH):
        """Initialize mock app auth."""
        self.app_id = app_id
        self.private_key_path = private_key_path
    
    def generate_jwt(self) -> str:
        """Generate mock JWT token."""
        return MOCK_JWT_TOKEN
    
    async def get_installation_token(self, installation_id: int) -> str:
        """Get mock installation token."""
        return MOCK_INSTALLATION_TOKEN
    
    async def close(self):
        """Mock close method."""
        pass


def create_mock_private_key_file(path: str = MOCK_PRIVATE_KEY_PATH):
    """
    Create mock private key file for testing.
    
    Args:
        path: Path to create mock key file
    """
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, 'w') as f:
        f.write(MOCK_PRIVATE_KEY_PEM)


def cleanup_mock_private_key_file(path: str = MOCK_PRIVATE_KEY_PATH):
    """
    Remove mock private key file.
    
    Args:
        path: Path to mock key file
    """
    import os
    if os.path.exists(path):
        os.remove(path)
