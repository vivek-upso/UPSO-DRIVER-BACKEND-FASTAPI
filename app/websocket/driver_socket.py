# app/websocket/driver_socket.py

import socketio
from app.websocket.socket import sio
from app.websocket.manager import manager
from app.core.ws_auth import get_user_from_ws_token
import logging

logger = logging.getLogger("driver-socket")

socket_app = socketio.ASGIApp(sio)


@sio.event
async def connect(sid, environ, auth):
    try:
        logger.info("🔐 WS connect attempt: sid=%s", sid)

        token = auth.get("token") if auth else None
        if not token:
            logger.warning("❌ WS rejected (no token)")
            return False

        user = await get_user_from_ws_token(token)
        if not user or user.get("role") != "driver":
            logger.warning("❌ WS rejected (invalid user)")
            return False

        driver_id = str(user["_id"])

        # 🔑 join logical room (future-safe)
        await sio.enter_room(sid, f"driver:{driver_id}")

        # 🔗 register connection
        await manager.connect(driver_id, sid)

        logger.info("🟢 WS connected: driver=%s sid=%s", driver_id, sid)
        return True

    except Exception as e:
        logger.exception("🔥 WS CONNECT ERROR")
        return False


@sio.event
async def disconnect(sid):
    await manager.disconnect_by_sid(sid)
    logger.info("🔴 WS disconnected: sid=%s", sid)