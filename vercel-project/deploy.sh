#!/bin/bash

# AI Video Generation Platform - Vercel Deployment Script (PostgreSQL Version)
# This script helps you deploy your AI video generation platform to Vercel with Neon PostgreSQL

echo "🚀 AI Video Generation Platform - Vercel Deployment (PostgreSQL)"
echo "================================================================="

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
echo ""
echo "🗄️  Database (Neon PostgreSQL):"
echo "   - DATABASE_URL (Neon PostgreSQL connection string)"
echo ""
echo "🤖 AI Services:"
echo "   - GROQ_API_KEY (Groq API key)"
echo "   - RUNWAYML_API_KEY (RunwayML API key)"  
echo "   - GEMINI_API_KEY (Google Gemini API key)"
echo "   - ELEVENLABS_API_KEY (ElevenLabs API key)"
echo ""
echo "☁️  Cloud Storage (Cloudflare R2):"
echo "   - CLOUDFLARE_ACCOUNT_ID (Cloudflare account ID)"
echo "   - CLOUDFLARE_R2_ENDPOINT (R2 endpoint URL)"
echo "   - R2_ACCESS_KEY_ID (R2 access key ID)"
echo "   - R2_SECRET_ACCESS_KEY (R2 secret access key)"
echo "   - R2_BUCKET_NAME (R2 bucket name)"
echo ""
echo "🔐 Authentication (Stack Auth):"
echo "   - NEXT_PUBLIC_STACK_PROJECT_ID (Stack project ID)"
echo "   - NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY (Stack client key)"
echo "   - STACK_SECRET_SERVER_KEY (Stack server key)"
echo ""
echo "4. Redeploy after setting environment variables"
echo ""
echo "🔍 Testing URLs:"
echo "   - Frontend: https://your-app.vercel.app"
echo "   - API Health: https://your-app.vercel.app/api/projects"
echo ""
echo "🎉 Your AI Video Generation Platform is now live on Vercel with PostgreSQL!"
echo ""
echo "📚 For detailed documentation, see README.md"