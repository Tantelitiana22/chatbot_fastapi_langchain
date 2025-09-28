"""
LLM Service Implementation - LangChain integration
"""
import langchain
from langchain.chains import ConversationChain
from langchain.memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory,
    ConversationTokenBufferMemory,
)
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage
from langchain_community.cache import SQLiteCache
from langchain_ollama import ChatOllama

from chat_app.application.use_cases import LLMService
from chat_app.domain.entities import Conversation
from chat_app.domain.value_objects import (
    Language,
    LLMConfiguration,
    MemoryStats,
    MemoryType,
    MessageMetadata,
)

# Enhanced caching for faster responses
langchain.llm_cache = SQLiteCache("llm_cache.db")


class LangChainLLMService(LLMService):
    """LangChain implementation of LLM service"""

    def __init__(self):
        self.classifier_llm = ChatOllama(
            model="mistral", temperature=0.1, num_predict=10, num_ctx=512
        )

    async def generate_response(
        self,
        conversation: Conversation,
        user_message: str,
        language: Language,
        memory_type: MemoryType,
        message_metadata: MessageMetadata,
    ) -> str:
        """Generate AI response for user message"""

        # Select model and configuration
        llm_config = self._select_model_config(memory_type, message_metadata)

        # Create LLM instance
        llm = ChatOllama(
            model=llm_config.model_name,
            temperature=llm_config.temperature,
            num_predict=llm_config.num_predict,
            num_ctx=llm_config.num_ctx,
            top_k=llm_config.top_k,
            top_p=llm_config.top_p,
            repeat_penalty=llm_config.repeat_penalty,
            num_thread=llm_config.num_thread,
            stop=["Human:", "Assistant:", "User:", "AI:"],
        )

        # Create memory
        memory = self._create_memory(llm, memory_type, language)

        # Load conversation history into memory
        self._load_conversation_into_memory(memory, conversation)

        # Create system prompt
        system_prompt = self._create_system_prompt(language)

        # Create conversation chain
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        conversation_chain = ConversationChain(
            llm=llm, memory=memory, prompt=prompt, verbose=False
        )

        # Generate response
        response = await conversation_chain.ainvoke({"input": user_message})
        if isinstance(response, dict):
            result = response.get("response", "")
            return str(result) if result is not None else ""
        return str(response)

    async def classify_message(self, content: str) -> str:
        """Classify message using LLM"""
        prompt = f"Classify: 'code' or 'general'? Message: {content[:100]}"
        try:
            result = await self.classifier_llm.ainvoke([HumanMessage(content=prompt)])
            return "code" if "code" in result.content.lower() else "general"
        except Exception as e:
            print(f"Classification error: {e}")
            return "general"

    def _select_model_config(
        self, memory_type: MemoryType, message_metadata: MessageMetadata
    ) -> LLMConfiguration:
        """Select model configuration based on memory type and message metadata"""

        if memory_type in [MemoryType.SUMMARY, MemoryType.TOKEN_BUFFER]:
            # Use Mistral for summary and token buffer memory types
            base_config = LLMConfiguration.for_mistral()
        else:
            # Use classification for buffer memory type
            if message_metadata.is_code_request:
                base_config = LLMConfiguration.for_deepseek_coder()
            else:
                base_config = LLMConfiguration.for_llama3()

        # Optimize for simple messages
        if message_metadata.message_type.value == "simple":
            return LLMConfiguration.for_simple_message(base_config)

        return base_config

    def _create_memory(self, llm, memory_type: MemoryType, language: Language):
        """Create appropriate memory instance"""

        if memory_type == MemoryType.BUFFER:
            return ConversationBufferMemory(
                memory_key="chat_history", return_messages=True, input_key="input"
            )

        if memory_type == MemoryType.SUMMARY:
            return ConversationSummaryMemory(
                llm=llm,
                memory_key="chat_history",
                return_messages=True,
                input_key="input",
            )

        if memory_type == MemoryType.TOKEN_BUFFER:
            return ConversationTokenBufferMemory(
                llm=llm,
                memory_key="chat_history",
                return_messages=True,
                input_key="input",
                max_token_limit=1500,
            )

        return ConversationBufferMemory(
            memory_key="chat_history", return_messages=True, input_key="input"
        )

    def _load_conversation_into_memory(self, memory, conversation: Conversation):
        """Load existing conversation messages into memory"""

        # Clear existing memory to avoid duplicates
        memory.clear()

        # Limit the number of messages loaded for performance
        max_messages = 20
        recent_messages = conversation.get_recent_messages(max_messages)

        # Load messages into memory
        for message in recent_messages:
            if message.role == "user":
                memory.chat_memory.add_user_message(message.content)
            elif message.role == "assistant":
                memory.chat_memory.add_ai_message(message.content)

    def _create_system_prompt(self, language: Language) -> str:
        """Create system prompt based on language"""

        if language == Language.FRENCH:
            return (
                "Vous êtes un assistant IA utile avec des capacités de mémoire. "
                "Vous pouvez vous souvenir et faire référence aux messages précédents "
                "de notre conversation. Lorsque vous fournissez des exemples de code, "
                "formatez-les toujours en utilisant des blocs de code Markdown avec la "
                "coloration syntaxique appropriée. Utilisez ```python pour le code "
                "Python, ```javascript pour JavaScript, ```html pour HTML, etc. "
                "Fournissez des "
                "exemples complets et fonctionnels quand c'est possible.\n\n"
                "Vous pouvez référencer les parties précédentes de notre conversation "
                "quand c'est pertinent. Par exemple :\n"
                '- "Comme nous en avons discuté plus tôt..."\n'
                "- \"En s'appuyant sur l'exemple précédent...\"\n"
                '- "Vous souvenez-vous quand vous avez demandé..."\n'
                '- "En suivant notre conversation précédente sur..."\n\n'
                "Cela aide à maintenir le contexte et à fournir des réponses plus "
                "cohérentes et utiles."
            )
        else:
            return (
                "You are a helpful AI assistant with memory capabilities. "
                "You can remember and refer to previous messages in our conversation. "
                "When providing code examples, always format them using Markdown code "
                "blocks with proper syntax highlighting. Use ```python for Python "
                "code, ```javascript for JavaScript, ```html for HTML, etc. Provide "
                "complete, "
                "working examples when possible.\n\n"
                "You can reference previous parts of our conversation when relevant. "
                "For example:\n"
                '- "As we discussed earlier..."\n'
                '- "Building on the previous example..."\n'
                '- "Remember when you asked about..."\n'
                '- "Following up on our previous conversation about..."\n\n'
                "This helps maintain context and provide more coherent, helpful "
                "responses."
            )

    def get_memory_stats(self, memory) -> MemoryStats:
        """Get statistics about the current memory state"""
        stats = {
            "type": type(memory).__name__,
            "message_count": len(memory.chat_memory.messages)
            if hasattr(memory, "chat_memory")
            else 0,
        }

        if hasattr(memory, "buffer") and memory.buffer:
            stats["buffer_length"] = len(memory.buffer)

        if hasattr(memory, "summary"):
            stats["has_summary"] = bool(memory.summary)

        if hasattr(memory, "token_count"):
            stats["token_count"] = memory.token_count

        return MemoryStats(
            memory_type=str(stats["type"]),
            message_count=int(str(stats["message_count"])),
            buffer_length=int(str(stats.get("buffer_length", 0)))
            if stats.get("buffer_length") is not None
            else None,
            has_summary=bool(stats.get("has_summary"))
            if stats.get("has_summary") is not None
            else None,
            token_count=int(str(stats.get("token_count", 0)))
            if stats.get("token_count") is not None
            else None,
        )
