import pytest
from fastapi.testclient import TestClient
from app.app import app

client = TestClient(app)

def test_voice_route_text():
    # Simulate a full conversation with form data (no audio)
    response = client.post("/voice", data={"SpeechResult": "John Doe", "Confidence": "0.9"})
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]
    assert "date of birth" in response.text.lower()

    response = client.post("/voice", data={"SpeechResult": "01/01/1990", "Confidence": "0.9"})
    assert response.status_code == 200
    assert "phone number" in response.text.lower()

    response = client.post("/voice", data={"SpeechResult": "5551234567", "Confidence": "0.9"})
    assert response.status_code == 200
    assert "reason for your call" in response.text.lower()

    response = client.post("/voice", data={"SpeechResult": "I want to book an appointment", "Confidence": "0.9"})
    assert response.status_code == 200
    assert "new or existing patient" in response.text.lower() 