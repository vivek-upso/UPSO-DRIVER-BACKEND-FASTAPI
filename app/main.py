from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.core.order_socket import start_order_socket
from app.websocket.driver_socket import socket_app
from app.core.mongo import init_mongo
from app.api.v1.router import router as v1_router
from app.core.auto_offline import auto_offline_worker
from app.core.health import health_check

app = FastAPI(title="UPSO Driver Backend")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- STARTUP ----------------
@app.on_event("startup")
async def startup_event():
    await init_mongo()
    asyncio.create_task(start_order_socket())

    print(" Order socket client started")
    #  Only non-Redis background tasks
    asyncio.create_task(auto_offline_worker())

# ---------------- HEALTH ----------------
@app.get("/health/live")
async def live():
    return {"status": "alive"}

@app.get("/health/ready")
async def ready():
    return await health_check()

@app.get("/health")
async def health():
    return {"api": "ok"}

# ---------------- SOCKET.IO ----------------
#  CORRECT mount
app.mount("/socket.io", socket_app)

# ---------------- API ----------------
app.include_router(v1_router, prefix="/api/v1")