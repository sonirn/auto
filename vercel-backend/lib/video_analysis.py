"""Video analysis service for Vercel serverless functions"""
import os
import cv2
import json
import uuid
import logging
import asyncio
from typing import Dict, Any, Optional
import litellm

logger = logging.getLogger(__name__)

class VideoAnalysisService:
    """Video analysis service using Groq AI"""
    
    def __init__(self):
        self.groq_api_key = os.environ.get('GROQ_API_KEY')
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

Return your analysis in JSON format with 'analysis' and 'plan' keys."""
    
    async def analyze_video(self, video_path: str, character_image_path: Optional[str] = None, 
                           audio_path: Optional[str] = None) -> Dict[str, Any]:
        """Analyze video and create generation plan"""
        try:
            # Extract video metadata
            video_metadata = await self._extract_video_metadata(video_path)
            
            # Create analysis prompt
            analysis_prompt = f"""
            Please analyze this video based on the metadata provided: {json.dumps(video_metadata, indent=2)}
            
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
            {"Audio file provided for reference." if audio_path else "No audio file provided."}
            
            Return response in JSON format with 'analysis' and 'plan' keys.
            """
            
            # Use litellm for AI analysis
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await asyncio.to_thread(
                litellm.completion,
                model="groq/llama3-8b-8192",
                messages=messages,
                api_key=self.groq_api_key,
                temperature=0.7,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                analysis_data = json.loads(response_text)
                
                # Ensure proper structure
                if 'analysis' not in analysis_data:
                    analysis_data = {'analysis': analysis_data, 'plan': {}}
                
                if 'plan' not in analysis_data:
                    analysis_data['plan'] = {
                        "description": "Video generation plan created based on analysis",
                        "recommended_model": "runwayml_gen4",
                        "scenes": [],
                        "audio_requirements": {},
                        "editing_instructions": {}
                    }
                
                # Add metadata to analysis
                analysis_data['analysis']['metadata'] = video_metadata
                analysis_data['analysis']['processing_info'] = {
                    "character_image_provided": bool(character_image_path),
                    "audio_provided": bool(audio_path),
                    "analysis_model": "groq/llama3-8b-8192",
                    "timestamp": str(uuid.uuid4())
                }
                
                return analysis_data
                
            except json.JSONDecodeError:
                # If not valid JSON, structure the response
                return {
                    "analysis": {
                        "raw_response": response_text,
                        "metadata": video_metadata,
                        "processing_info": {
                            "character_image_provided": bool(character_image_path),
                            "audio_provided": bool(audio_path),
                            "analysis_model": "groq/llama3-8b-8192",
                            "note": "Analysis based on video metadata and AI interpretation"
                        }
                    },
                    "plan": {
                        "description": "Plan extracted from analysis",
                        "recommended_model": "runwayml_gen4",
                        "scenes": [],
                        "note": "Video generation plan created based on analysis"
                    }
                }
            
        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}")
            raise Exception(f"Video analysis failed: {str(e)}")
    
    async def _extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extract video metadata using OpenCV"""
        try:
            # Use OpenCV to extract basic metadata
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                # If OpenCV fails, return basic info
                import os
                file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
                return {
                    "file_size": file_size,
                    "error": "Could not open video file with OpenCV",
                    "file_path": video_path
                }
            
            # Extract video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            duration = frame_count / fps if fps > 0 else 0
            
            # Get additional properties
            fourcc = cap.get(cv2.CAP_PROP_FOURCC)
            
            cap.release()
            
            metadata = {
                "fps": fps,
                "frame_count": int(frame_count),
                "width": int(width),
                "height": int(height),
                "duration": duration,
                "aspect_ratio": f"{int(width)}:{int(height)}",
                "fourcc": int(fourcc),
                "format_info": {
                    "codec": "unknown",  # Would need additional processing
                    "container": video_path.split('.')[-1] if '.' in video_path else "unknown"
                }
            }
            
            # Try to get file size
            try:
                import os
                metadata["file_size"] = os.path.getsize(video_path)
            except:
                metadata["file_size"] = 0
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting video metadata: {str(e)}")
            return {
                "error": str(e),
                "file_path": video_path
            }

# Create global video analysis service instance
video_analysis_service = VideoAnalysisService()