import asyncio
import logging

import aiohttp
import aioredis
import asyncpg
from aiohttp import web

from polar.lang import UserMessage, Interactivity, Event, OutMessageEvent
from polar.meta.meta_service import MetaService
from polar.proxy import proxy_conf, legacy


logger = logging.getLogger(__name__)


class WsInteractivity(Interactivity):
    def __init__(self, ws, request_id):
        self.ws = ws
        self.request_id = request_id

    async def send_event(self, event: Event):
        if not isinstance(event, OutMessageEvent):
            raise RuntimeError("Only OutMessageEvent cant be used in interactive")

        resp_text = "".join(event.parts)
        send = {"type": "text", "text": resp_text, "request_id": self.request_id}
        logger.info("Response %s", send)
        await self.ws.send_json(send)


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    meta: MetaService = request.app["meta"]

    session_id: str = None

    logger.debug("New websocket request")

    while not ws.closed:
        msg = await ws.receive()

        if msg.type == aiohttp.WSMsgType.TEXT:
            logger.info("Got %s", msg.data)
            js = msg.json()

            if not js.get("request_id"):
                await ws.send_json({"type": "error", "text": "Missing 'request_id' in message", "code": 11})
                continue

            if not js.get("type"):
                await ws.send_json({"type": "error", "text": "Missing 'type' in message", "code": 10, "request_id": js["request_id"]})
                continue



            if js["type"] == "hello":
                session_id = await meta.init_session(js["bot_id"])
            elif js["type"] == "text":
                event = UserMessage(js["text"])
                inter = WsInteractivity(ws, request_id=js["request_id"])
                await meta.push_request(event, session_id, inter)
            else:
                await ws.send_json({"type": "error", "text": f"Unknown type '{js['type']}'", "code": 12, "request_id": js["request_id"]})
                continue

        elif msg.type == aiohttp.WSMsgType.CLOSE:
            logger.info("websocket connection closed")
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.info("ws connection closed with exception %s" % ws.exception())

    return ws


def main():
    app = web.Application()

    logging.basicConfig(level=logging.INFO)

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
