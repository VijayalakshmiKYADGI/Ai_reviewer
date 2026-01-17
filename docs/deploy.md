# Deployment Guide (Phase 12)

This guide covers deploying the Code Review Crew to various platforms using Docker.

## Local Development (Docker Compose)

The easiest way to run the full stack locally is with Docker Compose.

1. **Build & Start**:
   ```bash
   docker-compose up --build
   ```

2. **Verify Health**:
   - API: `http://localhost:8000/health`
   - Docs: `http://localhost:8000/docs`

3. **Stop**:
   ```bash
   docker-compose down
   ```

---

## Production Deployment: Render.com

We use a `render.yaml` Blueprint for Infrastructure as Code deployment.

### Prerequisite
- Push your code to a GitHub repository.

### Steps
1. Log in to **Render.com**.
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub repository.
4. Render will auto-detect `deploy/render.yaml`.
5. **Environment Variables**:
   - You will be prompted to enter values for:
     - `GEMINI_API_KEY`
     - `GITHUB_APP_ID`
     - `GITHUB_WEBHOOK_SECRET`
   - *Note*: For `GITHUB_PRIVATE_KEY_PATH`, Render recommends uploading the file as a "Secret File" mounted to `/etc/secrets/github_private_key.pem`. Update your env var accordingly.

### Configuration (`deploy/render.yaml`)
- **Type**: Web Service
- **Runtime**: Docker
- **Plan**: Starter (recommended for AI workloads)

---

## Other Platforms

### Vercel / Railway / Heroku
Since the project includes a standard `Dockerfile`, you can deploy to any container platform.

1. **Heroku**:
   ```bash
   heroku container:login
   heroku container:push web
   heroku container:release web
   ```

2. **Railway**:
   - Connect GitHub repo.
   - Railway auto-detects Dockerfile.
   - Add variables in Dashboard.

---

## Architecture

- **Multi-Stage Build**: Keeps image size small (<500MB) by discarding build tools.
- **Non-Root User**: Runs as `crewai` user for security.
- **Healthchecks**: Built-in `curl` check for orchestration uptime.
- **Entrypoint**: `docker/entrypoint.sh` handles DB init and startup.
