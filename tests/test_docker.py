"""
Docker Configuration Tests

Verifies:
- Dockerfile syntax and structure
- Docker Compose configuration validity
- Security best practices (non-root user)
- Healthcheck configuration
"""

import pytest
import os
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def test_dockerfile_syntax():
    """Verify Dockerfile exists and contains key instructions."""
    dockerfile_path = PROJECT_ROOT / "Dockerfile"
    assert dockerfile_path.exists()
    
    with open(dockerfile_path, "r") as f:
        content = f.read()
        
    # Check multi-stage build
    assert "FROM python:3.12-slim AS builder" in content
    assert "FROM python:3.12-slim" in content
    assert "COPY --from=builder" in content
    
    # Check requirements
    assert "COPY requirements.txt ." in content
    assert "RUN pip install" in content
    
    # Check workdir
    assert "WORKDIR /app" in content


def test_docker_compose_valid():
    """Verify docker-compose files are valid YAML."""
    compose_files = [
        PROJECT_ROOT / "docker-compose.yml",
        PROJECT_ROOT / "deploy/docker-compose.prod.yml"
    ]
    
    for compose_file in compose_files:
        assert compose_file.exists()
        with open(compose_file, "r") as f:
            content = yaml.safe_load(f)
            
        assert "services" in content
        assert "api" in content["services"]
        assert "redis" in content["services"]


def test_non_root_user():
    """Verify Dockerfile uses a non-root user."""
    dockerfile_path = PROJECT_ROOT / "Dockerfile"
    with open(dockerfile_path, "r") as f:
        content = f.read()
        
    assert "useradd -m crewai" in content
    assert "USER crewai" in content


def test_healthcheck_configured():
    """Verify Dockerfile has HEALTHCHECK instruction."""
    dockerfile_path = PROJECT_ROOT / "Dockerfile"
    with open(dockerfile_path, "r") as f:
        content = f.read()
        
    assert "HEALTHCHECK" in content
    assert "--interval=30s" in content
    assert "curl -f http://localhost:8000/health" in content


def test_port_exposed():
    """Verify Dockerfile exposes port 8000."""
    dockerfile_path = PROJECT_ROOT / "Dockerfile"
    with open(dockerfile_path, "r") as f:
        content = f.read()
        
    assert "EXPOSE 8000" in content


def test_render_yaml_valid():
    """Verify Render deployment config is valid."""
    render_file = PROJECT_ROOT / "deploy/render.yaml"
    assert render_file.exists()
    
    with open(render_file, "r") as f:
        content = yaml.safe_load(f)
        
    assert "services" in content
    service = content["services"][0]
    assert service["name"] == "code-review-crew"
    assert service["env"] == "python"
    assert "buildCommand" in service
    assert "startCommand" in service


def test_dockerignore_configured():
    """Verify .dockerignore excludes critical files."""
    dockerignore_path = PROJECT_ROOT / ".dockerignore"
    assert dockerignore_path.exists()
    
    with open(dockerignore_path, "r") as f:
        content = f.read()
        
    assert ".env" in content
    assert ".git" in content
    assert "env/" in content
    assert "venv/" in content
    assert "github_private_key.pem" in content


def test_entrypoint_exists():
    """Verify entrypoint script exists and is executable (conceptually)."""
    entrypoint_path = PROJECT_ROOT / "docker/entrypoint.sh"
    assert entrypoint_path.exists()
    
    with open(entrypoint_path, "r") as f:
        content = f.read()
        
    assert "#!/bin/bash" in content
    assert "uvicorn api.main:app" in content
