import random
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from app.core.mongo import init_mongo
from app.core.security import hash_text, verify_text
from app.core.jwt import create_access_token
from app.core.config import settings

OTP_EXP_MIN = 5


# ================= OTP HELPERS =================

def generate_otp() -> str:
    return "111111" if settings.USE_DUMMY_OTP else str(random.randint(100000, 999999))


async def create_otp(phone: str, purpose: str):
    db = await init_mongo()
    otp = generate_otp()

    await db.otp_requests.insert_one({
        "phone": phone,
        "purpose": purpose,
        "otp_hash": hash_text(otp),
        "expires_at": datetime.utcnow() + timedelta(minutes=OTP_EXP_MIN),
        "created_at": datetime.utcnow(),
    })

    # SMS integration later
    print(f"[OTP] {phone} ({purpose}) => {otp}")


async def verify_otp(phone: str, otp: str, purpose: str):
    db = await init_mongo()

    record = await db.otp_requests.find_one(
        {"phone": phone, "purpose": purpose},
        sort=[("created_at", -1)]
    )

    if not record:
        raise HTTPException(400, "OTP not found")

    if record["expires_at"] < datetime.utcnow():
        raise HTTPException(400, "OTP expired")

    if not verify_text(otp, record["otp_hash"]):
        raise HTTPException(400, "Invalid OTP")

    # one-time use OTP
    await db.otp_requests.delete_one({"_id": record["_id"]})


# ================= REGISTER =================

async def register_send_otp(phone: str):
    db = await init_mongo()

    if await db.users.find_one({"phone": phone}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This phone number already exists",
        )

    await create_otp(phone, "register")


async def register_verify_otp(phone: str, otp: str) -> str:
    """
    STEP 2:
    Verify OTP and return TEMP token
    """
    await verify_otp(phone, otp, "register")

    otp_token = create_access_token({
        "phone": phone,
        "type": "register_otp",
    })

    return otp_token


async def create_driver_profile(
    phone: str,
    name: str,
    vehicle_type: str,
    license_no: str | None,
    license_image: dict | None,
) -> str:
    """
    STEP 3:
    Create user and return FINAL access token
    """
    db = await init_mongo()

    if await db.users.find_one({"phone": phone}):
        raise HTTPException(400, "User already exists")

    user = {
        "phone": phone,
        "name": name,
        "vehicle_type": vehicle_type,
        "license_no": license_no,
        "license_image": license_image,
        "role": "driver",
        "profile_completed": True,
        "is_online": False,
        "created_at": datetime.utcnow(),
    }

    result = await db.users.insert_one(user)

    token = create_access_token({
        "user_id": str(result.inserted_id),
        "phone": phone,
        "role": "driver",
    })

    return token


# ================= LOGIN =================

async def login_send_otp(phone: str):
    db = await init_mongo()

    if not await db.users.find_one({"phone": phone}):
        raise HTTPException(404, "User not registered")

    await create_otp(phone, "login")


async def login_verify_otp(phone: str, otp: str):
    await verify_otp(phone, otp, "login")

    db = await init_mongo()
    user = await db.users.find_one({"phone": phone})

    token = create_access_token({
        "user_id": str(user["_id"]),
        "phone": phone,
        "role": user.get("role", "driver"),
    })

    return token, user
