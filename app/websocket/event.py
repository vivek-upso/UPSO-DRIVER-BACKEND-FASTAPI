# app/websocket/event.py

from datetime import datetime
from typing import Dict, Any


def order_event(
    order_id: str,
    event: str,
    payload: Dict[str, Any] | None = None,
):
    """
    Standard order event for WebSocket communication
    """
    return {
        "type": "ORDER_EVENT",
        "orderId": order_id,
        "event": event,  # Assigned, PickupReached, Delivered, etc.
        "payload": payload or {},
        "timestamp": datetime.utcnow().isoformat(),
    }
