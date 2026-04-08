from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_current_user
from app.core.mongo import init_mongo
from app.websocket.manager import manager

router = APIRouter(
    prefix="/presence",
    tags=["Presence - Driver"]
)

@router.post("/online")
async def driver_online(current_user=Depends(get_current_user)):

    db = await init_mongo()

    await db.users.update_one(
        {"_id": current_user["_id"]},   # ObjectId – correct
        {"$set": {"is_online": True}}
    )

    try:
        await manager.set_driver_online(str(current_user["_id"]))  # string for WS
    except Exception as e:
        print("WS error (online):", e)

    return {"status": "online"}


@router.post("/offline")
async def driver_offline(current_user=Depends(get_current_user)):
    db = await init_mongo()

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"is_online": False}}
    )

    try:
        await manager.set_driver_offline(str(current_user["_id"]))
    except Exception as e:
        print("WS error (offline):", e)

    return {"status": "offline"}
