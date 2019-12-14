from aiohttp import web
from aiohttp.web_response import json_response

from polar.meta.meta_service import MetaService


async def chat_init(request):
    js = await request.json()

    meta: MetaService = request.app["meta"]

    session = await meta.init_session(js["bot_id"])

    # return session.session_id

    resp = {
        "cuid": session.session_id,
    }
    return json_response(resp)


async def chat_request(request):
    pass


