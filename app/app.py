from fastapi import FastAPI
from app.routes import twilio

app = FastAPI()
app.include_router(twilio.router)
