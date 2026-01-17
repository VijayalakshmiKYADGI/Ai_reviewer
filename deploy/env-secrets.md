# Render Secrets Setup Guide

This guide helps you set up the secure environment variables (Environment Groups) required for the `render.yml` blueprint.

## Step 1: Create Database
1. Go to Render Dashboard.
2. Click **New +** -> **PostgreSQL**.
3. Name: `code-review-crew-db`
4. Region: **Singapore** (Must match web service).
5. Plan: Starter/Free.
6. Create.
7. Copy the **Internal Connection String** (starts with `postgres://...`).

## Step 2: Create Environment Group
1. Go to **Environment Groups** tab.
2. Click **New Environment Group**.
3. Name: `code-review-crew`
4. Add the following secrets:
   - `GEMINI_API_KEY`: Your Google Gemini API Key.
   - `GITHUB_APP_ID`: Your GitHub App ID (e.g., `123456`).
   - `GITHUB_INSTALLATION_ID`: Your Installation ID (e.g., `12345678`).
   - `GITHUB_WEBHOOK_SECRET`: The secret string you generated for the Webhook.
   - `app_id`: Same as `GITHUB_APP_ID` (referenced in render.yml).
   - `webhook_secret`: Same as `GITHUB_WEBHOOK_SECRET` (referenced in render.yml).
   - `installation_id`: Same as `GITHUB_INSTALLATION_ID` (referenced in render.yml).

   *(Note: The `render.yml` uses `fromDatabase` mapping. You can also just set these directly on the service if you prefer simpler config, but Environment Groups are cleaner.)*

## Step 3: Private Key
1. Go to your Web Service settings (after it's created via Blueprint).
2. Go to **Secret Files**.
3. Upload `github_private_key.pem`.
4. Mount path: `/etc/secrets/github_private_key.pem`.
