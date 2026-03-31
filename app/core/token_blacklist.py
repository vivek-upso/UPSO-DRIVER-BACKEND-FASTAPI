import redis.asyncio as redis
from app.core.config import settings

PREFIX = "bl:"
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)


async def blacklist_token(jti: str, exp_seconds: int):
    try:
        await redis_client.setex(f"{PREFIX}{jti}", exp_seconds, "1")
    except Exception:
        pass  # do not crash app


async def is_blacklisted(jti: str) -> bool:
    try:
        return await redis_client.exists(f"{PREFIX}{jti}") == 1
    except Exception:
        # Redis down → allow token (DEV SAFE)
        return False
