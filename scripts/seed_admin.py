import asyncio
from app.core.mongo import init_mongo
from app.core.security import hash_text
from datetime import datetime

async def seed_admin():
    db = await init_mongo()

    email = "admin@upso.com"

    exists = await db.admins.find_one({"email": email})
    if exists:
        print("Admin already exists")
        return

    await db.admins.insert_one({
        "name": "Super Admin",
        "email": email,
        "password_hash": hash_text("Admin@123"),
        "is_active": True,
        "created_at": datetime.utcnow()
    })

    print("Admin created")
    print("Email: admin@upso.com")
    print("Password: Admin@123")

asyncio.run(seed_admin())
