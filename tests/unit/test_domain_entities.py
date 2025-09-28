"""
Unit tests for domain entities
"""
from datetime import datetime

import pytest

from chat_app.domain.entities import (
    Conversation,
    ConversationId,
    Message,
    MessageId,
    User,
    UserId,
)


class TestUserId:
    """Test UserId value object"""

    def test_user_id_creation(self):
        """Test UserId creation"""
        user_id = UserId("test_user")
        assert user_id.value == "test_user"

    def test_user_id_validation(self):
        """Test UserId validation"""
        with pytest.raises(ValueError):
            UserId("")

        with pytest.raises(ValueError):
            UserId(None)


class TestConversationId:
    """Test ConversationId value object"""

    def test_conversation_id_generation(self):
        """Test ConversationId generation"""
        conv_id = ConversationId.generate()
        assert isinstance(conv_id.value, str)
        assert len(conv_id.value) > 0

    def test_conversation_id_string_representation(self):
        """Test ConversationId string representation"""
        conv_id = ConversationId.generate()
        assert str(conv_id) == conv_id.value


class TestMessageId:
    """Test MessageId value object"""

    def test_message_id_generation(self):
        """Test MessageId generation"""
        msg_id = MessageId.generate()
        assert isinstance(msg_id.value, str)
        assert len(msg_id.value) > 0


class TestUser:
    """Test User entity"""

    def test_user_creation(self):
        """Test User creation"""
        user_id = UserId("test_user")
        user = User(user_id=user_id, token="test_token")

        assert user.user_id == user_id
        assert user.token == "test_token"
        assert isinstance(user.created_at, datetime)

    def test_user_token_validation(self):
        """Test User token validation"""
        user_id = UserId("test_user")

        with pytest.raises(ValueError):
            User(user_id=user_id, token="")

        with pytest.raises(ValueError):
            User(user_id=user_id, token=None)


class TestMessage:
    """Test Message entity"""

    def test_message_creation(self):
        """Test Message creation"""
        msg_id = MessageId.generate()
        message = Message(message_id=msg_id, role="user", content="Hello, world!")

        assert message.message_id == msg_id
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert isinstance(message.timestamp, datetime)

    def test_message_role_validation(self):
        """Test Message role validation"""
        msg_id = MessageId.generate()

        with pytest.raises(ValueError):
            Message(message_id=msg_id, role="invalid", content="test")

    def test_message_content_validation(self):
        """Test Message content validation"""
        msg_id = MessageId.generate()

        with pytest.raises(ValueError):
            Message(message_id=msg_id, role="user", content="")

        with pytest.raises(ValueError):
            Message(message_id=msg_id, role="user", content=None)


class TestConversation:
    """Test Conversation aggregate"""

    def test_conversation_creation(self):
        """Test Conversation creation"""
        conv_id = ConversationId.generate()
        user_id = UserId("test_user")
        conversation = Conversation(
            conversation_id=conv_id, user_id=user_id, title="Test Conversation"
        )

        assert conversation.conversation_id == conv_id
        assert conversation.user_id == user_id
        assert conversation.title == "Test Conversation"
        assert not conversation.messages
        assert isinstance(conversation.created_at, datetime)
        assert isinstance(conversation.updated_at, datetime)

    def test_add_message(self):
        """Test adding message to conversation"""
        conv_id = ConversationId.generate()
        user_id = UserId("test_user")
        conversation = Conversation(
            conversation_id=conv_id, user_id=user_id, title="Test Conversation"
        )

        msg_id = MessageId.generate()
        message = Message(message_id=msg_id, role="user", content="Hello!")

        conversation.add_message(message)

        assert len(conversation.messages) == 1
        assert conversation.messages[0] == message
        assert conversation.get_message_count() == 1

    def test_get_recent_messages(self):
        """Test getting recent messages"""
        conv_id = ConversationId.generate()
        user_id = UserId("test_user")
        conversation = Conversation(
            conversation_id=conv_id, user_id=user_id, title="Test Conversation"
        )

        # Add multiple messages
        for i in range(5):
            msg_id = MessageId.generate()
            message = Message(message_id=msg_id, role="user", content=f"Message {i}")
            conversation.add_message(message)

        # Test getting recent messages
        recent = conversation.get_recent_messages(3)
        assert len(recent) == 3
        assert recent[0].content == "Message 2"
        assert recent[1].content == "Message 3"
        assert recent[2].content == "Message 4"

    def test_update_title(self):
        """Test updating conversation title"""
        conv_id = ConversationId.generate()
        user_id = UserId("test_user")
        conversation = Conversation(
            conversation_id=conv_id, user_id=user_id, title="Old Title"
        )

        conversation.update_title("New Title")
        assert conversation.title == "New Title"

    def test_is_empty(self):
        """Test conversation empty check"""
        conv_id = ConversationId.generate()
        user_id = UserId("test_user")
        conversation = Conversation(
            conversation_id=conv_id, user_id=user_id, title="Test Conversation"
        )

        assert conversation.is_empty()

        msg_id = MessageId.generate()
        message = Message(message_id=msg_id, role="user", content="Hello!")
        conversation.add_message(message)

        assert not conversation.is_empty()
