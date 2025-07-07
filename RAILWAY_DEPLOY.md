# AI Video Generation Platform - Railway Deployment Guide

This is a comprehensive AI-powered video generation platform that analyzes sample videos and generates similar content using multiple AI models.

## 🚀 Quick Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new?template=https://github.com/your-repo/ai-video-generator)

## 📋 Prerequisites

Before deploying to Railway, ensure you have:

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Fork or clone this repository
3. **Required API Keys**: Get API keys for the services listed below

## 🔑 Required Environment Variables

Set these environment variables in your Railway project:

### Database
```
DATABASE_URL=postgresql://username:password@host:port/database
```

### Authentication (Supabase)
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
```

### AI/LLM APIs
```
GROQ_API_KEY=your-groq-api-key
XAI_API_KEY=your-xai-api-key (optional)
AIML_API_KEY=your-aiml-api-key (optional)
```

### Video Generation APIs
```
RUNWAYML_API_KEY=your-runwayml-api-key
GEMINI_API_KEY=your-google-gemini-api-key
```

### Audio APIs (Optional)
```
ELEVENLABS_API_KEY=your-elevenlabs-api-key
```

### Cloud Storage (Cloudflare R2)
```
CLOUDFLARE_ACCOUNT_ID=your-cloudflare-account-id
CLOUDFLARE_R2_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your-r2-access-key
R2_SECRET_ACCESS_KEY=your-r2-secret-key
R2_BUCKET_NAME=video-generation-storage
R2_TOKEN=your-r2-token
```

### Video Processing (Optional)
```
MUX_TOKEN_ID=your-mux-token-id
MUX_TOKEN_SECRET=your-mux-token-secret
SHOTSTACK_API_KEY=your-shotstack-api-key
SHOTSTACK_OWNER_ID=your-shotstack-owner-id
```

## 🛠️ Deployment Steps

### Method 1: One-Click Deploy (Recommended)

1. Click the "Deploy on Railway" button above
2. Connect your GitHub account
3. Select this repository
4. Add all required environment variables
5. Deploy!

### Method 2: Manual Deploy

1. **Create Railway Project**
   ```bash
   railway login
   railway new
   ```

2. **Connect Repository**
   ```bash
   railway link your-project-id
   ```

3. **Set Environment Variables**
   ```bash
   railway variables set DATABASE_URL="your-database-url"
   railway variables set GROQ_API_KEY="your-groq-key"
   # ... add all other variables
   ```

4. **Deploy**
   ```bash
   railway up
   ```

### Method 3: Railway CLI with GitHub

1. **Fork/Clone Repository**
2. **Create Railway Project** and connect to GitHub
3. **Add Environment Variables** in Railway dashboard
4. **Trigger Deployment** by pushing to main branch

## 🔧 Configuration Details

### Port Configuration
The application automatically detects Railway's `PORT` environment variable. No manual configuration needed.

### Database Setup
- Uses PostgreSQL with automatic table creation
- Database initialization happens on startup
- Compatible with Railway's PostgreSQL service

### File Storage
- Configured for Cloudflare R2 cloud storage
- Falls back to local storage if R2 is unavailable
- 7-day automatic file retention policy

### Health Checks
- Health check endpoint: `/api/storage/status`
- Monitors storage and database connectivity
- 120-second timeout configured

## 📊 Deployment Files

- `Procfile`: Railway start command
- `railway.json`: Railway-specific configuration
- `nixpacks.toml`: Build configuration
- `start.sh`: Startup script with database initialization
- `backend/requirements.txt`: Python dependencies

## 🚦 Post-Deployment

### 1. Verify Deployment
Check these endpoints after deployment:
- `https://your-app.railway.app/api/storage/status` - Storage status
- `https://your-app.railway.app/api/database/status` - Database status

### 2. Test Core Features
- Create a video project: `POST /api/projects`
- Upload sample video: `POST /api/projects/{id}/upload-sample`
- Analyze video: `POST /api/projects/{id}/analyze`

### 3. Set Up Domain (Optional)
1. Go to Railway dashboard
2. Navigate to your project
3. Add custom domain under "Settings"

## 🔍 Monitoring

### Health Checks
Railway automatically monitors the health check endpoint and restarts if needed.

### Logs
View application logs in Railway dashboard or via CLI:
```bash
railway logs
```

### Metrics
Monitor performance in Railway dashboard under "Metrics" tab.

## 🛠️ Troubleshooting

### Common Issues

**1. Database Connection Errors**
- Verify `DATABASE_URL` is correctly set
- Ensure PostgreSQL service is running
- Check connection string format

**2. Missing API Keys**
- All AI service API keys must be set
- Verify key formats and permissions
- Test keys independently if needed

**3. Storage Issues**
- Verify Cloudflare R2 credentials
- Check bucket exists and permissions
- Application falls back to local storage

**4. Port Binding Issues**
- Railway automatically sets `PORT` variable
- Application automatically detects and uses it
- No manual configuration needed

### Debug Commands
```bash
# View environment variables
railway variables

# View logs
railway logs --tail

# SSH into deployment
railway shell
```

## 📚 API Documentation

### Core Endpoints
- `POST /api/projects` - Create video project
- `POST /api/projects/{id}/upload-sample` - Upload sample video
- `POST /api/projects/{id}/analyze` - Analyze video with AI
- `POST /api/projects/{id}/chat` - Chat with AI for modifications
- `POST /api/projects/{id}/generate` - Generate video
- `GET /api/projects/{id}/status` - Check generation status
- `GET /api/projects/{id}/download` - Download generated video

### Authentication Endpoints
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

## 🔄 Updates and Maintenance

### Updating the Application
1. Push changes to your GitHub repository
2. Railway automatically redeploys
3. Monitor deployment in Railway dashboard

### Database Migrations
Database schema updates are handled automatically on startup.

### Scaling
- Railway automatically scales based on usage
- Configure scaling limits in project settings
- Monitor resource usage in dashboard

## 🆘 Support

### Resources
- [Railway Documentation](https://docs.railway.app)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Project GitHub Repository](https://github.com/your-repo)

### Getting Help
1. Check Railway logs for errors
2. Review environment variable configuration
3. Test API endpoints individually
4. Contact support if needed

## 🏷️ Version Info

- **Python**: 3.11+
- **FastAPI**: 0.104.1+
- **PostgreSQL**: Latest
- **Railway**: Compatible
- **Last Updated**: January 2025

---

**Ready to deploy?** Click the Railway button above to get started! 🚀