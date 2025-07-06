#!/bin/bash

# AI Video Generation Platform - Vercel Deployment Script
# This script helps you deploy your AI video generation platform to Vercel

echo "🚀 AI Video Generation Platform - Vercel Deployment"
echo "=================================================="

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if user is logged in to Vercel
echo "🔐 Checking Vercel authentication..."
if ! vercel whoami &> /dev/null; then
    echo "🔑 Please log in to Vercel:"
    vercel login
fi

# Install dependencies
echo "📦 Installing dependencies..."
yarn install

# Build the project
echo "🏗️  Building the project..."
yarn build

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
vercel --prod

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Next Steps:"
echo "1. Go to your Vercel dashboard"
echo "2. Navigate to Settings > Environment Variables"
echo "3. Add the required environment variables:"
echo "   - MONGO_URL (MongoDB connection string)"
echo "   - DB_NAME (MongoDB database name)"
echo "   - GROQ_API_KEY (Groq API key)"
echo "   - RUNWAYML_API_KEY (RunwayML API key)"
echo "   - GEMINI_API_KEY (Google Gemini API key)"
echo "   - SUPABASE_URL (Supabase project URL)"
echo "   - SUPABASE_KEY (Supabase anon key)"
echo "   - SUPABASE_JWT_SECRET (Supabase JWT secret)"
echo "   - CLOUDFLARE_ACCOUNT_ID (Cloudflare account ID)"
echo "   - CLOUDFLARE_R2_ENDPOINT (R2 endpoint URL)"
echo "   - R2_ACCESS_KEY_ID (R2 access key ID)"
echo "   - R2_SECRET_ACCESS_KEY (R2 secret access key)"
echo "   - R2_BUCKET_NAME (R2 bucket name)"
echo ""
echo "4. Redeploy after setting environment variables"
echo ""
echo "🎉 Your AI Video Generation Platform is now live on Vercel!"