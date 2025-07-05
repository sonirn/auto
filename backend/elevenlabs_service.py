import os
import logging
from typing import Optional, Dict, Any, List
import httpx
import asyncio
from pathlib import Path
import aiofiles

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = os.environ.get('ELEVENLABS_API_KEY')
        self.base_url = "https://api.elevenlabs.io/v1"
        self.available = bool(self.api_key and self.api_key != 'sk_613429b69a534539f725091aab14705a535bbeeeb6f52133')
        
        # Default voices for different character types
        self.default_voices = {
            'male': '21m00Tcm4TlvDq8ikWAM',  # Josh (male)
            'female': 'EXAVITQu4vr4fq4Q6itJ',  # Bella (female)
            'narrator': 'onwK4e9ZLuTAKqWW03F9',  # Daniel (narrator)
            'child': 'pFZP5JQG7iQjIQuC4Bf7',  # Lily (child)
        }
    
    async def generate_voice(self, text: str, voice_type: str = 'narrator', 
                           voice_settings: Optional[Dict] = None) -> Optional[bytes]:
        """Generate voice audio from text using ElevenLabs TTS"""
        if not self.available:
            logger.warning("ElevenLabs service not available, skipping voice generation")
            return None
        
        try:
            voice_id = self.default_voices.get(voice_type, self.default_voices['narrator'])
            
            # Default voice settings
            settings = {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
            
            if voice_settings:
                settings.update(voice_settings)
            
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": settings
            }
            
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/text-to-speech/{voice_id}",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error generating voice with ElevenLabs: {str(e)}")
            return None
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices from ElevenLabs"""
        if not self.available:
            return []
        
        try:
            headers = {
                "xi-api-key": self.api_key,
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/voices",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("voices", [])
                else:
                    logger.error(f"Failed to get voices: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching voices: {str(e)}")
            return []
    
    async def clone_voice(self, voice_name: str, audio_file_path: str) -> Optional[str]:
        """Clone a voice from an audio file (requires sufficient credits)"""
        if not self.available:
            logger.warning("ElevenLabs service not available, skipping voice cloning")
            return None
        
        try:
            headers = {
                "xi-api-key": self.api_key
            }
            
            # Read audio file
            async with aiofiles.open(audio_file_path, 'rb') as audio_file:
                audio_content = await audio_file.read()
            
            files = {
                'files': (Path(audio_file_path).name, audio_content, 'audio/mpeg')
            }
            
            data = {
                'name': voice_name,
                'description': f'Cloned voice for {voice_name}'
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/voices/add",
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('voice_id')
                else:
                    logger.error(f"Voice cloning failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error cloning voice: {str(e)}")
            return None
    
    async def enhance_audio_for_video(self, text: str, video_context: Dict[str, Any]) -> Optional[bytes]:
        """Generate contextually appropriate voice for video content"""
        if not self.available:
            return None
        
        # Analyze video context to choose appropriate voice and settings
        voice_type = self._determine_voice_type(video_context)
        voice_settings = self._get_contextual_settings(video_context)
        
        return await self.generate_voice(text, voice_type, voice_settings)
    
    def _determine_voice_type(self, video_context: Dict[str, Any]) -> str:
        """Determine appropriate voice type based on video analysis"""
        analysis = video_context.get('analysis', {})
        
        # Check for character mentions or style
        content = str(analysis).lower()
        
        if any(word in content for word in ['child', 'kid', 'young']):
            return 'child'
        elif any(word in content for word in ['woman', 'female', 'girl']):
            return 'female'
        elif any(word in content for word in ['man', 'male', 'boy']):
            return 'male'
        else:
            return 'narrator'
    
    def _get_contextual_settings(self, video_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get voice settings based on video context"""
        analysis = video_context.get('analysis', {})
        content = str(analysis).lower()
        
        # Base settings
        settings = {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
        
        # Adjust based on video style
        if any(word in content for word in ['energetic', 'exciting', 'dynamic']):
            settings["stability"] = 0.3  # More variation
            settings["style"] = 0.2
        elif any(word in content for word in ['calm', 'peaceful', 'relaxing']):
            settings["stability"] = 0.8  # More stable
            settings["style"] = 0.0
        elif any(word in content for word in ['dramatic', 'intense', 'powerful']):
            settings["stability"] = 0.4
            settings["style"] = 0.3
        
        return settings

# Global instance
elevenlabs_service = ElevenLabsService()