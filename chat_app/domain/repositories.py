"""
Repository Interfaces (Ports) - Abstract contracts for data access
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from chat_app.domain.entities import Conversation, ConversationId, User, UserId


class UserRepository(ABC):
    """Repository interface for User entities"""

    @abstractmethod
    async def find_by_token(self, token: str) -> Optional[User]:
        """Find user by authentication token"""
        pass

    @abstractmethod
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Find user by ID"""
        pass

    @abstractmethod
    async def save(self, user: User) -> None:
        """Save user entity"""
        pass

    @abstractmethod
    async def delete(self, user_id: UserId) -> bool:
        """Delete user entity"""
        pass


class ConversationRepository(ABC):
    """Repository interface for Conversation entities"""

    @abstractmethod
    async def find_by_id(
        self, conversation_id: ConversationId, user_id: UserId
    ) -> Optional[Conversation]:
        """Find conversation by ID and user ID"""
        pass

    @abstractmethod
    async def find_by_user(self, user_id: UserId) -> List[Conversation]:
        """Find all conversations for a user"""
        pass

    @abstractmethod
    async def save(self, conversation: Conversation) -> None:
        """Save conversation entity"""
        pass

    @abstractmethod
    async def delete(self, conversation_id: ConversationId, user_id: UserId) -> None:
        """Delete conversation"""
        pass
