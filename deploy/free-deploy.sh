#!/bin/bash

echo "🚀 CODE REVIEW CREW - FREE PRODUCTION DEPLOYMENT"
echo "================================================"

# Check dependencies
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install: npm install -g @railway/cli"
    exit 1
fi

if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found. Please install via your package manager."
    echo "   (Or create project manually at supabase.com and get connection string)"
    # We won't exit here strictly as user might skip Supabase CLI if using web UI
fi

echo "Step 1: Deploying Web Service to Railway..."
# Login check
railway whoami || railway login

# specialized init if needed, or just up
railway init
railway up --detach

echo "✅ Web Service is deploying..."
echo "   Check status: railway status"
SERVICE_URL=$(railway status | grep "Service" | grep "up.railway.app" | awk '{print $NF}')
echo "   Live URL: https://$SERVICE_URL"

echo ""
echo "Step 2: Database Setup (Supabase)"
echo "   1. Go to https://supabase.com -> New Project (Free Tier)"
echo "   2. Go to SQL Editor -> New Query"
echo "   3. Copy/Paste content of deploy/supabase.sql"
echo "   4. Run Query"
echo "   5. Get Connection String (Transaction mode)"
echo "   6. Set DATABASE_URL in Railway Dashboard Variables"

echo ""
echo "Step 3: Secrets Configuration"
echo "   Set these variables in Railway Dashboard:"
echo "   - GEMINI_API_KEY"
echo "   - GITHUB_APP_ID"
echo "   - GITHUB_WEBHOOK_SECRET"
echo "   - GITHUB_INSTALLATION_ID"
echo "   - DATABASE_URL (from Supabase)"
echo "   - GITHUB_PRIVATE_KEY_PATH (or upload file)"

echo ""
echo "Step 4: Webhook Update"
echo "   Update GitHub App Webhook URL to: https://$SERVICE_URL/webhook/github"

echo "================================================"
echo "🎉 DEPLOYMENT INSTRUCTIONS COMPLETE"
