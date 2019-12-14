import asyncio
import json

import aiohttp


BOT_ID = "0c8e467f-a24e-4f72-9f16-58d88ea3aae3"

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect("http://localhost:8090/ws") as ws:
            await ws.send_str(json.dumps({"type": "hello", "bot_id": BOT_ID}))

            text = input("<--")
            await ws.send_str(json.dumps({"type": "text", "text": text}))

            async for msg in ws:
                text = input("<--")
                await ws.send_str(json.dumps({"type": "text", "text": text}))

                if msg.type == aiohttp.WSMsgType.TEXT:
                    print("-->", msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())

