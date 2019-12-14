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
        resp_events = await meta.push_request(event, session_id)

        if resp_events:
            texts = []
            for resp_event in resp_events:
                resp_text = "".join(resp_event.parts)
                texts.append(resp_text)

            text = "<br>".join(texts)

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
