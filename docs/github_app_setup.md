# GitHub App Setup Guide (Phase 10)

This guide walks you through creating and configuring a GitHub App for production-ready authentication.

## Why GitHub App?
- **Higher Rate Limits**: 15,000 requests/hour (vs 5,000 for PAT)
- **Better Security**: Short-lived tokens (1 hour) instead of long-lived PATs
- **Granular Access**: Install on specific repositories only
- **No User Account Required**: Acts as a bot user

---

## Step 1: Create GitHub App

1. Go to **GitHub Settings** → **Developer settings** → **GitHub Apps**
2. Click **New GitHub App**
3. Fill in details:
   - **GitHub App name**: `code-review-crew-YOURNAME` (must be unique)
   - **Homepage URL**: `https://github.com/YOUR_USERNAME/code-review-crew` (or your repo URL)
   - **Callback URL**: `https://github.com/YOUR_USERNAME/code-review-crew` (not used yet)
   - **Webhook**: Active
   - **Webhook URL**: Your ngrok URL (e.g., `https://abc.ngrok-free.app/webhook/github`)
   - **Webhook secret**: Generate a random string (save to `.env` as `GITHUB_WEBHOOK_SECRET`)

---

## Step 2: Configure Permissions

Scroll down to **Permissions** and set the following:

### Repository Permissions
| Permission | Access | Reason |
|------------|--------|--------|
| **Contents** | Read-only | To fetch PR diffs and file content |
| **Pull requests** | Read & Write | To post review comments |
| **Issues** | Read & Write | To comment on issues (optional) |
| **Metadata** | Read-only | Required (default) |

### Subscribe to Events
Scroll to **Subscribe to events** and check:
- [x] **Pull request**

Click **Create GitHub App**.

---

## Step 3: Generate Private Key

1. On the App settings page, scroll to **Private keys**.
2. Click **Generate a private key**.
3. A `.pem` file will download automatically.
4. Rename it to `github_private_key.pem`.
5. Move it to the root of your project:
   ```bash
   mv ~/Downloads/code-review-crew*.pem ./github_private_key.pem
   ```
6. **IMPORTANT**: Update your `.gitignore` to unclude `*.pem` (already done).

---

## Step 4: Install App

1. On the App settings page, click **Install App** (left sidebar).
2. Click **Install** next to your account/organization.
3. Select **Only select repositories** and choose your test repository.
4. Click **Install**.

---

## Step 5: Configure Environment

1. **Get App ID**: 
   - Found in **General** settings page (About section).
   - Add to `.env`: `GITHUB_APP_ID=123456`

2. **Get Installation ID**:
   - Go to the installed repo settings or look at the URL after installation:
   - URL format: `https://github.com/settings/installations/12345678`
   - The number at the end is your `GITHUB_INSTALLATION_ID`.
   - Add to `.env`: `GITHUB_INSTALLATION_ID=12345678`

3. **Update `.env`**:
   ```bash
   # Phase 10: GitHub App Authentication
   GITHUB_APP_ID=123456
   GITHUB_PRIVATE_KEY_PATH=./github_private_key.pem
   GITHUB_INSTALLATION_ID=12345678
   GITHUB_WEBHOOK_SECRET=your_webhook_secret
   ```

---

## Step 6: Verify Setup

Run the validation script to check your configuration:

```bash
python validate_phase10.py
```

If checks 1-4 pass (using your real key but mock ID, or real ID if configured), you are ready!

To test fully check `validate_phase10.py` logic which mocks credentials by default. To test REAL production auth:

```python
# test_real_auth.py
import asyncio
from github_integration import GitHubAppAuth, InstallationManager

async def test():
    # Update with REAL values
    APP_ID = 123456
    INSTALLATION_ID = 789012 
    KEY_PATH = "./github_private_key.pem"
    
    auth = GitHubAppAuth(APP_ID, KEY_PATH)
    token = await auth.get_installation_token(INSTALLATION_ID)
    print(f"Success! Token: {token[:10]}...")
    await auth.close()

if __name__ == "__main__":
    asyncio.run(test())
```
