# PraisonAI Phone Agent

A robust, flexible, and LLM-powered conversational agent for healthcare scheduling and triage, built with FastAPI.

## Features
- Flexible natural language input (LLM + fuzzy matching)
- Patient scheduling and triage flows
- Twilio voice integration
- Speech-to-text and text-to-speech (OpenAI Whisper, ElevenLabs, gTTS)
- Modular, test-driven design

## Project Structure
```
app/
  app.py                # FastAPI app entrypoint
  routes/
    twilio.py           # Voice and status callback endpoints
  services/
    scheduler_agent.py  # Main agent logic (LLM/fuzzy matching)
    speech_service.py   # Speech-to-text and text-to-speech
    twilio_service.py   # Twilio integration
    helpers.py          # Matching helpers (LLM, fuzzy)
    email_service.py    # Email forwarding (optional)
  tools/                # Tool wrappers (optional)
create_praisonai_structure.py # Project scaffolding script
README.md
requirements.txt / pyproject.toml
```

## Setup
1. **Clone the repo:**
   ```bash
   git clone https://github.com/Proconnai/prasionai-phone-agent.git
   cd prasionai-phone-agent
   ```
2. **Create and activate a virtual environment:**
   ```bash
   uv venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt  # or use pyproject.toml with uv/pdm/poetry
   ```
4. **Set environment variables:**
   - Copy `.env.example` to `.env` and fill in:
     - `OPENAI_API_KEY`
     - `ELEVENLABS_API_KEY`
     - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
     - `PROVIDER_1_NAME`, `PROVIDER_2_NAME`

## Running the App
```bash
uvicorn app.app:app --reload
```

## Testing
```bash
pytest --maxfail=3 --disable-warnings -v
```

## Contributing
- Please document new features and add tests.
- Use clear commit messages.

## License
MIT
