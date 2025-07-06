# AI Video Generation Platform - Vercel Deployment

This is a complete AI-powered video generation platform converted to work on Vercel's serverless infrastructure.

## 🚀 Features

- **Video Analysis**: AI-powered video analysis using Groq LLM
- **Video Generation**: Multiple AI models (RunwayML Gen 4/3, Google Veo)
- **Chat Interface**: AI-powered plan modifications
- **Cloud Storage**: Cloudflare R2 integration for file storage
- **Modern UI**: React with Tailwind CSS
- **Serverless**: Fully serverless using Vercel Functions

## 📁 Project Structure

```
/
├── api/                    # Vercel serverless functions
│   ├── projects.py         # Project management
│   ├── upload-sample.py    # Video upload
│   ├── upload-character.py # Character image upload
│   ├── upload-audio.py     # Audio upload
│   ├── analyze.py          # Video analysis
│   ├── chat.py             # AI chat interface
│   ├── generate.py         # Video generation
│   ├── status.py          # Project status
│   ├── download.py         # Video download
│   └── project-details.py  # Project details
├── lib/                    # Shared utilities
│   ├── database.py         # MongoDB integration
│   ├── cloud_storage.py    # Cloudflare R2 storage
│   ├── video_analysis.py   # Video analysis service
│   ├── video_generation.py # Video generation service
│   └── auth.py             # Authentication service
├── src/                    # React frontend
├── public/                 # Static assets
├── vercel.json             # Vercel configuration
├── requirements.txt        # Python dependencies
└── package.json            # Node.js dependencies
```

## 🔧 Environment Variables

Set these environment variables in your Vercel dashboard:

### Database
- `MONGO_URL` - MongoDB connection string
- `DB_NAME` - MongoDB database name

### AI Services
- `GROQ_API_KEY` - Groq API key for video analysis
- `RUNWAYML_API_KEY` - RunwayML API key for video generation
- `GEMINI_API_KEY` - Google Gemini API key
- `ELEVENLABS_API_KEY` - ElevenLabs API key (optional)

### Authentication
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `SUPABASE_JWT_SECRET` - Supabase JWT secret

### Cloud Storage
- `CLOUDFLARE_ACCOUNT_ID` - Cloudflare account ID
- `CLOUDFLARE_R2_ENDPOINT` - R2 endpoint URL
- `R2_ACCESS_KEY_ID` - R2 access key ID
- `R2_SECRET_ACCESS_KEY` - R2 secret access key
- `R2_BUCKET_NAME` - R2 bucket name

## 🚀 Deployment Steps

1. **Fork or Clone this repository**

2. **Connect to Vercel**
   ```bash
   npm install -g vercel
   vercel login
   vercel --prod
   ```

3. **Set Environment Variables**
   - Go to your Vercel dashboard
   - Navigate to Settings > Environment Variables
   - Add all the required environment variables listed above

4. **Deploy**
   ```bash
   vercel --prod
   ```

## 📱 API Endpoints

All API endpoints are available at `/api/`:

- `POST /api/projects` - Create new project
- `GET /api/projects` - List user projects
- `DELETE /api/projects?project_id=<id>` - Delete project
- `POST /api/upload-sample` - Upload sample video
- `POST /api/upload-character` - Upload character image
- `POST /api/upload-audio` - Upload audio file
- `POST /api/analyze` - Analyze video and create plan
- `POST /api/chat` - Chat with AI for plan modifications
- `POST /api/generate` - Start video generation
- `GET /api/status` - Get project status
- `GET /api/project-details` - Get project details
- `GET /api/download` - Download generated video

## 🔐 Authentication

The platform supports:
- Supabase authentication (production)
- Fallback authentication (development)

## 💾 Storage

Files are stored in Cloudflare R2 with:
- 7-day automatic expiration
- Structured organization: `users/{user_id}/projects/{project_id}/`
- Secure S3-compatible API access

## 🎥 Video Generation Models

Supported AI models:
- **RunwayML Gen 4 Turbo** (fastest, latest)
- **RunwayML Gen 3 Alpha** (stable, reliable)
- **Google Veo 2** (placeholder - implementation needed)
- **Google Veo 3** (placeholder - implementation needed)

## 🔄 Workflow

1. **Upload**: Sample video, character image (optional), audio (optional)
2. **Analysis**: AI analyzes video and creates generation plan
3. **Chat**: Modify plan through AI chat interface
4. **Generate**: Select AI model and start generation
5. **Download**: Get generated video as base64

## 🛠️ Development

To run locally:

```bash
# Install dependencies
yarn install

# Start development server
yarn start

# For API testing, you'll need to set up Vercel CLI
vercel dev
```

## 📊 Features Status

### ✅ Implemented
- Complete video upload system
- AI video analysis with Groq
- Interactive chat interface
- Video generation with RunwayML
- Cloud storage with Cloudflare R2
- Modern responsive UI
- Serverless architecture

### 🚧 To Be Implemented
- Google Veo integration
- ElevenLabs voice generation
- Multi-clip video editing
- User authentication (full Supabase)
- Analytics dashboard

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Search existing issues
3. Create a new issue with detailed information

---

**Note**: This platform requires valid API keys for AI services. Make sure to obtain proper credentials before deployment.
