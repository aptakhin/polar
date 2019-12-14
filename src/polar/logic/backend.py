from abc import abstractmethod

import asyncpg


class LogicBaseBackend:

    @abstractmethod
    async def get_templates(self, bot_id):
        pass


class LogicPostgresBackend(LogicBaseBackend):
    def __init__(self, db: asyncpg.pool):
        self.db = db

    async def get_templates(self, bot_id):
        async with self.db.acquire() as connection:
            result = await connection.fetch("""
                SELECT * FROM suites s
                RIGHT JOIN templates t ON t.suite_id=s.id
                WHERE s.profile_id=$1
            """, bot_id)
            return result
