"""Service for handling speech-to-text and text-to-speech operations."""

import os
import logging
import base64
import io
from typing import Optional, Dict, Any
import httpx
from openai import OpenAI
import elevenlabs
from elevenlabs import generate, voices, Voice, VoiceSettings

logger = logging.getLogger(__name__)

class SpeechService:
    """Handles speech-to-text (STT) and text-to-speech (TTS) operations."""
    
    def __init__(self):
        """Initialize the speech service with API clients."""
        # OpenAI client for Whisper STT
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY environment variable is not set")
            self.openai_client = None
        else:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # ElevenLabs client for TTS
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        if not self.elevenlabs_api_key:
            logger.warning("ELEVENLABS_API_KEY environment variable is not set")
        else:
            logger.info(f"Setting ElevenLabs API key: {self.elevenlabs_api_key[:4]}...{self.elevenlabs_api_key[-4:]}")
            try:
                # Method 1: Using the api_key property
                elevenlabs.api_key = self.elevenlabs_api_key
                # Method 2: Using the set_api_key function
                elevenlabs.set_api_key(self.elevenlabs_api_key)
                logger.info("ElevenLabs API key set successfully")
            except Exception as e:
                logger.error(f"Error setting ElevenLabs API key: {e}")
        
        # Configure voices for TTS
        self.spanish_voice_id = os.getenv('ELEVENLABS_SPANISH_VOICE_ID', 'pNInz6obpgDQGcFmaJgB')
        self.english_voice_id = os.getenv('ELEVENLABS_ENGLISH_VOICE_ID', 'pNInz6obpgDQGcFmaJgB')
        
        # Deepgram client for STT fallback
        self.deepgram_api_key = os.getenv('DEEPGRAM_API_KEY')
        if not self.deepgram_api_key:
            logger.warning("DEEPGRAM_API_KEY environment variable is not set")
        
        logger.info("SpeechService initialized successfully")
    
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        language: str = "es",
        audio_format: str = "mp3"
    ) -> Optional[str]:
        """
        Transcribe audio to text using OpenAI Whisper with Deepgram fallback.
        
        Args:
            audio_data: Audio data in bytes
            language: Language code (default: "es" for Spanish)
            audio_format: Audio format (default: "mp3")
            
        Returns:
            Transcribed text or None if all transcription methods fail
        """
        # First try Whisper if available
        if self.openai_client:
            try:
                logger.info(f"Transcribing with Whisper (language: {language})")
                
                # Create a file-like object from the audio bytes
                audio_file = io.BytesIO(audio_data)
                audio_file.name = f"audio.{audio_format}"
                
                # Call OpenAI Whisper API
                response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="text"
                )
                
                transcript = response.strip()
                if transcript:
                    logger.info(f"Whisper transcription successful: {transcript}")
                    return transcript
                    
            except Exception as e:
                logger.error(f"Whisper transcription error: {e}")
        
        # If Whisper fails or is not available, try Deepgram
        if self.deepgram_api_key:
            try:
                return await self._transcribe_with_deepgram(audio_data, language)
            except Exception as e:
                logger.error(f"Deepgram transcription error: {e}")
        
        logger.error("All transcription methods failed")
        return None
    
    async def _transcribe_with_deepgram(self, audio_data: bytes, language: str) -> Optional[str]:
        """Transcribe audio using Deepgram API."""
        try:
            logger.info(f"Transcribing with Deepgram (language: {language})")
            
            # Map language codes to Deepgram language codes
            language_map = {
                'es': 'es-419',  # Latin American Spanish
                'en': 'en-US',    # US English
                'fr': 'fr-FR',    # French
                'de': 'de-DE',    # German
                'it': 'it-IT',    # Italian
                'pt': 'pt-BR',    # Brazilian Portuguese
                'ru': 'ru-RU',    # Russian
                'ja': 'ja-JP',    # Japanese
                'ko': 'ko-KR',    # Korean
                'zh': 'zh-CN'     # Chinese (Simplified)
            }
            
            # Default to English if language not in map
            deepgram_language = language_map.get(language, 'en-US')
            
            # Prepare the request
            url = "https://api.deepgram.com/v1/listen"
            headers = {
                "Authorization": f"Token {self.deepgram_api_key}",
                "Content-Type": "audio/mp3"
            }
            params = {
                "model": "nova-2",
                "language": deepgram_language,
                "punctuate": "true",
                "utterances": "true",
                "interim_results": "false"
            }
            
            # Make the request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    params=params,
                    content=audio_data,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
            
            # Extract the transcript
            transcript = result.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "").strip()
            
            if transcript:
                logger.info(f"Deepgram transcription successful: {transcript}")
                return transcript
                
            logger.error("Deepgram returned empty transcript")
            return None
            
        except Exception as e:
            logger.error(f"Deepgram transcription failed: {e}")
            raise
    
    async def generate_speech(
        self, 
        text: str, 
        language: str = "es",
        output_format: str = "mp3_44100_128"
    ) -> Optional[bytes]:
        """
        Generate speech from text using ElevenLabs TTS with fallback to gTTS.
        
        Args:
            text: Text to convert to speech
            language: Language code (default: "es" for Spanish)
            output_format: Audio output format (not used for gTTS fallback)
            
        Returns:
            Audio data in bytes or None if all generation methods fail
        """
        # First try ElevenLabs
        elevenlabs_audio = await self._generate_with_elevenlabs(text, language)
        if elevenlabs_audio:
            return elevenlabs_audio
            
        # If ElevenLabs fails, try gTTS
        logger.warning("ElevenLabs TTS failed, falling back to gTTS")
        return await self._generate_with_gtts(text, language)
    
    async def _generate_with_elevenlabs(self, text: str, language: str) -> Optional[bytes]:
        """Generate speech using ElevenLabs TTS."""
        try:
            logger.info(f"Generating speech with ElevenLabs: {text[:50]}...")
            
            # Select voice based on language
            voice_id = self.spanish_voice_id if language == "es" else self.english_voice_id
            
            # Generate audio using ElevenLabs
            audio = generate(
                text=text,
                voice=voice_id,
                model="eleven_multilingual_v2"
            )
            
            if not audio:
                logger.error("ElevenLabs returned empty audio")
                return None
                
            # Convert to bytes if it's not already
            if isinstance(audio, bytes):
                audio_data = audio
            elif hasattr(audio, 'read'):  # If it's a file-like object
                audio_data = audio.read()
            else:
                logger.error(f"Unexpected audio type from ElevenLabs: {type(audio)}")
                return None
                
            logger.info(f"ElevenLabs TTS successful, generated {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error in ElevenLabs TTS: {e}")
            return None # Indicate failure for ElevenLabs

    async def _generate_with_gtts(self, text: str, language: str) -> Optional[bytes]:
        """Fallback to gTTS when ElevenLabs fails."""
        try:
            logger.info(f"Generating speech with gTTS: {text[:50]}...")
            
            from gtts import gTTS # Ensure gTTS is imported
            from io import BytesIO
            
            # Map language codes
            lang_map = {
                'es': 'es',  # Spanish
                'en': 'en'   # English
            }
            lang = lang_map.get(language, 'es')  # Default to Spanish
            
            # Create gTTS object and generate audio
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # Save to bytes buffer
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_data = audio_buffer.read()
            
            logger.info(f"gTTS TTS successful, generated {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error in gTTS generation: {e}")
            return None

    
    def audio_to_base64(self, audio_data: bytes) -> str:
        """Convert audio bytes to base64 string."""
        return base64.b64encode(audio_data).decode('utf-8')
    
    def base64_to_audio(self, base64_string: str) -> bytes:
        """Convert base64 string to audio bytes."""
        return base64.b64decode(base64_string)
