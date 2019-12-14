import abc
import uuid

from polar import Bot


class MetaBotStorageBaseBackend:
    @abc.abstractmethod
    async def init(self, bot: Bot):
        pass

    @abc.abstractmethod
    async def get(self, meta_bot_id):
        pass


class MetaMemoryBotStorageBackend(MetaBotStorageBaseBackend):
    def __init__(self):
        self.bots = {}

    async def init(self, bot: Bot):
        meta_bot_id = uuid.uuid4()
        self.bots[meta_bot_id] = bot
        return meta_bot_id

    async def get(self, meta_bot_id):
        return self.bots.get(meta_bot_id)


class MetaBotStorage:
    def __init__(self, backend: MetaBotStorageBaseBackend):
         self._backend = backend

    async def init(self, bot: Bot):
        return await self._backend.init(bot)

    async def get(self, meta_bot_id):
        return await self._backend.get(meta_bot_id)
