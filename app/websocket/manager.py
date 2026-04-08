# app/websocket/manager.py

from datetime import datetime
import asyncio
import logging
from bson import ObjectId
from app.websocket.socket import sio
from app.core.mongo import init_mongo

logger = logging.getLogger("connection-manager")


class ConnectionManager:
    def __init__(self):
        self.driver_to_sid = {}
        self.sid_to_driver = {}
        self.online_drivers = set()
        self._lock = asyncio.Lock()

    async def set_driver_online(self, driver_id: str):
        async with self._lock:
            self.online_drivers.add(driver_id)

    async def set_driver_offline(self, driver_id: str):
        async with self._lock:
            self.online_drivers.discard(driver_id)
    # ---------------- CONNECT ----------------
    async def connect(self, driver_id: str, sid: str):
        async with self._lock:
            self.driver_to_sid[driver_id] = sid
            self.sid_to_driver[sid] = driver_id
            self.online_drivers.add(driver_id)

        # 🔁 REPLAY pending NEW orders
        try:
            db = await init_mongo()

            pending_orders = await db.orders.find(
                {
                    "status": "NEW",
                    "assignedDriverId": None,
                    "expiresAt": {"$gte": datetime.utcnow()},
                }
            ).to_list(length=20)

            for order in pending_orders:
                await sio.emit(
                    "dispatch:event",
                    {
                        "type": "NEW_ORDER",
                        "order": {
                            "orderId": str(order["_id"]),
                            "distanceKm": order.get("distanceKm"),
                            "etaMin": order.get("etaMin"),
                            "cashToCollect": order.get("cashToCollect"),
                            "paymentMethod": order.get("paymentMethod"),
                            "pickup": {
                                "name": order.get("restaurant", {}).get("name"),
                                "address": order.get("restaurant", {})
                                    .get("address", {})
                                    .get("addressLine"),
                                "lat": order.get("restaurant", {}).get("lat"),
                                "lng": order.get("restaurant", {}).get("lng"),
                            },
                            "delivery": {
                                "address": order.get("address", {}).get("addressLine"),
                                "lat": order.get("address", {}).get("lat"),
                                "lng": order.get("address", {}).get("lng"),
                            },
                        },
                    },
                    room=sid,  # 🔥 direct sid
                )

                await db.orders.update_one(
                    {"_id": order["_id"]},
                    {"$set": {"socketDelivered": True}},
                )

        except Exception as e:
            logger.error("Replay on connect failed: %s", e)

    # ---------------- DISCONNECT ----------------
    async def disconnect_by_sid(self, sid: str):
        async with self._lock:
            driver_id = self.sid_to_driver.pop(sid, None)
            if driver_id:
                self.driver_to_sid.pop(driver_id, None)
                self.online_drivers.discard(driver_id)

    # ---------------- SEND TO DRIVER ----------------
    async def send_to_driver(self, driver_id: str, payload: dict) -> bool:
        sid = self.driver_to_sid.get(driver_id)
        if not sid:
            return False

        try:
            await sio.emit("dispatch:event", payload, room=sid)
            return True
        except Exception as e:
            logger.error("Emit failed: %s", e)
            return False

    # ---------------- BROADCAST ----------------
    async def broadcast(self, payload: dict):
        async with self._lock:
            driver_ids = list(self.online_drivers)

        for driver_id in driver_ids:
            await self.send_to_driver(driver_id, payload)

    # ---------------- ADMIN BROADCAST ----------------
    async def broadcast_to_admin(self, payload: dict):
        try:
            await sio.emit("admin:event", payload, room="admins")
        except Exception as e:
            logger.error("Admin broadcast failed: %s", e)

    # ---------------- NEW ORDER BROADCAST ----------------
    async def broadcast_new_order(self, order_id: str):
        db = await init_mongo()

        order = await db.orders.find_one({"_id": ObjectId(order_id)})
        if not order:
            return

        if order.get("expiresAt") and datetime.utcnow() > order["expiresAt"]:
            return

        payload = {
            "type": "NEW_ORDER",
            "order": {
                "orderId": str(order["_id"]),
                "distanceKm": order.get("distanceKm"),
                "etaMin": order.get("etaMin"),
                "cashToCollect": order.get("cashToCollect"),
                "paymentMethod": order.get("paymentMethod"),
                "pickup": {
                    "name": order.get("restaurant", {}).get("name"),
                    "address": order.get("restaurant", {})
                        .get("address", {})
                        .get("addressLine"),
                    "lat": order.get("restaurant", {}).get("lat"),
                    "lng": order.get("restaurant", {}).get("lng"),
                },
                "delivery": {
                    "address": order.get("address", {}).get("addressLine"),
                    "lat": order.get("address", {}).get("lat"),
                    "lng": order.get("address", {}).get("lng"),
                },
            },
        }

        await self.broadcast(payload)


manager = ConnectionManager()