import asyncio
import aiohttp
import asyncpg
from aiohttp import web

from polar import UserMessage
from polar.meta.meta_service import MetaService, MetaContext
from polar.proxy import proxy_conf


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    meta: MetaService = request.app["meta"]

    context: MetaContext = None

    while not ws.closed:
        msg = await ws.receive()

        if msg.type == aiohttp.WSMsgType.TEXT:
            print("Got", msg.data)
            js = msg.json()

            if js["type"] == "hello":
                context = await meta.init_session(js["bot_id"])
            elif js["type"] == "text":
                event = UserMessage(js["text"])
                resp_events = await meta.push_request(event, context)
                if resp_events:
                    for resp_event in resp_events:
                        resp_text = "".join(resp_event.parts)
                        await ws.send_json({"type": "text", "text": resp_text})

        elif msg.type == aiohttp.WSMsgType.CLOSE:
            print("websocket connection closed")
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print("ws connection closed with exception %s" % ws.exception())

    return ws


def main():
    app = web.Application()

    db_pool = asyncio.get_event_loop().run_until_complete(asyncpg.create_pool(dsn=proxy_conf.LOGIC_POSTGRES_DSN))

    app["meta"] = MetaService(db_pool)
    app.add_routes([
        web.get('/ws', websocket_handler),
    ])
    web.run_app(app, port=8090)


if __name__ == "__main__":
    main()
