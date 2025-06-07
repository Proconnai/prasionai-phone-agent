"""Service for handling Twilio voice interactions and call bridging."""

import os
import logging
from typing import Dict, Optional, List
from twilio.twiml.voice_response import VoiceResponse, Gather, Record, Play
from twilio.rest import Client

logger = logging.getLogger(__name__)

class TwilioService:
    """Handles Twilio voice interactions and call bridging."""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.base_url = os.getenv('BASE_URL', 'http://localhost:5011')
        
        # Get the phone number and clean it if necessary
        phone_number = os.getenv('TWILIO_PHONE_NUMBER', '')
        if '#' in phone_number:
            # Remove any inline comments
            phone_number = phone_number.split('#')[0].strip()
            
        self.phone_number = phone_number
        logger.info(f"Using Twilio phone number: {self.phone_number}")
        self.client = Client(self.account_sid, self.auth_token)
    
    def generate_voice_response_with_audio(
        self, 
        audio_url: str, 
        action: str = '/voice',
        timeout: int = 10,  # Increased timeout to give users more time to respond
        finish_on_key: str = '#',
        speech_timeout: str = 'auto', 
        language: str = 'es-ES',
        hints: Optional[List[str]] = None
    ) -> str:
        """
        Generate a TwiML response that plays audio and gathers user input via speech or DTMF.
        
        Args:
            audio_url: URL of the audio file to play
            action: URL to send the user's input to
            timeout: Time in seconds to wait for user input (default: 10)
            finish_on_key: Key to end input (default: '#')
            speech_timeout: How long to wait for speech input (default: 'auto')
            language: Language for speech recognition (default: 'es-ES')
            hints: Optional list of words to help with speech recognition
        """
        response = VoiceResponse()
        
        # Configure the gather with speech recognition
        gather = Gather(
            input='speech dtmf',
            action=action,
            method='POST',
            timeout=timeout,
            num_digits=1,  
            speech_timeout='3', 
            language=language if '-' in language else f"{language}-US", 
            finish_on_key=finish_on_key,
            hints=','.join(hints) if hints and isinstance(hints, list) and len(hints) > 0 else None,
            enhanced=True
        )
        
        # Play the audio message
        gather.play(audio_url)
        
        # Add a silent prompt (empty say) to avoid the robotic voice
        gather.say('', voice='Polly.Lupe-Neural')  
        
        # Add the gather to the response
        response.append(gather)
        
        # If no input, redirect to the same endpoint
        response.redirect(method='POST', url=action)
        
        return str(response)
    
    def generate_simple_response(self, text: str, hangup: bool = False) -> str:
        """
        Generate a simple TwiML response with text.
        Used for fallback scenarios.
        
        Args:
            text: The text to speak
            hangup: Whether to hang up after speaking
            
        Returns:
            str: TwiML XML string
        """
        response = VoiceResponse()
        response.say(text)
        
        if hangup:
            response.hangup()
        
        return str(response)
    
    async def send_sms(self, to_number: str, message: str) -> bool:
        """
        Send an SMS message.
        
        Args:
            to_number: The phone number to send the message to
            message: The message to send
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_number
            )
            logger.info(f"Sent SMS to {to_number}: {message.body}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {e}")
            return False
    
    async def send_appointment_confirmation(
        self, 
        to_number: str, 
        patient_name: str, 
        provider_name: str, 
        appointment_date: str,
        appointment_time: str
    ) -> bool:
        """
        Send an appointment confirmation SMS.
        
        Args:
            to_number: The patient's phone number
            patient_name: The patient's name
            provider_name: The provider's name
            appointment_date: The appointment date
            appointment_time: The appointment time
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        message = (
            f"Hi {patient_name},\n\n"
            f"Your appointment with {provider_name} has been confirmed for {appointment_date} at {appointment_time}.\n\n"
            "Please arrive 15 minutes early to complete any necessary paperwork.\n\n"
            "If you need to reschedule or cancel, please call us at (555) 123-4567 at least 24 hours in advance.\n\n"
            "Thank you for choosing Family Care Team!"
        )
        
        return await self.send_sms(to_number, message)
    
    def parse_user_input(self, form_data: Dict) -> dict:
        """
        Parse user input from Twilio form data.
        
        Args:
            form_data: The form data from Twilio
            
        Returns:
            dict: Contains the user's input (speech or DTMF) and confidence score
        """
        # Try to get speech input first, fall back to DTMF
        user_input = form_data.get('SpeechResult', '').strip()
        confidence = float(form_data.get('Confidence', 0))
        
        # If no speech input or very low confidence, check for DTMF
        if not user_input:
            user_input = form_data.get('Digits', '').strip()
            # DTMF input is always high confidence if present
            if user_input:
                confidence = 1.0
        
        # Log the input and confidence for debugging
        logger.info(f"Parsed user input: '{user_input}' with confidence: {confidence}")
        
        return {
            'input': user_input,
            'confidence': confidence
        }
