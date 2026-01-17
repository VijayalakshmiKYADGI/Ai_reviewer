"""
Tests for GitHub App Authentication (Phase 10)

Tests cover:
- JWT generation and signing
- Installation token exchange
- Dual-mode client authentication (App + PAT)
- Fallback mechanisms
- Configuration validation
"""

import pytest
import os
import time
import jwt
from unittest.mock import Mock, patch, AsyncMock
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from github_integration import GitHubAppAuth, GitHubClient, InstallationManager
from config.app_config import GitHubAppConfig
from tests.fixtures.github_app import (
    MockAppAuth,
    create_mock_private_key_file,
    cleanup_mock_private_key_file,
    MOCK_APP_ID,
    MOCK_INSTALLATION_ID,
    MOCK_PRIVATE_KEY_PATH,
    MOCK_JWT_TOKEN,
    MOCK_INSTALLATION_TOKEN
)


@pytest.fixture
def mock_private_key():
    """Create mock private key file for tests."""
    create_mock_private_key_file()
    yield MOCK_PRIVATE_KEY_PATH
    cleanup_mock_private_key_file()


@pytest.fixture
def keys():
    """Generate a real RSA key pair for testing JWT verification."""
    from cryptography.hazmat.primitives.asymmetric import rsa
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    public_key = private_key.public_key()
    
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return pem_private, pem_public


# Test 1: JWT Generation
def test_app_auth_jwt_generation(keys):
    """Test valid RS256 JWT generation."""
    private_pem, public_pem = keys
    
    # Write private key to temp file
    key_path = "temp_test_key.pem"
    with open(key_path, "wb") as f:
        f.write(private_pem)
    
    try:
        app_id = 123456
        auth = GitHubAppAuth(app_id, key_path)
        token = auth.generate_jwt()
        
        # Verify JWT
        decoded = jwt.decode(
            token,
            public_pem,
            algorithms=["RS256"],
            audience=None  # GitHub JWTs don't have audience
        )
        
        assert decoded["iss"] == app_id
        assert "exp" in decoded
        assert "iat" in decoded
        
        # Check expiry (10 mins)
        assert decoded["exp"] - decoded["iat"] == 600
        
    finally:
        if os.path.exists(key_path):
            os.remove(key_path)


# Test 2: Installation Token Exchange
@pytest.mark.asyncio
async def test_app_auth_installation_token(mock_private_key):
    """Test exchange of JWT for installation token."""
    auth = GitHubAppAuth(MOCK_APP_ID, mock_private_key)
    
    # Mock HTTP client response
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "token": "ghs_test_token",
        "expires_at": "2024-01-01T00:00:00Z"
    }
    
    auth.http_client = AsyncMock()
    auth.http_client.post.return_value = mock_response
    
    token = await auth.get_installation_token(MOCK_INSTALLATION_ID)
    
    assert token == "ghs_test_token"
    auth.http_client.post.assert_called_once()
    assert "Authorization" in auth.http_client.post.call_args[1]["headers"]


# Test 3: Client Dual-Mode Authentication
@pytest.mark.asyncio
async def test_client_app_mode(mock_private_key):
    """Test client initialization in 'app' mode."""
    with patch.dict(os.environ, {
        "GITHUB_APP_ID": str(MOCK_APP_ID),
        "GITHUB_PRIVATE_KEY_PATH": mock_private_key,
        "GITHUB_INSTALLATION_ID": str(MOCK_INSTALLATION_ID)
    }):
        # Initialize client in app mode
        client = GitHubClient(auth_mode="app")
        
        assert client.auth_mode == "app"
        assert client.app_auth is not None
        assert client.installation_manager is not None
        
        # Mock getting installation token
        client.installation_manager.get_installation_id = AsyncMock(return_value=MOCK_INSTALLATION_ID)
        client.app_auth.get_installation_token = AsyncMock(return_value="ghs_mock_token")
        
        token = await client.get_access_token("owner/repo")
        assert token == "ghs_mock_token"


# Test 4: Installation ID Extraction
@pytest.mark.asyncio
async def test_installation_id_extraction():
    """Test getting installation ID for a repo."""
    manager = InstallationManager()
    
    # Mock config loading
    with patch("config.app_config.GitHubAppConfig.from_env") as mock_config:
        mock_config.return_value = Mock(installation_id=999)
        
        install_id = await manager.get_installation_id("owner/repo")
        assert install_id == 999
        
        # Verify caching
        assert manager._installation_cache["owner/repo"] == 999
        
        # Second call should use cache (mock config won't be called again if cached logic works)
        # But we want to verify it returns correctly
        install_id_2 = await manager.get_installation_id("owner/repo")
        assert install_id_2 == 999


# Test 5: JWT Expiry
def test_jwt_expiry(mock_private_key):
    """Test that JWT expiry is set correctly."""
    auth = GitHubAppAuth(MOCK_APP_ID, mock_private_key)
    
    # We can peek at generate_jwt implementation via jwt library decoding
    # But since we already tested full generation in test 1, we'll verify logic here
    token = auth.generate_jwt()
    # Decode without verify to check claims
    claims = jwt.decode(token, options={"verify_signature": False})
    
    now = int(time.time())
    assert claims["exp"] > now
    assert claims["exp"] <= now + 600 + 5  # Allow 5s buffer


# Test 6: Private Key Loading
def test_private_key_loading(mock_private_key):
    """Test loading of PEM private key."""
    auth = GitHubAppAuth(MOCK_APP_ID, mock_private_key)
    assert auth.private_key is not None
    
    # Test invalid path
    with pytest.raises(FileNotFoundError):
        GitHubAppAuth(MOCK_APP_ID, "non_existent_key.pem")


# Test 7: Fallback to Token
def test_fallback_to_token():
    """Test fallback to PAT when App auth fails."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_fallback_token"}):
        # Force App auth failure by providing invalid config
        with patch("config.app_config.GitHubAppConfig.from_env", side_effect=Exception("Config failed")):
            client = GitHubClient(auth_mode="app")
            
            # Should have fallen back to token
            assert client.auth_mode == "token"
            assert client.token == "ghp_fallback_token"
            assert client.github is not None


# Test 8: App Permissions (Mocked)
# Testing permissions requires integration test, so we verify config here
def test_app_permissions_config():
    """Test that client configured correctly for app permissions."""
    # This is more of a config check
    config = GitHubAppConfig(
        app_id=123,
        private_key_path="key.pem",
        webhook_secret="secret"
    )
    assert config.app_id == 123


# Test 9: Mock App Integration
@pytest.mark.asyncio
async def test_mock_app_integration():
    """Test MockAppAuth class."""
    mock_auth = MockAppAuth()
    
    jwt_token = mock_auth.generate_jwt()
    assert jwt_token == MOCK_JWT_TOKEN
    
    install_token = await mock_auth.get_installation_token(123)
    assert install_token == MOCK_INSTALLATION_TOKEN


# Test 10: Production Config
def test_production_config():
    """Test loading config from environment."""
    env_vars = {
        "GITHUB_APP_ID": "555",
        "GITHUB_PRIVATE_KEY_PATH": "./prod_key.pem",
        "GITHUB_WEBHOOK_SECRET": "prod_secret",
        "GITHUB_INSTALLATION_ID": "777"
    }
    
    with patch.dict(os.environ, env_vars):
        config = GitHubAppConfig.from_env()
        
        assert config.app_id == 555
        assert config.private_key_path == "./prod_key.pem"
        assert config.webhook_secret == "prod_secret"
        assert config.installation_id == 777
        assert config.validate() is False  # False because key file doesn't exist
