# app/core/mongo.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

_client: AsyncIOMotorClient | None = None
db = None

async def init_mongo():
    global _client, db

    if db is not None:
        return db

    _client = AsyncIOMotorClient(
        settings.MONGO_URI,
        serverSelectionTimeoutMS=3000
    )

    db = _client.get_default_database()
    await db.command("ping")

    print("✅ Mongo connected")
    return db


def get_db():
    if db is None:
        raise RuntimeError("Mongo not initialized")
    return db