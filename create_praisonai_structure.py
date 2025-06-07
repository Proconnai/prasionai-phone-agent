import os

# Define folders and files to create
structure = {
    "app": [
        "app.py",
        "routes/twilio.py",
        "services/speech_service.py",
        "services/twilio_service.py",
        "services/scheduler_agent.py",
        "services/email_service.py",
        "tools/SpeechService.py",
        "tools/TwilioService.py",
        "tools/EmailForwarder.py"
    ],
    ".": [
        ".env",
        "pyproject.toml",
        "agents.yaml",
        "run.sh",
        "Dockerfile",
        "README.md",
        ".gitignore"
    ]
}

for base, files in structure.items():
    for file in files:
        full_path = os.path.join(base, file)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write("")  # Empty file for now

print("✅ Project structure created.")
