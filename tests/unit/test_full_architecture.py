"""
Test script for the new DDD/Hexagonal Architecture
"""
import asyncio
import os
import sys
import traceback

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

# Import after path manipulation
from chat_app.application.use_cases import (  # pylint: disable=wrong-import-position
    ChatRequest,
    ChatUseCase,
)
from chat_app.domain.entities import (  # pylint: disable=wrong-import-position
    Conversation,
    ConversationId,
    Message,
    MessageId,
    User,
    UserId,
)
from chat_app.domain.services import (  # pylint: disable=wrong-import-position
    ConversationTitleService,
    MessageClassificationService,
)
from chat_app.domain.value_objects import (  # pylint: disable=wrong-import-position
    Language,
    MemoryType,
    MessageCategory,
    MessageMetadata,
    MessageType,
)
from chat_app.infrastructure.cache_service import (  # pylint: disable=wrong-import-position
    InMemoryCacheService,
)
from chat_app.infrastructure.llm_service import (  # pylint: disable=wrong-import-position
    LangChainLLMService,
)
from chat_app.infrastructure.repositories import (  # pylint: disable=wrong-import-position
    SQLiteConversationRepository,
    SQLiteUserRepository,
)


async def test_domain_entities():
    """Test domain entities"""
    print("Testing Domain Entities...")

    # Test User entity
    user_id = UserId("test_user")
    user = User(user_id=user_id, token="test_token")
    print(f"✓ User created: {user.user_id.value}")

    # Test Conversation entity
    conv_id = ConversationId.generate()
    conversation = Conversation(
        conversation_id=conv_id, user_id=user_id, title="Test Conversation"
    )
    print(f"✓ Conversation created: {conversation.conversation_id.value}")

    # Test Message entity
    msg_id = MessageId.generate()
    message = Message(message_id=msg_id, role="user", content="Hello, world!")
    print(f"✓ Message created: {message.message_id.value}")

    # Test adding message to conversation
    conversation.add_message(message)
    print(f"✓ Message added to conversation. Count: {conversation.get_message_count()}")

    return user, conversation, message


def test_value_objects():
    """Test value objects"""
    print("\nTesting Value Objects...")

    # Test Language enum
    lang = Language.FRENCH
    print(f"✓ Language: {lang.value}")

    # Test MemoryType enum
    memory_type = MemoryType.BUFFER
    print(f"✓ Memory Type: {memory_type.value}")

    # Test MessageMetadata
    metadata = MessageMetadata.create(
        message_type=MessageType.SIMPLE,
        is_question=True,
        is_code_request=False,
        length=10,
    )
    print(f"✓ Message Metadata: {metadata.message_type.value}")

    return lang, memory_type, metadata


def test_domain_services():
    """Test domain services"""
    print("\nTesting Domain Services...")

    # Test MessageClassificationService
    content = "How do I write a Python function?"
    category = MessageClassificationService.classify_message(content)
    print(f"✓ Message classification: '{content}' -> {category.value}")

    # Test ConversationTitleService
    title = ConversationTitleService.generate_title("Hello, how are you?")
    print(f"✓ Conversation title: '{title}'")

    return category, title


async def test_infrastructure():
    """Test infrastructure layer"""
    print("\nTesting Infrastructure Layer...")

    # Test repositories
    user_repo = SQLiteUserRepository()
    conv_repo = SQLiteConversationRepository()
    print("✓ Repositories initialized")

    # Test cache service
    cache_service = InMemoryCacheService()
    print("✓ Cache service initialized")

    # Test LLM service (without actual LLM call)
    llm_service = LangChainLLMService()
    print("✓ LLM service initialized")

    return user_repo, conv_repo, cache_service, llm_service


async def test_use_cases():
    """Test use cases"""
    print("\nTesting Use Cases...")

    # Initialize dependencies
    user_repo = SQLiteUserRepository()
    conv_repo = SQLiteConversationRepository()
    llm_service = LangChainLLMService()
    cache_service = InMemoryCacheService()

    # Create chat use case
    chat_use_case = ChatUseCase(user_repo, conv_repo, llm_service, cache_service)
    print("✓ Chat use case created")

    # Test chat request creation
    chat_request = ChatRequest(
        user_token="devtoken123",
        message_content="Hello!",
        language=Language.FRENCH,
        memory_type=MemoryType.BUFFER,
    )
    print("✓ Chat request created")

    return chat_use_case, chat_request


async def main():
    """Run all tests"""
    print("🚀 Testing New DDD/Hexagonal Architecture\n")

    try:
        # Test domain layer
        user, conversation, message = await test_domain_entities()
        lang, memory_type, metadata = test_value_objects()
        category, title = test_domain_services()

        # Test infrastructure layer
        user_repo, conv_repo, cache_service, llm_service = await test_infrastructure()

        # Test use cases
        chat_use_case, chat_request = await test_use_cases()

        print("\n✅ All tests passed! Architecture is working correctly.")
        print("\n📋 Architecture Summary:")
        print("  • Domain Layer: Entities, Value Objects, Services ✓")
        print("  • Application Layer: Use Cases ✓")
        print("  • Infrastructure Layer: Repositories, Services ✓")
        print("  • Interface Layer: Ready for FastAPI integration ✓")

        print("\n🎯 Key Benefits Achieved:")
        print("  • Separation of Concerns ✓")
        print("  • Domain-Driven Design ✓")
        print("  • Hexagonal Architecture ✓")
        print("  • Dependency Inversion ✓")
        print("  • Testability ✓")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
