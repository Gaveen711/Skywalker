"""Local SQLite conversation repository with transactional writes."""

import sqlite3
from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path

from skywalker.domain.ai import ChatMessage


class ConversationStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as database:
            database.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY, title TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY, conversation_id INTEGER NOT NULL
                        REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                    content TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS messages_conversation ON messages(conversation_id, id);
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY, content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=5)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                yield connection
        finally:
            connection.close()

    def create(self, title: str) -> int:
        with self.connect() as database:
            cursor = database.execute("INSERT INTO conversations(title) VALUES (?)", (title[:100],))
            return int(cursor.lastrowid)

    def append(self, conversation_id: int, message: ChatMessage) -> None:
        with self.connect() as database:
            database.execute(
                "INSERT INTO messages(conversation_id, role, content) VALUES (?,?,?)",
                (conversation_id, message.role, message.content),
            )

    def list_conversations(self) -> list[tuple[int, str]]:
        with self.connect() as database:
            return database.execute("SELECT id,title FROM conversations ORDER BY id DESC").fetchall()

    def load(self, conversation_id: int) -> list[ChatMessage]:
        with self.connect() as database:
            return [ChatMessage(*row) for row in database.execute(
                "SELECT role,content FROM messages WHERE conversation_id=? ORDER BY id",
                (conversation_id,),
            )]

    def delete(self, conversation_id: int) -> None:
        with self.connect() as database:
            database.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))

    def save_memory(self, content: str) -> int:
        if not content.strip():
            raise ValueError("Memory cannot be empty")
        with self.connect() as database:
            cursor = database.execute("INSERT INTO memories(content) VALUES (?)", (content,))
            return int(cursor.lastrowid)

    def list_memories(self) -> list[tuple[int, str]]:
        with self.connect() as database:
            return database.execute("SELECT id,content FROM memories ORDER BY id DESC").fetchall()

    def delete_memory(self, identifier: int) -> None:
        with self.connect() as database:
            database.execute("DELETE FROM memories WHERE id=?", (identifier,))
