# app/core/driver_dispatch_worker.py

import json
import asyncio
from app.websocket.manager import manager
from app.websocket.driver_socket import sio as driver_sio
from app.core.redis import redis_client

async def driver_dispatch_worker():
    while True:
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("driver:dispatch")

            print("Driver dispatch worker subscribed")

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")

                payload = json.loads(data)

                driver_id = str(payload.get("driver_id"))

                sent = await manager.send_to_driver(driver_id, payload)

                if not sent:
                    await redis_client.lpush(
                        f"pending:orders:{driver_id}",
                        json.dumps(payload),
                    )
                    print(f"Buffered order for driver {driver_id}")

        except asyncio.CancelledError:
            print("Driver dispatch worker cancelled")
            break

        except Exception as e:
            print("Driver dispatch worker error:", e)
            await asyncio.sleep(2)  # prevent tight restart loop
