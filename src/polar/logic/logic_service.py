from polar.lang.json_parser import JsonBotParser
from polar.logic.backend import LogicBaseBackend


class LogicService:
    def __init__(self, backend: LogicBaseBackend):
        self._backend = backend

    async def get_bot(self, bot_id: str, version: int):
        templates = await self._backend.get_templates(bot_id)

        parser = JsonBotParser()
        bot = parser.load_bot(templates)

        return bot
