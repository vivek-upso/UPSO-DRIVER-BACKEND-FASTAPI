from fastapi import HTTPException
from app.core.mongo import init_mongo
from app.core.security import create_access_token, verify_text

async def admin_login(email: str, password: str):
    db = await init_mongo()

    admin = await db.admins.find_one({"email": email})
    if not admin:
        raise HTTPException(401, "Invalid email or password")

    if not verify_text(password, admin["password_hash"]):
        raise HTTPException(401, "Invalid email or password")

    if not admin.get("is_active", True):
        raise HTTPException(403, "Admin account disabled")

    # IMPORTANT: include role + sub
    access_token = create_access_token(
        data={
            "sub": str(admin["_id"]),
            "role": "admin",
        }
    )

    return access_token