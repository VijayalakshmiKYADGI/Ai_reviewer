"""
Phase 7 validation script.
Verifies API server startup and endpoints.
"""
import sys
import time
import requests
import subprocess
import threading
from api.main import app
from fastapi.testclient import TestClient

def validate_phase7():
    print("=" * 60)
    print("PHASE 7 VALIDATION")
    print("=" * 60)
    
    errors = []
    
    # We use TestClient for instant validation without spawning uvicorn process
    client = TestClient(app)
    
    # [CHECK 1] Health Endpoint
    print("\n[CHECK 1] /health endpoint...")
    try:
        resp = client.get("/health")
        if resp.status_code == 200:
            print(f"  [OK] Status 200, {resp.json()}")
        else:
            errors.append(f"Health check failed: {resp.status_code}")
            print(f"  [FAIL] {resp.status_code}")
    except Exception as e:
         errors.append(f"Health request failed: {e}")
         print(f"  [FAIL] {e}")

    # [CHECK 2] PR Review Endpoints (Mocked DB/Queue)
    print("\n[CHECK 3] POST /review/pr (Async)...")
    try:
        # DB requires connection. If testing env doesn't have DB sets up tables, might fail.
        # But 'create_tables' runs on startup. TestClient calls startup events.
        # SQLite should be fine.
        payload = {
            "repo_name": "test-repo", 
            "pr_number": 999, 
            "files_changed": ["a.py"],
            "diff_content": "diff --git a/a.py b/a.py\nnew file",
            "pr_url": "http://github.com/a"
        }
        # Note: We are running real code so 'save_review_start' will run.
        # If DB is not available, it throws.
        # We assume local sqlite is working.
        
        resp = client.post("/review/pr", json=payload)
        if resp.status_code == 202:
             print("  [OK] 202 Accepted")
             print(f"  ID: {resp.json().get('review_id')}")
        else:
             errors.append(f"PR Review failed: {resp.status_code}")
             print(f"  [FAIL] {resp.status_code} - {resp.text}")
    except Exception as e:
        errors.append(f"PR request failed: {e}")
        print(f"  [FAIL] {e}")

    # [CHECK 3] OpenAPI components
    print("\n[CHECK 6] OpenAPI docs...")
    try:
        if app.openapi():
            print("  [OK] OpenAPI schema generated")
    except Exception as e:
        errors.append(f"Schema generation failed: {e}")
        print(f"  [FAIL] {e}")

    print("\n" + "=" * 60)
    if errors:
        print("PHASE 7 [FAIL] VALIDATION FAILED")
        sys.exit(1)
    else:
        print("PHASE 7 [SUCCESS] VALIDATED")
        print("FastAPI Backend ready.")
    print("=" * 60)

if __name__ == "__main__":
    validate_phase7()
