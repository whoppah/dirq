# Railway Deployment Guide - Dixa Workflow API

Complete step-by-step guide to deploy the Dixa Workflow API to Railway.

## 🚀 Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Railway CLI**: Install globally via npm
3. **Environment Variables**: Gather all required API keys and configurations
4. **MongoDB Database**: Set up a MongoDB instance (Railway, MongoDB Atlas, or other)

## 🛠️ Step 1: Install Railway CLI

```bash
npm install -g @railway/cli

# Verify installation
railway --version
```

## 🔐 Step 2: Prepare Environment Variables

Before deploying, gather these required values:

### Required Environment Variables

| Variable | Description | Example | Where to Get |
|----------|-------------|---------|--------------|
| `DIXA_API_KEY` | Dixa API authentication token | `eyJhbGciOiJIUzI1NiJ9...` | Dixa Developer Dashboard |
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-...` | OpenAI Platform |
| `MONGODB_URL` | MongoDB connection string | `mongodb://user:pass@host:port/db` | MongoDB Atlas or Railway |
| `WEBHOOK_BASE_URL` | Your Railway app URL | `https://your-app.up.railway.app` | Set after deployment |
| `OPENAI_ASSISTANT_ID` | OpenAI Assistant ID | `asst_ddwAna95PNJj3m0ZDmnVB7yf` | OpenAI Assistants |
| `AGENT_ID` | Dixa Agent identifier | `65355895-3def-4735-aed4-82ef1f2b7000` | From n8n workflow |
| `QUEUE_ID` | Dixa Queue identifier | `d768da52-2eb2-4841-a5e8-ce2d7eed3f3f` | From n8n workflow |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DIXA_BASE_URL` | Dixa API base URL | `https://dev.dixa.io/v1` |

## 📚 Step 3: Set Up MongoDB Database

### Option A: Railway PostgreSQL (Alternative)
If you prefer PostgreSQL over MongoDB, you'll need to modify the database service.

### Option B: MongoDB on Railway
1. Add MongoDB service to your Railway project
2. Get connection string from Railway dashboard

### Option C: MongoDB Atlas (Recommended)
1. Create account at [mongodb.com/atlas](https://mongodb.com/atlas)
2. Create a cluster
3. Create database user
4. Get connection string: `mongodb+srv://username:password@cluster.mongodb.net/database`

## 🚢 Step 4: Deploy to Railway

### Method 1: CLI Deployment (Recommended)

```bash
# 1. Navigate to your project directory
cd /path/to/dirq

# 2. Login to Railway
railway login

# 3. Create new Railway project (or link existing)
railway create dixa-workflow-api
# OR link to existing project
# railway link [project-id]

# 4. Set environment variables (all at once)
railway variables set DIXA_API_KEY="your_dixa_api_key"
railway variables set OPENAI_API_KEY="your_openai_api_key"  
railway variables set MONGODB_URL="mongodb://user:pass@host:port/db"
railway variables set OPENAI_ASSISTANT_ID="asst_ddwAna95PNJj3m0ZDmnVB7yf"
railway variables set AGENT_ID="65355895-3def-4735-aed4-82ef1f2b7000"
railway variables set QUEUE_ID="d768da52-2eb2-4841-a5e8-ce2d7eed3f3f"
railway variables set DIXA_BASE_URL="https://dev.dixa.io/v1"

# 5. Deploy
railway up

# 6. Get your app URL
railway domain
```

### Method 2: GitHub Integration

1. Push code to GitHub repository
2. Connect Railway to your GitHub repo
3. Configure environment variables in Railway dashboard
4. Auto-deploy on git push

## 🔧 Step 5: Post-Deployment Configuration

### 1. Get Your Railway URL
```bash
railway domain
# Output: https://your-app-name.up.railway.app
```

### 2. Update WEBHOOK_BASE_URL
```bash
railway variables set WEBHOOK_BASE_URL="https://your-app-name.up.railway.app"
```

### 3. Trigger Redeploy
```bash
railway redeploy
```

## 🧪 Step 6: Test Your Deployment

### Health Check
```bash
curl https://your-app-name.up.railway.app/health
# Expected: {"status":"healthy","service":"dixa-webhook"}
```

### API Documentation
Visit: `https://your-app-name.up.railway.app/docs`

### Test Webhook Endpoint
```bash
curl -X POST https://your-app-name.up.railway.app/dixa_conversation_started \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

## 🔍 Step 7: Configure Dixa Webhook

1. **Login to Dixa Dashboard**
2. **Go to Settings > Integrations > Webhooks**
3. **Create New Webhook:**
   - **URL**: `https://your-app-name.up.railway.app/dixa_conversation_started`
   - **Events**: `CONVERSATION_MESSAGE_ADDED`
   - **Method**: `POST`
   - **Content-Type**: `application/json`

## 📊 Monitoring & Logs

### View Logs
```bash
# Real-time logs
railway logs

# Service-specific logs
railway logs --service your-service-name
```

### Railway Dashboard
- Monitor metrics at [railway.app/dashboard](https://railway.app/dashboard)
- View deployments, logs, and metrics
- Manage environment variables

## 🐛 Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Check build logs
   railway logs --deployment [deployment-id]
   
   # Verify requirements.txt
   cat requirements.txt
   ```

2. **Environment Variable Issues**
   ```bash
   # List all variables
   railway variables
   
   # Update variable
   railway variables set VAR_NAME="new_value"
   ```

3. **Port Issues**
   - Railway automatically sets `PORT` environment variable
   - App listens on `0.0.0.0:$PORT`
   - Health check endpoint: `/health`

4. **Database Connection Issues**
   ```bash
   # Test MongoDB connection
   railway run python -c "from core.services.database_service import MongoDBService; print('DB Connected' if MongoDBService().client else 'DB Failed')"
   ```

### Debug Commands

```bash
# SSH into Railway container
railway shell

# Run one-off commands
railway run python -c "import sys; print(sys.version)"

# Environment inspection
railway run env | grep -E "(DIXA|OPENAI|MONGODB)"
```

## 🔄 Updates & Redeployment

### Code Updates
```bash
# Push changes and redeploy
git add .
git commit -m "Update: description"
git push origin main

# Manual redeploy
railway redeploy
```

### Environment Variable Updates
```bash
# Update single variable
railway variables set VARIABLE_NAME="new_value"

# Bulk update (create script)
./scripts/update_railway_vars.sh
```

## 🛡️ Security Best Practices

1. **Never commit `.env` files**
2. **Rotate API keys regularly**
3. **Use Railway's secret management**
4. **Enable Railway's built-in security features**
5. **Monitor logs for suspicious activity**

## 📈 Scaling & Performance

### Railway Pro Features
- **Auto-scaling**: Handles traffic spikes
- **Custom domains**: Use your own domain
- **Team collaboration**: Multiple developers
- **Advanced metrics**: Performance monitoring

### Configuration
```bash
# Configure scaling (Railway Pro)
railway service scale --replicas 2
railway service scale --memory 1GB
railway service scale --cpu 1000m
```

## 🆘 Support

### Railway Support
- [Railway Documentation](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [Railway Status](https://status.railway.app)

### Application Support
- Check application logs: `railway logs`
- Review deployment status: `railway status`
- Test endpoints: Use the `/health` endpoint

## 📋 Deployment Checklist

- [ ] Railway CLI installed and authenticated
- [ ] All environment variables configured
- [ ] MongoDB database set up and accessible
- [ ] Application deployed successfully
- [ ] Health check endpoint responding
- [ ] API documentation accessible at `/docs`
- [ ] Webhook URL updated in environment variables
- [ ] Dixa webhook configured with Railway URL
- [ ] Test webhook endpoint with sample payload
- [ ] Logs monitoring set up
- [ ] Domain configuration (if using custom domain)

## 🔗 Quick Links

- **Railway Dashboard**: [railway.app/dashboard](https://railway.app/dashboard)
- **Application Health**: `https://your-app.up.railway.app/health`
- **API Docs**: `https://your-app.up.railway.app/docs`
- **Deployment Guide**: This document

---

**Need Help?** Check the troubleshooting section above or reach out to the development team.