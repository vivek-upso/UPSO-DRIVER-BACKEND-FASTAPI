from datetime import datetime, timedelta
from jose import jwt, JWTError
from uuid import uuid4
from app.core.mongo import init_mongo
from app.core.config import settings

ALGORITHM = "HS256"



# ---------------- ACCESS TOKEN ----------------
def create_access_token(data: dict, minutes: int = 15):
    payload = data.copy()
    payload.update({
        "exp": datetime.utcnow() + timedelta(minutes=minutes),
        "jti": str(uuid4()),
        "type": "access",
    })
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ---------------- REFRESH TOKEN ----------------
async def create_refresh_token(user_id: str):
    db = await init_mongo()

    token = str(uuid4())

    await db.refresh_tokens.insert_one({
        "user_id": user_id,
        "token": token,
        "expires_at": datetime.utcnow() + timedelta(days=14),
        "revoked": False,
        "created_at": datetime.utcnow(),
    })

    return token

# ------------------
# DUMMY PASSWORD UTILS (TEMP)
# ------------------
def hash_text(text: str) -> str:
    return text


def verify_text(plain: str, hashed: str) -> bool:
    return plain == hashed


# ------------------
# DEPRECATED (COMPAT)
# ------------------
def get_current_token():
    raise RuntimeError(
        "get_current_token is removed. Use get_current_user from app.core.deps"
    )
