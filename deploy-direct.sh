#!/bin/bash

echo "🚀 Direct Railway Deployment (Bypassing GitHub)"
echo "================================================"

# Set your Railway token
export RAILWAY_TOKEN="c0ac895a-e3bb-43e8-957e-91f941a5b192"

# Install Railway CLI if not present
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install Railway CLI. Please install Node.js first."
        exit 1
    fi
fi

echo "✅ Railway CLI ready"

# Login using token
echo "🔐 Authenticating with Railway..."
echo "$RAILWAY_TOKEN" | railway login

if [ $? -ne 0 ]; then
    echo "❌ Authentication failed. Trying alternative method..."
    railway login --token "$RAILWAY_TOKEN"
fi

# Navigate to project directory
cd /app

# Create new project directly
echo "📦 Creating new Railway project..."
railway new --name "ai-video-generator-$(date +%s)"

# Link the project
echo "🔗 Linking project..."
railway link

# Add environment variables directly via CLI
echo "🔧 Setting up environment variables..."

# Core variables
railway variables set GROQ_API_KEY="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"
railway variables set RUNWAYML_API_KEY="key_2154d202435a6b1b8d6d887241a4e25ccade366566db56b7de2fe2aa2c133a41ee92654206db5d43b127b448e06db7774fb2625e06d35745e2ab808c11f761d4"
railway variables set GEMINI_API_KEY="AIzaSyD36dRBkEZUyCpDHLxTVuMO4P98SsYjkbc"

# Authentication
railway variables set SUPABASE_URL="https://tgjuxfndmuxwzloxezev.supabase.co"
railway variables set SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnanV4Zm5kbXV4d3psb3hlemV2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEzMjkyNzEsImV4cCI6MjA2NjkwNTI3MX0.RXU5k9AGfddAvI8Rq6eUqi02suwPDPIRSWVb1eil0rA"
railway variables set SUPABASE_JWT_SECRET="VQnWJiGtGd2YrKdkAVnVONKHGLmJJsrNkqQhJKGfTXyVoMgQFNiNFLfXjHxQSVJmZgJlGgGhWpZrVvNhQqMfXjKrJpQnGmXhJmKzRrVnSlQhPkLlJrKzVgXsNsJkMhFzVxNxTjRmKcNzNnJkRlQfTwVmPkLzGrQnVvJpMrJzHgQrJfVvKlPrQmNmJhKhNrQxJzVjVpJyKlNhVnJzMhGhVrJzRrJyTvJhLlGmJfVhJsKlQfVxJrKzNzJhNmJz"

# Storage
railway variables set CLOUDFLARE_ACCOUNT_ID="69317cc9622018bb255db5a590d143c2"
railway variables set R2_ACCESS_KEY_ID="7804ed0f387a54af1eafbe2659c062f7"
railway variables set R2_SECRET_ACCESS_KEY="c94fe3a0d93c4594c8891b4f7fc54e5f26c76231972d8a4d0d8260bb6da61788"
railway variables set R2_BUCKET_NAME="video-generation-storage"

# Optional
railway variables set ELEVENLABS_API_KEY="sk_613429b69a534539f725091aab14705a535bbeeeb6f52133"

echo "✅ Environment variables set"

# Add PostgreSQL database
echo "🗄️ Adding PostgreSQL database..."
echo "⚠️  You need to add PostgreSQL service manually:"
echo "   1. Go to railway.app/dashboard"
echo "   2. Select your project"
echo "   3. Click 'New Service' → 'PostgreSQL'"
echo "   4. DATABASE_URL will be auto-generated"
echo ""
echo "Press Enter after adding PostgreSQL service..."
read -p ""

# Deploy the application
echo "🚀 Deploying application..."
railway up --detach

echo ""
echo "✅ Deployment initiated!"
echo "📊 Check status at: https://railway.app/dashboard"
echo "🌐 Your app will be available at the generated Railway URL"
echo ""
echo "🔍 To check deployment status:"
echo "railway status"
echo ""
echo "📋 To view logs:"
echo "railway logs"