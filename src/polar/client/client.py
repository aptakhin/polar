import asyncio
import json

import aiohttp


BOT_ID = "437e4d60-dad7-4ad7-a433-98d21dbecd97"

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
                    if msg.data == "close cmd":
                        await ws.close()
                        break
                    # else:
                    #     await ws.send_str(msg.data + "/answer")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())

