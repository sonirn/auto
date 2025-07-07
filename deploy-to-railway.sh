#!/bin/bash

# Railway Deployment Script
# Run this script to deploy your AI Video Generation Platform to Railway

echo "🚀 Railway Deployment Script for AI Video Generation Platform"
echo "============================================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

echo "✅ Railway CLI is available"

# Login with your token
echo "🔐 Logging in to Railway..."
railway login --token c0ac895a-e3bb-43e8-957e-91f941a5b192

# Create new project
echo "📦 Creating new Railway project..."
railway new

# Set up environment variables
echo "🔧 Setting up environment variables..."
echo "Please add these environment variables in Railway dashboard:"
echo ""
echo "Required Variables:"
echo "DATABASE_URL=<will-be-auto-generated-when-you-add-postgresql>"
echo "GROQ_API_KEY=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"
echo "RUNWAYML_API_KEY=key_2154d202435a6b1b8d6d887241a4e25ccade366566db56b7de2fe2aa2c133a41ee92654206db5d43b127b448e06db7774fb2625e06d35745e2ab808c11f761d4"
echo "GEMINI_API_KEY=AIzaSyD36dRBkEZUyCpDHLxTVuMO4P98SsYjkbc"
echo "SUPABASE_URL=https://tgjuxfndmuxwzloxezev.supabase.co"
echo "SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnanV4Zm5kbXV4d3psb3hlemV2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEzMjkyNzEsImV4cCI6MjA2NjkwNTI3MX0.RXU5k9AGfddAvI8Rq6eUqi02suwPDPIRSWVb1eil0rA"
echo "SUPABASE_JWT_SECRET=VQnWJiGtGd2YrKdkAVnVONKHGLmJJsrNkqQhJKGfTXyVoMgQFNiNFLfXjHxQSVJmZgJlGgGhWpZrVvNhQqMfXjKrJpQnGmXhJmKzRrVnSlQhPkLlJrKzVgXsNsJkMhFzVxNxTjRmKcNzNnJkRlQfTwVmPkLzGrQnVvJpMrJzHgQrJfVvKlPrQmNmJhKhNrQxJzVjVpJyKlNhVnJzMhGhVrJzRrJyTvJhLlGmJfVhJsKlQfVxJrKzNzJhNmJz"
echo "CLOUDFLARE_ACCOUNT_ID=69317cc9622018bb255db5a590d143c2"
echo "R2_ACCESS_KEY_ID=7804ed0f387a54af1eafbe2659c062f7"
echo "R2_SECRET_ACCESS_KEY=c94fe3a0d93c4594c8891b4f7fc54e5f26c76231972d8a4d0d8260bb6da61788"
echo "R2_BUCKET_NAME=video-generation-storage"
echo "ELEVENLABS_API_KEY=sk_613429b69a534539f725091aab14705a535bbeeeb6f52133"
echo ""
echo "⚠️  Go to Railway dashboard and add these variables before deploying!"
echo "📱 Press Enter when you've added the environment variables..."
read -p ""

# Add PostgreSQL service
echo "🗄️  Adding PostgreSQL service..."
echo "Go to your Railway project and click 'New Service' -> 'PostgreSQL'"
echo "This will auto-generate the DATABASE_URL variable"
echo "📱 Press Enter when you've added PostgreSQL service..."
read -p ""

# Deploy
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment initiated!"
echo "📊 Monitor your deployment at: https://railway.app/dashboard"
echo "🔍 Check logs for any errors"
echo "🌐 Your app will be available at the generated Railway URL"