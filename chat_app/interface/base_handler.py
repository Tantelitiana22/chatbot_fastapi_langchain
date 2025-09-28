"""
Base Handler - Shared initialization logic for API handlers
"""
from chat_app.application.use_cases import ChatUseCase
from chat_app.infrastructure.cache_service import InMemoryCacheService
from chat_app.infrastructure.llm_service import LangChainLLMService
from chat_app.infrastructure.repositories import (
    SQLiteConversationRepository,
    SQLiteUserRepository,
)


class BaseHandler:
    """Base class for API handlers with shared initialization logic"""

    def __init__(self):
        """Initialize repositories and services"""
        self.user_repository = SQLiteUserRepository()
        self.conversation_repository = SQLiteConversationRepository()
        self.llm_service = LangChainLLMService()
        self.cache_service = InMemoryCacheService()

        # Initialize use case
        self.chat_use_case = ChatUseCase(
            self.user_repository,
            self.conversation_repository,
            self.llm_service,
            self.cache_service,
        )
