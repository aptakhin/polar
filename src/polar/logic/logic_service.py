from polar.logic.backend import LogicBaseBackend
from polar.logic.parser import ArmBotParser


class LogicService:
    def __init__(self, backend: LogicBaseBackend):
        self._backend = backend

    async def get_bot(self, bot_id: str, version: int):
        templates = await self._backend.get_templates(bot_id)

        parser = ArmBotParser()
        bot = parser.load_bot(templates)

        return bot
