# app/utils/distance.py
import httpx
from app.core.config import settings

DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


async def get_distance_eta(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
):
    params = {
        "origins": f"{origin_lat},{origin_lng}",
        "destinations": f"{dest_lat},{dest_lng}",
        "key": settings.GCP_GEOCODING_API_KEY,
        "units": "metric",
    }

    async with httpx.AsyncClient(timeout=5) as client:
        res = await client.get(DISTANCE_MATRIX_URL, params=params)
        data = res.json()

    if data.get("status") != "OK":
        return None, None

    element = data["rows"][0]["elements"][0]

    if element.get("status") != "OK":
        return None, None

    distance_km = element["distance"]["value"] / 1000
    duration_min = element["duration"]["value"] / 60

    return round(distance_km, 2), round(duration_min)
