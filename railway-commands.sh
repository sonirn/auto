#!/bin/bash

# Simple Railway deployment commands
echo "🚀 Railway Deployment Commands"
echo "============================="

echo "1. Install Railway CLI:"
echo "npm install -g @railway/cli"
echo ""

echo "2. Login to Railway:"
echo "railway login --token c0ac895a-e3bb-43e8-957e-91f941a5b192"
echo ""

echo "3. Deploy from this directory:"
echo "cd /app && railway new && railway up"
echo ""

echo "4. Add environment variables in Railway dashboard:"
echo "   - Go to railway.app/dashboard"
echo "   - Select your project"
echo "   - Go to Variables tab"
echo "   - Add all variables from RAILWAY_DEPLOY_DIRECT.md"
echo ""

echo "5. Add PostgreSQL service:"
echo "   - In Railway dashboard: New Service → PostgreSQL"
echo "   - DATABASE_URL will be auto-generated"
echo ""

echo "6. Monitor deployment:"
echo "   - Check logs in Railway dashboard"
echo "   - Test health endpoint: https://your-app.railway.app/api/storage/status"
echo ""

echo "✅ Your app will be live once deployment completes!"