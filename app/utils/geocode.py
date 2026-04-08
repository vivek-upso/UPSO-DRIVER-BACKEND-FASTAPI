import json
import httpx
from app.core.config import settings
from app.core.redis import redis_client

GCP_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

CACHE_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days


def _cache_key(address: str) -> str:
    return f"geocode:{address.lower().strip()}"


async def geocode_address(address: str):
    if not address:
        return None, None

    key = _cache_key(address)

    #  Try Redis cache
    try:
        cached = await redis_client.get(key)
        if cached:
            data = json.loads(cached)
            return data["lat"], data["lng"]
    except Exception:
        pass  # Redis down → fallback safely

    #  Call Google API
    async with httpx.AsyncClient(timeout=5) as client:
        res = await client.get(
            GCP_GEOCODE_URL,
            params={
                "address": address,
                "key": settings.GCP_GEOCODING_API_KEY,
            }
        )
        res.raise_for_status()
        data = res.json()

    if not data.get("results"):
        return None, None

    location = data["results"][0]["geometry"]["location"]
    lat = location.get("lat")
    lng = location.get("lng")

    #  Store in Redis
    try:
        await redis_client.setex(
            key,
            CACHE_TTL_SECONDS,
            json.dumps({"lat": lat, "lng": lng})
        )
    except Exception:
        pass  # Don’t break flow if Redis fails

    return lat, lng
