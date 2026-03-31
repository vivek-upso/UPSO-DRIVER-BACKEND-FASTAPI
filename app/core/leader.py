import uuid
from app.core.redis import redis_client

INSTANCE_ID = str(uuid.uuid4())
LEADER_KEY = "order_socket_leader"

async def acquire_leader() -> bool:
    return await redis_client.set(
        LEADER_KEY,
        INSTANCE_ID,
        nx=True,   # only set if not exists
        ex=30     # auto-expire in 30 seconds
    )

async def renew_leader():
    await redis_client.expire(LEADER_KEY, 30)
