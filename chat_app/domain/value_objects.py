"""
Value Objects - Immutable objects without identity
"""
import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class MemoryType(Enum):
    """Memory management strategy for conversations"""

    BUFFER = "buffer"
    SUMMARY = "summary"
    TOKEN_BUFFER = "token_buffer"


class Language(Enum):
    """Supported languages"""

    FRENCH = "fr"
    ENGLISH = "en"


class MessageType(Enum):
    """Type of message for processing optimization"""

    SIMPLE = "simple"
    COMPLEX = "complex"


class MessageCategory(Enum):
    """Category of message for model selection"""

    CODE = "code"
    GENERAL = "general"


@dataclass(frozen=True)
class MessageMetadata:
    """Metadata about a message for processing optimization"""

    message_type: MessageType
    is_question: bool
    is_code_request: bool
    length: int
    has_quick_response: bool
    quick_response: Optional[str] = None

    @classmethod
    def create(
        cls,
        message_type: MessageType,
        is_question: bool,
        is_code_request: bool,
        length: int,
        has_quick_response: bool = False,
        quick_response: Optional[str] = None,
    ) -> "MessageMetadata":
        """Create message metadata with the given parameters."""
        return cls(
            message_type=message_type,
            is_question=is_question,
            is_code_request=is_code_request,
            length=length,
            has_quick_response=has_quick_response,
            quick_response=quick_response,
        )


@dataclass(frozen=True)
class LLMConfiguration:
    """Configuration for LLM model selection and parameters"""

    model_name: str
    temperature: float
    num_predict: int
    num_ctx: int
    top_k: int = 40
    top_p: float = 0.9
    repeat_penalty: float = 1.1
    num_thread: int = 4

    @classmethod
    def for_mistral(cls) -> "LLMConfiguration":
        """Create configuration for Mistral model."""
        return cls(
            model_name="mistral", temperature=0.7, num_predict=1024, num_ctx=2048
        )

    @classmethod
    def for_deepseek_coder(cls) -> "LLMConfiguration":
        """Create configuration for DeepSeek Coder model."""
        return cls(
            model_name="deepseek-coder", temperature=0.3, num_predict=1024, num_ctx=4096
        )

    @classmethod
    def for_llama3(cls) -> "LLMConfiguration":
        """Create configuration for Llama3 model."""
        return cls(model_name="llama3", temperature=0.7, num_predict=2048, num_ctx=4096)

    @classmethod
    def for_simple_message(cls, base_config: "LLMConfiguration") -> "LLMConfiguration":
        """Optimized configuration for simple messages"""
        return cls(
            model_name=base_config.model_name,
            temperature=0.5,
            num_predict=512,
            num_ctx=2048,
            top_k=base_config.top_k,
            top_p=base_config.top_p,
            repeat_penalty=base_config.repeat_penalty,
            num_thread=base_config.num_thread,
        )


@dataclass(frozen=True)
class MemoryStats:
    """Statistics about conversation memory state"""

    memory_type: str
    message_count: int
    buffer_length: Optional[int] = None
    has_summary: Optional[bool] = None
    token_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory stats to dictionary."""
        return {
            "type": self.memory_type,
            "message_count": self.message_count,
            "buffer_length": self.buffer_length,
            "has_summary": self.has_summary,
            "token_count": self.token_count,
        }


@dataclass(frozen=True)
class CacheKey:
    """Cache key for response caching"""

    value: str

    @classmethod
    def from_content(
        cls, user_msg: str, conversation_context: str = "", lang: str = "fr"
    ) -> "CacheKey":
        """Create cache key from message content and context."""
        content = f"{user_msg}|{conversation_context}|{lang}"
        return cls(value=hashlib.md5(content.encode()).hexdigest())


@dataclass(frozen=True)
class PerformanceMetrics:
    """Performance monitoring metrics"""

    total_time: float
    checkpoints: Dict[str, float]
    operation: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert performance metrics to dictionary."""
        return {
            "total_time": self.total_time,
            "checkpoints": self.checkpoints,
            "operation": self.operation,
        }
