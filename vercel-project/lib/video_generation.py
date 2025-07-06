"""Video generation service for Vercel serverless functions"""
import os
import asyncio
import json
import logging
from typing import Dict, Any, Optional
import httpx
from enum import Enum

logger = logging.getLogger(__name__)

class VideoModel(str, Enum):
    RUNWAYML_GEN4 = "runwayml_gen4"
    RUNWAYML_GEN3 = "runwayml_gen3"
    GOOGLE_VEO2 = "google_veo2"
    GOOGLE_VEO3 = "google_veo3"

class VideoGenerationService:
    """Video generation service using multiple AI models"""
    
    def __init__(self):
        self.runwayml_api_key = os.environ.get('RUNWAYML_API_KEY')
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
        
        if not self.runwayml_api_key:
            logger.warning("RUNWAYML_API_KEY not found, RunwayML generation will not work")
        
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY not found, Google Veo generation will not work")
        
        logger.info("VideoGenerationService initialized")
    
    async def generate_video(self, project_id: str, generation_plan: Dict[str, Any], 
                           model: VideoModel) -> Dict[str, Any]:
        """Generate video using specified model"""
        try:
            if model in [VideoModel.RUNWAYML_GEN4, VideoModel.RUNWAYML_GEN3]:
                return await self._generate_with_runwayml(project_id, generation_plan, model)
            elif model in [VideoModel.GOOGLE_VEO2, VideoModel.GOOGLE_VEO3]:
                return await self._generate_with_veo(project_id, generation_plan, model)
            else:
                raise ValueError(f"Unsupported model: {model}")
                
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise
    
    async def _generate_with_runwayml(self, project_id: str, generation_plan: Dict[str, Any], 
                                    model: VideoModel) -> Dict[str, Any]:
        """Generate video using RunwayML"""
        try:
            if not self.runwayml_api_key:
                raise ValueError("RunwayML API key not configured")
            
            # Map model to RunwayML model name
            model_mapping = {
                VideoModel.RUNWAYML_GEN4: "gen4-turbo",
                VideoModel.RUNWAYML_GEN3: "gen3-alpha"
            }
            
            model_name = model_mapping.get(model, "gen4-turbo")
            plan_description = generation_plan.get('description', 'Generate a video based on the provided plan')
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.runwayml_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Create generation request
                payload = {
                    "model": model_name,
                    "prompt": plan_description,
                    "duration": 10,
                    "ratio": "9:16",
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
                    raise Exception("No generation ID received from RunwayML")
                
                return {
                    "status": "started",
                    "generation_id": generation_id,
                    "model": model_name,
                    "estimated_time": 120  # 2 minutes
                }
                
        except Exception as e:
            logger.error(f"RunwayML generation error: {str(e)}")
            raise
    
    async def _generate_with_veo(self, project_id: str, generation_plan: Dict[str, Any], 
                                model: VideoModel) -> Dict[str, Any]:
        """Generate video using Google Veo (placeholder implementation)"""
        try:
            # This is a placeholder implementation
            # In practice, you would integrate with Google's Veo API
            
            logger.info(f"Veo generation requested for model: {model}")
            
            # For now, return a placeholder response
            return {
                "status": "started",
                "generation_id": f"veo_{project_id}",
                "model": model.value,
                "estimated_time": 180,  # 3 minutes
                "note": "Veo integration is a placeholder - actual implementation needed"
            }
            
        except Exception as e:
            logger.error(f"Veo generation error: {str(e)}")
            raise
    
    async def check_generation_status(self, generation_id: str, model: VideoModel) -> Dict[str, Any]:
        """Check generation status"""
        try:
            if model in [VideoModel.RUNWAYML_GEN4, VideoModel.RUNWAYML_GEN3]:
                return await self._check_runwayml_status(generation_id)
            elif model in [VideoModel.GOOGLE_VEO2, VideoModel.GOOGLE_VEO3]:
                return await self._check_veo_status(generation_id)
            else:
                raise ValueError(f"Unsupported model: {model}")
                
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            raise
    
    async def _check_runwayml_status(self, generation_id: str) -> Dict[str, Any]:
        """Check RunwayML generation status"""
        try:
            if not self.runwayml_api_key:
                raise ValueError("RunwayML API key not configured")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.runwayml_api_key}",
                    "Content-Type": "application/json"
                }
                
                response = await client.get(
                    f"https://api.runwayml.com/v1/generations/{generation_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise Exception(f"RunwayML status check error: {response.text}")
                
                data = response.json()
                status = data.get("status", "unknown")
                
                result = {
                    "status": status,
                    "generation_id": generation_id,
                    "progress": 0
                }
                
                if status == "completed":
                    result["video_url"] = data.get("video_url")
                    result["progress"] = 100
                elif status == "processing":
                    result["progress"] = 50
                elif status == "failed":
                    result["error"] = data.get("error", "Generation failed")
                
                return result
                
        except Exception as e:
            logger.error(f"RunwayML status check failed: {e}")
            raise
    
    async def _check_veo_status(self, generation_id: str) -> Dict[str, Any]:
        """Check Veo generation status (placeholder)"""
        # Placeholder implementation
        return {
            "status": "processing",
            "generation_id": generation_id,
            "progress": 25,
            "note": "Veo status checking is a placeholder"
        }
    
    async def download_video(self, video_url: str) -> bytes:
        """Download generated video"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(video_url)
                response.raise_for_status()
                return response.content
                
        except Exception as e:
            logger.error(f"Video download failed: {e}")
            raise