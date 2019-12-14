from polar.logic.backend import LogicPostgresBackend
from polar.logic.logic_service import LogicService


class MetaContext:
    def __init__(self, bot):
        self.bot = bot


class MetaService:
    def __init__(self, db):
        self.db = db

        self._logic_service = LogicService(LogicPostgresBackend(db))

    async def init_session(self, bot_id: str) -> MetaContext:
        bot = await self._logic_service.get_bot(bot_id, 0)
        return MetaContext(bot)

    async def push_request(self, request: str, context: MetaContext):
        pass
