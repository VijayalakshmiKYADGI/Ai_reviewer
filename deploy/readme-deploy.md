# Production Deployment Checklist ✅

Follow this checklist to deploy the Code Review Crew to production.

## 1. Preparation
- [ ] Push `code-review-crew` code to a public/private GitHub repository.
- [ ] Have your `.env` secrets ready (Gemini Key, GitHub App details).
- [ ] Have your `github_private_key.pem` file ready.

## 2. Deploy to Render
- [ ] Go to [dashboard.render.com](https://dashboard.render.com).
- [ ] Click **New +** -> **Blueprint**.
- [ ] Connect your repository.
- [ ] Render will detect `deploy/render.yml`.
- [ ] Fulfill the secrets requirements (see `deploy/env-secrets.md`).
- [ ] Click **Apply**.

## 3. Post-Deployment Configuration
- [ ] Wait for deployment to finish (~3-5 mins).
- [ ] Copy your new Service URL (e.g., `https://code-review-crew-xyz.onrender.com`).
- [ ] Go to GitHub App Settings -> **Webhooks**.
- [ ] Update **Payload URL** to: `https://code-review-crew-xyz.onrender.com/webhook/github`.

## 4. Verification
- [ ] Visit `https://code-review-crew-xyz.onrender.com/health` -> Should return `{"status": "healthy"}`.
- [ ] Visit `https://code-review-crew-xyz.onrender.com/metrics` -> Should see stats.

## 5. Live Test
- [ ] Push to your `my-test-app` repo (branch `test-quality`).
- [ ] Verify that the comment appears on the PR.

## Costs
- **Web Service**: ~$7/month (Starter)
- **Database**: ~$7/month (Starter)
- **Total**: ~$14/month
