from fastapi import APIRouter, Request, Response
from app.services.speech_service import SpeechService
from app.services.scheduler_agent import SchedulerAgent
from app.services.twilio_service import TwilioService

router = APIRouter()

speech = SpeechService()
scheduler = SchedulerAgent()
twilio = TwilioService()

@router.post("/voice")
async def voice(request: Request):
    form = await request.form()
    form_data = dict(form)

    # Try to parse user input (speech or DTMF)
    parsed = twilio.parse_user_input(form_data)
    user_input = parsed.get('input', '')

    # If audio file is present, transcribe it
    if 'audio' in form:
        audio_file = form['audio']
        audio_bytes = await audio_file.read()
        transcript = await speech.transcribe_audio(audio_bytes)
        if transcript:
            user_input = transcript

    # Process input with the scheduler agent
    response_text, hints = await scheduler.process_input(user_input)

    # Generate TTS audio (returns bytes)
    audio_bytes = await speech.generate_speech(response_text)
    # For Twilio, you need to serve the audio file via a URL. Here, you would upload to S3 or static hosting and get a URL.
    # For now, let's assume you have a function to upload and return a URL: upload_audio_and_get_url(audio_bytes)
    # For this example, we'll fallback to a simple TwiML response with text.

    # If you have audio_url, use:
    # twiml = twilio.generate_voice_response_with_audio(audio_url, hints=hints)
    # Otherwise, fallback:
    twiml = twilio.generate_simple_response(response_text)

    return Response(content=twiml, media_type="application/xml")

@router.post("/status_callback")
async def status_callback():
    return {"message": "status callback received"}
