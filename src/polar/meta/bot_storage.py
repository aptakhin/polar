import uuid
from abc import abstractmethod

from polar.lang.eval import Bot


class MetaBotStorageBaseBackend:
    @abstractmethod
    async def init(self, bot: Bot):
        pass

    @abstractmethod
    async def get(self, meta_bot_id):
        pass


class MetaMemoryBotStorageBackend(MetaBotStorageBaseBackend):
    def __init__(self):
        self.bots = {}

    async def init(self, bot: Bot):
        meta_bot_id = uuid.uuid4()
        self.bots[str(meta_bot_id)] = bot
        return meta_bot_id

    async def get(self, meta_bot_id):
        return self.bots.get(str(meta_bot_id))


class MetaBotStorage:
    def __init__(self, backend: MetaBotStorageBaseBackend):
         self._backend = backend

    async def init(self, bot: Bot):
        return await self._backend.init(bot)

    async def get(self, meta_bot_id):
        return await self._backend.get(meta_bot_id)
