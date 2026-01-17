"""
Phase 13 Validation Script - Production Deployment

Validates:
- Render configuration
- Deployment readiness checks
- Monitoring endpoints
- Documentation presence
"""

import sys
import os
import yaml
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix Windows console encoding
if sys.platform == "win32":
    import codecs
    try:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).parent

def print_check(check_num: int, description: str, status: str, details: str = ""):
    """Print formatted check result."""
    status_symbol = "[OK]" if status == "OK" else "[FAIL]" if status == "FAIL" else "[SKIP]"
    print(f"[CHECK {check_num}] {description}... {status_symbol}")
    if details:
        print(f"          {details}")

def check_1_render_config():
    """Check 1: render.yml validity."""
    render_file = PROJECT_ROOT / "deploy/render.yml"
    if not render_file.exists():
        return "FAIL", "deploy/render.yml missing"
        
    try:
        with open(render_file, "r") as f:
            config = yaml.safe_load(f)
        if "services" in config and config["services"][0]["env"] == "docker":
            return "OK", "Valid Docker service config"
        return "FAIL", "Invalid structure"
    except Exception as e:
        return "FAIL", str(e)

def check_2_deploy_url():
    """Check 2: Manual deployment check."""
    return "SKIP", "Manual verification required (see docs/deploy.md)"

def check_3_production_env():
    """Check 3: Env vars presence in config."""
    render_file = PROJECT_ROOT / "deploy/render.yml"
    with open(render_file, "r") as f:
        config = yaml.safe_load(f)
        
    vars_list = [v["key"] for v in config["services"][0]["envVars"]]
    required = ["GEMINI_API_KEY", "DATABASE_URL", "GITHUB_WEBHOOK_SECRET"]
    
    missing = [r for r in required if r not in vars_list]
    if missing:
        return "FAIL", f"Missing vars: {missing}"
    return "OK", "Critical env vars configured"

def check_4_db_config():
    """Check 4: Database URL config."""
    render_file = PROJECT_ROOT / "deploy/render.yml"
    with open(render_file, "r") as f:
        config = yaml.safe_load(f)
    
    env_vars = config["services"][0]["envVars"]
    db_ok = any(v["key"] == "DATABASE_URL" and "fromDatabase" in v for v in env_vars)
    
    if db_ok:
        return "OK", "DATABASE_URL mapped to DB service"
    return "FAIL", "DATABASE_URL not mapped correctly"

def check_5_webhook_ready():
    """Check 5: Webhook endpoint existence."""
    # Static check of main.py
    main_file = PROJECT_ROOT / "api/main.py"
    with open(main_file, "r") as f:
        content = f.read()
    
    if "app.include_router(webhook.router)" in content:
        return "OK", "Webhook router included"
    return "FAIL", "Webhook router missing"

def check_6_metrics():
    """Check 6: Metrics endpoint."""
    metrics_file = PROJECT_ROOT / "monitoring/metrics.py"
    if metrics_file.exists():
        return "OK", "Metrics module present"
    return "FAIL", "metrics.py missing"

def check_7_e2e_ready():
    """Check 7: E2E test project."""
    test_proj = PROJECT_ROOT / "tests/test-project"
    if test_proj.exists():
        return "OK", "Test project ready"
    return "FAIL", "Test project missing"

def main():
    print("\n" + "="*60)
    print("PHASE 13 VALIDATION - Production Deployment")
    print("="*60 + "\n")
    
    checks = [
        (1, "Render config", check_1_render_config),
        (2, "Deploy URL", check_2_deploy_url),
        (3, "Production env vars", check_3_production_env),
        (4, "Database config", check_4_db_config),
        (5, "Webhook endpoint", check_5_webhook_ready),
        (6, "Metrics endpoint", check_6_metrics),
        (7, "E2E integration", check_7_e2e_ready),
    ]
    
    results = []
    for num, desc, func in checks:
        status, details = func()
        print_check(num, desc, status, details)
        results.append((num, status))

    print("\n" + "="*60)
    
    passed = sum(1 for _, status in results if status == "OK")
    failed = sum(1 for _, status in results if status == "FAIL")
    skipped = sum(1 for _, status in results if status == "SKIP")
    
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed > 0:
        print("\n❌ PHASE 13 VALIDATION FAILED")
        return 1
    else:
        print("\n✅ PHASE 13 COMPLETE")
        return 0

if __name__ == "__main__":
    sys.exit(main())
