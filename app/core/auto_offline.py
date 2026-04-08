# app/core/auto_offline.py
from datetime import datetime, timedelta
import asyncio
from app.core.mongo import init_mongo

INACTIVITY_MINUTES = 2

async def auto_offline_worker():
    while True:
        try:
            db = await init_mongo()
            cutoff = datetime.utcnow() - timedelta(minutes=INACTIVITY_MINUTES)

            result = await db.users.update_many(
                {
                    "is_online": True,
                    "last_active_at": {"$lt": cutoff}
                },
                {
                    "$set": {"is_online": False}
                }
            )

            if result.modified_count:
                print(f"Auto-offline drivers: {result.modified_count}")

        except Exception as e:
            print("Auto-offline error:", e)

        await asyncio.sleep(30)  # check every 30s
