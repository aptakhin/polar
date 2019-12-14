import asyncio
import aiohttp
import aioredis
import asyncpg
from aiohttp import web

from polar import UserMessage
from polar.meta.meta_service import MetaService
from polar.proxy import proxy_conf, legacy


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    meta: MetaService = request.app["meta"]

    session_id: str = None

    while not ws.closed:
        msg = await ws.receive()

        if msg.type == aiohttp.WSMsgType.TEXT:
            print("Got", msg.data)
            js = msg.json()

            if js["type"] == "hello":
                session_id = await meta.init_session(js["bot_id"])
            elif js["type"] == "text":
                event = UserMessage(js["text"])
                resp_events = await meta.push_request(event, session_id)
                if resp_events:
                    for resp_event in resp_events:
                        resp_text = "".join(resp_event.parts)
                        send = {"type": "text", "text": resp_text}
                        print("-->", send)
                        await ws.send_json(send)

        elif msg.type == aiohttp.WSMsgType.CLOSE:
            print("websocket connection closed")
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print("ws connection closed with exception %s" % ws.exception())

    return ws


def main():
    app = web.Application()


    db = asyncio.get_event_loop().run_until_complete(asyncpg.create_pool(dsn=proxy_conf.LOGIC_POSTGRES_DSN))
    redis = asyncio.get_event_loop().run_until_complete(aioredis.create_redis_pool(proxy_conf.LOGIC_REDIS_DSN))

    app["meta"] = MetaService(db=db, redis=redis)
    app.add_routes([
        web.get('/ws', websocket_handler),
        web.post('/Chat.init', legacy.chat_init),
        web.post('/Chat.request', legacy.chat_request),
    ])
    web.run_app(app, port=proxy_conf.PROXY_PORT)


if __name__ == "__main__":
    main()
