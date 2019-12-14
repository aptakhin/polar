from aiohttp.web_response import json_response

from polar import UserMessage
from polar.meta.meta_service import MetaService


async def chat_init(request):
    js = await request.json()

    if not js.get("uuid"):
        return json_response({"cuid": ""})

    meta: MetaService = request.app["meta"]

    session_id = await meta.init_session(js["uuid"])

    resp = {
        "cuid": str(session_id),
    }
    return json_response(resp)


async def chat_request(request):
    js = await request.json()

    text = ""

    if js.get("cuid") and js.get("text"):
        meta: MetaService = request.app["meta"]

        session_id = js["cuid"]
        event = UserMessage(js["text"])
        resp_events = await meta.push_request(event, session_id)

        if resp_events:
            for resp_event in resp_events:
                resp_text = "".join(resp_event.parts)
                text += resp_text + "<br>"

    resp = {
        "text": {
            "value": text,
            "delay": "",
            "status": "",
        },
        "animation": {
            "type": "",
            "duration": "",
            "isFaded": "",
        },
        "navigate": {
            "url": "",
        },
        "token": "",
        "showExpSys": "",
        "rubric": "",
        "cuid": "",
        "context": {},
        # "_arm_ext": self._arm_ext,
        # "id": self.message_id,
    }

    return json_response(resp)
