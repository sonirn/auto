from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import aiofiles
import tempfile
import asyncio
import json
import cv2
import base64
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logging.warning("moviepy not available, video metadata extraction will be limited")

from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
import httpx
from enum import Enum

# Import our AI Video Editor
# from ai_video_editor import ai_video_editor  # TODO: Implement this module later

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
        self.llm_chat = LlmChat(
            api_key=os.environ['GEMINI_API_KEY'],
            session_id="video_analysis",
            system_message="""You are an expert video analysis AI. Your task is to analyze sample videos in extreme detail and create comprehensive plans for generating similar videos.

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

Return your analysis in JSON format.""",
            model="google/gemini-1.5-pro"  # Using format provider/model
        )
    
    async def analyze_video(self, video_path: str, character_image_path: Optional[str] = None, audio_path: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Extract video metadata
            video_metadata = await self._extract_video_metadata(video_path)
            
            # For now, let's test without file attachments to isolate the issue
            # TODO: Re-enable file attachments once provider issue is resolved
            
            # Create analysis prompt without file attachments
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
            
            # Send to LLM for analysis
            user_message = UserMessage(text=analysis_prompt)
            
            response = await self.llm_chat.send_message(user_message)
            
            # Parse JSON response
            try:
                analysis_data = json.loads(response)
                return analysis_data
            except json.JSONDecodeError:
                # If not valid JSON, structure the response
                return {
                    "analysis": {
                        "raw_response": response,
                        "metadata": video_metadata,
                        "note": "File attachments temporarily disabled - analysis based on metadata only"
                    },
                    "plan": {
                        "description": "Plan extracted from analysis",
                        "recommended_model": "runwayml_gen4",
                        "note": "This is a basic plan - will be enhanced once file analysis is working"
                    }
                }
            
        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")
    
    async def _extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
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
            # This is a placeholder implementation
            # Google Veo integration would require specific API calls
            raise NotImplementedError("Google Veo integration coming soon")
            
        except Exception as e:
            logger.error(f"Veo generation error: {str(e)}")
            raise
    
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

# API Routes
@api_router.post("/projects", response_model=VideoProject)
async def create_project(input: VideoProjectCreate):
    """Create a new video project"""
    project = VideoProject(**input.dict())
    await db.video_projects.insert_one(project.dict())
    return project

@api_router.post("/projects/{project_id}/upload-sample")
async def upload_sample_video(project_id: str, file: UploadFile = File(...)):
    """Upload sample video for analysis"""
    try:
        # Validate file
        if not file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Save uploaded file
        file_path = UPLOAD_DIR / f"{project_id}_sample.mp4"
        
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        # Update project
        await db.video_projects.update_one(
            {"id": project_id},
            {
                "$set": {
                    "sample_video_path": str(file_path),
                    "status": VideoStatus.ANALYZING
                }
            }
        )
        
        return {"message": "Sample video uploaded successfully"}
        
    except Exception as e:
        logger.error(f"Error uploading sample video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/projects/{project_id}/upload-character")
async def upload_character_image(project_id: str, file: UploadFile = File(...)):
    """Upload character image (optional)"""
    try:
        # Validate file
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save uploaded file
        file_path = UPLOAD_DIR / f"{project_id}_character.jpg"
        
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        # Update project
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"character_image_path": str(file_path)}}
        )
        
        return {"message": "Character image uploaded successfully"}
        
    except Exception as e:
        logger.error(f"Error uploading character image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/projects/{project_id}/upload-audio")
async def upload_audio(project_id: str, file: UploadFile = File(...)):
    """Upload audio file (optional)"""
    try:
        # Validate file
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Save uploaded file
        file_path = UPLOAD_DIR / f"{project_id}_audio.mp3"
        
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        # Update project
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"audio_path": str(file_path)}}
        )
        
        return {"message": "Audio file uploaded successfully"}
        
    except Exception as e:
        logger.error(f"Error uploading audio file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/projects/{project_id}/analyze")
async def analyze_video(project_id: str):
    """Analyze uploaded video and generate plan"""
    try:
        # Get project
        project_doc = await db.video_projects.find_one({"id": project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found")
        
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
async def chat_with_plan(project_id: str, chat_request: ChatMessage):
    """Chat with AI to modify the generation plan"""
    try:
        # Get project
        project_doc = await db.video_projects.find_one({"id": project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = VideoProject(**project_doc)
        
        # Create chat session for plan modification
        chat = LlmChat(
            api_key=os.environ['GROQ_API_KEY'],
            session_id=f"plan_modification_{project_id}",
            system_message=f"""You are helping to modify a video generation plan. 
            Current plan: {json.dumps(project.generation_plan, indent=2)}
            
            The user wants to make changes to this plan. Listen to their requests and provide an updated plan.
            Always return your response in JSON format with 'response' and 'updated_plan' keys."""
        ).with_model(provider="groq", model="llama3-70b-8192")  # Using Groq for chat
        
        # Send user message
        user_message = UserMessage(text=chat_request.message)
        response = await chat.send_message(user_message)
        
        try:
            # Parse JSON response
            response_data = json.loads(response)
            
            # Update plan if provided
            if response_data.get("updated_plan"):
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"generation_plan": response_data["updated_plan"]}}
                )
            
            return ChatResponse(
                response=response_data.get("response", response),
                updated_plan=response_data.get("updated_plan")
            )
            
        except json.JSONDecodeError:
            return ChatResponse(response=response)
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/projects/{project_id}/generate")
async def start_video_generation(project_id: str, model: VideoModel, background_tasks: BackgroundTasks):
    """Start video generation process"""
    try:
        # Get project
        project_doc = await db.video_projects.find_one({"id": project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found")
        
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
async def get_project_status(project_id: str):
    """Get current project status"""
    try:
        project_doc = await db.video_projects.find_one({"id": project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found")
        
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
async def get_project(project_id: str):
    """Get project details"""
    try:
        project_doc = await db.video_projects.find_one({"id": project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return VideoProject(**project_doc)
        
    except Exception as e:
        logger.error(f"Error getting project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/projects/{project_id}/download")
async def download_video(project_id: str):
    """Download generated video"""
    try:
        project_doc = await db.video_projects.find_one({"id": project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found")
        
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)