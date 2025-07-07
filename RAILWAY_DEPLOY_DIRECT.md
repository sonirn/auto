# 🚀 Direct Railway Deployment Guide

## Quick Deploy Steps

### Option 1: Use Railway CLI (Recommended)

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login with your token**
   ```bash
   railway login --token c0ac895a-e3bb-43e8-957e-91f941a5b192
   ```

3. **Create and deploy project**
   ```bash
   cd /app
   railway new
   railway up
   ```

### Option 2: Use Web Dashboard

1. Go to [railway.app/dashboard](https://railway.app/dashboard)
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your GitHub repository
4. Railway will auto-deploy

## 🔧 Environment Variables Setup

**CRITICAL**: Add these in Railway dashboard before deployment:

```bash
# Core API Keys
GROQ_API_KEY=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
RUNWAYML_API_KEY=key_2154d202435a6b1b8d6d887241a4e25ccade366566db56b7de2fe2aa2c133a41ee92654206db5d43b127b448e06db7774fb2625e06d35745e2ab808c11f761d4
GEMINI_API_KEY=AIzaSyD36dRBkEZUyCpDHLxTVuMO4P98SsYjkbc

# Authentication
SUPABASE_URL=https://tgjuxfndmuxwzloxezev.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnanV4Zm5kbXV4d3psb3hlemV2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEzMjkyNzEsImV4cCI6MjA2NjkwNTI3MX0.RXU5k9AGfddAvI8Rq6eUqi02suwPDPIRSWVb1eil0rA
SUPABASE_JWT_SECRET=VQnWJiGtGd2YrKdkAVnVONKHGLmJJsrNkqQhJKGfTXyVoMgQFNiNFLfXjHxQSVJmZgJlGgGhWpZrVvNhQqMfXjKrJpQnGmXhJmKzRrVnSlQhPkLlJrKzVgXsNsJkMhFzVxNxTjRmKcNzNnJkRlQfTwVmPkLzGrQnVvJpMrJzHgQrJfVvKlPrQmNmJhKhNrQxJzVjVpJyKlNhVnJzMhGhVrJzRrJyTvJhLlGmJfVhJsKlQfVxJrKzNzJhNmJz

# Storage
CLOUDFLARE_ACCOUNT_ID=69317cc9622018bb255db5a590d143c2
R2_ACCESS_KEY_ID=7804ed0f387a54af1eafbe2659c062f7
R2_SECRET_ACCESS_KEY=c94fe3a0d93c4594c8891b4f7fc54e5f26c76231972d8a4d0d8260bb6da61788
R2_BUCKET_NAME=video-generation-storage

# Optional
ELEVENLABS_API_KEY=sk_613429b69a534539f725091aab14705a535bbeeeb6f52133
```

## 🗄️ Add PostgreSQL Database

1. In Railway dashboard → "New Service" → "PostgreSQL"
2. Railway will auto-generate `DATABASE_URL`
3. No manual configuration needed

## 🚨 Common Deployment Errors & Fixes

### Error: "Build failed"
**Fix**: Check if `requirements.txt` is in the correct location
```bash
# Should be at: /app/backend/requirements.txt
ls -la /app/backend/requirements.txt
```

### Error: "Module not found"
**Fix**: Update the start command in `railway.json`:
```json
{
  "deploy": {
    "startCommand": "cd backend && gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --host 0.0.0.0 --port $PORT"
  }
}
```

### Error: "Port binding failed"
**Fix**: Ensure server.py uses PORT environment variable:
```python
port = int(os.environ.get("PORT", 8001))
uvicorn.run(app, host="0.0.0.0", port=port)
```

### Error: "Database connection failed"
**Fix**: 
1. Add PostgreSQL service in Railway
2. Verify DATABASE_URL is auto-generated
3. Check database initialization in startup

### Error: "Storage service unavailable"
**Fix**: Verify Cloudflare R2 credentials are correct:
```bash
# Test R2 connection endpoint after deployment
curl https://your-app.railway.app/api/storage/status
```

## 🔍 Verify Deployment

After deployment, test these endpoints:

1. **Health Check**
   ```bash
   curl https://your-app.railway.app/api/storage/status
   ```

2. **Database Status**
   ```bash
   curl https://your-app.railway.app/api/database/status
   ```

3. **Create Project Test**
   ```bash
   curl -X POST https://your-app.railway.app/api/projects \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test-user"}'
   ```

## 📊 Monitor Deployment

1. **View Logs**: Railway dashboard → Project → Deployments → View Logs
2. **Check Metrics**: Monitor CPU, Memory, Response times
3. **Set Alerts**: Configure notifications for failures

## 🆘 If Still Having Issues

1. **Check Railway Logs** for specific error messages
2. **Verify Environment Variables** are all set correctly
3. **Test Locally** with same environment variables
4. **Check API Keys** are valid and have correct permissions

## 🎯 Success Indicators

✅ Deployment shows "Running"
✅ Health check returns 200 OK
✅ No errors in logs
✅ Database connected
✅ Storage service active

Your AI Video Generation Platform should now be live on Railway! 🚀