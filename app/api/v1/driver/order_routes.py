from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
)
from bson import ObjectId
from datetime import datetime, timedelta
from app.websocket.driver_socket import sio as driver_sio
from app.api.v1.driver.schemas import OrderAcceptResponse, OrderHistoryResponse, OrderStatusResponse, LatestOrdersResponse
from .order_service import update_order_status
from pymongo import ReturnDocument
from app.core.deps import get_current_user
from app.core.mongo import init_mongo
from app.websocket.manager import manager

router = APIRouter(
    prefix="/orders",
    tags=["Orders - Driver"]
)

def require_driver(user):
    if user["role"] != "driver":
        raise HTTPException(403, "Driver access only")

# ---------------- ORDER HISTORY ----------------
@router.get("/history", response_model=OrderHistoryResponse,
    summary="Get driver order history",
    description="Returns paginated completed orders (Delivered / NotDelivered) for the logged-in driver.")
async def driver_order_history(
    range: str | None = Query(None, description="7d, 1m, 1y"),
    month: str | None = Query(None, description="YYYY-MM"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=50),
    current_user=Depends(get_current_user)
):
    require_driver(current_user)

    db = await init_mongo()
    driver_id = current_user["_id"]

    query = {
        "assignedDriverId": driver_id,
        "status": {"$in": ["Delivered", "NotDelivered"]}
    }

    now = datetime.utcnow()

    # -------- DATE FILTERS --------
    if range:
        if range == "7d":
            query["createdAt"] = {"$gte": now - timedelta(days=7)}

        elif range == "1m":
            query["createdAt"] = {"$gte": now - timedelta(days=30)}

        elif range == "1y":
            query["createdAt"] = {"$gte": now - timedelta(days=365)}

    elif month:
        try:
            year, mon = map(int, month.split("-"))
            start = datetime(year, mon, 1)

            if mon == 12:
                end = datetime(year + 1, 1, 1)
            else:
                end = datetime(year, mon + 1, 1)

            query["createdAt"] = {"$gte": start, "$lt": end}
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid month format")

    # -------- PAGINATION --------
    skip = (page - 1) * limit

    cursor = (
        db.orders
        .find(query)
        .sort("createdAt", -1)
        .skip(skip)
        .limit(limit)
    )

    orders = []
    async for order in cursor:
        orders.append({
            "orderId": str(order["_id"]),
            "date": order["createdAt"],
            "amount": order.get("totalAmount"),
            "payment": order.get("paymentMethod"),
            "status": order.get("status"),

            "pickup": {
                "name": order.get("restaurant", {}).get("name"),
            },
            "delivery": {
                "address": order.get("address", {}).get("addressLine"),
            }
        })

    total = await db.orders.count_documents(query)

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "orders": orders
    }

# ---------------- LATEST COMPLETED ORDERS ----------------
@router.get(
    "/latest",
     response_model=LatestOrdersResponse,
    summary="Get latest completed orders",
    description="Returns today's summary, lifetime completed count, and last 5 delivered orders."
)
async def latest_completed_orders(
    current_user=Depends(get_current_user)
):
    require_driver(current_user)

    db = await init_mongo()
    driver_id = current_user["_id"]

    # ---------------- TIME RANGE (TODAY) ----------------
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)

    # ---------------- LATEST 5 ORDERS ----------------
    latest_cursor = (
        db.orders
        .find(
            {
                "assignedDriverId": driver_id,
                "status": "Delivered"
            }
        )
        .sort("createdAt", -1)
        .limit(5)
    )

    latest_orders = []
    async for order in latest_cursor:
        latest_orders.append({
            "orderId": str(order["_id"]),
            "date": order.get("createdAt"),
            "amount": order.get("totalAmount"),
            "payment": order.get("paymentMethod"),

            "pickup": {
                "name": order.get("restaurant", {}).get("name"),
            },
            "delivery": {
                "address": order.get("address", {}).get("addressLine"),
            }
        })

    # ---------------- TODAY SUMMARY ----------------
    today_filter = {
        "assignedDriverId": driver_id,
        "status": "Delivered",
        "createdAt": {"$gte": today_start}
    }

    today_orders_count = await db.orders.count_documents(today_filter)

    pipeline = [
        {"$match": today_filter},
        {"$group": {
            "_id": None,
            "total": {"$sum": "$totalAmount"}
        }}
    ]

    agg = await db.orders.aggregate(pipeline).to_list(length=1)
    today_earnings = agg[0]["total"] if agg else 0

    # ---------------- LIFETIME COUNT ----------------
    total_completed_orders = await db.orders.count_documents(
        {
            "assignedDriverId": driver_id,
            "status": "Delivered"
        }
    )

    return {
        "today": {
            "orders": today_orders_count,
            "earnings": round(today_earnings, 2)
        },
        "lifetime": {
            "completed_orders": total_completed_orders
        },
        "latest_orders": latest_orders
    }


@router.post(
    "/{order_id}/accept",
    response_model=OrderAcceptResponse,
)
async def accept_order(order_id: str, current_user=Depends(get_current_user)):
    require_driver(current_user)

    db = await init_mongo()
    driver_id = str(current_user["_id"])

    try:
        oid = ObjectId(order_id)
    except Exception:
        raise HTTPException(400, "Invalid order ID")

    order = await db.orders.find_one_and_update(
        {
            "_id": oid,
            "status": "NEW",
            "assignedDriverId": None
        },
        {
            "$set": {
                "assignedDriverId": driver_id,
                "status": "Assigned",
                "assignedAt": datetime.utcnow(),
                "lastStatusAt": datetime.utcnow()
            },
            "$push": {
                "timeline": {
                    "status": "Assigned",
                    "by": driver_id,
                    "at": datetime.utcnow()
                }
            }
        },
        return_document=ReturnDocument.AFTER
    )

    if not order:
        raise HTTPException(409, "Order already taken")

    # 🔔 notify THIS driver
    await manager.send_to_driver(
        driver_id,
        {
            "type": "ORDER_ASSIGNED",
            "order": {
                "orderId": order_id,
                "status": "Assigned"
            }
        }
    )

    return {
        "success": True,
        "assigned": True,
        "orderId": order_id
    }

@router.post(
     "/{order_id}/decline",
    summary="Decline an available order",
    description="Allows driver to decline an order before assignment.",
    responses={
        200: {
            "description": "Order declined",
            "content": {
                "application/json": {
                    "example": {
                        "declined": True
                    }
                }
            }
        },
        409: {
            "description": "Order cannot be declined",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Order cannot be declined"
                    }
                }
            }
        },
    },
)
async def decline_order(order_id: str, user=Depends(get_current_user)):
    require_driver(user)

    db = await init_mongo()

    result = await db.orders.update_one(
        {
            "_id": ObjectId(order_id),
            "status": "Accepted"
        },
        {
            "$set": {
                "status": "Accepted",
                "assignedDriverId": None
            },
            "$push": {
                "timeline": {
                    "status": "Declined",
                    "by": user["_id"],
                    "at": datetime.utcnow()
                }
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(409, "Order cannot be declined")

    return {"declined": True}


@router.post(
    "/{order_id}/pickup-reached",
    response_model=OrderStatusResponse,
    summary="Mark pickup as reached",
    description="Driver confirms arrival at pickup location.",)
async def pickup_reached(order_id: str, user=Depends(get_current_user)):
    require_driver(user)

    db = await init_mongo()
    await update_order_status(db, order_id, user["_id"], "PickupReached")
    return {"status": "PickupReached"}


@router.post("/{order_id}/items-collected")
async def items_collected(order_id: str, user=Depends(get_current_user)):
    require_driver(user)

    db = await init_mongo()
    await update_order_status(db, order_id, user["_id"], "ItemsCollected")
    return {"status": "ItemsCollected"}


@router.post("/{order_id}/delivery-reached")
async def delivery_reached(order_id: str, user=Depends(get_current_user)):
    require_driver(user)

    db = await init_mongo()
    await update_order_status(db, order_id, user["_id"], "DeliveryReached")
    return {"status": "DeliveryReached"}


@router.post(
             "/{order_id}/delivered",
    response_model=OrderStatusResponse,
    summary="Mark order as delivered",
    description="Final delivery confirmation by driver.",)
async def delivered(order_id: str, user=Depends(get_current_user)):
    require_driver(user)

    db = await init_mongo()
    await update_order_status(db, order_id, user["_id"], "Delivered")
    return {"status": "Delivered"}


@router.post(
     "/{order_id}/not-delivered",
    response_model=OrderStatusResponse,
    summary="Mark order as not delivered",
    description="Marks order as not delivered due to an issue.",
)
async def not_delivered(order_id: str, user=Depends(get_current_user)):
    require_driver(user)

    db = await init_mongo()
    await update_order_status(db, order_id, user["_id"], "NotDelivered")
    return {"status": "NotDelivered"}


# ---------------- ACTIVE ORDERS (RECOVERY) ----------------
@router.get(
    "/active",
    summary="Get active order for driver",
    description="Used to restore state after app restart / socket reconnect"
)
async def get_active_orders(current_user=Depends(get_current_user)):
    require_driver(current_user)

    db = await init_mongo()
    driver_id = current_user["_id"]

    ACTIVE_STATUSES = [
        "Assigned",
        "PickupReached",
        "ItemsCollected",
        "DeliveryReached",
    ]

    cursor = (
        db.orders
        .find(
            {
                "assignedDriverId": driver_id,
                "status": {"$in": ACTIVE_STATUSES},
            }
        )
        .sort("createdAt", 1)
    )

    orders = []

    async for order in cursor:
        orders.append(
            {
                "orderId": str(order["_id"]),
                "status": order.get("status"),

                "totalAmount": order.get("totalAmount"),
                "paymentMethod": order.get("paymentMethod"),

                "distanceKm": order.get("distanceKm"),
                "etaMin": order.get("etaMin"),
                "cashToCollect": order.get("cashToCollect"),

                "pickup": {
                    "name": order.get("restaurant", {}).get("name"),
                    "address": order.get("restaurant", {})
                        .get("address", {})
                        .get("addressLine"),
                    "lat": order.get("restaurant", {}).get("lat"),
                    "lng": order.get("restaurant", {}).get("lng"),
                },
                "delivery": {
                    "address": order.get("address", {})
                        .get("addressLine"),
                    "lat": order.get("address", {}).get("lat"),
                    "lng": order.get("address", {}).get("lng"),
                },
                "createdAt": order.get("createdAt"),
            }
        )

    return {"orders": orders}