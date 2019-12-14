import asyncio

import aiohttp
import asyncpg
from aiohttp import web
from polar.meta.meta_service import MetaService
from polar.proxy import proxy_conf


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    meta: MetaService = request.app["meta"]


    while not ws.closed:
        msg = await ws.receive()

        if msg.type == aiohttp.WSMsgType.TEXT:
            print("Got", msg.data)

            context = await meta.init_session("437e4d60-dad7-4ad7-a433-98d21dbecd97")

            await meta.push_request(msg.data, context)
            if msg.data == "close":
                await ws.close()

        elif msg.type == aiohttp.WSMsgType.CLOSE:
            print("websocket connection closed")
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print("ws connection closed with exception %s" % ws.exception())

    return ws


def main():
    # web.Application
    # server = web.Server(websocket_handler)
    # runner = web.ServerRunner(server)
    # await runner.setup()
    # site = web.TCPSite(runner, "localhost", 8080)
    # await site.start()
    app = web.Application()

    db_pool = asyncio.get_event_loop().run_until_complete(asyncpg.create_pool(dsn=proxy_conf.LOGIC_POSTGRES_DSN))

    app["meta"] = MetaService(db_pool)
    app.add_routes([web.get('/ws', websocket_handler)])
    web.run_app(app, port=8090)


if __name__ == "__main__":
    main()
