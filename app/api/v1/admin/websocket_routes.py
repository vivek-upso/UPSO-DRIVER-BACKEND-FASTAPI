from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.ws_auth import get_admin_from_ws_token
from app.websocket.manager import manager

router = APIRouter()

@router.websocket("/ws/orders")
async def admin_orders_ws(
    websocket: WebSocket,
    admin=Depends(get_admin_from_ws_token)
):
    admin_id = str(admin["_id"])
    await manager.connect_admin(admin_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_admin(admin_id)
