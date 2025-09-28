"""
Infrastructure Repositories - Concrete implementations of repository interfaces
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from chat_app.domain.entities import (
    Conversation,
    ConversationId,
    Message,
    MessageId,
    User,
    UserId,
)
from chat_app.domain.repositories import ConversationRepository, UserRepository


class SQLiteUserRepository(UserRepository):
    """SQLite implementation of UserRepository"""

    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Create users table if it doesn't exist
        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        # Insert default users if they don't exist
        default_users = [
            ("user1", "token_user1"),
            ("user2", "token_user2"),
            ("dev", "devtoken123"),
        ]

        for user_id, token in default_users:
            cur.execute(
                """
            INSERT OR IGNORE INTO users (user_id, token) VALUES (?, ?)
            """,
                (user_id, token),
            )

        conn.commit()
        conn.close()

    async def find_by_token(self, token: str) -> Optional[User]:
        """Find user by authentication token"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute(
            "SELECT user_id, token, created_at FROM users WHERE token = ?", (token,)
        )
        row = cur.fetchone()
        conn.close()

        if row:
            user_id, token, created_at = row
            return User(
                user_id=UserId(value=user_id),
                token=token,
                created_at=datetime.fromisoformat(created_at)
                if created_at
                else datetime.now(),
            )
        return None

    async def save(self, user: User) -> None:
        """Save user entity"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute(
            """
        INSERT OR REPLACE INTO users (user_id, token, created_at) VALUES (?, ?, ?)
        """,
            (user.user_id.value, user.token, user.created_at.isoformat()),
        )

        conn.commit()
        conn.close()


class SQLiteConversationRepository(ConversationRepository):
    """SQLite implementation of ConversationRepository"""

    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Check if conversations table exists
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'"
        )
        table_exists = cur.fetchone() is not None

        if not table_exists:
            # Create new table with all columns
            cur.execute(
                """
            CREATE TABLE conversations (
                id TEXT,
                user_id TEXT,
                title TEXT,
                messages TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id, user_id)
            )
            """
            )
        else:
            # Check which columns exist and add missing ones
            cur.execute("PRAGMA table_info(conversations)")
            existing_columns = [col[1] for col in cur.fetchall()]

            if "title" not in existing_columns:
                try:
                    cur.execute("ALTER TABLE conversations ADD COLUMN title TEXT")
                except sqlite3.OperationalError:
                    pass

            if "created_at" not in existing_columns:
                try:
                    cur.execute(
                        "ALTER TABLE conversations ADD COLUMN created_at TIMESTAMP"
                    )
                except sqlite3.OperationalError:
                    pass

            if "updated_at" not in existing_columns:
                try:
                    cur.execute(
                        "ALTER TABLE conversations ADD COLUMN updated_at TIMESTAMP"
                    )
                except sqlite3.OperationalError:
                    pass

        conn.commit()
        conn.close()

    async def find_by_id(
        self, conversation_id: ConversationId, user_id: UserId
    ) -> Optional[Conversation]:
        """Find conversation by ID and user ID"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute(
            """
        SELECT id, user_id, title, messages, created_at, updated_at
        FROM conversations
        WHERE id = ? AND user_id = ?
        """,
            (conversation_id.value, user_id.value),
        )

        row = cur.fetchone()
        conn.close()

        if row:
            conv_id, user_id_str, title, messages_json, created_at, updated_at = row
            messages_data = json.loads(messages_json) if messages_json else []

            # Convert messages data to Message entities

            messages = []
            for msg_data in messages_data:
                message = Message(
                    message_id=MessageId(value=msg_data.get("message_id", "")),
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(
                        msg_data.get("timestamp", datetime.now().isoformat())
                    ),
                )
                messages.append(message)

            return Conversation(
                conversation_id=ConversationId(value=conv_id),
                user_id=UserId(value=user_id_str),
                title=title or "New Conversation",
                messages=messages,
                created_at=datetime.fromisoformat(created_at)
                if created_at
                else datetime.now(),
                updated_at=datetime.fromisoformat(updated_at)
                if updated_at
                else datetime.now(),
            )
        return None

    async def find_by_user(self, user_id: UserId) -> List[Conversation]:
        """Find all conversations for a user"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute(
            """
        SELECT id, user_id, title, messages, created_at, updated_at
        FROM conversations
        WHERE user_id = ?
        ORDER BY updated_at DESC
        """,
            (user_id.value,),
        )

        rows = cur.fetchall()
        conn.close()

        conversations = []
        for row in rows:
            conv_id, user_id_str, title, messages_json, created_at, updated_at = row
            messages_data = json.loads(messages_json) if messages_json else []

            # Convert messages data to Message entities

            messages = []
            for msg_data in messages_data:
                message = Message(
                    message_id=MessageId(value=msg_data.get("message_id", "")),
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(
                        msg_data.get("timestamp", datetime.now().isoformat())
                    ),
                )
                messages.append(message)

            conversation = Conversation(
                conversation_id=ConversationId(value=conv_id),
                user_id=UserId(value=user_id_str),
                title=title or "New Conversation",
                messages=messages,
                created_at=datetime.fromisoformat(created_at)
                if created_at
                else datetime.now(),
                updated_at=datetime.fromisoformat(updated_at)
                if updated_at
                else datetime.now(),
            )
            conversations.append(conversation)

        return conversations

    async def save(self, conversation: Conversation) -> None:
        """Save conversation entity"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Convert messages to serializable format
        messages_data = []
        for msg in conversation.messages:
            messages_data.append(
                {
                    "message_id": str(msg.message_id.value),
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                }
            )

        cur.execute(
            """
        INSERT INTO conversations (id, user_id, title, messages, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id, user_id) DO UPDATE SET
            messages=excluded.messages,
            title=excluded.title,
            updated_at=excluded.updated_at
        """,
            (
                conversation.conversation_id.value,
                conversation.user_id.value,
                conversation.title,
                json.dumps(messages_data),
                conversation.created_at.isoformat(),
                conversation.updated_at.isoformat(),
            ),
        )

        conn.commit()
        conn.close()

    async def delete(self, conversation_id: ConversationId, user_id: UserId) -> None:
        """Delete conversation"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute(
            """
        DELETE FROM conversations WHERE id = ? AND user_id = ?
        """,
            (conversation_id.value, user_id.value),
        )

        conn.commit()
        conn.close()
