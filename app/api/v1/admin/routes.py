from fastapi import APIRouter
from .auth_routes import router as auth_router
from .order_routes import router as order_router
from .websocket_routes import router as ws_router

router = APIRouter(prefix="/admin", tags=["Admin"])

router.include_router(auth_router)
router.include_router(order_router)
router.include_router(ws_router)
