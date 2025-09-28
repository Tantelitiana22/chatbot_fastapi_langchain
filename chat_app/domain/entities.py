"""
Domain Entities - Core business objects with identity and lifecycle
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import uuid4


@dataclass
class UserId:
    """Value object representing a user identifier"""

    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("UserId must be a non-empty string")


@dataclass
class ConversationId:
    """Value object representing a conversation identifier"""

    value: str

    @classmethod
    def generate(cls) -> "ConversationId":
        """Generate a new conversation ID."""
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass
class MessageId:
    """Value object representing a message identifier"""

    value: str

    @classmethod
    def generate(cls) -> "MessageId":
        """Generate a new message ID."""
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass
class User:
    """User entity representing an authenticated user"""

    user_id: UserId
    token: str
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.token or not isinstance(self.token, str):
            raise ValueError("Token must be a non-empty string")


@dataclass
class Message:
    """Message entity representing a single chat message"""

    message_id: MessageId
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.role not in ["user", "assistant"]:
            raise ValueError("Role must be 'user' or 'assistant'")
        if not self.content or not isinstance(self.content, str):
            raise ValueError("Content must be a non-empty string")


@dataclass
class Conversation:
    """Conversation aggregate root managing chat sessions"""

    conversation_id: ConversationId
    user_id: UserId
    title: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_message(self, message: Message) -> None:
        """Add a message to the conversation"""
        if not isinstance(message, Message):
            raise ValueError("Message must be a Message entity")

        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_recent_messages(self, limit: int = 20) -> List[Message]:
        """Get recent messages for context"""
        return self.messages[-limit:] if len(self.messages) > limit else self.messages

    def update_title(self, new_title: str) -> None:
        """Update conversation title"""
        if not new_title or not isinstance(new_title, str):
            raise ValueError("Title must be a non-empty string")
        self.title = new_title
        self.updated_at = datetime.now()

    def get_message_count(self) -> int:
        """Get total number of messages in conversation"""
        return len(self.messages)

    def is_empty(self) -> bool:
        """Check if conversation has no messages"""
        return not self.messages
