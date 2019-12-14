import copy

from polar import Bot, Executor, Context, Event
from polar.logic.backend import LogicPostgresBackend
from polar.logic.logic_service import LogicService


class MetaContext:
    def __init__(self, bot):
        self.bot: Bot = bot
        self.executor: Executor = Executor()
        self.context = Context()


class MetaService:
    def __init__(self, db):
        self.db = db

        self._logic_service = LogicService(LogicPostgresBackend(db))

    async def init_session(self, bot_id: str) -> MetaContext:
        bot = await self._logic_service.get_bot(bot_id, 0)
        return MetaContext(bot)

    async def push_request(self, event: Event, context: MetaContext):
        ctx = copy.deepcopy(context.context)
        ctx["random_seed"] = 123

        resp_event = await context.executor._execute_event(event=event, bot=context.bot, context=ctx)
        return resp_event
