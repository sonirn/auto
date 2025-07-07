# Railway Deployment Checklist

## ✅ Pre-Deployment Setup

### 1. Repository Setup
- [ ] Fork or clone this repository to your GitHub account
- [ ] Ensure all deployment files are present:
  - [ ] `Procfile`
  - [ ] `railway.json`
  - [ ] `nixpacks.toml`
  - [ ] `start.sh` (executable)
  - [ ] `backend/requirements.txt`

### 2. API Keys Required
- [ ] **GROQ_API_KEY** - Required for AI video analysis
- [ ] **RUNWAYML_API_KEY** - Required for video generation
- [ ] **GEMINI_API_KEY** - Required for video generation
- [ ] **SUPABASE_URL** - Required for authentication
- [ ] **SUPABASE_KEY** - Required for authentication
- [ ] **SUPABASE_JWT_SECRET** - Required for authentication
- [ ] **CLOUDFLARE_ACCOUNT_ID** - Required for file storage
- [ ] **R2_ACCESS_KEY_ID** - Required for file storage
- [ ] **R2_SECRET_ACCESS_KEY** - Required for file storage
- [ ] **R2_BUCKET_NAME** - Required for file storage
- [ ] **ELEVENLABS_API_KEY** - Optional for voice generation

## 🚀 Railway Deployment Steps

### Step 1: Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your forked repository

### Step 2: Configure Environment Variables
In Railway dashboard > Variables tab, add:

**Essential Variables:**
```
DATABASE_URL=<Railway will auto-generate if you add PostgreSQL service>
GROQ_API_KEY=<your-groq-api-key>
RUNWAYML_API_KEY=<your-runwayml-api-key>
GEMINI_API_KEY=<your-gemini-api-key>
SUPABASE_URL=<your-supabase-url>
SUPABASE_KEY=<your-supabase-key>
SUPABASE_JWT_SECRET=<your-supabase-jwt-secret>
CLOUDFLARE_ACCOUNT_ID=<your-cloudflare-account-id>
R2_ACCESS_KEY_ID=<your-r2-access-key>
R2_SECRET_ACCESS_KEY=<your-r2-secret-key>
R2_BUCKET_NAME=video-generation-storage
```

**Optional Variables:**
```
ELEVENLABS_API_KEY=<your-elevenlabs-key>
XAI_API_KEY=<your-xai-key>
AIML_API_KEY=<your-aiml-key>
MUX_TOKEN_ID=<your-mux-token>
MUX_TOKEN_SECRET=<your-mux-secret>
SHOTSTACK_API_KEY=<your-shotstack-key>
```

### Step 3: Add PostgreSQL Service
1. In Railway dashboard, click "New Service"
2. Select "PostgreSQL"
3. Railway will auto-generate DATABASE_URL
4. Copy the DATABASE_URL to your variables

### Step 4: Deploy
1. Railway will automatically deploy after adding variables
2. Monitor deployment in "Deployments" tab
3. Check logs for any errors

## 🔍 Post-Deployment Verification

### Health Checks
Test these endpoints after deployment:

1. **Storage Status**: `GET https://your-app.railway.app/api/storage/status`
   ```json
   {
     "available": true,
     "storage_info": {
       "service": "Cloudflare R2",
       "status": "connected"
     }
   }
   ```

2. **Database Status**: `GET https://your-app.railway.app/api/database/status`
   ```json
   {
     "available": true,
     "database_info": {
       "status": "connected"
     }
   }
   ```

### Functional Tests

1. **Create Project**: `POST /api/projects`
   ```bash
   curl -X POST https://your-app.railway.app/api/projects \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test-user"}'
   ```

2. **Upload Sample Video**: `POST /api/projects/{id}/upload-sample`
3. **Analyze Video**: `POST /api/projects/{id}/analyze`

## 🛠️ Troubleshooting

### Common Issues

**Deployment Fails**
- Check logs in Railway dashboard
- Verify all required environment variables are set
- Ensure `start.sh` has execute permissions

**Database Connection Errors**
- Verify PostgreSQL service is running
- Check DATABASE_URL format
- Ensure database initialization completed

**Storage Errors**
- Verify Cloudflare R2 credentials
- Check bucket exists and permissions
- Test R2 connection independently

**API Key Errors**
- Verify all required API keys are set
- Test keys independently
- Check key formats and permissions

### Debug Commands

```bash
# View deployment logs
railway logs

# Check environment variables
railway variables

# Connect to deployment
railway shell
```

## 📊 Performance Considerations

### Scaling
- Default: 4 Gunicorn workers
- Adjust workers based on traffic
- Monitor CPU and memory usage

### Database
- PostgreSQL auto-scaling on Railway
- Connection pooling enabled
- Monitor connection count

### Storage
- Cloudflare R2 for file storage
- 7-day automatic cleanup
- Global CDN for fast access

## 🔒 Security

### Environment Variables
- Never commit API keys to repository
- Use Railway's secure variable storage
- Rotate keys regularly

### Authentication
- Supabase JWT validation
- Secure endpoints with auth middleware
- CORS properly configured

## 📈 Monitoring

### Metrics to Watch
- Response times
- Error rates
- Database connections
- Storage usage
- API key usage limits

### Alerts
- Set up Railway alerts for:
  - High CPU usage
  - Memory limits
  - Error rates
  - Deployment failures

## ✅ Final Checklist

- [ ] Repository connected to Railway
- [ ] All environment variables configured
- [ ] PostgreSQL service added
- [ ] Deployment successful
- [ ] Health checks passing
- [ ] Basic API tests working
- [ ] Domain configured (optional)
- [ ] Monitoring set up
- [ ] Documentation updated

## 🎉 Success!

Your AI Video Generation Platform is now deployed on Railway!

**Next Steps:**
1. Share your deployed URL
2. Test all features thoroughly
3. Set up monitoring and alerts
4. Plan for production traffic
5. Consider custom domain setup

---

**Need Help?** Check the logs, review environment variables, and test API endpoints step by step.