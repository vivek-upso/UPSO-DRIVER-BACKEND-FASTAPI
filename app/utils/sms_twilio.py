from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from app.core.config import settings

# Create client once (important)
twilio_client = Client(
    settings.TWILIO_SID,
    settings.TWILIO_AUTH_TOKEN
)


def send_otp_twilio(phone: str, otp: str) -> str:
    message = (
        f"Your UPSO OTP is {otp}. "
        "Valid for 5 minutes. Do not share."
    )

    try:
        response = twilio_client.messages.create(
            body=message,
            from_=settings.TWILIO_FROM,
            to=phone
        )
        return response.sid

    except TwilioRestException as e:
        # Log this in real apps (Sentry / logs)
        raise RuntimeError(f"Twilio SMS failed: {e.msg}")
