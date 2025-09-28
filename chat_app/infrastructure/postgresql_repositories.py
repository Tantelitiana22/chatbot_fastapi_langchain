"""
PostgreSQL Repositories - PostgreSQL implementations of repository interfaces
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from chat_app.domain.entities import (
    Conversation,
    ConversationId,
    Message,
    MessageId,
    User,
    UserId,
)
from chat_app.domain.repositories import ConversationRepository, UserRepository


# SQLAlchemy Base
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class UserModel(Base):
    """SQLAlchemy model for User entity"""

    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    token = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationModel(Base):
    """SQLAlchemy model for Conversation entity"""

    __tablename__ = "conversations"

    conversation_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MessageModel(Base):
    """SQLAlchemy model for Message entity"""

    __tablename__ = "messages"

    message_id = Column(String, primary_key=True)
    conversation_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PostgreSQLUserRepository(UserRepository):
    """PostgreSQL implementation of UserRepository"""

    def __init__(self, database_url: str):
        """Initialize PostgreSQL repository with database URL."""
        self.database_url = database_url
        self.engine = create_async_engine(database_url)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def save(self, user: User) -> None:
        """Save user to PostgreSQL database."""
        async with self.async_session() as session:
            user_model = UserModel(
                user_id=str(user.user_id),
                token=user.token,
            )
            await session.merge(user_model)
            await session.commit()

    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Find user by ID in PostgreSQL database."""
        async with self.async_session() as session:
            result = await session.get(UserModel, str(user_id))
            if result:
                return User(
                    user_id=UserId(result.user_id),
                    token=result.token,
                )
            return None

    async def find_by_token(self, token: str) -> Optional[User]:
        """Find user by token in PostgreSQL database."""
        async with self.async_session() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.token == token)
            )
        user_model = result.scalar_one_or_none()
        if user_model:
            return User(
                user_id=UserId(user_model.user_id),
                token=user_model.token,
            )
        return None

    async def delete(self, user_id: UserId) -> bool:
        """Delete user from PostgreSQL database."""
        async with self.async_session() as session:
            result = await session.execute(
                sql_delete(UserModel).where(UserModel.user_id == str(user_id))
            )
        await session.commit()
        return bool(result.rowcount > 0)


class PostgreSQLConversationRepository(ConversationRepository):
    """PostgreSQL implementation of ConversationRepository"""

    def __init__(self, database_url: str):
        """Initialize PostgreSQL repository with database URL."""
        self.database_url = database_url
        self.engine = create_async_engine(database_url)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def save(self, conversation: Conversation) -> None:
        """Save conversation to PostgreSQL database."""
        async with self.async_session() as session:
            # Save conversation
            conv_model = ConversationModel(
                conversation_id=str(conversation.conversation_id),
                user_id=str(conversation.user_id),
                title=conversation.title,
            )
            await session.merge(conv_model)

            # Save messages
            for message in conversation.messages:
                msg_model = MessageModel(
                    message_id=str(message.message_id),
                    conversation_id=str(conversation.conversation_id),
                    role=message.role,
                    content=message.content,
                )
                await session.merge(msg_model)

            await session.commit()

    async def find_by_id(
        self, conversation_id: ConversationId, user_id: UserId
    ) -> Optional[Conversation]:
        """Find conversation by ID in PostgreSQL database."""
        async with self.async_session() as session:
            # Get conversation
            conv_result = await session.execute(
                select(ConversationModel).where(
                    ConversationModel.conversation_id == str(conversation_id),
                    ConversationModel.user_id == str(user_id),
                )
            )
        conv_model = conv_result.scalar_one_or_none()
        if not conv_model:
            return None

        # Get messages
        msg_result = await session.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == str(conversation_id))
            .order_by(MessageModel.created_at)
        )
        msg_models = msg_result.scalars().all()

        # Convert to domain entities
        messages = [
            Message(
                message_id=MessageId(msg.message_id),
                role=msg.role,
                content=msg.content,
            )
            for msg in msg_models
        ]

        return Conversation(
            conversation_id=ConversationId(conv_model.conversation_id),
            user_id=UserId(conv_model.user_id),
            title=conv_model.title,
            messages=messages,
        )

    async def find_by_user(self, user_id: UserId) -> List[Conversation]:
        """Find conversations by user ID in PostgreSQL database."""
        async with self.async_session() as session:
            # Get conversations
            conv_result = await session.execute(
                select(ConversationModel)
                .where(ConversationModel.user_id == str(user_id))
                .order_by(ConversationModel.updated_at.desc())
            )
        conv_models = conv_result.scalars().all()

        conversations = []
        for conv_model in conv_models:
            # Get messages for this conversation
            msg_result = await session.execute(
                select(MessageModel)
                .where(MessageModel.conversation_id == conv_model.conversation_id)
                .order_by(MessageModel.created_at)
            )
            msg_models = msg_result.scalars().all()

            # Convert to domain entities
            messages = [
                Message(
                    message_id=MessageId(msg.message_id),
                    role=msg.role,
                    content=msg.content,
                )
                for msg in msg_models
            ]

            conversation = Conversation(
                conversation_id=ConversationId(conv_model.conversation_id),
                user_id=UserId(conv_model.user_id),
                title=conv_model.title,
                messages=messages,
            )
            conversations.append(conversation)

        return conversations

    async def delete(self, conversation_id: ConversationId, user_id: UserId) -> None:
        """Delete conversation from PostgreSQL database."""
        async with self.async_session() as session:
            # Delete messages first (foreign key constraint)
            await session.execute(
                sql_delete(MessageModel).where(
                    MessageModel.conversation_id == str(conversation_id)
                )
            )

            # Delete conversation
            await session.execute(
                sql_delete(ConversationModel).where(
                    ConversationModel.conversation_id == str(conversation_id),
                    ConversationModel.user_id == str(user_id),
                )
            )
        await session.commit()


async def create_tables(database_url: str) -> None:
    """Create database tables."""
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
