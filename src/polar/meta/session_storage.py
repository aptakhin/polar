import json
import uuid
from abc import abstractmethod

from polar import util


class MetaSession:
    def __init__(self):
        self.meta_bot_id = None
        self.context = {}

    @classmethod
    def from_json(cls, jstr):
        session = MetaSession()
        js = json.loads(jstr)
        session.meta_bot_id = str(js["meta_bot_id"])
        session.context = js["context"]
        return session

    def to_json(self):
        obj = {
            "meta_bot_id": self.meta_bot_id,
            "context": self.context,
        }
        return json.dumps(obj, default=util.json_serial)


class MetaSessionStorageBaseBackend:
    @abstractmethod
    async def init(self, session: MetaSession):
        pass

    @abstractmethod
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


class MetaRedisSessionStorageBackend(MetaSessionStorageBaseBackend):
    def __init__(self, redis):
        self._redis = redis
        self._prefix = "polar:session:"

    async def init(self, session: MetaSession):
        session_id = uuid.uuid4()
        await self._redis.set(self._prefix + str(session_id), session.to_json())
        return session_id

    async def get(self, meta_session_id):
        result = await self._redis.get(self._prefix + str(meta_session_id), encoding="utf-8")
        return MetaSession.from_json(result) if result else None


class MetaSessionStorage:
    def __init__(self, backend: MetaSessionStorageBaseBackend):
        self._backend = backend

    async def init(self, session: MetaSession):
        return await self._backend.init(session)

    async def get(self, meta_session_id):
        return await self._backend.get(meta_session_id)

