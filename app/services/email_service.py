import smtplib
from email.mime.text import MIMEText
import os

class EmailService:
    def send(self, subject, body):
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = os.getenv("EMAIL_FROM")
        msg["To"] = os.getenv("EMAIL_TO")
        with smtplib.SMTP(os.getenv("SMTP_HOST"), 587) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
            server.send_message(msg)
