"""Video analysis service for Vercel serverless functions"""
import os
import asyncio
import json
import logging
from typing import Dict, Any, Optional
import tempfile
import cv2
import base64
import litellm
from pathlib import Path

logger = logging.getLogger(__name__)

class VideoAnalysisService:
    """Video analysis service using Groq LLM"""
    
    def __init__(self):
        self.groq_api_key = os.environ.get('GROQ_API_KEY')
        self.model = "groq/llama3-8b-8192"
        
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        # Configure litellm
        litellm.set_verbose = False
        os.environ['GROQ_API_KEY'] = self.groq_api_key
        
        logger.info("VideoAnalysisService initialized with Groq")
    
    async def analyze_video(self, video_path: str, character_image_path: Optional[str] = None, 
                          audio_path: Optional[str] = None) -> Dict[str, Any]:
        """Analyze video and create generation plan"""
        try:
            # Extract video metadata
            metadata = await self._extract_video_metadata(video_path)
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(metadata, character_image_path, audio_path)
            
            # Call Groq LLM for analysis
            response = await self._call_groq_llm(prompt)
            
            # Parse and structure response
            analysis = self._parse_analysis_response(response)
            
            return {
                "video_analysis": analysis,
                "generation_plan": self._create_generation_plan(analysis),
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            raise
    
    async def _extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extract video metadata using OpenCV"""
        try:
            # For URL paths, download first
            if video_path.startswith('http'):
                video_path = await self._download_video_temp(video_path)
            
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError("Cannot open video file")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            # Get first frame for analysis
            ret, frame = cap.read()
            first_frame_b64 = None
            if ret:
                _, buffer = cv2.imencode('.jpg', frame)
                first_frame_b64 = base64.b64encode(buffer).decode()
            
            cap.release()
            
            return {
                "duration": duration,
                "fps": fps,
                "frame_count": frame_count,
                "resolution": {"width": width, "height": height},
                "aspect_ratio": f"{width}:{height}",
                "first_frame_b64": first_frame_b64,
                "filesize": os.path.getsize(video_path) if os.path.exists(video_path) else 0
            }
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {"error": str(e)}
    
    async def _download_video_temp(self, video_url: str) -> str:
        """Download video to temporary file"""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(video_url)
                response.raise_for_status()
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
                    tmp_file.write(response.content)
                    return tmp_file.name
                    
        except Exception as e:
            logger.error(f"Video download failed: {e}")
            raise
    
    def _create_analysis_prompt(self, metadata: Dict[str, Any], character_image_path: Optional[str], 
                               audio_path: Optional[str]) -> str:
        """Create analysis prompt for LLM"""
        prompt = f"""
        Analyze this video and create a detailed generation plan:

        Video Metadata:
        - Duration: {metadata.get('duration', 0):.2f} seconds
        - Resolution: {metadata.get('resolution', {})}
        - FPS: {metadata.get('fps', 0)}
        - Aspect Ratio: {metadata.get('aspect_ratio', 'unknown')}

        Please provide a comprehensive analysis including:
        1. Visual Analysis: Describe scenes, objects, lighting, colors, composition
        2. Style Analysis: Identify the genre, mood, pacing, cinematography style
        3. Content Analysis: Summarize the story, theme, message, characters
        4. Technical Analysis: Comment on video quality, effects, transitions

        Then create a generation plan with:
        1. Scene breakdown (if multiple scenes)
        2. Key visual elements to recreate
        3. Recommended video generation settings
        4. Suggested prompts for AI video generation

        Format your response as JSON with the following structure:
        {{
            "visual_analysis": {{
                "scenes": ["scene descriptions"],
                "objects": ["key objects"],
                "lighting": "lighting description",
                "colors": ["dominant colors"],
                "composition": "composition analysis"
            }},
            "style_analysis": {{
                "genre": "genre",
                "mood": "mood description",
                "pacing": "pacing analysis",
                "cinematography": "cinematography style"
            }},
            "content_analysis": {{
                "story": "story summary",
                "theme": "main theme",
                "message": "key message",
                "characters": ["character descriptions"]
            }},
            "generation_plan": {{
                "description": "overall generation plan",
                "key_elements": ["key elements to recreate"],
                "recommended_model": "runwayml_gen4",
                "prompts": ["generation prompts"],
                "duration": 10,
                "aspect_ratio": "9:16"
            }}
        }}
        """
        
        return prompt
    
    async def _call_groq_llm(self, prompt: str) -> str:
        """Call Groq LLM for analysis"""
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq LLM call failed: {e}")
            raise
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse and structure LLM response"""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # If not JSON, create structured response
            return {
                "visual_analysis": {
                    "scenes": ["Scene analysis from video"],
                    "objects": ["Various objects detected"],
                    "lighting": "Professional lighting setup",
                    "colors": ["Dominant colors in video"],
                    "composition": "Well-composed shots"
                },
                "style_analysis": {
                    "genre": "Modern video style",
                    "mood": "Engaging and dynamic",
                    "pacing": "Good pacing throughout",
                    "cinematography": "Professional cinematography"
                },
                "content_analysis": {
                    "story": "Video story and narrative",
                    "theme": "Main themes identified",
                    "message": "Key messages conveyed",
                    "characters": ["Main characters or subjects"]
                },
                "raw_response": response
            }
            
        except Exception as e:
            logger.error(f"Response parsing failed: {e}")
            return {"error": str(e), "raw_response": response}
    
    def _create_generation_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create generation plan from analysis"""
        return {
            "description": "Generate a video based on the analyzed content",
            "key_elements": analysis.get("visual_analysis", {}).get("objects", []),
            "recommended_model": "runwayml_gen4",
            "prompts": ["Create a 9:16 aspect ratio video based on the analysis"],
            "duration": 10,
            "aspect_ratio": "9:16",
            "scenes": [
                {
                    "scene_number": 1,
                    "description": "Main scene recreation",
                    "duration": 10,
                    "prompt": "Generate video content matching the original style"
                }
            ]
        }