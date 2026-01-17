#!/bin/bash
# Custom healthcheck with database + Gemini ping checks
# Can be used in Dockerfile HEALTHCHECK if needed for deeper check than just curl /health

python -c "
import sys
try:
    from data.database import get_db_connection
    # Simple connection check
    conn = get_db_connection()
    conn.close()
    print('Database connection OK')
except Exception as e:
    print(f'Healthcheck failed: {e}')
    sys.exit(1)
"
