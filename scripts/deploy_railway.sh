#!/bin/bash

# Railway Deployment Script for Dixa Workflow API
# Usage: ./scripts/deploy_railway.sh

set -e

echo "🚀 Starting Railway deployment..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway:"
    railway login
fi

# Set environment variables
echo "🔧 Setting environment variables..."

read -p "Enter DIXA_API_KEY: " DIXA_API_KEY
read -p "Enter OPENAI_API_KEY: " OPENAI_API_KEY
read -p "Enter MONGODB_URL: " MONGODB_URL
read -p "Enter WEBHOOK_BASE_URL (leave empty to set after deployment): " WEBHOOK_BASE_URL

# Set required variables
railway variables set DIXA_API_KEY="$DIXA_API_KEY"
railway variables set OPENAI_API_KEY="$OPENAI_API_KEY"
railway variables set MONGODB_URL="$MONGODB_URL"
railway variables set OPENAI_ASSISTANT_ID="asst_ddwAna95PNJj3m0ZDmnVB7yf"
railway variables set AGENT_ID="65355895-3def-4735-aed4-82ef1f2b7000"
railway variables set QUEUE_ID="d768da52-2eb2-4841-a5e8-ce2d7eed3f3f"
railway variables set DIXA_BASE_URL="https://dev.dixa.io/v1"

if [ -n "$WEBHOOK_BASE_URL" ]; then
    railway variables set WEBHOOK_BASE_URL="$WEBHOOK_BASE_URL"
fi

echo "✅ Environment variables set successfully"

# Deploy
echo "🚢 Deploying to Railway..."
railway up

# Get URL
echo "🌐 Getting deployment URL..."
RAILWAY_URL=$(railway domain 2>/dev/null || echo "URL will be available after deployment")
echo "Your app will be available at: $RAILWAY_URL"

# Update webhook URL if it wasn't set initially
if [ -z "$WEBHOOK_BASE_URL" ] && [ "$RAILWAY_URL" != "URL will be available after deployment" ]; then
    echo "🔧 Updating WEBHOOK_BASE_URL with Railway domain..."
    railway variables set WEBHOOK_BASE_URL="$RAILWAY_URL"
    echo "♻️  Redeploying with updated webhook URL..."
    railway redeploy
fi

echo "🎉 Deployment complete!"
echo "📍 App URL: $RAILWAY_URL"
echo "🏥 Health check: $RAILWAY_URL/health"
echo "📚 API docs: $RAILWAY_URL/docs"

# Test health endpoint
echo "🧪 Testing deployment..."
if command -v curl &> /dev/null; then
    sleep 10  # Wait for deployment
    if curl -f -s "$RAILWAY_URL/health" > /dev/null; then
        echo "✅ Health check passed!"
    else
        echo "⚠️  Health check failed - check logs with: railway logs"
    fi
fi

echo "
📋 Next Steps:
1. Configure Dixa webhook: $RAILWAY_URL/dixa_conversation_started
2. Test the webhook with a sample payload
3. Monitor logs: railway logs
4. View metrics: railway dashboard
"