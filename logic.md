# AI Video Generation Platform - Complete Logic Documentation

## 📋 Project Overview

This is a comprehensive AI-powered video generation platform that allows users to upload sample videos and generate similar content using multiple AI models. The system analyzes the sample video, creates a generation plan, and produces high-quality videos without watermarks.

## 🏗️ System Architecture

### Technology Stack
- **Frontend**: React.js with Tailwind CSS
- **Backend**: FastAPI with Python
- **Database**: MongoDB for project data
- **Authentication**: Supabase (to be implemented)
- **Storage**: Cloudflare R2 (to be implemented, currently local)
- **AI Models**: 
  - Groq LLM for video analysis
  - RunwayML Gen 4/3 for video generation
  - Google Veo 2/3 (to be implemented)
  - ElevenLabs for voice generation (to be implemented)
  - MMAudio for sound effects (to be implemented)

### Core Components
1. **File Upload System**
2. **Video Analysis Engine**
3. **AI Chat Interface**
4. **Video Generation Pipeline**
5. **Background Processing**
6. **Progress Tracking**
7. **User Authentication** (to be implemented)
8. **Cloud Storage** (to be implemented)

## 🔄 Complete Workflow Logic

### Phase 1: User Onboarding & File Upload
```
User Access → Simple Supabase Registration → File Upload Interface
```

#### 1.1 Authentication Flow (TO BE IMPLEMENTED)
- Simple sign-up with Supabase
- No OTP or complex auth required
- Generate unique user ID
- Store user session

#### 1.2 File Upload Process
- **Sample Video (Required)**: Max 60 seconds, 9:16 aspect ratio preferred
- **Character Image (Optional)**: For consistent character generation
- **Audio File (Optional)**: Custom audio track

#### 1.3 File Storage Logic
```
Current: Local storage (/tmp/uploads)
Target: Cloudflare R2 bucket with 7-day retention
```

### Phase 2: Video Analysis & Plan Generation
```
File Upload → Video Analysis → AI Plan Generation → User Review
```

#### 2.1 Video Analysis Pipeline
1. **Metadata Extraction**
   - Duration, resolution, frame rate
   - Audio properties
   - Technical specifications

2. **AI Analysis using Groq LLM**
   - Visual analysis (scenes, objects, lighting, colors)
   - Audio analysis (music, effects, voice)
   - Style analysis (genre, mood, pacing)
   - Content analysis (story, theme, message)

3. **Generation Plan Creation**
   - Scene breakdown with timestamps
   - Visual requirements per scene
   - Audio requirements
   - Transition effects
   - Recommended AI model selection

#### 2.2 Plan Review & Modification
- Display analysis results to user
- Interactive chat interface for plan modifications
- Regeneration option for new plans
- User confirmation before proceeding

### Phase 3: Video Generation Process
```
Plan Approval → Model Selection → Background Generation → Progress Tracking
```

#### 3.1 AI Model Selection Logic
- **RunwayML Gen 4 Turbo**: Latest, fastest (IMPLEMENTED)
- **RunwayML Gen 3 Alpha**: Stable, reliable (IMPLEMENTED)
- **Google Veo 2**: Advanced model (TO BE IMPLEMENTED)
- **Google Veo 3**: Latest Google model (TO BE IMPLEMENTED)

#### 3.2 Generation Pipeline
1. **Video Clip Generation**
   - Break plan into multiple clips
   - Generate each clip using selected AI model
   - Handle API rate limits with multiple keys

2. **Audio Processing** (TO BE IMPLEMENTED)
   - Use ElevenLabs for character voices
   - Use MMAudio for background music/effects
   - Combine custom audio if provided

3. **Video Editing & Combining** (TO BE IMPLEMENTED)
   - Combine individual clips
   - Add transitions and effects
   - Ensure 9:16 aspect ratio
   - Apply color correction and enhancement

#### 3.3 Background Processing
- Use FastAPI BackgroundTasks
- Continue processing even if user leaves
- Update progress in database
- Handle errors and retry logic

### Phase 4: Final Video Delivery
```
Generation Complete → Quality Check → Cloud Storage → User Download
```

#### 4.1 Video Quality Assurance
- Check final video meets requirements
- Ensure no watermarks or logos
- Verify aspect ratio (9:16)
- Confirm duration under 60 seconds

#### 4.2 Storage & Access Management
- Store final video in Cloudflare R2
- Set 7-day expiration
- Generate secure download link
- Track download attempts

## 📊 Database Schema

### MongoDB Collections

#### 1. video_projects
```json
{
  "_id": "project_uuid",
  "user_id": "user_uuid",
  "status": "uploading|analyzing|planning|generating|processing|completed|failed",
  "sample_video_path": "cloudflare_r2_url",
  "character_image_path": "cloudflare_r2_url",
  "audio_path": "cloudflare_r2_url",
  "video_analysis": {
    "visual_analysis": {},
    "audio_analysis": {},
    "style_analysis": {},
    "technical_specs": {}
  },
  "generation_plan": {
    "scenes": [],
    "audio_requirements": {},
    "recommended_model": "string",
    "editing_instructions": {}
  },
  "generated_video_path": "cloudflare_r2_url",
  "progress": 0.0,
  "estimated_time_remaining": 0,
  "created_at": "datetime",
  "expires_at": "datetime (7 days)",
  "error_message": "string",
  "selected_model": "enum",
  "chat_history": [],
  "download_count": 0
}
```

#### 2. users (TO BE IMPLEMENTED)
```json
{
  "_id": "user_uuid",
  "email": "string",
  "created_at": "datetime",
  "last_login": "datetime",
  "projects": [],
  "subscription_status": "free|premium"
}
```

#### 3. generation_jobs (TO BE IMPLEMENTED)
```json
{
  "_id": "job_uuid",
  "project_id": "string",
  "model_used": "string",
  "api_key_used": "string",
  "clips_generated": [],
  "processing_time": 0,
  "status": "pending|processing|completed|failed",
  "error_logs": []
}
```

## 🔌 API Endpoints

### Existing Endpoints
- `POST /api/projects` - Create new project
- `POST /api/projects/{id}/upload-sample` - Upload sample video
- `POST /api/projects/{id}/upload-character` - Upload character image
- `POST /api/projects/{id}/upload-audio` - Upload audio file
- `POST /api/projects/{id}/analyze` - Analyze video and create plan
- `POST /api/projects/{id}/chat` - Chat with AI for plan modifications
- `POST /api/projects/{id}/generate` - Start video generation
- `GET /api/projects/{id}/status` - Get project status
- `GET /api/projects/{id}` - Get project details
- `GET /api/projects/{id}/download` - Download generated video

### TO BE IMPLEMENTED Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `GET /api/projects` - List user projects
- `DELETE /api/projects/{id}` - Delete project
- `POST /api/projects/{id}/regenerate` - Regenerate video with new settings

## 🔧 AI Integration Logic

### 1. Video Analysis Service
```python
class VideoAnalysisService:
    def __init__(self):
        self.groq_api_key = os.environ['GROQ_API_KEY']
        self.model = "groq/llama3-8b-8192"
    
    async def analyze_video(self, video_path, character_image=None, audio_path=None):
        # Extract metadata using OpenCV/moviepy
        # Create comprehensive analysis prompt
        # Call Groq LLM for analysis
        # Parse and structure response
        # Return analysis and generation plan
```

### 2. Video Generation Service
```python
class VideoGenerationService:
    def __init__(self):
        self.runwayml_keys = [multiple_keys]  # Rotate keys for rate limits
        self.gemini_key = os.environ['GEMINI_API_KEY']
    
    async def generate_video(self, project_id, plan, model):
        # Route to appropriate model
        # Handle API rate limits
        # Generate multiple clips if needed
        # Poll for completion
        # Return generated video paths
```

### 3. Audio Processing Service (TO BE IMPLEMENTED)
```python
class AudioProcessingService:
    def __init__(self):
        self.elevenlabs_key = os.environ['ELEVENLABS_API_KEY']
        self.mmaudio_config = {}
    
    async def process_audio(self, plan, custom_audio=None):
        # Generate character voices with ElevenLabs
        # Add background music/effects with MMAudio
        # Sync audio with video timing
        # Return processed audio track
```

### 4. Video Editing Service (TO BE IMPLEMENTED)
```python
class VideoEditingService:
    def __init__(self):
        self.shotstack_key = os.environ['SHOTSTACK_API_KEY']
        self.mux_credentials = {}
    
    async def combine_clips(self, clips, transitions, effects):
        # Combine multiple video clips
        # Add transitions and effects
        # Ensure 9:16 aspect ratio
        # Apply color correction
        # Return final video
```

## 🗂️ File Storage Logic

### Current Implementation (Local Storage)
```
/tmp/uploads/
├── {project_id}_sample.mp4
├── {project_id}_character.jpg
├── {project_id}_audio.mp3
└── generated_{project_id}.mp4
```

### Target Implementation (Cloudflare R2)
```
Bucket: video-generation-storage
Structure:
├── users/{user_id}/
│   ├── projects/{project_id}/
│   │   ├── input/
│   │   │   ├── sample_video.mp4
│   │   │   ├── character_image.jpg
│   │   │   └── audio.mp3
│   │   ├── generated/
│   │   │   ├── clips/
│   │   │   │   ├── clip_01.mp4
│   │   │   │   └── clip_02.mp4
│   │   │   └── final_video.mp4
│   │   └── temp/
│   │       └── processing_files/
```

### Storage Management
- **Retention Policy**: 7 days for all files
- **Cleanup Job**: Daily cleanup of expired files
- **Access Control**: Signed URLs for secure access
- **Backup Strategy**: No backup needed (temporary files)

## ⚙️ Processing Pipeline

### 1. Upload Phase
```
User Upload → File Validation → Virus Scan → Cloud Storage → Database Update
```

### 2. Analysis Phase
```
File Retrieved → Metadata Extraction → AI Analysis → Plan Generation → User Display
```

### 3. Generation Phase
```
Plan Confirmed → Model Selection → Background Job → Multiple Clips → Progress Updates
```

### 4. Editing Phase (TO BE IMPLEMENTED)
```
Clips Generated → Audio Processing → Video Combining → Effects/Transitions → Final Video
```

### 5. Delivery Phase
```
Final Video → Quality Check → Cloud Storage → Download Link → User Notification
```

## 🔐 Security & Privacy

### Data Protection
- No personal data stored beyond email
- Videos automatically deleted after 7 days
- Secure file upload with validation
- API rate limiting and abuse prevention

### API Security
- JWT tokens for authentication
- CORS configuration
- Input validation and sanitization
- Error handling without data exposure

## 📱 Mobile Optimization

### Responsive Design
- Mobile-first approach
- Touch-friendly interface
- Optimized file upload for mobile
- Progressive loading for slow connections

### Performance Optimization
- Lazy loading of components
- Compressed images and videos
- CDN for static assets
- Efficient API calls

## 🚀 Scaling Considerations

### Horizontal Scaling
- Stateless backend services
- Queue-based job processing
- Load balancing for multiple instances
- Database sharding if needed

### Performance Optimization
- Redis caching for frequently accessed data
- CDN for video delivery
- Background job optimization
- API response compression

## 📊 Analytics & Monitoring

### Key Metrics (TO BE IMPLEMENTED)
- Video generation success rate
- Processing time per video
- User engagement metrics
- API performance metrics

### Error Tracking
- Comprehensive logging
- Error monitoring and alerting
- Performance monitoring
- User feedback collection

## 🔄 Deployment & CI/CD

### Current Setup
- Docker containerization
- Supervisor for process management
- Environment-based configuration
- Manual deployment

### Production Considerations
- Automated testing pipeline
- Staged deployments
- Health checks and monitoring
- Rollback procedures

## 📋 TODO List - Missing Features

### High Priority
1. **Supabase Authentication Integration**
2. **Cloudflare R2 Storage Implementation**
3. **7-day Access Limitation System**
4. **ElevenLabs Voice Generation**
5. **MMAudio Sound Effects**

### Medium Priority
6. **Google Veo 2/3 Integration**
7. **Video Editing & Combining**
8. **Advanced Audio Processing**
9. **User Project Management**

### Low Priority
10. **Analytics Dashboard**
11. **Advanced Error Handling**
12. **Performance Optimization**
13. **Admin Interface**

## 🎯 Success Criteria

### Technical Requirements
- ✅ Video generation working
- ✅ Mobile-responsive interface
- ✅ Background processing
- ❌ Cloud storage implementation
- ❌ User authentication
- ❌ Audio enhancement

### User Experience
- ✅ Intuitive upload interface
- ✅ Real-time progress tracking
- ✅ Chat-based plan modification
- ❌ Seamless audio integration
- ❌ Professional video quality

### Performance
- ✅ Fast video analysis
- ✅ Efficient API responses
- ❌ Optimized cloud storage
- ❌ Advanced caching

This logic document serves as the complete technical specification for the AI Video Generation Platform, covering all current implementations and future enhancements.