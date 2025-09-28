"""
Use Cases - Application-specific business logic
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from chat_app.domain.entities import (
    Conversation,
    ConversationId,
    Message,
    MessageId,
    UserId,
)
from chat_app.domain.repositories import ConversationRepository, UserRepository
from chat_app.domain.services import (
    ConversationContextService,
    ConversationTitleService,
    MessageClassificationService,
)
from chat_app.domain.value_objects import (
    CacheKey,
    Language,
    MemoryStats,
    MemoryType,
    MessageMetadata,
    PerformanceMetrics,
)


@dataclass
class ChatRequest:
    """Request for chat use case"""

    user_token: str
    message_content: str
    conversation_id: Optional[str] = None
    language: Language = Language.FRENCH
    memory_type: MemoryType = MemoryType.BUFFER


@dataclass
class ChatResponse:
    """Response from chat use case"""

    conversation_id: str
    response_content: str
    memory_stats: MemoryStats
    performance_metrics: PerformanceMetrics
    is_cached: bool = False
    is_quick_response: bool = False


class LLMService(ABC):
    """Abstract LLM service interface"""

    @abstractmethod
    async def generate_response(
        self,
        conversation: Conversation,
        user_message: str,
        language: Language,
        memory_type: MemoryType,
        message_metadata: MessageMetadata,
    ) -> str:
        """Generate AI response for user message"""
        pass

    @abstractmethod
    async def classify_message(self, content: str) -> str:
        """Classify message using LLM"""
        pass


class CacheService(ABC):
    """Abstract cache service interface"""

    @abstractmethod
    async def get_cached_response(self, cache_key: CacheKey) -> Optional[str]:
        """Get cached response if available"""
        pass

    @abstractmethod
    async def cache_response(self, cache_key: CacheKey, response: str) -> None:
        """Cache response for future use"""
        pass

    @abstractmethod
    async def clear_cache(self) -> None:
        """Clear all cached responses"""
        pass


class ChatUseCase:
    """Use case for handling chat interactions"""

    def __init__(
        self,
        user_repository: UserRepository,
        conversation_repository: ConversationRepository,
        llm_service: LLMService,
        cache_service: CacheService,
    ):
        self.user_repository = user_repository
        self.conversation_repository = conversation_repository
        self.llm_service = llm_service
        self.cache_service = cache_service

    async def execute(self, request: ChatRequest) -> ChatResponse:
        """Execute chat use case"""
        # Authenticate user
        user = await self.user_repository.find_by_token(request.user_token)
        if not user:
            raise ValueError("Invalid authentication token")

        # Get or create conversation
        conversation = await self._get_or_create_conversation(
            request.conversation_id, user.user_id
        )

        # Analyze message
        message_metadata = MessageClassificationService.analyze_message(
            request.message_content
        )

        # Check for quick response
        if message_metadata.has_quick_response:
            response_content = message_metadata.quick_response or ""
            is_quick_response = True
            is_cached = False
        else:
            # Check cache
            cache_key = CacheKey.from_content(
                request.message_content,
                ConversationContextService.get_context_summary(conversation),
                request.language.value,
            )

            cached_response = await self.cache_service.get_cached_response(cache_key)
            if cached_response:
                response_content = cached_response
                is_cached = True
                is_quick_response = False
            else:
                # Generate new response
                response_content = await self.llm_service.generate_response(
                    conversation,
                    request.message_content,
                    request.language,
                    request.memory_type,
                    message_metadata,
                )

                # Cache the response
                await self.cache_service.cache_response(cache_key, response_content)
                is_cached = False
                is_quick_response = False

        # Create message entities
        user_message = Message(
            message_id=MessageId.generate(),
            role="user",
            content=request.message_content,
        )

        assistant_message = Message(
            message_id=MessageId.generate(), role="assistant", content=response_content
        )

        # Add messages to conversation
        conversation.add_message(user_message)
        conversation.add_message(assistant_message)

        # Update conversation title if it's the first message
        if (
            conversation.get_message_count() == 2
        ):  # Just added user + assistant messages
            title = ConversationTitleService.generate_title(request.message_content)
            conversation.update_title(title)

        # Save conversation
        await self.conversation_repository.save(conversation)

        # Create response
        return ChatResponse(
            conversation_id=str(conversation.conversation_id),
            response_content=response_content,
            memory_stats=MemoryStats(
                memory_type=request.memory_type.value,
                message_count=conversation.get_message_count(),
            ),
            performance_metrics=PerformanceMetrics(
                total_time=0.0,  # Will be set by performance monitoring
                checkpoints={},
                operation="chat_response",
            ),
            is_cached=is_cached,
            is_quick_response=is_quick_response,
        )

    async def _get_or_create_conversation(
        self, conversation_id: Optional[str], user_id: UserId
    ) -> Conversation:
        """Get existing conversation or create new one"""
        if conversation_id:
            conv_id = ConversationId(value=conversation_id)
            conversation = await self.conversation_repository.find_by_id(
                conv_id, user_id
            )
            if conversation:
                return conversation

        # Create new conversation
        conversation = Conversation(
            conversation_id=ConversationId.generate(),
            user_id=user_id,
            title="New Conversation",
        )

        return conversation


class GetConversationsUseCase:
    """Use case for retrieving user conversations"""

    def __init__(
        self,
        user_repository: UserRepository,
        conversation_repository: ConversationRepository,
    ):
        self.user_repository = user_repository
        self.conversation_repository = conversation_repository

    async def execute(self, user_token: str) -> List[Conversation]:
        """Execute get conversations use case"""
        # Authenticate user
        user = await self.user_repository.find_by_token(user_token)
        if not user:
            raise ValueError("Invalid authentication token")

        # Get conversations
        conversations = await self.conversation_repository.find_by_user(user.user_id)
        return conversations


class GetConversationUseCase:
    """Use case for retrieving a specific conversation"""

    def __init__(
        self,
        user_repository: UserRepository,
        conversation_repository: ConversationRepository,
    ):
        self.user_repository = user_repository
        self.conversation_repository = conversation_repository

    async def execute(
        self, user_token: str, conversation_id: str
    ) -> Optional[Conversation]:
        """Execute get conversation use case"""
        # Authenticate user
        user = await self.user_repository.find_by_token(user_token)
        if not user:
            raise ValueError("Invalid authentication token")

        # Get conversation
        conv_id = ConversationId(value=conversation_id)
        conversation = await self.conversation_repository.find_by_id(
            conv_id, user.user_id
        )
        return conversation


class ClearCacheUseCase:
    """Use case for clearing response cache"""

    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service

    async def execute(self) -> None:
        """Execute clear cache use case"""
        await self.cache_service.clear_cache()
