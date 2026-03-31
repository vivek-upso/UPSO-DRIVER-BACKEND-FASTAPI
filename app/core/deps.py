from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from jose import JWTError

from app.core.security import decode_access_token
from app.core.mongo import init_mongo

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login/verify-otp"
)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid access token")

    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid access token")

    try:
        user_id = ObjectId(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    db = await init_mongo()
    user = await db.users.find_one({"_id": user_id})

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ---------------- ADMIN ----------------

admin_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/admin/login"
)


async def get_current_admin(token: str = Depends(admin_oauth2_scheme)):
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        admin_id = ObjectId(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    db = await init_mongo()
    admin = await db.admins.find_one({"_id": admin_id})

    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")

    return admin