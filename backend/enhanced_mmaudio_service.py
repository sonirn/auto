"""
Enhanced MMAudio Service for Background Sound Effects and Music
"""
import os
import asyncio
import aiofiles
import tempfile
import logging
from typing import Optional, List, Dict, Any
import httpx
import json

logger = logging.getLogger(__name__)

class EnhancedMMAudioService:
    def __init__(self):
        self.hf_api_token = os.environ.get('AIML_API_KEY')  # Using AI/ML API key for HuggingFace
        if not self.hf_api_token:
            logger.warning("AIML_API_KEY not found, using limited mode")
        
        self.api_url = "https://api-inference.huggingface.co/models/facebook/musicgen-large"
        self.headers = {
            "Authorization": f"Bearer {self.hf_api_token}" if self.hf_api_token else "",
            "Content-Type": "application/json"
        }
    
    async def generate_background_music(
        self, 
        prompt: str, 
        duration: float = 30.0,
        output_path: Optional[str] = None
    ) -> str:
        """Generate background music from text prompt"""
        try:
            # Use MusicGen via Hugging Face Inference API
            payload = {
                "inputs": prompt,
                "parameters": {
                    "duration": min(duration, 30.0),  # Max 30 seconds for free tier
                    "temperature": 0.7,
                    "do_sample": True
                }
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"HuggingFace API error: {response.text}")
                    # Fallback to sample music
                    return await self._create_sample_music(prompt, output_path)
                
                audio_data = response.content
            
            # Save audio to file
            if not output_path:
                output_path = f"/tmp/bg_music_{hash(prompt)}.wav"
            
            async with aiofiles.open(output_path, "wb") as f:
                await f.write(audio_data)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating background music: {str(e)}")
            # Fallback to sample music
            return await self._create_sample_music(prompt, output_path)
    
    async def generate_sound_effects(
        self, 
        effect_description: str,
        duration: float = 5.0,
        output_path: Optional[str] = None
    ) -> str:
        """Generate sound effects from description"""
        try:
            # For sound effects, we'll use a simplified approach
            # In production, you might use specialized sound effect APIs
            
            # Create prompt for sound effect
            prompt = f"sound effect: {effect_description}, short duration, high quality"
            
            return await self.generate_background_music(prompt, duration, output_path)
            
        except Exception as e:
            logger.error(f"Error generating sound effects: {str(e)}")
            return await self._create_sample_sound_effect(effect_description, output_path)
    
    async def enhance_video_audio(
        self, 
        video_description: str,
        scene_descriptions: List[str],
        total_duration: float = 60.0
    ) -> List[Dict[str, Any]]:
        """Generate audio enhancements for video scenes"""
        try:
            audio_tracks = []
            
            # Generate background music for entire video
            bg_music_path = await self.generate_background_music(
                f"background music for {video_description}",
                duration=total_duration
            )
            
            audio_tracks.append({
                "type": "background_music",
                "path": bg_music_path,
                "start_time": 0.0,
                "duration": total_duration,
                "volume": 0.3  # Background volume
            })
            
            # Generate sound effects for each scene
            scene_duration = total_duration / len(scene_descriptions) if scene_descriptions else total_duration
            
            for i, scene in enumerate(scene_descriptions):
                effect_path = await self.generate_sound_effects(
                    scene,
                    duration=min(scene_duration, 10.0)
                )
                
                audio_tracks.append({
                    "type": "sound_effect",
                    "path": effect_path,
                    "start_time": i * scene_duration,
                    "duration": min(scene_duration, 10.0),
                    "volume": 0.7  # Effect volume
                })
            
            return audio_tracks
            
        except Exception as e:
            logger.error(f"Error enhancing video audio: {str(e)}")
            return []
    
    async def _create_sample_music(self, prompt: str, output_path: Optional[str] = None) -> str:
        """Create sample background music as fallback"""
        try:
            if not output_path:
                output_path = f"/tmp/sample_music_{hash(prompt)}.wav"
            
            # Create a simple sine wave as placeholder
            import numpy as np
            import wave
            
            sample_rate = 44100
            duration = 10.0
            frequency = 440.0  # A note
            
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
            
            # Convert to 16-bit integers
            audio_data = (audio_data * 32767).astype(np.int16)
            
            # Save as WAV file
            with wave.open(output_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating sample music: {str(e)}")
            # Create empty file as last resort
            if not output_path:
                output_path = f"/tmp/empty_audio_{hash(prompt)}.wav"
            async with aiofiles.open(output_path, "wb") as f:
                await f.write(b"")
            return output_path
    
    async def _create_sample_sound_effect(self, description: str, output_path: Optional[str] = None) -> str:
        """Create sample sound effect as fallback"""
        return await self._create_sample_music(description, output_path)
    
    async def combine_audio_tracks(
        self, 
        tracks: List[Dict[str, Any]], 
        output_path: str
    ) -> str:
        """Combine multiple audio tracks into single file"""
        try:
            # This is a simplified implementation
            # In production, you'd use FFmpeg or similar for proper audio mixing
            
            if not tracks:
                # Create silence
                return await self._create_sample_music("silence", output_path)
            
            # For now, just use the first track
            first_track = tracks[0]
            
            # Copy the first track to output
            async with aiofiles.open(first_track["path"], "rb") as src:
                audio_data = await src.read()
            
            async with aiofiles.open(output_path, "wb") as dst:
                await dst.write(audio_data)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error combining audio tracks: {str(e)}")
            return await self._create_sample_music("combined", output_path)