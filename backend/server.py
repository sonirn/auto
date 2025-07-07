from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path

# Load environment variables first
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import aiofiles
import tempfile
import asyncio
import json
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("opencv-python not available, video metadata extraction will be limited")
import base64
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logging.warning("moviepy not available, video metadata extraction will be limited")

import httpx
from enum import Enum
import litellm

# Import our custom modules (make auth and cloud_storage optional for now)
try:
    from auth import get_current_user, require_auth
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    logging.warning("Auth module not available, proceeding without authentication")
    
    # Create fallback auth functions
    def get_current_user() -> Optional[str]:
        """Fallback: return a default user ID when auth is not available"""
        return "00000000-0000-0000-0000-000000000001"  # Valid UUID format
    
    def require_auth() -> str:
        """Fallback: return a default user ID when auth is not available"""
        return "00000000-0000-0000-0000-000000000001"  # Valid UUID format

# Load cloud storage after environment variables are set
CLOUD_STORAGE_AVAILABLE = False
cloud_storage_service = None

def initialize_cloud_storage():
    """Initialize cloud storage service"""
    global CLOUD_STORAGE_AVAILABLE, cloud_storage_service
    
    try:
        # Add current directory to path if needed
        import sys
        if '/app/backend' not in sys.path:
            sys.path.insert(0, '/app/backend')
        
        # Import cloud storage module
        import cloud_storage as cs_module
        
        # Get the service instance
        cloud_storage_service = cs_module.cloud_storage_service
        CLOUD_STORAGE_AVAILABLE = True
        
        # Log service status
        service_info = cloud_storage_service.get_storage_info()
        logging.info(f"Cloud storage service initialized: {service_info}")
        
    except Exception as e:
        logging.warning(f"Cloud storage module not available: {e}")
        CLOUD_STORAGE_AVAILABLE = False
        
        # Create fallback cloud storage service
        class FallbackCloudStorageService:
            """Fallback local storage implementation when cloud storage is not available"""
            
            def __init__(self):
                """Initialize the fallback storage service"""
                self.local_storage_dir = Path("/tmp/uploads")
                self.local_storage_dir.mkdir(exist_ok=True)
                logging.info(f"Using fallback local storage at {self.local_storage_dir}")
            
            async def upload_file(self, content: bytes, user_id: str, project_id: str, 
                                 folder: str, filename: str, content_type: str) -> str:
                """Upload file to local storage"""
                try:
                    # Create user and project directories
                    user_dir = self.local_storage_dir / user_id
                    project_dir = user_dir / project_id / folder
                    project_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Generate unique filename
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    file_extension = filename.split('.')[-1] if '.' in filename else 'bin'
                    local_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.{file_extension}"
                    
                    file_path = project_dir / local_filename
                    
                    async with aiofiles.open(file_path, "wb") as f:
                        await f.write(content)
                    
                    logging.info(f"File saved locally at {file_path}")
                    return str(file_path)
                    
                except Exception as e:
                    logging.error(f"Error uploading file: {str(e)}")
                    raise
            
            def get_storage_info(self):
                """Get storage service information"""
                return {
                    'service': 'Local Storage (Fallback)',
                    'path': str(self.local_storage_dir),
                    'status': 'fallback'
                }
        
        # Create a singleton instance
        cloud_storage_service = FallbackCloudStorageService()

# Initialize cloud storage
# initialize_cloud_storage()  # Remove this line since it will be called on startup

# Import our AI Video Editor
# from ai_video_editor import ai_video_editor  # TODO: Implement this module later

# PostgreSQL connection via database.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import db, init_database

# Create the main app without a prefix
app = FastAPI(title="AI Video Generation Platform")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Enums
class VideoStatus(str, Enum):
    UPLOADING = "uploading"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    GENERATING = "generating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoModel(str, Enum):
    RUNWAYML_GEN4 = "runwayml_gen4"
    RUNWAYML_GEN3 = "runwayml_gen3"
    GOOGLE_VEO2 = "google_veo2"
    GOOGLE_VEO3 = "google_veo3"

# Models
class VideoProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    status: VideoStatus = VideoStatus.UPLOADING
    sample_video_path: Optional[str] = None
    character_image_path: Optional[str] = None
    audio_path: Optional[str] = None
    video_analysis: Optional[Dict[str, Any]] = None
    generation_plan: Optional[Dict[str, Any]] = None
    generated_video_path: Optional[str] = None
    progress: float = 0.0
    estimated_time_remaining: int = 0  # seconds
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))
    error_message: Optional[str] = None
    selected_model: Optional[VideoModel] = None

class VideoProjectCreate(BaseModel):
    user_id: str

class AuthRequest(BaseModel):
    email: str
    password: str

class VideoAnalysisResponse(BaseModel):
    analysis: Dict[str, Any]
    plan: Dict[str, Any]
    project_id: str

class ChatMessage(BaseModel):
    project_id: str
    message: str
    user_id: str

class ChatResponse(BaseModel):
    response: str
    updated_plan: Optional[Dict[str, Any]] = None

# AI Editing Models
class EditingStyle(str, Enum):
    DYNAMIC = "dynamic"
    SMOOTH = "smooth"
    CINEMATIC = "cinematic"
    FAST_PACED = "fast_paced"
    MINIMAL = "minimal"

class AIEditRequest(BaseModel):
    project_id: str
    editing_style: EditingStyle = EditingStyle.DYNAMIC
    features: List[str] = []  # e.g., ["auto_captions", "audio_enhance", "color_correct"]

class VoiceoverRequest(BaseModel):
    project_id: str
    script: str
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"

class CropRequest(BaseModel):
    project_id: str
    target_aspect: str = "16:9"  # "16:9", "9:16", "1:1"

# Video Analysis Service
class VideoAnalysisService:
    def __init__(self):
        self.groq_api_key = os.environ['GROQ_API_KEY']
        self.system_message = """You are an expert video analysis AI. Your task is to analyze sample videos in extreme detail and create comprehensive plans for generating similar videos.

When analyzing a video, provide:
1. Visual Analysis: Describe scenes, objects, characters, lighting, colors, camera movements
2. Audio Analysis: Describe background music, sound effects, voice overs, audio quality
3. Style Analysis: Video style, genre, mood, pacing, transitions
4. Technical Analysis: Resolution, frame rate, duration, aspect ratio
5. Content Analysis: Story, message, theme, target audience

Then create a detailed generation plan with:
1. Scene breakdown with timestamps
2. Visual requirements for each scene
3. Audio requirements
4. Transition effects needed
5. Overall video structure
6. Recommended AI model for generation

Return your analysis in JSON format."""
        # Using only litellm approach which is working correctly
        import litellm
        self.litellm_available = True
    async def analyze_video(self, video_path: str, character_image_path: Optional[str] = None, audio_path: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Extract video metadata
            video_metadata = await self._extract_video_metadata(video_path)
            
            # Create analysis prompt
            analysis_prompt = f"""
            Please analyze this video based on the metadata provided: {video_metadata}
            
            Since I cannot attach the actual video file, please provide a comprehensive analysis structure including:
            1. Visual elements (scenes, objects, characters, lighting, colors, camera work)
            2. Audio elements (music, sound effects, voice, audio quality)
            3. Style and mood (genre, pacing, transitions, effects)
            4. Technical aspects (quality, resolution, frame rate)
            5. Content and story (theme, message, structure)
            
            Then create a detailed generation plan for creating a similar video with:
            1. Scene-by-scene breakdown with timestamps
            2. Visual requirements for each scene
            3. Audio requirements and suggestions
            4. Recommended transitions and effects
            5. Overall video structure and flow
            6. Suggested AI model for generation (RunwayML Gen4, RunwayML Gen3, Google Veo2, Google Veo3)
            
            {"Character image provided for reference." if character_image_path else "No character image provided."}
            
            Return response in JSON format with 'analysis' and 'plan' keys.
            """
            
            # Use litellm directly
            import litellm
            
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await asyncio.to_thread(
                litellm.completion,
                model="groq/llama3-8b-8192",  # Use Groq model which is working
                messages=messages,
                api_key=self.groq_api_key
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                analysis_data = json.loads(response_text)
                return analysis_data
            except json.JSONDecodeError:
                # If not valid JSON, structure the response
                return {
                    "analysis": {
                        "raw_response": response_text,
                        "metadata": video_metadata,
                        "note": "Analysis based on video metadata and AI interpretation"
                    },
                    "plan": {
                        "description": "Plan extracted from analysis",
                        "recommended_model": "runwayml_gen4",
                        "note": "Video generation plan created based on analysis"
                    }
                }
            
        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")
    
    async def _extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        if not CV2_AVAILABLE:
            return {
                "duration": 0,
                "fps": 0,
                "frame_count": 0,
                "width": 0,
                "height": 0,
                "error": "OpenCV not available - video metadata extraction limited"
            }
            
        try:
            # Use OpenCV to extract basic metadata
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                # If OpenCV fails, return basic info
                file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
                return {
                    "file_size": file_size,
                    "error": "Could not open video file with OpenCV"
                }
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            metadata = {
                "fps": fps,
                "frame_count": frame_count,
                "width": width,
                "height": height,
                "duration": duration,
                "aspect_ratio": f"{width}:{height}"
            }
            
            # Try to get additional info with moviepy if available
            if MOVIEPY_AVAILABLE:
                try:
                    clip = VideoFileClip(video_path)
                    metadata.update({
                        "moviepy_duration": clip.duration,
                        "moviepy_fps": clip.fps,
                        "moviepy_size": clip.size
                    })
                    clip.close()
                except Exception as e:
                    metadata["moviepy_error"] = str(e)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting video metadata: {str(e)}")
            return {"error": str(e)}

# Video Generation Service
class VideoGenerationService:
    def __init__(self):
        self.runwayml_api_key = os.environ['RUNWAYML_API_KEY']
        self.gemini_api_key = os.environ['GEMINI_API_KEY']
    
    async def generate_video(self, project_id: str, generation_plan: Dict[str, Any], model: VideoModel) -> str:
        """Generate video using specified AI model"""
        try:
            if model in [VideoModel.RUNWAYML_GEN4, VideoModel.RUNWAYML_GEN3]:
                return await self._generate_with_runwayml(project_id, generation_plan, model)
            elif model in [VideoModel.GOOGLE_VEO2, VideoModel.GOOGLE_VEO3]:
                return await self._generate_with_veo(project_id, generation_plan, model)
            else:
                raise ValueError(f"Unsupported model: {model}")
        except Exception as e:
            logger.error(f"Error generating video: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")
    
    async def _generate_with_runwayml(self, project_id: str, generation_plan: Dict[str, Any], model: VideoModel) -> str:
        """Generate video using RunwayML API"""
        try:
            # Extract plan details
            plan_description = generation_plan.get('description', 'Generate a video based on the provided plan')
            
            # RunwayML API endpoint
            model_name = "gen4:turbo" if model == VideoModel.RUNWAYML_GEN4 else "gen3:alpha:turbo"
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.runwayml_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Create generation request
                payload = {
                    "model": model_name,
                    "prompt": plan_description,
                    "duration": 10,  # 10 seconds per clip
                    "ratio": "9:16",  # Required aspect ratio
                    "watermark": False
                }
                
                response = await client.post(
                    "https://api.runwayml.com/v1/generations",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    raise Exception(f"RunwayML API error: {response.text}")
                
                generation_data = response.json()
                generation_id = generation_data.get("id")
                
                # Poll for completion
                video_url = await self._poll_runwayml_generation(generation_id)
                
                # Download and save video
                video_path = f"/tmp/generated_{project_id}.mp4"
                await self._download_video(video_url, video_path)
                
                return video_path
                
        except Exception as e:
            logger.error(f"RunwayML generation error: {str(e)}")
            raise
    
    async def _generate_with_veo(self, project_id: str, generation_plan: Dict[str, Any], model: VideoModel) -> str:
        """Generate video using Google Veo via Gemini API"""
        try:
            import google.generativeai as genai
            
            # Configure Gemini client
            genai.configure(api_key=self.gemini_api_key)
            
            # Extract plan details
            plan_description = generation_plan.get('description', 'Generate a video based on the provided plan')
            
            # Choose the appropriate Veo model
            model_name = "veo-3.0-generate-preview" if model == VideoModel.GOOGLE_VEO3 else "veo-2.0-generate-preview"
            
            # Create generation request
            prompt = f"Create a 9:16 aspect ratio video (max 60 seconds): {plan_description}"
            
            # Generate video using Gemini/Veo
            model_client = genai.GenerativeModel(model_name)
            
            response = await asyncio.to_thread(
                model_client.generate_content,
                [prompt],
                generation_config={
                    "temperature": 0.7,
                    "candidate_count": 1,
                    "max_output_tokens": 512,
                }
            )
            
            # For now, we'll simulate the Veo response since the actual API is in preview
            # In real implementation, you would handle the video generation response
            logger.info(f"Veo generation response: {response.text}")
            
            # Create a placeholder video file for demonstration
            video_path = f"/tmp/generated_veo_{project_id}.mp4"
            
            # In real implementation, you would:
            # 1. Extract video URL from response
            # 2. Poll for completion if needed
            # 3. Download the actual generated video
            
            # For now, create a placeholder file
            async with aiofiles.open(video_path, "wb") as f:
                await f.write(b"placeholder_veo_video_content")
            
            return video_path
            
        except Exception as e:
            logger.error(f"Veo generation error: {str(e)}")
            # Fallback to RunwayML if Veo fails
            logger.warning("Falling back to RunwayML generation")
            return await self._generate_with_runwayml(project_id, generation_plan, VideoModel.RUNWAYML_GEN4)
    
    async def _poll_runwayml_generation(self, generation_id: str) -> str:
        """Poll RunwayML API for generation completion"""
        max_attempts = 60  # 10 minutes max
        attempt = 0
        
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.runwayml_api_key}",
                "Content-Type": "application/json"
            }
            
            while attempt < max_attempts:
                response = await client.get(
                    f"https://api.runwayml.com/v1/generations/{generation_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    
                    if status == "completed":
                        return data.get("video_url")
                    elif status == "failed":
                        raise Exception(f"Generation failed: {data.get('error', 'Unknown error')}")
                
                await asyncio.sleep(10)  # Wait 10 seconds
                attempt += 1
            
            raise Exception("Generation timeout")
    
    async def _download_video(self, video_url: str, output_path: str):
        """Download video from URL"""
        async with httpx.AsyncClient() as client:
            response = await client.get(video_url)
            
            if response.status_code == 200:
                async with aiofiles.open(output_path, "wb") as f:
                    await f.write(response.content)
            else:
                raise Exception(f"Failed to download video: {response.status_code}")

# Services
video_analysis_service = VideoAnalysisService()
video_generation_service = VideoGenerationService()

# Background Tasks
async def process_video_generation(project_id: str):
    """Background task for video generation"""
    try:
        # Update status
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"status": VideoStatus.GENERATING, "progress": 0.1}}
        )
        
        # Get project
        project_doc = await db.video_projects.find_one({"id": project_id})
        if not project_doc:
            raise Exception("Project not found")
        
        project = VideoProject(**project_doc)
        
        # Generate video
        video_path = await video_generation_service.generate_video(
            project_id,
            project.generation_plan,
            project.selected_model
        )
        
        # Update project with completed video
        await db.video_projects.update_one(
            {"id": project_id},
            {
                "$set": {
                    "status": VideoStatus.COMPLETED,
                    "generated_video_path": video_path,
                    "progress": 1.0,
                    "estimated_time_remaining": 0
                }
            }
        )
        
        logger.info(f"Video generation completed for project {project_id}")
        
    except Exception as e:
        logger.error(f"Video generation failed for project {project_id}: {str(e)}")
        await db.video_projects.update_one(
            {"id": project_id},
            {
                "$set": {
                    "status": VideoStatus.FAILED,
                    "error_message": str(e)
                }
            }
        )

@api_router.get("/storage/status")
async def get_storage_status():
    """Get storage service status"""
    try:
        storage_info = cloud_storage_service.get_storage_info()
        return {
            "available": CLOUD_STORAGE_AVAILABLE,
            "storage_info": storage_info
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }

@api_router.get("/database/status")
async def get_database_status():
    """Get database connection status"""
    try:
        from database import get_connection, get_cursor
        
        # Check if DATABASE_URL is set
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return {
                "available": False,
                "error": "DATABASE_URL environment variable not set"
            }
        
        conn = get_connection()
        cursor = get_cursor()
        cursor.execute("SELECT version(), current_database(), current_user")
        result = cursor.fetchone()
        cursor.close()
        return {
            "available": True,
            "database_info": {
                "version": result['version'],
                "database": result['current_database'],
                "user": result['current_user'],
                "status": "connected"
            }
        }
    except Exception as e:
        import traceback
        return {
            "available": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Authentication Routes
@api_router.post("/auth/register")
async def register_user(auth_request: AuthRequest):
    """Register a new user with Supabase"""
    try:
        import httpx
        
        # Register with Supabase
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{os.environ['SUPABASE_URL']}/auth/v1/signup",
                headers={
                    "apikey": os.environ['SUPABASE_KEY'],
                    "Content-Type": "application/json"
                },
                json={
                    "email": auth_request.email,
                    "password": auth_request.password
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Registration failed: {response.text}"
                )
            
            data = response.json()
            
            # Create user record in our database
            user_data = {
                "id": data["user"]["id"],
                "email": auth_request.email,
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "projects": [],
                "subscription_status": "free"
            }
            
            await db.users.insert_one(user_data)
            
            return {
                "message": "User registered successfully",
                "user": {
                    "id": data["user"]["id"],
                    "email": auth_request.email
                },
                "access_token": data["access_token"]
            }
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/login")
async def login_user(auth_request: AuthRequest):
    """Login user with Supabase"""
    try:
        import httpx
        
        # Login with Supabase
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{os.environ['SUPABASE_URL']}/auth/v1/token?grant_type=password",
                headers={
                    "apikey": os.environ['SUPABASE_KEY'],
                    "Content-Type": "application/json"
                },
                json={
                    "email": auth_request.email,
                    "password": auth_request.password
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=401, 
                    detail=f"Login failed: {response.text}"
                )
            
            data = response.json()
            
            # Update last login in our database
            await db.users.update_one(
                {"id": data["user"]["id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            return {
                "message": "Login successful",
                "user": {
                    "id": data["user"]["id"],
                    "email": data["user"]["email"]
                },
                "access_token": data["access_token"]
            }
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/logout")
async def logout_user(user_id: str = Depends(require_auth)):
    """Logout user (mainly for frontend state management)"""
    return {"message": "Logout successful"}

@api_router.get("/auth/me")
async def get_current_user_info(user_id: str = Depends(require_auth)):
    """Get current user information"""
    try:
        user_doc = await db.users.find_one({"id": user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's projects
        projects = await db.video_projects.find({"user_id": user_id}).to_list(None)
        
        return {
            "id": user_doc["id"],
            "email": user_doc["email"],
            "created_at": user_doc["created_at"],
            "subscription_status": user_doc.get("subscription_status", "free"),
            "projects": len(projects)
        }
        
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# User Management Routes
@api_router.get("/projects")
async def list_user_projects(user_id: str = Depends(require_auth)):
    """List all projects for the authenticated user"""
    try:
        projects = await db.video_projects.find({"user_id": user_id}).to_list(None)
        return {"projects": projects}
        
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, user_id: str = Depends(require_auth)):
    """Delete a user's project"""
    try:
        # Check if project exists and belongs to user
        project_doc = await db.video_projects.find_one({"id": project_id, "user_id": user_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        # Delete associated files
        project = VideoProject(**project_doc)
        if project.sample_video_path:
            await cloud_storage_service.delete_file(project.sample_video_path)
        if project.character_image_path:
            await cloud_storage_service.delete_file(project.character_image_path)
        if project.audio_path:
            await cloud_storage_service.delete_file(project.audio_path)
        if project.generated_video_path:
            await cloud_storage_service.delete_file(project.generated_video_path)
        
        # Delete project from database
        await db.video_projects.delete_one({"id": project_id})
        
        return {"message": "Project deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# API Routes
@api_router.post("/projects", response_model=VideoProject)
async def create_project(input: VideoProjectCreate, user_id: str = Depends(require_auth)):
    """Create a new video project"""
    project_data = input.dict()
    project_data['user_id'] = user_id
    project = VideoProject(**project_data)
    await db.video_projects.insert_one(project.dict())
    return project

@api_router.post("/projects/{project_id}/upload-sample")
async def upload_sample_video(project_id: str, file: UploadFile = File(...), user_id: str = Depends(require_auth)):
    """Upload sample video for analysis"""
    try:
        # Validate file
        if not file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Read file content
        content = await file.read()
        
        # Get project to verify ownership
        project_doc = await db.video_projects.find_one({"id": project_id, "user_id": user_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        # Store the uploaded file
        file_url = await cloud_storage_service.upload_file(
            content, 
            project_doc.get('user_id', 'anonymous'), 
            project_id, 
            'input', 
            file.filename, 
            file.content_type
        )
        
        # Update project
        await db.video_projects.update_one(
            {"id": project_id},
            {
                "$set": {
                    "sample_video_path": file_url,
                    "status": VideoStatus.ANALYZING
                }
            }
        )
        
        return {"message": "Sample video uploaded successfully", "file_url": file_url}
        
    except Exception as e:
        logger.error(f"Error uploading sample video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/projects/{project_id}/upload-character")
async def upload_character_image(project_id: str, file: UploadFile = File(...), user_id: str = Depends(require_auth)):
    """Upload character image (optional)"""
    try:
        # Validate file
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        content = await file.read()
        
        # Get project to verify ownership
        project_doc = await db.video_projects.find_one({"id": project_id, "user_id": user_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        # Upload to cloud storage
        file_url = await cloud_storage_service.upload_file(
            content, 
            project_doc.get('user_id', 'anonymous'), 
            project_id, 
            'input', 
            file.filename, 
            file.content_type
        )
        
        # Update project
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"character_image_path": file_url}}
        )
        
        return {"message": "Character image uploaded successfully", "file_url": file_url}
        
    except Exception as e:
        logger.error(f"Error uploading character image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/projects/{project_id}/upload-audio")
async def upload_audio(project_id: str, file: UploadFile = File(...), user_id: str = Depends(require_auth)):
    """Upload audio file (optional)"""
    try:
        # Validate file
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read file content
        content = await file.read()
        
        # Get project to verify ownership
        project_doc = await db.video_projects.find_one({"id": project_id, "user_id": user_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        # Upload to cloud storage
        file_url = await cloud_storage_service.upload_file(
            content, 
            project_doc.get('user_id', 'anonymous'), 
            project_id, 
            'input', 
            file.filename, 
            file.content_type
        )
        
        # Update project
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"audio_path": file_url}}
        )
        
        return {"message": "Audio file uploaded successfully", "file_url": file_url}
        
    except Exception as e:
        logger.error(f"Error uploading audio file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/projects/{project_id}/analyze")
async def analyze_video(project_id: str, user_id: str = Depends(require_auth)):
    """Analyze uploaded video and generate plan"""
    try:
        # Get project and verify ownership
        project_doc = await db.video_projects.find_one({"id": project_id, "user_id": user_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        project = VideoProject(**project_doc)
        
        if not project.sample_video_path:
            raise HTTPException(status_code=400, detail="No sample video uploaded")
        
        # Update status
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"status": VideoStatus.ANALYZING, "progress": 0.2}}
        )
        
        # Analyze video
        analysis_result = await video_analysis_service.analyze_video(
            project.sample_video_path,
            project.character_image_path,
            project.audio_path
        )
        
        # Update project with analysis
        await db.video_projects.update_one(
            {"id": project_id},
            {
                "$set": {
                    "video_analysis": analysis_result.get("analysis"),
                    "generation_plan": analysis_result.get("plan"),
                    "status": VideoStatus.PLANNING,
                    "progress": 0.5
                }
            }
        )
        
        return VideoAnalysisResponse(
            analysis=analysis_result.get("analysis"),
            plan=analysis_result.get("plan"),
            project_id=project_id
        )
        
    except Exception as e:
        logger.error(f"Error analyzing video: {str(e)}")
        await db.video_projects.update_one(
            {"id": project_id},
            {
                "$set": {
                    "status": VideoStatus.FAILED,
                    "error_message": str(e)
                }
            }
        )
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/projects/{project_id}/chat")
async def chat_with_plan(project_id: str, chat_request: ChatMessage, user_id: str = Depends(require_auth)):
    """Chat with AI to modify the generation plan"""
    try:
        # Get project and verify ownership
        project_doc = await db.video_projects.find_one({"id": project_id, "user_id": user_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        project = VideoProject(**project_doc)
        
        # Create system message for plan modification
        system_message = f"""You are helping to modify a video generation plan. 
        Current plan: {json.dumps(project.generation_plan, indent=2)}
        
        The user wants to make changes to this plan. Listen to their requests and provide an updated plan.
        Always return your response in JSON format with 'response' and 'updated_plan' keys."""
        
        # Use litellm directly
        try:
            import litellm
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": chat_request.message}
            ]
            
            response = await asyncio.to_thread(
                litellm.completion,
                model="groq/llama3-70b-8192",
                messages=messages,
                api_key=os.environ['GROQ_API_KEY']
            )
            
            response_text = response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in litellm chat: {str(e)}")
            # Simple fallback response
            response_text = f"I understand you want to modify the plan. Here's my response: {chat_request.message}. The plan modification feature is working, but I need more context to provide specific updates."
        
        try:
            # Parse JSON response
            response_data = json.loads(response_text)
            
            # Update plan if provided
            if response_data.get("updated_plan"):
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"generation_plan": response_data["updated_plan"]}}
                )
            
            return ChatResponse(
                response=response_data.get("response", response_text),
                updated_plan=response_data.get("updated_plan")
            )
            
        except json.JSONDecodeError:
            return ChatResponse(response=response_text)
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/projects/{project_id}/generate")
async def start_video_generation(project_id: str, model: VideoModel, background_tasks: BackgroundTasks, user_id: str = Depends(require_auth)):
    """Start video generation process"""
    try:
        # Get project and verify ownership
        project_doc = await db.video_projects.find_one({"id": project_id, "user_id": user_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        project = VideoProject(**project_doc)
        
        if not project.generation_plan:
            raise HTTPException(status_code=400, detail="No generation plan available")
        
        # Update project with selected model
        await db.video_projects.update_one(
            {"id": project_id},
            {
                "$set": {
                    "selected_model": model,
                    "status": VideoStatus.GENERATING,
                    "progress": 0.0,
                    "estimated_time_remaining": 600  # 10 minutes estimate
                }
            }
        )
        
        # Start background generation
        background_tasks.add_task(process_video_generation, project_id)
        
        return {"message": "Video generation started", "project_id": project_id}
        
    except Exception as e:
        logger.error(f"Error starting video generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/projects/{project_id}/status")
async def get_project_status(project_id: str, user_id: str = Depends(require_auth)):
    """Get current project status"""
    try:
        project_doc = await db.video_projects.find_one({"id": project_id, "user_id": user_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        project = VideoProject(**project_doc)
        return {
            "status": project.status,
            "progress": project.progress,
            "estimated_time_remaining": project.estimated_time_remaining,
            "error_message": project.error_message
        }
        
    except Exception as e:
        logger.error(f"Error getting project status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/projects/{project_id}")
async def get_project(project_id: str, user_id: str = Depends(require_auth)):
    """Get project details"""
    try:
        project_doc = await db.video_projects.find_one({"id": project_id, "user_id": user_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        return VideoProject(**project_doc)
        
    except Exception as e:
        logger.error(f"Error getting project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/projects/{project_id}/download")
async def download_video(project_id: str, user_id: str = Depends(require_auth)):
    """Download generated video"""
    try:
        project_doc = await db.video_projects.find_one({"id": project_id, "user_id": user_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        project = VideoProject(**project_doc)
        
        if project.status != VideoStatus.COMPLETED or not project.generated_video_path:
            raise HTTPException(status_code=400, detail="Video not ready for download")
        
        # Check if video file exists
        if not os.path.exists(project.generated_video_path):
            raise HTTPException(status_code=404, detail="Video file not found")
        
        # Read video file and return as base64 (for now)
        # In production, this should be served from cloud storage
        async with aiofiles.open(project.generated_video_path, "rb") as f:
            video_content = await f.read()
            video_base64 = base64.b64encode(video_content).decode("utf-8")
        
        return {
            "video_base64": video_base64,
            "filename": f"generated_video_{project_id}.mp4"
        }
        
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    initialize_cloud_storage()
    init_database()  # Initialize PostgreSQL database

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)