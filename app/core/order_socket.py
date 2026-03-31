# app/core/order_socket.py

import asyncio
import contextlib
import socketio
from bson import ObjectId
from datetime import datetime, timedelta
from app.core.mongo import get_db
from app.websocket.manager import manager
from app.utils.geocode import geocode_address
from app.utils.distance import get_distance_eta
from app.core.config import settings
from app.core.mongo import init_mongo

order_sio = socketio.AsyncClient(
    reconnection=True,
    reconnection_attempts=0,
    reconnection_delay=2,
)

ORDER_SOCKET_URL = settings.ORDER_SOCKET_URL

_socket_task: asyncio.Task | None = None
_stop_event = asyncio.Event()


@order_sio.event
async def connect():
    print("[ORDER-SOCKET] Connected")

    # Tell Node we are READY
    await order_sio.emit("order_consumer_ready", {
        "service": "driver-backend"
    })
@order_sio.event
async def disconnect():
    print("[ORDER-SOCKET] Disconnected")


@order_sio.event
async def connect_error(err):
    print("[ORDER-SOCKET] Connect error:", err)


@order_sio.on("order_updated")
async def on_order_updated(data):
    try:
        await process_order_event(data)
    except Exception as e:
        print("ORDER EVENT FAILED:", repr(e))


async def process_order_event(data: dict):
    """
    Receives restaurant order events
    Saves order to DB
    Delegates broadcast to ConnectionManager
    """
    print(77777777777,data.get("status"))
    if data.get("status") != "Accepted":
        return

    print("ORDER EVENT RECEIVED:", data.get("_id"))

    # db = await init_mongo()
    order_id = ObjectId(data["_id"])
    print("STEP A: before get_db")
    db = get_db()
    print("STEP B: after get_db")
    existing = await db.orders.find_one({"_id": order_id})
    if existing:
        print("Order already exists (safe reconnect):", order_id)
        return

    restaurant = data.get("restaurant")
    address = data.get("address")
    if not restaurant or not address:
        return

    pickup_lat = restaurant.get("lat")
    pickup_lng = restaurant.get("lng")
    delivery_lat = address.get("lat")
    delivery_lng = address.get("lng")

    if not pickup_lat or not pickup_lng:
        return

    if not delivery_lat or not delivery_lng:
        delivery_lat, delivery_lng = await geocode_address(
            address.get("addressLine", "")
        )
        if not delivery_lat:
            return

    distance_km, eta_min = await get_distance_eta(
        pickup_lat,
        pickup_lng,
        delivery_lat,
        delivery_lng,
    )

    payment_method = data.get("paymentMethod")
    cash_to_collect = data.get("totalAmount") if payment_method == "cod" else 0
    order_doc = {
        "_id": order_id,
        "status": "NEW",  #  IMPORTANT
        "assignedDriverId": None,

        "restaurant": restaurant,
        "address": address,
        "items": data.get("items"),

        "totalAmount": data.get("totalAmount"),
        "paymentMethod": payment_method,

        "distanceKm": distance_km,
        "etaMin": eta_min,
        "cashToCollect": cash_to_collect,

        "socketDelivered": False,

        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "expiresAt": datetime.utcnow() + timedelta(minutes=2),
    }

    await db.orders.insert_one(order_doc)
    print("Order saved to DB:", order_id)

    # SINGLE SOURCE OF TRUTH FOR SOCKET EMIT
    await manager.broadcast_new_order(str(order_id))


async def start_order_socket():
    print("STARTING ORDER SOCKET LOOP")
    global _socket_task

    if _socket_task and not _socket_task.done():
        return

    _stop_event.clear()

    async def _runner():
        # Initialize Mongo in THIS loop
        await init_mongo()
        print("Mongo ready for order socket")

        while not _stop_event.is_set():
            try:
                await order_sio.connect(
                    ORDER_SOCKET_URL,
                    transports=["websocket", "polling"],
                    auth={"token": settings.ORDER_SOCKET_TOKEN},
                )
                await order_sio.wait()
            except Exception as e:
                print("[ORDER SOCKET] Reconnect failed:", e)
                await asyncio.sleep(3)

    _socket_task = asyncio.create_task(_runner())


async def stop_order_socket():
    _stop_event.set()

    if order_sio.connected:
        await order_sio.disconnect()

    if _socket_task:
        _socket_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _socket_task