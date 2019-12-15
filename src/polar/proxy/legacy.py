import logging

from aiohttp.web_response import json_response

from polar import UserMessage, Interactivity, Event, OutMessageEvent
from polar.meta.meta_service import MetaService


logger = logging.getLogger(__name__)


class LegacyInteractivity(Interactivity):
    def __init__(self):
        self.messages = []

    async def send_event(self, event: Event):
        if not isinstance(event, OutMessageEvent):
            raise RuntimeError("Only OutMessageEvent cant be used in interactive")

        resp_text = "".join(event.parts)
        self.messages.append(resp_text)


async def chat_init(request):
    js = await request.json()

    if not js.get("uuid"):
        return json_response({"cuid": ""})

    meta: MetaService = request.app["meta"]

    session_id = await meta.init_session(js["uuid"])

    resp = {
        "result": {
            "cuid": str(session_id),
            "inf": {
                "name": None,
            },
            "text": {
                "delay": "",
            },
            "events": {},
        },
        "id": "0",
    }
    return json_response(resp)


async def chat_request(request):
    js = await request.json()

    text = ""

    if js.get("cuid") and js.get("text"):
        meta: MetaService = request.app["meta"]

        session_id = js["cuid"]
        event = UserMessage(js["text"])
        inter = LegacyInteractivity()
        await meta.push_request(event, session_id, inter)

        text = "<br>".join(inter.messages)

    resp = {
        "result": {
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
            "context": {
                # "auto_event_ids": "",
                # "auto_request_counter": "1",
                # "auto_response_type": "user request from main base"
            },
            # "_arm_ext": {
            #     "template_id": null,
            #     "suite_id": null
            # },
            # "id": "2f5b2249-fa9e-4a40-80e0-5dcee0d8ea9f"
        },
        "id": "0",
    }

    return json_response(resp)
