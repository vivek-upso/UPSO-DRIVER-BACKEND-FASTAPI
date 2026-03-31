import asyncio
from app.core.leader import acquire_leader, renew_leader
from app.core.order_socket import start_order_socket

async def leader_worker():
    while True:
        try:
            if await acquire_leader():
                print("🟢 I AM LEADER")
                await start_order_socket()

                while True:
                    await renew_leader()
                    await asyncio.sleep(10)

            else:
                await asyncio.sleep(5)

        except Exception as e:
            print("🔥 Leader worker error:", e)
            await asyncio.sleep(5)
