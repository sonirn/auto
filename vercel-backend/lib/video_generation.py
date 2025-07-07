"""Video generation service for Vercel serverless functions"""
import os
import httpx
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class VideoModel(str, Enum):
    RUNWAYML_GEN4 = "runwayml_gen4"
    RUNWAYML_GEN3 = "runwayml_gen3"
    GOOGLE_VEO2 = "google_veo2"
    GOOGLE_VEO3 = "google_veo3"

class VideoGenerationService:
    """Video generation service using RunwayML and Google Veo"""
    
    def __init__(self):
        self.runwayml_api_key = os.environ.get('RUNWAYML_API_KEY')
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
    
    async def generate_video(self, project_id: str, generation_plan: Dict[str, Any], 
                           model: VideoModel) -> Dict[str, Any]:
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
            raise Exception(f"Video generation failed: {str(e)}")
    
    async def _generate_with_runwayml(self, project_id: str, generation_plan: Dict[str, Any], 
                                    model: VideoModel) -> Dict[str, Any]:
        """Generate video using RunwayML API"""
        try:
            # Extract plan details
            plan_description = generation_plan.get('description', 'Generate a video based on the provided plan')
            
            # Improve prompt based on plan
            if 'scenes' in generation_plan and generation_plan['scenes']:
                scenes_text = "\n".join([f"Scene {i+1}: {scene}" for i, scene in enumerate(generation_plan['scenes'][:3])])
                plan_description = f"{plan_description}\n\nKey scenes:\n{scenes_text}"
            
            # RunwayML API configuration
            model_name = "gen4:turbo" if model == VideoModel.RUNWAYML_GEN4 else "gen3:alpha:turbo"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
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
                
                if not generation_id:
                    raise Exception("No generation ID returned from RunwayML")
                
                logger.info(f"RunwayML generation started: {generation_id}")
                
                # Return generation info (polling will be handled by background task)
                return {
                    "generation_id": generation_id,
                    "model_used": model_name,
                    "estimated_time": 120,  # 2 minutes estimate
                    "status": "initiated",
                    "prompt": plan_description
                }
                
        except Exception as e:
            logger.error(f"RunwayML generation error: {str(e)}")
            raise e
    
    async def _generate_with_veo(self, project_id: str, generation_plan: Dict[str, Any], 
                               model: VideoModel) -> Dict[str, Any]:
        """Generate video using Google Veo via Gemini API"""
        try:
            # For now, Google Veo is not fully available, so we'll simulate
            # In production, this would integrate with the actual Veo API
            
            logger.info(f"Veo generation requested for project {project_id} with model {model}")
            
            # Simulate Veo response
            generation_id = f"veo_{project_id}_{model.value}"
            
            return {
                "generation_id": generation_id,
                "model_used": model.value,
                "estimated_time": 180,  # 3 minutes estimate for Veo
                "status": "initiated",
                "note": "Google Veo integration in development"
            }
            
        except Exception as e:
            logger.error(f"Veo generation error: {str(e)}")
            # Fallback to RunwayML if Veo fails
            logger.warning("Falling back to RunwayML generation")
            return await self._generate_with_runwayml(project_id, generation_plan, VideoModel.RUNWAYML_GEN4)
    
    async def poll_generation_status(self, generation_id: str, model: VideoModel) -> Dict[str, Any]:
        """Poll generation status"""
        try:
            if model in [VideoModel.RUNWAYML_GEN4, VideoModel.RUNWAYML_GEN3]:
                return await self._poll_runwayml_generation(generation_id)
            elif model in [VideoModel.GOOGLE_VEO2, VideoModel.GOOGLE_VEO3]:
                return await self._poll_veo_generation(generation_id)
            else:
                raise ValueError(f"Unsupported model for polling: {model}")
        except Exception as e:
            logger.error(f"Error polling generation status: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def _poll_runwayml_generation(self, generation_id: str) -> Dict[str, Any]:
        """Poll RunwayML API for generation completion"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.runwayml_api_key}",
                    "Content-Type": "application/json"
                }
                
                response = await client.get(
                    f"https://api.runwayml.com/v1/generations/{generation_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    
                    result = {
                        "status": status,
                        "generation_id": generation_id
                    }
                    
                    if status == "completed":
                        result["video_url"] = data.get("video_url")
                        result["download_url"] = data.get("download_url")
                    elif status == "failed":
                        result["error"] = data.get("error", "Generation failed")
                    elif status in ["pending", "processing"]:
                        result["progress"] = data.get("progress", 0)
                    
                    return result
                else:
                    return {
                        "status": "error",
                        "error": f"API error: {response.status_code}"
                    }
            
        except Exception as e:
            logger.error(f"Error polling RunwayML: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _poll_veo_generation(self, generation_id: str) -> Dict[str, Any]:
        """Poll Veo generation status (simulated for now)"""
        # Simulate Veo polling
        return {
            "status": "processing",
            "generation_id": generation_id,
            "progress": 0.5,
            "note": "Veo polling simulation"
        }
    
    async def download_video(self, video_url: str, output_path: str) -> bool:
        """Download video from URL"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(video_url)
                
                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    logger.info(f"Video downloaded successfully: {output_path}")
                    return True
                else:
                    raise Exception(f"Failed to download video: {response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            return False

# Create global video generation service instance
video_generation_service = VideoGenerationService()