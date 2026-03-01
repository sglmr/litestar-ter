import aiosqlite
from typing import TypedDict


class UserRecord(TypedDict):
    id: int
    username: str


class UserRepository:
    def __init__(self, connection: aiosqlite.Connection) -> None:
        self.conn = connection
        self.conn.row_factory = aiosqlite.Row

    async def get_all_users(self) -> list[UserRecord]:
        async with self.conn.execute(
            "SELECT id, username FROM users ORDER BY id;"
        ) as cursor:
            records = await cursor.fetchall()
            return [{"id": row["id"], "username": row["username"]} for row in records]

    async def create_user(self, username: str) -> UserRecord:
        query = "INSERT INTO users (username) VALUES (?) RETURNING id, username;"
        async with self.conn.execute(query, (username,)) as cursor:
            row = await cursor.fetchone()
            await self.conn.commit()
            if not row:
                raise RuntimeError("Failed to insert user.")
            return {"id": row["id"], "username": row["username"]}
