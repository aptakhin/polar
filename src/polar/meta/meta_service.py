import copy

from polar import Executor, Event
from polar.logic.backend import LogicPostgresBackend
from polar.logic.logic_service import LogicService
from polar.meta.bot_storage import MetaBotStorage, MetaMemoryBotStorageBackend
from polar.meta.session_storage import MetaSessionStorage, MetaMemorySessionStorageBackend, MetaSession


class MetaService:
    def __init__(self, db):
        self.db = db

        self._bots = MetaBotStorage(MetaMemoryBotStorageBackend())
        self._sessions = MetaSessionStorage(MetaMemorySessionStorageBackend())

        self._logic_service = LogicService(LogicPostgresBackend(db))

        self._executor = Executor()

    async def init_session(self, bot_id: str) -> str:
        bot = await self._logic_service.get_bot(bot_id, 0)

        meta_bot_id = await self._bots.init(bot)

        session = MetaSession()
        session.meta_bot_id = meta_bot_id
        session.context = {
            "update_every_request": bot_id,
        }

        session_id = await self._sessions.init(session)

        return session_id

    async def push_request(self, event: Event, session_id):
        session = await self._sessions.get(session_id)

        if not session:
            # pity
            print("Can't find session", session_id)
            return None

        if session.context.get("update_every_request"):
            # Debug flag to update bot templates every request
            public_bot_id = session.context["update_every_request"]
            bot = await self._logic_service.get_bot(public_bot_id, 0)
        else:
            bot = await self._bots.get(session.meta_bot_id)

        context = copy.deepcopy(session.context)
        context["random_seed"] = 123

        resp_event = await self._executor.execute_event(event=event, bot=bot, context=context)
        return resp_event
