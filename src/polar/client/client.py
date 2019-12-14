import asyncio
import concurrent
import json

import aiohttp


BOT_ID = "0c8e467f-a24e-4f72-9f16-58d88ea3aae3"

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect("http://localhost:5000/ws") as ws:

            await ws.send_str(json.dumps({"type": "hello", "bot_id": BOT_ID}))

            while True:
                text = input("<--")
                await ws.send_str(json.dumps({"type": "text", "text": text}))

                try:
                    while True:
                        msg = await ws.receive(timeout=5)
                        if msg.data is None:
                            break
                        print("-->", msg.data)
                except concurrent.futures._base.TimeoutError:
                    pass



if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())

