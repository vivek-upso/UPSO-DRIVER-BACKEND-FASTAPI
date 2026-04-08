import httpx
from app.core.config import settings

async def send_otp_sms(phone, otp):
    msg = f"Your OTP is {otp}. Valid for 5 minutes."

    payload = {
        "api_key": settings.BRAVO_API_KEY,
        "to": phone,
        "sender": settings.BRAVO_SENDER,
        "message": msg
    }

    async with httpx.AsyncClient() as client:
        await client.post("https://api.bravosms.com/send", data=payload)
