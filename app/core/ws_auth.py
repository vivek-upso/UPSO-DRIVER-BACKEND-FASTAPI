from fastapi import WebSocketException, status
from jose import JWTError, jwt
from bson import ObjectId
from app.core.config import settings
from app.core.mongo import init_mongo

ALGORITHM = "HS256"


def _decode_ws_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[ALGORITHM],
        )

        # try common keys
        return (
            payload.get("user_id")
            or payload.get("sub")
            or payload.get("id")
        )

    except JWTError:
        return None



async def get_user_from_ws_token(token: str):
    user_id = _decode_ws_token(token)
    if not user_id:
        return None

    db = await init_mongo()

    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None

    return user


# -------------------------------------------------
# ADMIN WS AUTH (THIS FIXES YOUR ERROR)
# -------------------------------------------------
async def get_admin_from_ws_token(token: str):
    admin_id = _decode_ws_token(token)

    db = await init_mongo()
    admin = await db.admins.find_one(
        {"_id": ObjectId(admin_id)}
    )

    if not admin:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION
        )

    return admin
