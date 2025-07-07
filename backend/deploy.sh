#!/bin/bash

# AI Video Generation Platform - Vercel Backend Deployment Script
# Deploy the comprehensive backend with PostgreSQL to Vercel

echo "🚀 AI Video Generation Platform - Vercel Backend Deployment"
echo "==========================================================="

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

# Create .vercelignore if it doesn't exist
echo "📝 Creating .vercelignore..."
cat > .vercelignore << EOF
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.DS_Store
.coverage
htmlcov/
.pytest_cache/
sample_video.mp4
sample_image.jpg
sample_audio.mp3
*.mp4
*.jpg
*.jpeg
*.png
*.mp3
*.wav
enhanced_*
ai_video_editor.py
mmaudio_service.py
elevenlabs_service.py
EOF

# Deploy to Vercel
echo "🚀 Deploying backend to Vercel..."
vercel --prod

echo ""
echo "✅ Backend deployment completed!"
echo ""
echo "📋 IMPORTANT: Set these environment variables in Vercel dashboard:"
echo ""
echo "🗄️  Database (Neon PostgreSQL):"
echo "   - DATABASE_URL (Your Neon PostgreSQL connection string)"
echo ""
echo "🤖 AI Services:"
echo "   - GROQ_API_KEY (Your Groq API key)"
echo "   - RUNWAYML_API_KEY (Your RunwayML API key)"  
echo "   - GEMINI_API_KEY (Your Google Gemini API key)"
echo "   - ELEVENLABS_API_KEY (Your ElevenLabs API key)"
echo ""
echo "🔐 Authentication (Supabase):"
echo "   - SUPABASE_URL (Your Supabase project URL)"
echo "   - SUPABASE_KEY (Your Supabase anon key)"
echo "   - SUPABASE_JWT_SECRET (Your Supabase JWT secret)"
echo ""
echo "☁️  Cloud Storage (Cloudflare R2):"
echo "   - CLOUDFLARE_ACCOUNT_ID (Your Cloudflare account ID)"
echo "   - CLOUDFLARE_R2_ENDPOINT (Your R2 endpoint URL)"
echo "   - R2_ACCESS_KEY_ID (Your R2 access key ID)"
echo "   - R2_SECRET_ACCESS_KEY (Your R2 secret access key)"
echo "   - R2_BUCKET_NAME (Your R2 bucket name)"
echo ""
echo "🔄 After setting environment variables, redeploy with:"
echo "   vercel --prod"
echo ""
echo "🎉 Your AI Video Generation Backend is now live on Vercel!"
echo ""
echo "📋 Your backend will be available at:"
echo "   https://your-backend.vercel.app/api/..."
echo ""
echo "🔍 Test endpoints:"
echo "   - https://your-backend.vercel.app/api/storage/status"
echo "   - https://your-backend.vercel.app/api/projects"
echo ""
echo "📚 Remember to update your frontend REACT_APP_BACKEND_URL to point to your Vercel backend!"