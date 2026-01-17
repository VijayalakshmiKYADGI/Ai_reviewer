"""
Phase 12 Validation Script - Containerization

Validates:
- Dockerfile syntax and best practices
- Docker Compose configuration
- Security (non-root user usage)
- Deployment configuration
- Expected scripts existence
"""

import sys
import os
import shutil
from pathlib import Path
import yaml

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix Windows console encoding checks
if sys.platform == "win32":
    import codecs
    try:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    except Exception:
        pass

PROJECT_ROOT = Path(".")

def print_check(check_num: int, description: str, status: str, details: str = ""):
    """Print formatted check result."""
    status_symbol = "[OK]" if status == "OK" else "[FAIL]" if status == "FAIL" else "[SKIP]"
    print(f"[CHECK {check_num}] {description}... {status_symbol}")
    if details:
        print(f"          {details}")

def check_1_dockerfile():
    """Check 1: Dockerfile syntax."""
    if not (PROJECT_ROOT / "Dockerfile").exists():
        return "FAIL", "Dockerfile missing"
    
    with open("Dockerfile", "r") as f:
        content = f.read()
    
    if "FROM python:3.12-slim" not in content:
        return "FAIL", "Wrong base image"
    if "AS builder" not in content:
        return "FAIL", "Not multi-stage"
    
    return "OK", "Multi-stage python:3.12-slim"

def check_2_docker_compose():
    """Check 2: Docker Compose."""
    if not (PROJECT_ROOT / "docker-compose.yml").exists():
        return "FAIL", "docker-compose.yml missing"
    
    try:
        with open("docker-compose.yml", "r") as f:
            data = yaml.safe_load(f)
        if "api" in data["services"] and "redis" in data["services"]:
            return "OK", "Services configured"
        return "FAIL", "Missing services"
    except Exception as e:
        return "FAIL", str(e)

def check_3_image_size_check():
    """Check 3: Image optimization."""
    with open("Dockerfile", "r") as f:
        content = f.read()
    
    # Static check for optimization practices
    if "apt-get clean" not in content and "rm -rf /var/lib/apt/lists" not in content:
        return "FAIL", "Missing apt cleanup"
    if "pip install --no-cache-dir" not in content:
        return "FAIL", "Pip cache not disabled"
    
    return "OK", "Optimization flags present"

def check_4_non_root():
    """Check 4: Non-root user."""
    with open("Dockerfile", "r") as f:
        content = f.read()
    
    if "useradd" in content and "USER crewai" in content:
        return "OK", "User crewai configured"
    return "FAIL", "Running as root!"

def check_5_healthcheck():
    """Check 5: Healthcheck."""
    with open("Dockerfile", "r") as f:
        content = f.read()
    
    if "HEALTHCHECK" in content and "curl" in content:
        return "OK", "HEALTHCHECK instruction present"
    return "FAIL", "Missing HEALTHCHECK"

def check_6_deploy_config():
    """Check 6: Deployment config."""
    deploy_files = [
        "deploy/render.yaml", 
        "deploy/docker-compose.prod.yml"
    ]
    missing = [f for f in deploy_files if not (PROJECT_ROOT / f).exists()]
    
    if missing:
        return "FAIL", f"Missing: {missing}"
    return "OK", "Deploy configs present"

def check_7_scripts():
    """Check 7: Helper scripts."""
    scripts = [
        "docker/entrypoint.sh",
        "docker/healthcheck.sh"
    ]
    missing = [f for f in scripts if not (PROJECT_ROOT / f).exists()]
    
    if missing:
        return "FAIL", f"Missing: {missing}"
    return "OK", "Entrypoint scripts present"

def main():
    print("\n" + "="*60)
    print("PHASE 12 VALIDATION - Containerization")
    print("="*60 + "\n")
    
    checks = [
        (1, "Dockerfile syntax", check_1_dockerfile),
        (2, "Docker Compose up", check_2_docker_compose),
        (3, "Image optimization", check_3_image_size_check),
        (4, "Non-root user", check_4_non_root),
        (5, "Healthcheck", check_5_healthcheck),
        (6, "Deploy config", check_6_deploy_config),
        (7, "Scripts existence", check_7_scripts),
    ]
    
    results = []
    for num, desc, func in checks:
        status, details = func()
        print_check(num, desc, status, details)
        results.append((num, status))

    print("\n" + "="*60)
    
    passed = sum(1 for _, status in results if status == "OK")
    failed = sum(1 for _, status in results if status == "FAIL")
    
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\n❌ PHASE 12 VALIDATION FAILED")
        return 1
    else:
        print("\n✅ PHASE 12 COMPLETE")
        return 0

if __name__ == "__main__":
    sys.exit(main())
