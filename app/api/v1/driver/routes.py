from fastapi import APIRouter
from .presence_routes import router as presence_router
from .profile_routes import router as profile_router
from .order_routes import router as orders_router
from .wallet_routes import router as wallet_router
from .stripe_routes import router as stripe_router
router = APIRouter(prefix="/driver")

router.include_router(presence_router)
router.include_router(profile_router)
router.include_router(orders_router)
router.include_router(wallet_router)
router.include_router(stripe_router)
