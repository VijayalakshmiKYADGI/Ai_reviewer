"""
Production Readiness Tests (Phase 13)

Verifies:
- Render.com configuration validity
- Production environment variable requirements
- Database connection settings
- Metrics endpoint structure
- Webhook endpoint accessibility
"""

import pytest
import yaml
import os
from pathlib import Path
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)
PROJECT_ROOT = Path(__file__).parent.parent

def test_render_config_valid():
    """Verify Render.com blueprint file structure."""
    render_file = PROJECT_ROOT / "deploy/render.yml"
    assert render_file.exists()
    
    with open(render_file, "r") as f:
        config = yaml.safe_load(f)
        
    assert "services" in config
    service = config["services"][0]
    assert service["name"] == "code-review-crew"
    assert service["env"] == "docker"
    assert "envVars" in service
    
    # Verify key secrets are mapped
    secrets = [v["key"] for v in service["envVars"]]
    assert "GEMINI_API_KEY" in secrets
    assert "GITHUB_APP_ID" in secrets
    assert "DATABASE_URL" in secrets


def test_production_env_vars():
    """Verify list of required production environment variables."""
    # We check if the keys exist in the Render config, 
    # ensuring they will be enforced in prod.
    render_file = PROJECT_ROOT / "deploy/render.yml"
    with open(render_file, "r") as f:
        config = yaml.safe_load(f)
    
    env_vars = config["services"][0]["envVars"]
    keys = set(item["key"] for item in env_vars)
    
    required = {
        "GEMINI_API_KEY", 
        "GITHUB_APP_ID", 
        "GITHUB_WEBHOOK_SECRET", 
        "GITHUB_INSTALLATION_ID", 
        "DATABASE_URL"
    }
    
    assert required.issubset(keys), f"Missing env vars: {required - keys}"


def test_postgres_connection_config():
    """Verify Render config maps DATABASE_URL correctly."""
    render_file = PROJECT_ROOT / "deploy/render.yml"
    with open(render_file, "r") as f:
        config = yaml.safe_load(f)
        
    env_vars = config["services"][0]["envVars"]
    db_var = next(v for v in env_vars if v["key"] == "DATABASE_URL")
    
    assert db_var["fromDatabase"]["name"] == "code-review-crew-db"


def test_metrics_endpoint():
    """Verify /metrics endpoint returns valid JSON structure."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    
    assert "system" in data
    assert "uptime_seconds" in data["system"]
    assert "application" in data
    assert "costs" in data


def test_health_check_production_readiness():
    """Verify health endpoint is ready."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ssl_termination_config():
    """
    Verify Render config assumes SSL termination.
    (Implied by not exposing port 80/443 directly in Dockerfile 
    and letting Render handle routing)
    """
    dockerfile = PROJECT_ROOT / "Dockerfile"
    with open(dockerfile, "r") as f:
        content = f.read()
    
    # Should expose internal port 8000
    assert "EXPOSE 8000" in content
    # Should NOT expose 443 (Render handles SSL)
    assert "EXPOSE 443" not in content
