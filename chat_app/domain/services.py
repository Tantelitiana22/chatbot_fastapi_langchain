"""
Domain Services - Business logic that doesn't belong to a single entity
"""
import re

from chat_app.domain.entities import Conversation
from chat_app.domain.value_objects import (
    Language,
    MessageCategory,
    MessageMetadata,
    MessageType,
)


class MessageClassificationService:
    """Domain service for classifying messages"""

    CODE_KEYWORDS = [
        "code",
        "function",
        "class",
        "variable",
        "loop",
        "if",
        "else",
        "python",
        "javascript",
        "html",
        "css",
        "sql",
        "api",
        "debug",
        "error",
        "exception",
        "import",
        "def",
        "return",
        "programming",
        "algorithm",
        "syntax",
        "compile",
        "execute",
        "script",
        "framework",
        "library",
        "package",
        "module",
        "method",
        "parameter",
        "argument",
        "array",
        "object",
        "string",
        "integer",
        "boolean",
        "float",
        "list",
        "dictionary",
        "tuple",
        "set",
    ]

    QUICK_RESPONSES = {
        "hello": "Hello! How can I help you today?",
        "hi": "Hi there! What would you like to know?",
        "thanks": "You're welcome! Is there anything else I can help with?",
        "thank you": "You're welcome! Feel free to ask if you need more help.",
        "bye": "Goodbye! Have a great day!",
        "goodbye": "See you later! Take care!",
    }

    @classmethod
    def classify_message(cls, content: str) -> MessageCategory:
        """Classify message as code or general"""
        content_lower = content.lower()

        # Quick keyword check
        for keyword in cls.CODE_KEYWORDS:
            if keyword in content_lower:
                return MessageCategory.CODE

        return MessageCategory.GENERAL

    @classmethod
    def analyze_message(cls, content: str) -> MessageMetadata:
        """Analyze message and return metadata for processing optimization"""
        cleaned_content = content.strip()

        # Basic validation
        if not cleaned_content:
            raise ValueError("Message content cannot be empty")

        if len(cleaned_content) > 4000:
            raise ValueError("Message content too long")

        # Detect message type
        message_type = (
            MessageType.SIMPLE if len(cleaned_content) < 50 else MessageType.COMPLEX
        )

        # Detect if it's a question
        is_question = cleaned_content.endswith("?") or any(
            word in cleaned_content.lower()
            for word in ["how", "what", "why", "when", "where", "who"]
        )

        # Detect if it's a code request
        is_code_request = cls.classify_message(cleaned_content) == MessageCategory.CODE

        # Check for quick response
        has_quick_response = cleaned_content.lower() in cls.QUICK_RESPONSES
        quick_response = (
            cls.QUICK_RESPONSES.get(cleaned_content.lower())
            if has_quick_response
            else None
        )

        return MessageMetadata.create(
            message_type=message_type,
            is_question=is_question,
            is_code_request=is_code_request,
            length=len(cleaned_content),
            has_quick_response=has_quick_response,
            quick_response=quick_response,
        )


class ConversationTitleService:
    """Domain service for generating conversation titles"""

    @classmethod
    def generate_title(cls, first_message: str) -> str:
        """Generate a meaningful title from the first user message"""

        # Clean up the message
        message = first_message.strip()

        # Remove common prefixes
        prefixes_to_remove = [
            r"^(hi|hello|hey|bonjour|salut)\s*,?\s*",
            r"^(can you|could you|please|peux-tu|pourrais-tu)\s+",
            r"^(i need|i want|je veux|j\'ai besoin)\s+",
            r"^(help me|aide-moi|m\'aider)\s+",
        ]

        for prefix in prefixes_to_remove:
            message = re.sub(prefix, "", message, flags=re.IGNORECASE)

        # Truncate if too long
        if len(message) > 50:
            message = message[:47] + "..."

        # Capitalize first letter
        if message:
            message = message[0].upper() + message[1:]

        # Fallback if message is too short or empty
        if len(message.strip()) < 3:
            return "New Conversation"

        return message.strip()


class ConversationContextService:
    """Domain service for managing conversation context"""

    @classmethod
    def get_context_summary(
        cls, conversation: Conversation, max_messages: int = 3
    ) -> str:
        """Get recent conversation context for caching and processing"""
        recent_messages = conversation.get_recent_messages(max_messages)

        context_parts = []
        for msg in recent_messages:
            if msg.role == "user":
                context_parts.append(f"U:{msg.content[:100]}")
            elif msg.role == "assistant":
                context_parts.append(f"A:{msg.content[:100]}")

        return "|".join(context_parts)

    @classmethod
    def should_use_cached_response(
        cls, conversation: Conversation, message_content: str, language: Language
    ) -> bool:
        """Determine if cached response should be used"""
        # Simple heuristic: use cache for repeated questions or greetings
        return (
            message_content.lower() in MessageClassificationService.QUICK_RESPONSES
            or conversation.get_message_count()
            > 5  # Use cache for longer conversations
        )
