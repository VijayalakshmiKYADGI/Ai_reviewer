# Production Testing Guide (Phase 11)

This guide walks you through the end-to-end production test of the Code Review Crew.

## Prerequisites
- [x] Phase 1-10 complete
- [x] GitHub App created and installed
- [x] Ngrok installed (`npm install -g ngrok` or download)

---

## Step 1: Start System

1. **Start Backend Server**:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Expose Localhost via Ngrok**:
   ```bash
   ngrok http 8000
   ```
   *Copy the https URL (e.g., `https://abc1234.ngrok-free.app`)*

3. **Update GitHub App Webhook**:
   - Go to: GitHub App Settings -> General -> Webhook URL
   - Paste: `https://abc1234.ngrok-free.app/webhook/github`
   - Ensure "Deep Check" secret matches `.env`

---

## Step 2: Create Test Repository

You need a *real* GitHub repository to receive webhooks.

1. **Create Repo**:
   - Name: `my-test-app`
   - Public/Private: Public (easier for free tier Actions)
   - *Do not initialize with README/license yet*

2. **Push Test Project Code**:
   ```bash
   # Go to the test project folder
   cd tests/test-project
   
   # Initialize git
   git init
   git add .
   git commit -m "Initial commit of flawed code"
   
   # Point to your NEW repo
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/my-test-app.git
   git push -u origin main
   ```

---

## Step 3: Install GitHub App

1. Go to your GitHub App Settings -> **Install App**.
2. Install it on your new `my-test-app` repository.

---

## Step 4: Run End-to-End Test

Now, trigger the automated PR creation workflow.

1. **Create & Push Test Branch**:
   ```bash
   # In tests/test-project/
   git checkout -b test-quality
   
   # Make a dummy change to trigger push event
   echo "# Trigger" >> README.md
   git add README.md
   git commit -m "Trigger quality review"
   
   # Push triggers GitHub Action
   git push origin test-quality
   ```

2. **Watch the Magic**:
   - **GitHub Actions**: Will run `test-pr-quality.yml` and create a PR named "🚨 Test Quality Review".
   - **Webhook**: GitHub sends `pull_request.opened` event to your ngrok URL.
   - **Backend**: `api/webhook.py` receives event -> `WebhookHandler` processes it.
   - **CrewAI**: Agents analyze code -> `GitHubCommenter` posts review.
   
3. **Verify Results**:
   - Go to the new PR on GitHub.
   - You should see comments on `flawed_quality.py`.
   - Example: "Missing docstring", "Undefined variable".

---

## Troubleshooting

- **Webhook 404/500**: Check `uvicorn` logs.
- **"Workflow not triggered"**: Check Actions tab in GitHub repo.
- **"App permission denied"**: Ensure App has `Pull requests: Write` permission.
- **No comments posted**: Check backend logs for `installation_id` errors.
