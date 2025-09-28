"""
Integration tests for repositories
"""
import os
import tempfile

import pytest

from chat_app.domain.entities import (
    Conversation,
    ConversationId,
    Message,
    MessageId,
    User,
    UserId,
)
from chat_app.infrastructure.repositories import (
    SQLiteConversationRepository,
    SQLiteUserRepository,
)


class TestSQLiteUserRepository:
    """Test SQLiteUserRepository"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def user_repo(self, temp_db):
        """Create user repository with temp database"""
        return SQLiteUserRepository(db_path=temp_db)

    @pytest.mark.asyncio
    async def test_find_by_token_existing(self, user_repo):
        """Test finding existing user by token"""
        user = await user_repo.find_by_token("devtoken123")
        assert user is not None
        assert user.user_id.value == "dev"
        assert user.token == "devtoken123"

    @pytest.mark.asyncio
    async def test_find_by_token_nonexistent(self, user_repo):
        """Test finding non-existent user by token"""
        user = await user_repo.find_by_token("nonexistent_token")
        assert user is None

    @pytest.mark.asyncio
    async def test_save_user(self, user_repo):
        """Test saving user"""
        user_id = UserId("test_user")
        user = User(user_id=user_id, token="test_token")

        await user_repo.save(user)

        # Verify user was saved
        retrieved_user = await user_repo.find_by_token("test_token")
        assert retrieved_user is not None
        assert retrieved_user.user_id.value == "test_user"
        assert retrieved_user.token == "test_token"


class TestSQLiteConversationRepository:
    """Test SQLiteConversationRepository"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def conv_repo(self, temp_db):
        """Create conversation repository with temp database"""
        return SQLiteConversationRepository(db_path=temp_db)

    @pytest.fixture
    def test_user_id(self):
        """Create test user ID"""
        return UserId("test_user")

    @pytest.mark.asyncio
    async def test_save_and_find_conversation(self, conv_repo, test_user_id):
        """Test saving and finding conversation"""
        conv_id = ConversationId.generate()
        conversation = Conversation(
            conversation_id=conv_id, user_id=test_user_id, title="Test Conversation"
        )

        # Add a message
        msg_id = MessageId.generate()
        message = Message(message_id=msg_id, role="user", content="Hello, world!")
        conversation.add_message(message)

        # Save conversation
        await conv_repo.save(conversation)

        # Retrieve conversation
        retrieved_conv = await conv_repo.find_by_id(conv_id, test_user_id)
        assert retrieved_conv is not None
        assert retrieved_conv.conversation_id.value == conv_id.value
        assert retrieved_conv.user_id.value == test_user_id.value
        assert retrieved_conv.title == "Test Conversation"
        assert len(retrieved_conv.messages) == 1
        assert retrieved_conv.messages[0].content == "Hello, world!"

    @pytest.mark.asyncio
    async def test_find_conversation_nonexistent(self, conv_repo, test_user_id):
        """Test finding non-existent conversation"""
        conv_id = ConversationId.generate()
        conversation = await conv_repo.find_by_id(conv_id, test_user_id)
        assert conversation is None

    @pytest.mark.asyncio
    async def test_find_conversations_by_user(self, conv_repo, test_user_id):
        """Test finding conversations by user"""
        # Create multiple conversations
        conversations = []
        for i in range(3):
            conv_id = ConversationId.generate()
            conversation = Conversation(
                conversation_id=conv_id, user_id=test_user_id, title=f"Conversation {i}"
            )
            conversations.append(conversation)
            await conv_repo.save(conversation)

        # Retrieve conversations
        retrieved_conversations = await conv_repo.find_by_user(test_user_id)
        assert len(retrieved_conversations) == 3

        # Check that conversations are ordered by updated_at (most recent first)
        titles = [conv.title for conv in retrieved_conversations]
        assert "Conversation 2" in titles
        assert "Conversation 1" in titles
        assert "Conversation 0" in titles

    @pytest.mark.asyncio
    async def test_delete_conversation(self, conv_repo, test_user_id):
        """Test deleting conversation"""
        conv_id = ConversationId.generate()
        conversation = Conversation(
            conversation_id=conv_id, user_id=test_user_id, title="To Be Deleted"
        )

        # Save conversation
        await conv_repo.save(conversation)

        # Verify it exists
        retrieved_conv = await conv_repo.find_by_id(conv_id, test_user_id)
        assert retrieved_conv is not None

        # Delete conversation
        await conv_repo.delete(conv_id, test_user_id)

        # Verify it's deleted
        retrieved_conv = await conv_repo.find_by_id(conv_id, test_user_id)
        assert retrieved_conv is None

    @pytest.mark.asyncio
    async def test_conversation_with_multiple_messages(self, conv_repo, test_user_id):
        """Test conversation with multiple messages"""
        conv_id = ConversationId.generate()
        conversation = Conversation(
            conversation_id=conv_id,
            user_id=test_user_id,
            title="Multi-Message Conversation",
        )

        # Add multiple messages
        for i in range(5):
            msg_id = MessageId.generate()
            user_msg = Message(
                message_id=msg_id, role="user", content=f"User message {i}"
            )
            conversation.add_message(user_msg)

            msg_id = MessageId.generate()
            assistant_msg = Message(
                message_id=msg_id, role="assistant", content=f"Assistant response {i}"
            )
            conversation.add_message(assistant_msg)

        # Save conversation
        await conv_repo.save(conversation)

        # Retrieve and verify
        retrieved_conv = await conv_repo.find_by_id(conv_id, test_user_id)
        assert retrieved_conv is not None
        assert len(retrieved_conv.messages) == 10
        assert retrieved_conv.messages[0].content == "User message 0"
        assert retrieved_conv.messages[1].content == "Assistant response 0"
        assert retrieved_conv.messages[8].content == "User message 4"
        assert retrieved_conv.messages[9].content == "Assistant response 4"
