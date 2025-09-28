# backend/llm.py
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_community.cache import SQLiteCache
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory, ConversationTokenBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import langchain
import os

# Enhanced caching for faster responses
langchain.llm_cache = SQLiteCache("llm_cache.db")

# Simple in-memory cache for recent responses
import hashlib
from typing import Dict, Any
response_cache: Dict[str, str] = {}
CACHE_SIZE_LIMIT = 100  # Limit cache size to prevent memory issues

# Optimized classifier with faster model and parameters
classifier_llm = ChatOllama(
    model="mistral",
    temperature=0.1,  # Lower temperature for faster, more deterministic responses
    num_predict=10,   # Limit response length for classification
    num_ctx=512       # Smaller context window for faster processing
)

# Memory types configuration
MEMORY_TYPES = {
    "buffer": ConversationBufferMemory,
    "summary": ConversationSummaryMemory,
    "token_buffer": ConversationTokenBufferMemory
}

async def classify_message(user_msg: str) -> str:
    """Fast classification using optimized parameters"""
    # Simple keyword-based classification for speed
    code_keywords = [
        'code', 'function', 'class', 'variable', 'loop', 'if', 'else', 'python', 'javascript', 
        'html', 'css', 'sql', 'api', 'debug', 'error', 'exception', 'import', 'def', 'return',
        'programming', 'algorithm', 'syntax', 'compile', 'execute', 'script', 'framework',
        'library', 'package', 'module', 'method', 'parameter', 'argument', 'array', 'object',
        'string', 'integer', 'boolean', 'float', 'list', 'dictionary', 'tuple', 'set'
    ]
    
    user_msg_lower = user_msg.lower()
    
    # Quick keyword check
    for keyword in code_keywords:
        if keyword in user_msg_lower:
            return "code"
    
    # Fallback to LLM classification only if no keywords found
    prompt = f"Classify: 'code' or 'general'? Message: {user_msg[:100]}"
    try:
        result = await classifier_llm.ainvoke([HumanMessage(content=prompt)])
        return "code" if "code" in result.content.lower() else "general"
    except Exception as e:
        print(f"Classification error: {e}")
        return "general"  # Default fallback

async def build_chain(conversation: dict, user_msg: str, lang: str, memory_type: str = "buffer", message_info: dict = None):
    """
    Build a conversation chain with memory management
    
    Args:
        conversation: Conversation data with messages
        user_msg: Current user message
        lang: Language preference
        memory_type: Type of memory to use ("buffer", "summary", "token_buffer")
    
    Returns:
        tuple: (llm, conversation_chain, memory)
    """
    category = await classify_message(user_msg)
    model_name = "deepseek-coder" if category == "code" else "llama3"
    
    # Optimize parameters based on message type
    if message_info and message_info.get("type") == "simple":
        # Faster parameters for simple messages
        temperature = 0.5
        num_predict = 512
        num_ctx = 2048
    elif message_info and message_info.get("is_code_request"):
        # Optimized for code generation
        temperature = 0.3
        num_predict = 1024
        num_ctx = 4096
    else:
        # Default balanced parameters
        temperature = 0.7
        num_predict = 2048
        num_ctx = 4096
    
    # Optimized LLM configuration for faster responses
    llm = ChatOllama(
        model=model_name,
        temperature=temperature,      # Dynamic based on message type
        num_predict=num_predict,     # Dynamic response length limit
        num_ctx=num_ctx,             # Dynamic context window
        top_k=40,                    # Reduce sampling for speed
        top_p=0.9,                   # Optimize probability mass
        repeat_penalty=1.1,          # Prevent repetition
        num_thread=4,                # Use multiple threads if available
        stop=["Human:", "Assistant:", "User:", "AI:"]  # Stop tokens for cleaner responses
    )

    # Enhanced system prompt with memory awareness
    system_prompt = """You are a helpful AI assistant with memory capabilities. You can remember and refer to previous messages in our conversation. When providing code examples, always format them using Markdown code blocks with proper syntax highlighting. Use ```python for Python code, ```javascript for JavaScript, ```html for HTML, etc. Provide complete, working examples when possible.

You can reference previous parts of our conversation when relevant. For example:
- "As we discussed earlier..."
- "Building on the previous example..."
- "Remember when you asked about..."
- "Following up on our previous conversation about..."

This helps maintain context and provide more coherent, helpful responses."""
    
    if lang == "fr":
        system_prompt = """Vous êtes un assistant IA utile avec des capacités de mémoire. Vous pouvez vous souvenir et faire référence aux messages précédents de notre conversation. Lorsque vous fournissez des exemples de code, formatez-les toujours en utilisant des blocs de code Markdown avec la coloration syntaxique appropriée. Utilisez ```python pour le code Python, ```javascript pour JavaScript, ```html pour HTML, etc. Fournissez des exemples complets et fonctionnels quand c'est possible.

Vous pouvez référencer les parties précédentes de notre conversation quand c'est pertinent. Par exemple :
- "Comme nous en avons discuté plus tôt..."
- "En s'appuyant sur l'exemple précédent..."
- "Vous souvenez-vous quand vous avez demandé..."
- "En suivant notre conversation précédente sur..."

Cela aide à maintenir le contexte et à fournir des réponses plus cohérentes et utiles."""

    # Create memory based on type
    memory = create_memory(llm, memory_type, lang)
    
    # Load conversation history into memory
    load_conversation_into_memory(memory, conversation)
    
    # Create conversation chain with memory
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])
    
    conversation_chain = ConversationChain(
        llm=llm,
        memory=memory,
        prompt=prompt,
        verbose=False
    )

    return llm, conversation_chain, memory

def create_memory(llm, memory_type: str, lang: str):
    """
    Create appropriate memory instance based on type
    
    Args:
        llm: Language model instance
        memory_type: Type of memory ("buffer", "summary", "token_buffer")
        lang: Language preference
    
    Returns:
        Memory instance
    """
    if memory_type not in MEMORY_TYPES:
        memory_type = "buffer"  # Default fallback
    
    if memory_type == "buffer":
        return ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="input"
        )
    
    elif memory_type == "summary":
        return ConversationSummaryMemory(
            llm=llm,
            memory_key="chat_history",
            return_messages=True,
            input_key="input"
        )
    
    elif memory_type == "token_buffer":
        return ConversationTokenBufferMemory(
            llm=llm,
            memory_key="chat_history",
            return_messages=True,
            input_key="input",
            max_token_limit=1500  # Reduced for faster processing
        )

def load_conversation_into_memory(memory, conversation: dict):
    """
    Load existing conversation messages into memory with optimization
    
    Args:
        memory: Memory instance
        conversation: Conversation data with messages
    """
    messages = conversation.get("messages", [])
    
    # Clear existing memory to avoid duplicates
    memory.clear()
    
    # Limit the number of messages loaded for performance
    max_messages = 20  # Reasonable limit for context
    recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
    
    # Load messages into memory
    for message in recent_messages:
        if message["role"] == "user":
            memory.chat_memory.add_user_message(message["content"])
        elif message["role"] == "assistant":
            memory.chat_memory.add_ai_message(message["content"])

def get_memory_stats(memory):
    """
    Get statistics about the current memory state
    
    Args:
        memory: Memory instance
    
    Returns:
        dict: Memory statistics
    """
    stats = {
        "type": type(memory).__name__,
        "message_count": len(memory.chat_memory.messages) if hasattr(memory, 'chat_memory') else 0
    }
    
    if hasattr(memory, 'buffer') and memory.buffer:
        stats["buffer_length"] = len(memory.buffer)
    
    if hasattr(memory, 'summary'):
        stats["has_summary"] = bool(memory.summary)
    
    if hasattr(memory, 'token_count'):
        stats["token_count"] = memory.token_count
    
    return stats

def get_cache_key(user_msg: str, conversation_context: str = "") -> str:
    """Generate a cache key for the user message and context"""
    # Create a hash of the message and recent context
    content = f"{user_msg}|{conversation_context}"
    return hashlib.md5(content.encode()).hexdigest()

def get_cached_response(cache_key: str) -> str:
    """Get cached response if available"""
    return response_cache.get(cache_key, "")

def cache_response(cache_key: str, response: str):
    """Cache the response"""
    # Limit cache size
    if len(response_cache) >= CACHE_SIZE_LIMIT:
        # Remove oldest entries (simple FIFO)
        oldest_key = next(iter(response_cache))
        del response_cache[oldest_key]
    
    response_cache[cache_key] = response

def get_conversation_context(conversation: dict, max_messages: int = 3) -> str:
    """Get recent conversation context for caching"""
    messages = conversation.get("messages", [])
    recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
    
    context_parts = []
    for msg in recent_messages:
        if msg.get("role") == "user":
            context_parts.append(f"U:{msg['content'][:100]}")
        elif msg.get("role") == "assistant":
            context_parts.append(f"A:{msg['content'][:100]}")
    
    return "|".join(context_parts)

# Performance monitoring
import time
from typing import Optional

class PerformanceMonitor:
    def __init__(self):
        self.start_time: Optional[float] = None
        self.checkpoints: dict = {}
    
    def start(self):
        self.start_time = time.time()
        self.checkpoints = {}
    
    def checkpoint(self, name: str):
        if self.start_time:
            self.checkpoints[name] = time.time() - self.start_time
    
    def get_total_time(self) -> float:
        if self.start_time:
            return time.time() - self.start_time
        return 0.0
    
    def log_performance(self, operation: str):
        total_time = self.get_total_time()
        print(f"Performance - {operation}: {total_time:.2f}s")
        for name, time_taken in self.checkpoints.items():
            print(f"  {name}: {time_taken:.2f}s")

# Global performance monitor
perf_monitor = PerformanceMonitor()

# Connection pooling for better resource management
import threading
from queue import Queue

class LLMConnectionPool:
    def __init__(self, max_connections=3):
        self.max_connections = max_connections
        self.connections = Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize LLM connections"""
        for _ in range(self.max_connections):
            # Create lightweight connection objects
            self.connections.put({"id": f"conn_{_}", "available": True})
    
    def get_connection(self):
        """Get an available connection"""
        try:
            return self.connections.get_nowait()
        except:
            return {"id": "temp", "available": True}
    
    def return_connection(self, conn):
        """Return connection to pool"""
        if conn["id"] != "temp":
            self.connections.put(conn)

# Global connection pool
connection_pool = LLMConnectionPool()
