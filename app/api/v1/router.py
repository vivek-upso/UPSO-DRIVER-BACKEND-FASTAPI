from fastapi import APIRouter
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.driver.routes import router as driver_router
from app.api.v1.admin.routes import router as admin_router
from app.api.v1.stripe.webhook import router as stripe_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(driver_router)
router.include_router(admin_router)

router.include_router(stripe_router)
