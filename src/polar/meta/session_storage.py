import abc
import uuid


class MetaSession:
    def __init__(self):
        self.meta_bot_id = None
        self.context = {}


class MetaSessionStorageBaseBackend:
    @abc.abstractmethod
    async def init(self, session: MetaSession):
        pass

    @abc.abstractmethod
    async def get(self, meta_session_id):
        pass


class MetaMemorySessionStorageBackend(MetaSessionStorageBaseBackend):
    def __init__(self):
        self.sessions = {}

    async def init(self, session: MetaSession):
        session_id = uuid.uuid4()
        self.sessions[str(session_id)] = session
        return session_id

    async def get(self, meta_session_id):
        return self.sessions.get(str(meta_session_id))


class MetaSessionStorage:
    def __init__(self, backend: MetaSessionStorageBaseBackend):
        self._backend = backend

    async def init(self, session: MetaSession):
        return await self._backend.init(session)

    async def get(self, meta_session_id):
        return await self._backend.get(meta_session_id)

