import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

async def test_mongo():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    print(f"URI: {uri}")
    client = AsyncIOMotorClient(uri)
    db = client.get_default_database()
    print(f"DB: {db}")
    if db is not None:
        try:
            await db.command("ping")
            print("Ping successful")
        except Exception as e:
            print(f"Ping failed: {e}")
    else:
        print("DB is None!")

if __name__ == "__main__":
    asyncio.run(test_mongo())
