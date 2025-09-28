"""
Integration tests for use cases
"""
import asyncio
import os
import tempfile

import pytest

from chat_app.application.use_cases import ChatRequest, ChatUseCase
from chat_app.domain.entities import UserId
from chat_app.domain.value_objects import Language, MemoryType
from chat_app.infrastructure.cache_service import InMemoryCacheService
from chat_app.infrastructure.repositories import (
    SQLiteConversationRepository,
    SQLiteUserRepository,
)


class TestChatUseCase:
    """Test ChatUseCase integration"""

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

    @pytest.fixture
    def conv_repo(self, temp_db):
        """Create conversation repository with temp database"""
        return SQLiteConversationRepository(db_path=temp_db)

    @pytest.fixture
    def cache_service(self):
        """Create cache service"""
        return InMemoryCacheService()

    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service"""

        class MockLLMService:
            """Mock LLM service for testing."""

            async def generate_response(
                self,
                conversation,
                user_message,
                language,
                memory_type,
                message_metadata,
            ):
                """Generate mock response."""
                return f"Mock response to: {user_message}"

            async def classify_message(self, content):
                """Classify message as general."""
                return "general"

        return MockLLMService()

    @pytest.fixture
    def chat_use_case(self, user_repo, conv_repo, mock_llm_service, cache_service):
        """Create chat use case with dependencies"""
        return ChatUseCase(user_repo, conv_repo, mock_llm_service, cache_service)

    @pytest.mark.asyncio
    async def test_chat_with_new_conversation(self, chat_use_case):
        """Test chat with new conversation"""
        request = ChatRequest(
            user_token="devtoken123",
            message_content="Hello, world!",
            language=Language.ENGLISH,
            memory_type=MemoryType.BUFFER,
        )

        response = await chat_use_case.execute(request)

        assert response.conversation_id is not None
        assert response.response_content == "Mock response to: Hello, world!"
        assert response.memory_stats.memory_type == "buffer"
        assert not response.is_cached
        assert not response.is_quick_response

    @pytest.mark.asyncio
    async def test_chat_with_existing_conversation(self, chat_use_case):
        """Test chat with existing conversation"""
        # First request
        request1 = ChatRequest(
            user_token="devtoken123",
            message_content="First message",
            language=Language.ENGLISH,
            memory_type=MemoryType.BUFFER,
        )

        response1 = await chat_use_case.execute(request1)
        conversation_id = response1.conversation_id

        # Second request with same conversation
        request2 = ChatRequest(
            user_token="devtoken123",
            message_content="Second message",
            conversation_id=conversation_id,
            language=Language.ENGLISH,
            memory_type=MemoryType.BUFFER,
        )

        response2 = await chat_use_case.execute(request2)

        assert response2.conversation_id == conversation_id
        assert response2.response_content == "Mock response to: Second message"

    @pytest.mark.asyncio
    async def test_chat_with_invalid_token(self, chat_use_case):
        """Test chat with invalid token"""
        request = ChatRequest(
            user_token="invalid_token",
            message_content="Hello, world!",
            language=Language.ENGLISH,
            memory_type=MemoryType.BUFFER,
        )

        with pytest.raises(ValueError, match="Invalid authentication token"):
            await chat_use_case.execute(request)

    @pytest.mark.asyncio
    async def test_chat_with_quick_response(self, chat_use_case):
        """Test chat with quick response"""
        request = ChatRequest(
            user_token="devtoken123",
            message_content="hello",
            language=Language.ENGLISH,
            memory_type=MemoryType.BUFFER,
        )

        response = await chat_use_case.execute(request)

        assert response.is_quick_response
        assert response.response_content == "Hello! How can I help you today?"
        assert not response.is_cached

    @pytest.mark.asyncio
    async def test_chat_with_different_languages(self, chat_use_case):
        """Test chat with different languages"""
        # English request
        request_en = ChatRequest(
            user_token="devtoken123",
            message_content="Hello",
            language=Language.ENGLISH,
            memory_type=MemoryType.BUFFER,
        )

        response_en = await chat_use_case.execute(request_en)
        assert response_en.response_content is not None

        # French request
        request_fr = ChatRequest(
            user_token="devtoken123",
            message_content="Bonjour",
            language=Language.FRENCH,
            memory_type=MemoryType.BUFFER,
        )

        response_fr = await chat_use_case.execute(request_fr)
        assert response_fr.response_content is not None

    @pytest.mark.asyncio
    async def test_chat_with_different_memory_types(self, chat_use_case):
        """Test chat with different memory types"""
        memory_types = [MemoryType.BUFFER, MemoryType.SUMMARY, MemoryType.TOKEN_BUFFER]

        for memory_type in memory_types:
            request = ChatRequest(
                user_token="devtoken123",
                message_content=f"Test with {memory_type.value}",
                language=Language.ENGLISH,
                memory_type=memory_type,
            )

            response = await chat_use_case.execute(request)
            assert response.memory_stats.memory_type == memory_type.value
            assert response.response_content is not None
