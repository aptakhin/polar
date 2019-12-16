from polar.lang import Interactivity, Event, OutMessageEvent


class LogInteractivity(Interactivity):
    def __init__(self):
        self.events = []

    async def send_event(self, event: Event):
        if not isinstance(event, OutMessageEvent):
            raise RuntimeError("Only OutMessageEvent can be sent")

        self.events.append(event)
