from fastapi import APIRouter, Depends, Query, HTTPException
from bson import ObjectId
from app.core.deps import get_current_admin
from app.core.mongo import init_mongo

router = APIRouter(prefix="/orders", tags=["Admin - Orders"])

def format_address(addr: dict | None) -> str | None:
    if not addr:
        return None

    parts = [
        addr.get("addressLine"),
        addr.get("city"),
        addr.get("postalCode"),
        addr.get("country"),
    ]

    return ", ".join([p for p in parts if p])
# ===============================
# LIST ORDERS
# ===============================
@router.get("")
async def list_orders(
    status: str | None = Query(None),
    admin=Depends(get_current_admin),
):
    db = await init_mongo()

    query = {}
    if status:
        query["status"] = status

    cursor = (
        db.orders
        .find(query)
        .sort("createdAt", -1)
        .limit(100)
    )

    orders = []
    async for o in cursor:
        restaurant = o.get("restaurant", {})
        restaurant_addr = restaurant.get("address", {})
        drop_addr = o.get("address")

        orders.append({
            "orderId": str(o["_id"]),
            "status": o.get("status"),

            # FULL pickup address
            "pickup": {
                "name": restaurant.get("name"),
                "address": format_address(restaurant_addr),
            },

            # FULL drop address
            "drop": format_address(drop_addr),

            "payment": o.get("paymentMethod"),
            "createdAt": o.get("createdAt"),
        })

    return orders

# ===============================
# GET ORDER DETAILS
# ===============================
@router.get("/{order_id}")
async def get_order(
    order_id: str,
    admin=Depends(get_current_admin),
):
    db = await init_mongo()

    try:
        oid = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order ID")

    order = await db.orders.find_one({"_id": oid})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "orderId": str(order["_id"]),
        "status": order.get("status"),
        "lastStatusAt": order.get("lastStatusAt"),
        "timeline": order.get("timeline", []),

        "driver": {
            "id": (
                str(order.get("assignedDriverId"))
                if order.get("assignedDriverId")
                else None
            )
        },

        "pickup": order.get("restaurant"),
        "drop": order.get("address"),

        "payment": {
            "method": order.get("paymentMethod"),
            "amount": order.get("totalAmount"),
        },

        "createdAt": order.get("createdAt"),
    }