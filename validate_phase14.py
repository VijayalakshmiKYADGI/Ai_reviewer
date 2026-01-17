"""
Phase 14 Validation Script - Free Production Deployment

Validates:
- Railway configuration validity
- Supabase SQL schema syntax/presence
- Deployment script presence
- Documentation updates
"""

import sys
import os
import toml
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

def check_1_railway_config():
    """Check 1: railway.toml validity."""
    config_file = PROJECT_ROOT / "deploy/railway.toml"
    if not config_file.exists():
        return "FAIL", "deploy/railway.toml missing"
        
    try:
        with open(config_file, "r") as f:
            data = toml.load(f)
        
        if "build" in data and data["build"].get("builder") == "NIXPACKS":
            return "OK", "Nixpacks builder configured"
        return "FAIL", "Invalid builder config"
    except Exception as e:
        return "FAIL", str(e)

def check_2_supabase_sql():
    """Check 2: Supabase SQL schema."""
    sql_file = PROJECT_ROOT / "deploy/supabase.sql"
    if not sql_file.exists():
        return "FAIL", "deploy/supabase.sql missing"
    
    with open(sql_file, "r") as f:
        content = f.read()
        
    if "CREATE TABLE IF NOT EXISTS reviews" in content:
        return "OK", "Reviews table schema present"
    return "FAIL", "Schema invalid or missing table"

def check_3_deploy_script():
    """Check 3: Deployment script."""
    script_file = PROJECT_ROOT / "deploy/free-deploy.sh"
    if script_file.exists():
        return "OK", "Script present"
    return "FAIL", "deploy/free-deploy.sh missing"

def check_4_readme_update():
    """Check 4: README documentation."""
    readme_file = PROJECT_ROOT / "README.md"
    with open(readme_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "FREE & OPEN SOURCE" in content and "Railway" in content:
        return "OK", "Free deploy section verified"
    return "FAIL", "README not updated correctly"

def main():
    print("\n" + "="*60)
    print("PHASE 14 VALIDATION - Free Production Deployment")
    print("="*60 + "\n")
    
    checks = [
        (1, "Railway Config", check_1_railway_config),
        (2, "Supabase Schema", check_2_supabase_sql),
        (3, "Deployment Script", check_3_deploy_script),
        (4, "README Updates", check_4_readme_update),
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
        print("\n❌ PHASE 14 VALIDATION FAILED")
        return 1
    else:
        print("\n✅ PHASE 14 COMPLETE")
        return 0

if __name__ == "__main__":
    sys.exit(main())
