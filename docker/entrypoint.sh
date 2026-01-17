#!/bin/bash
set -e

# Wait for dependencies (simple sleep loop for simplicity without external tool)
# In production with docker-compose, depends_on handles most startup order,
# but 'wait-for-it' logic is better for strict dependency.
# For this phase, we'll assume Redis is ready or retry logic in code handles it.

echo "Starting Code Review Crew API..."

# Initialize database (idempotent)
echo "Initializing database..."
python -c "from data.database import init_database; init_database()"

# Start server
echo "Starting Uvicorn..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000 "$@"
