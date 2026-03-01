import smtplib
from email.message import EmailMessage
from app.core.config import (
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_USERNAME,
    EMAIL_PASSWORD
)

def send_otp_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg["Subject"] = "SmartAttend - OTP Verification"
    msg["From"] = EMAIL_USERNAME
    msg["To"] = to_email

    msg.set_content(f"""
Hello,

Your OTP for SmartAttend account activation is: {otp}

This OTP will expire in 5 minutes.

Thank you.
""")

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.send_message(msg)
