from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from app.websocket.manager import manager
from app.websocket.event import order_event

ALLOWED_TRANSITIONS = {
    "Assigned": ["PickupReached"],
    "PickupReached": ["ItemsCollected"],
    "ItemsCollected": ["DeliveryReached"],
    "DeliveryReached": ["Delivered", "NotDelivered"],
}

async def update_order_status(db, order_id: str, driver_id, new_status: str):
    try:
        oid = ObjectId(order_id)
    except:
        raise HTTPException(400, "Invalid order ID")

    order = await db.orders.find_one({
        "_id": oid,
        "assignedDriverId": driver_id
    })

    if not order:
        raise HTTPException(404, "Order not found")

    current_status = order.get("status")

    if current_status == new_status:
        return

    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise HTTPException(
            400,
            f"Invalid transition {current_status} → {new_status}"
        )

    now = datetime.utcnow()

    await db.orders.update_one(
        {"_id": oid},
        {
            "$set": {
                "status": new_status,
                "lastStatusAt": now
            },
            "$push": {
                "timeline": {
                    "status": new_status,
                    "at": now,
                    "by": "driver"
                }
            }
        }
    )

    event = order_event(
        order_id=str(oid),
        event=new_status,
        payload={
            "driverId": str(driver_id),
            "timestamp": now.isoformat()
        }
    )

    await manager.broadcast(event)
    await manager.broadcast_to_admin(event)