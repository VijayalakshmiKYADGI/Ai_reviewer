# Stage 1: Builder
# Use slim image for smaller footprint
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies if needed (e.g., for cryptography/gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies (e.g., curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user for security
# Create non-root user for security and ensure data dir exists/permissions
RUN useradd -m crewai && \
    mkdir -p /app/data && \
    chown -R crewai:crewai /app

# Switch to non-root user
USER crewai

# Expose port
EXPOSE 8000

# Healthcheck configuration
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start command (overridden by entrypoint.sh usually, but good fallback)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
