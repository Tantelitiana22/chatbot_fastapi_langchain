"""
Unit tests for domain services
"""
import pytest

from chat_app.domain.entities import (
    Conversation,
    ConversationId,
    Message,
    MessageId,
    UserId,
)
from chat_app.domain.services import (
    ConversationContextService,
    ConversationTitleService,
    MessageClassificationService,
)


class TestMessageClassificationService:
    """Test MessageClassificationService"""

    def test_classify_code_message(self):
        """Test classification of code-related messages"""
        code_messages = [
            "How do I write a Python function?",
            "Can you help me debug this JavaScript code?",
            "What's the syntax for SQL queries?",
            "I need help with HTML and CSS",
            "How to create a class in Python?",
        ]

        for message in code_messages:
            category = MessageClassificationService.classify_message(message)
            assert category.value == "code"

    def test_classify_general_message(self):
        """Test classification of general messages"""
        general_messages = [
            "Hello, how are you?",
            "What's the weather like today?",
            "Tell me about history",
            "I need help with cooking",
            "What's your favorite color?",
        ]

        for message in general_messages:
            category = MessageClassificationService.classify_message(message)
            assert category.value == "general"

    def test_analyze_message(self):
        """Test message analysis"""
        # Test simple message
        metadata = MessageClassificationService.analyze_message("Hello!")
        assert metadata.message_type.value == "simple"
        assert metadata.length == 6
        assert not metadata.is_question
        assert not metadata.is_code_request

        # Test question
        metadata = MessageClassificationService.analyze_message("How are you?")
        assert metadata.is_question

        # Test code request
        metadata = MessageClassificationService.analyze_message(
            "Help me with Python code"
        )
        assert metadata.is_code_request

        # Test quick response
        metadata = MessageClassificationService.analyze_message("hello")
        assert metadata.has_quick_response
        assert metadata.quick_response is not None

    def test_analyze_message_validation(self):
        """Test message analysis validation"""
        with pytest.raises(ValueError):
            MessageClassificationService.analyze_message("")

        with pytest.raises(ValueError):
            MessageClassificationService.analyze_message("x" * 5000)


class TestConversationTitleService:
    """Test ConversationTitleService"""

    def test_generate_title_basic(self):
        """Test basic title generation"""
        title = ConversationTitleService.generate_title("Hello, how are you?")
        assert title == "How are you?"

    def test_generate_title_with_prefixes(self):
        """Test title generation with common prefixes"""
        test_cases = [
            ("Hi, can you help me?", "Can you help me?"),
            ("Hello, I need assistance", "I need assistance"),
            ("Hey, what's up?", "What's up?"),
            ("Bonjour, comment allez-vous?", "Comment allez-vous?"),
        ]

        for input_msg, expected in test_cases:
            title = ConversationTitleService.generate_title(input_msg)
            assert title == expected

    def test_generate_title_long_message(self):
        """Test title generation for long messages"""
        long_message = "This is a very long message that should be truncated because it exceeds the maximum length allowed for conversation titles"
        title = ConversationTitleService.generate_title(long_message)
        assert len(title) <= 50
        assert title.endswith("...")

    def test_generate_title_short_message(self):
        """Test title generation for short messages"""
        title = ConversationTitleService.generate_title("Hi")
        assert title == "New Conversation"


class TestConversationContextService:
    """Test ConversationContextService"""

    def test_get_context_summary(self):
        """Test getting conversation context summary"""
        # Create a test conversation
        conv_id = ConversationId.generate()
        user_id = UserId("test_user")
        conversation = Conversation(
            conversation_id=conv_id, user_id=user_id, title="Test Conversation"
        )

        # Add messages
        user_msg = Message(
            message_id=MessageId.generate(), role="user", content="Hello, how are you?"
        )
        assistant_msg = Message(
            message_id=MessageId.generate(),
            role="assistant",
            content="I'm doing well, thank you!",
        )

        conversation.add_message(user_msg)
        conversation.add_message(assistant_msg)

        # Get context summary
        context = ConversationContextService.get_context_summary(
            conversation, max_messages=2
        )

        assert "U:Hello, how are you?" in context
        assert "A:I'm doing well, thank you!" in context

    def test_get_context_summary_with_limit(self):
        """Test context summary with message limit"""
        # Create a test conversation with many messages
        conv_id = ConversationId.generate()
        user_id = UserId("test_user")
        conversation = Conversation(
            conversation_id=conv_id, user_id=user_id, title="Test Conversation"
        )

        # Add 5 messages
        for i in range(5):
            user_msg = Message(
                message_id=MessageId.generate(), role="user", content=f"Message {i}"
            )
            assistant_msg = Message(
                message_id=MessageId.generate(),
                role="assistant",
                content=f"Response {i}",
            )
            conversation.add_message(user_msg)
            conversation.add_message(assistant_msg)

        # Get context summary with limit
        context = ConversationContextService.get_context_summary(
            conversation, max_messages=2
        )

        # Should only contain the last 2 messages
        assert "U:Message 3" in context
        assert "A:Response 3" in context
        assert "U:Message 4" in context
        assert "A:Response 4" in context
        assert "U:Message 0" not in context
        assert "A:Response 0" not in context

    def test_should_use_cached_response(self):
        """Test cached response decision logic"""
        conv_id = ConversationId.generate()
        user_id = UserId("test_user")
        conversation = Conversation(
            conversation_id=conv_id, user_id=user_id, title="Test Conversation"
        )

        # Test with quick response message
        should_cache = ConversationContextService.should_use_cached_response(
            conversation, "hello", "fr"
        )
        assert should_cache

        # Test with long conversation
        for i in range(10):
            msg = Message(
                message_id=MessageId.generate(), role="user", content=f"Message {i}"
            )
            conversation.add_message(msg)

        should_cache = ConversationContextService.should_use_cached_response(
            conversation, "regular message", "fr"
        )
        assert should_cache
