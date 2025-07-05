"""
Enhanced ElevenLabs Service for Voice Generation and Cloning
"""
import os
import asyncio
import aiofiles
import tempfile
from typing import List, Optional, Dict, Any
from elevenlabs import AsyncElevenLabs, Voice, VoiceSettings
from elevenlabs.client import AsyncElevenLabs
import logging

logger = logging.getLogger(__name__)

class EnhancedElevenLabsService:
    def __init__(self):
        self.api_key = os.environ.get('ELEVENLABS_API_KEY')
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is required")
        
        self.client = AsyncElevenLabs(api_key=self.api_key)
        
    async def generate_speech(
        self, 
        text: str, 
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default voice
        stability: float = 0.7,
        similarity_boost: float = 0.8,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ) -> bytes:
        """Generate speech from text using specified voice"""
        try:
            voice_settings = VoiceSettings(
                stability=stability,
                similarity_boost=similarity_boost,
                style=style,
                use_speaker_boost=use_speaker_boost
            )
            
            audio_generator = await self.client.generate(
                text=text,
                voice=voice_id,
                voice_settings=voice_settings,
                model="eleven_multilingual_v2"
            )
            
            # Collect audio chunks
            audio_chunks = []
            async for chunk in audio_generator:
                audio_chunks.append(chunk)
            
            return b''.join(audio_chunks)
            
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            raise Exception(f"Speech generation failed: {str(e)}")
    
    async def clone_voice(
        self, 
        name: str, 
        audio_files: List[bytes], 
        description: Optional[str] = None
    ) -> str:
        """Clone a voice from audio samples"""
        try:
            # Create temporary files for audio samples
            temp_files = []
            for i, audio_data in enumerate(audio_files):
                temp_file = tempfile.NamedTemporaryFile(suffix=f"_sample_{i}.mp3", delete=False)
                await aiofiles.open(temp_file.name, "wb").write(audio_data)
                temp_files.append(temp_file.name)
            
            # Clone voice using ElevenLabs API
            voice = await self.client.clone(
                name=name,
                files=temp_files,
                description=description or f"Cloned voice: {name}"
            )
            
            # Cleanup temporary files
            for temp_file in temp_files:
                os.unlink(temp_file)
            
            return voice.voice_id
            
        except Exception as e:
            logger.error(f"Error cloning voice: {str(e)}")
            raise Exception(f"Voice cloning failed: {str(e)}")
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices"""
        try:
            voices = await self.client.voices.get_all()
            
            return [
                {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": voice.category,
                    "description": voice.description,
                    "labels": voice.labels
                }
                for voice in voices.voices
            ]
            
        except Exception as e:
            logger.error(f"Error getting voices: {str(e)}")
            raise Exception(f"Failed to get voices: {str(e)}")
    
    async def generate_speech_for_video(
        self, 
        script: str, 
        voice_id: str,
        output_path: str
    ) -> str:
        """Generate speech audio file for video integration"""
        try:
            audio_data = await self.generate_speech(script, voice_id)
            
            # Save audio to file
            async with aiofiles.open(output_path, "wb") as f:
                await f.write(audio_data)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating speech for video: {str(e)}")
            raise Exception(f"Video speech generation failed: {str(e)}")
    
    async def stream_speech(self, text: str, voice_id: str):
        """Stream speech generation for real-time audio"""
        try:
            voice_settings = VoiceSettings(
                stability=0.7,
                similarity_boost=0.8,
                style=0.0,
                use_speaker_boost=True
            )
            
            audio_stream = await self.client.generate(
                text=text,
                voice=voice_id,
                voice_settings=voice_settings,
                model="eleven_multilingual_v2",
                stream=True
            )
            
            async for chunk in audio_stream:
                yield chunk
                
        except Exception as e:
            logger.error(f"Error streaming speech: {str(e)}")
            raise Exception(f"Speech streaming failed: {str(e)}")