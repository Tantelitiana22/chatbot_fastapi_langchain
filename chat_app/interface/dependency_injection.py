"""
Dependency Injection Container
"""
from typing import Any, Dict

from chat_app.application.use_cases import (
    CacheService,
    ChatUseCase,
    ClearCacheUseCase,
    GetConversationsUseCase,
    GetConversationUseCase,
    LLMService,
)
from chat_app.domain.repositories import ConversationRepository, UserRepository
from chat_app.infrastructure.cache_service import InMemoryCacheService
from chat_app.infrastructure.llm_service import LangChainLLMService
from chat_app.infrastructure.repositories import (
    SQLiteConversationRepository,
    SQLiteUserRepository,
)


class DIContainer:
    """Dependency Injection Container"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._register_services()

    def _register_services(self):
        """Register all services in the container"""

        # Infrastructure services
        self._services["user_repository"] = SQLiteUserRepository()
        self._services["conversation_repository"] = SQLiteConversationRepository()
        self._services["llm_service"] = LangChainLLMService()
        self._services["cache_service"] = InMemoryCacheService()

        # Application services

        self._services["chat_use_case"] = ChatUseCase(
            self._services["user_repository"],
            self._services["conversation_repository"],
            self._services["llm_service"],
            self._services["cache_service"],
        )

        self._services["get_conversations_use_case"] = GetConversationsUseCase(
            self._services["user_repository"], self._services["conversation_repository"]
        )

        self._services["get_conversation_use_case"] = GetConversationUseCase(
            self._services["user_repository"], self._services["conversation_repository"]
        )

        self._services["clear_cache_use_case"] = ClearCacheUseCase(
            self._services["cache_service"]
        )

    def get(self, service_name: str) -> Any:
        """Get service by name"""
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' not found")
        return self._services[service_name]

    def get_user_repository(self) -> UserRepository:
        """Get user repository"""
        return self._services["user_repository"]  # type: ignore

    def get_conversation_repository(self) -> ConversationRepository:
        """Get conversation repository"""
        return self._services["conversation_repository"]  # type: ignore

    def get_llm_service(self) -> LLMService:
        """Get LLM service"""
        return self._services["llm_service"]  # type: ignore

    def get_cache_service(self) -> CacheService:
        """Get cache service"""
        return self._services["cache_service"]  # type: ignore

    def get_chat_use_case(self) -> ChatUseCase:
        """Get chat use case"""
        return self._services["chat_use_case"]  # type: ignore

    def get_get_conversations_use_case(self) -> GetConversationsUseCase:
        """Get conversations use case"""
        return self._services["get_conversations_use_case"]  # type: ignore

    def get_get_conversation_use_case(self) -> GetConversationUseCase:
        """Get conversation use case"""
        return self._services["get_conversation_use_case"]  # type: ignore

    def get_clear_cache_use_case(self) -> ClearCacheUseCase:
        """Get clear cache use case"""
        return self._services["clear_cache_use_case"]  # type: ignore


# Global container instance
container = DIContainer()
