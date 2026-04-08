from datetime import datetime
from bson import ObjectId
from app.core.mongo import init_mongo


async def update_driver_status(user_id: str, status: str):
    db = await init_mongo()

    update = {
        "is_online": status == "online",
        "last_online_at": datetime.utcnow() if status == "online" else None,
    }

    res = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update}
    )

    if res.matched_count == 0:
        raise Exception("Driver not found")

    return update


async def get_driver_status(user_id: str):
    db = await init_mongo()

    user = await db.users.find_one(
        {"_id": ObjectId(user_id)},
        {"is_online": 1, "last_online_at": 1}
    )

    if not user:
        raise Exception("Driver not found")

    return {
        "is_online": user.get("is_online", False),
        "last_online_at": user.get("last_online_at")
    }

def calculate_profile_completion(user: dict) -> int:
    fields = [
        user.get("name"),
        user.get("gender"),
        user.get("dob"),
        user.get("address"),
        user.get("driving_license_no"),
        user.get("bank", {}).get("account_no"),
        user.get("bank", {}).get("ifsc"),
    ]

    filled = sum(1 for f in fields if f)
    total = len(fields)

    return int((filled / total) * 100)

