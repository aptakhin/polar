import asyncio
import queue

from aiohttp import web

class Server:
    def __init__(self):
        pass

    async def loop(self):
        while True:
            print(1)
            await asyncio.sleep(3.)


class ClientExecutor:
    def __init__(self):
        self.inp_queue = queue.Queue()
        self.out_queue = queue.Queue()

    async def loop(self):
        while True:
            await asyncio.sleep(0.5)


async def handle(request):
    js = await request.json()
    return web.json_response({"msg": "ok"})


async def run():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 7070)

    server = Server()

    # comp_future = asyncio.gather(site.start(), server.loop())
    await asyncio.wait([site.start(), server.loop()])


if __name__ == "__main__":
    app = web.Application()
    app.add_routes([
        web.post("/", handle),
    ])

    asyncio.get_event_loop().run_until_complete(run())


