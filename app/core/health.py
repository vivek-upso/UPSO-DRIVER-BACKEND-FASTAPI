from datetime import datetime
from app.core.mongo import db
import asyncio

async def check_mongo():
    try:
        await db.command("ping")
        return {"status": "up"}
    except Exception as e:
        return {"status": "down", "error": str(e)}

async def health_check():
    mongo_status = await check_mongo()

    overall = "healthy" if mongo_status["status"] == "up" else "degraded"

    return {
        "status": overall,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "mongo": mongo_status
        }
    }
