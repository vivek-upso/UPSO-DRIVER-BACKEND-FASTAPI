from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from uuid import uuid4
from datetime import datetime, timedelta
import random

from app.api.v1.auth.schemas import SendOtpSchema, VerifyOtpSchema, RefreshTokenSchema, RegisterVerifyOtpResponse, CompleteProfileResponse
from app.core.config import settings
from app.core.mongo import init_mongo
from app.core.security import create_access_token, create_refresh_token

router = APIRouter(
    prefix="/auth",
    tags=["Auth - Driver"]
)

# ================= SEND OTP =================
@router.get('/')
async def getoutput():
    return 'welcome to auth'

@router.post(
    "/login/send-otp",
    summary="Send login OTP",
    responses={
        200: {
            "description": "OTP sent successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "OTP sent"
                    }
                }
            }
        }
    }
)
async def send_login_otp(payload: SendOtpSchema):
    db = await init_mongo()

    otp = "111111"
    # otp = str(random.randint(100000, 999999))

    await db.otps.delete_many({"phone": payload.phone, "purpose": "login"})

    await db.otps.insert_one({
        "phone": payload.phone,
        "otp": otp,
        "purpose": "login",
        "expires_at": datetime.utcnow() + timedelta(minutes=5),
        "attempts": 0,
        "used": False
    })

    # TODO: send SMS
    print("LOGIN OTP:", otp)

    return {"message": "OTP sent"}



@router.post(
    "/register/send-otp",
    summary="Send registration OTP",
    responses={
        200: {
            "description": "OTP sent successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "OTP sent"
                    }
                }
            }
        }
    }
)
async def send_register_otp(payload: SendOtpSchema):
    return {"message": "OTP sent"}

# ================= VERIFY OTP =================

@router.post(
    "/login/verify-otp",
    summary="Verify OTP and login",
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "def50200abcd...",
                        "user": {
                            "id": "65f1c9b7b41234abcd",
                            "name": "Ravi Kumar",
                            "phone": "9876543210",
                            "role": "driver"
                        }
                    }
                }
            }
        },
        400: {
            "description": "OTP expired / too many attempts",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "OTP expired"
                    }
                }
            }
        },
        401: {
            "description": "Invalid OTP",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid OTP"
                    }
                }
            }
        },
        404: {
            "description": "User not registered",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User not registered"
                    }
                }
            }
        }
    }
)
async def login_verify_otp(payload: VerifyOtpSchema):
    db = await init_mongo()

    otp_doc = await db.otps.find_one({
        "phone": payload.phone,
        "purpose": "login",
        "used": False
    })

    if not otp_doc:
        raise HTTPException(400, "OTP not found")

    if otp_doc["expires_at"] < datetime.utcnow():
        raise HTTPException(400, "OTP expired")

    if otp_doc["attempts"] >= 3:
        raise HTTPException(400, "Too many attempts")

    if otp_doc["otp"] != payload.otp:
        await db.otps.update_one(
            {"_id": otp_doc["_id"]},
            {"$inc": {"attempts": 1}}
        )
        raise HTTPException(401, "Invalid OTP")

    await db.otps.update_one(
        {"_id": otp_doc["_id"]},
        {"$set": {"used": True}}
    )

    user = await db.users.find_one({"phone": payload.phone})
    if not user:
        raise HTTPException(404, "User not registered")

    access_token = create_access_token(
        {"sub": str(user["_id"]), "role": user["role"]},
        minutes=15
    )

    refresh_token = await create_refresh_token(str(user["_id"]))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "phone": user["phone"],
            "role": user["role"]
        }
    }
    
@router.post(
    "/refresh",
    summary="Refresh access token",
    description="Issues a new access token if the refresh token is valid and not expired (refresh token valid for 14 days).",
    responses={
        200: {
            "description": "New tokens issued",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIs...",
                        "refresh_token": "def5020099aa..."
                    }
                }
            }
        },
        401: {
            "description": "Invalid or expired refresh token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid refresh token"
                    }
                }
            }
        }
    }
)
async def refresh_token(payload: RefreshTokenSchema):
    db = await init_mongo()

    token_doc = await db.refresh_tokens.find_one({
        "token": payload.refresh_token,
        "revoked": False,
    })

    if not token_doc:
        raise HTTPException(401, "Invalid refresh token")

    if token_doc["expires_at"] < datetime.utcnow():
        raise HTTPException(401, "Refresh token expired")

    # rotate refresh token
    await db.refresh_tokens.update_one(
        {"_id": token_doc["_id"]},
        {"$set": {"revoked": True}}
    )

    access_token = create_access_token({
        "sub": token_doc["user_id"],
        "role": "driver",
    })

    new_refresh_token = await create_refresh_token(token_doc["user_id"])

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
    }

@router.post("/register/verify-otp")
async def register_verify_otp(payload: VerifyOtpSchema):
    if payload.otp != settings.DUMMY_OTP:
        raise HTTPException(401, "Invalid OTP")

    otp_token = create_access_token({
        "phone": payload.phone,
        "type": "register_otp"
    })

    return {"otp_token": otp_token}


# ================= COMPLETE PROFILE =================
@router.post(
    "/register/complete-profile",
    response_model=CompleteProfileResponse,
    summary="Complete driver profile",
    description="Completes driver profile and returns access & refresh tokens",
    responses={
        400: {
            "description": "User already exists",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User already exists"
                    }
                }
            }
        }
    }
)
async def complete_profile(
    phone: str = Form(...),
    name: str = Form(...),
    vehicle_type: str = Form(...),
    license_no: str | None = Form(None),
    license_file: UploadFile | None = File(None),
):
    db = await init_mongo()

    if await db.users.find_one({"phone": phone}):
        raise HTTPException(400, "User already exists")

    # file upload hook (Cloudinary later)
    if license_file:
        print("License filename:", license_file.filename)

    user = {
        "phone": phone,
        "name": name,
        "vehicle_type": vehicle_type,
        "license_no": license_no,
        "role": "driver",
        "profile_completed": True,
        "is_online": False,
        "created_at": datetime.utcnow(),
    }

    result = await db.users.insert_one(user)

    access_token = create_access_token(
        {"sub": str(result.inserted_id), "role": "driver"},
        minutes=15
    )

    refresh_token = await create_refresh_token(str(result.inserted_id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "profile_completed": True
    }


# ================= LOGOUT =================

@router.post(
    "/logout",
    summary="Logout user",
    responses={
        200: {
            "description": "Logged out",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Logged out"
                    }
                }
            }
        }
    }
)
async def logout():
    return {"message": "Logged out"}
