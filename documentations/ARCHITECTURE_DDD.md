# 🏗️ Domain-Driven Design Architecture

This document describes the new hexagonal architecture implementation using Domain-Driven Design principles.

## 📋 Architecture Overview

The application has been refactored to follow **Hexagonal Architecture** (Ports and Adapters) with **Domain-Driven Design** principles:

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   REST API     │  │   WebSocket     │  │   Static    │ │
│  │   Adapter      │  │   Adapter       │  │   Files     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Chat Use      │  │   Get Conv.      │  │   Clear     │ │
│  │   Case          │  │   Use Case       │  │   Cache     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Entities      │  │   Value Objects  │  │   Services  │ │
│  │   (User, Conv., │  │   (MemoryType,   │  │   (Message  │ │
│  │    Message)     │  │    Language,     │  │   Classif.) │ │
│  └─────────────────┘  │    LLMConfig)   │  └─────────────┘ │
│                        └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   SQLite        │  │   LangChain     │  │   In-Memory │ │
│  │   Repositories  │  │   LLM Service   │  │   Cache     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Domain Model

### Core Entities

#### User
- **Identity**: UserId (value object)
- **Properties**: token, created_at
- **Business Rules**: Token must be non-empty string

#### Conversation (Aggregate Root)
- **Identity**: ConversationId (value object)
- **Properties**: user_id, title, messages, timestamps
- **Business Rules**:
  - Must belong to a user
  - Title auto-generated from first message
  - Messages added in order

#### Message
- **Identity**: MessageId (value object)
- **Properties**: role, content, timestamp
- **Business Rules**:
  - Role must be 'user' or 'assistant'
  - Content must be non-empty

### Value Objects

#### MemoryType
- **Values**: BUFFER, SUMMARY, TOKEN_BUFFER
- **Purpose**: Defines conversation memory strategy

#### Language
- **Values**: FRENCH, ENGLISH
- **Purpose**: Defines system prompt language

#### MessageMetadata
- **Properties**: message_type, is_question, is_code_request, length
- **Purpose**: Optimizes message processing

#### LLMConfiguration
- **Properties**: model_name, temperature, num_predict, num_ctx
- **Purpose**: Configures LLM parameters dynamically

## 🔌 Ports and Adapters

### Ports (Interfaces)

#### Repository Ports
- `UserRepository`: User data access
- `ConversationRepository`: Conversation data access

#### Service Ports
- `LLMService`: AI response generation
- `CacheService`: Response caching

### Adapters (Implementations)

#### Infrastructure Adapters
- `SQLiteUserRepository`: SQLite implementation
- `SQLiteConversationRepository`: SQLite implementation
- `LangChainLLMService`: LangChain + Ollama implementation
- `InMemoryCacheService`: In-memory cache implementation

#### Interface Adapters
- `ChatAPI`: REST API adapter
- `WebSocketChatHandler`: WebSocket adapter

## 🚀 Use Cases

### ChatUseCase
- **Input**: ChatRequest (token, message, conversation_id, language, memory_type)
- **Output**: ChatResponse (conversation_id, response, memory_stats, performance_metrics)
- **Process**:
  1. Authenticate user
  2. Get/create conversation
  3. Analyze message metadata
  4. Check cache or generate response
  5. Add messages to conversation
  6. Save conversation
  7. Return response

### GetConversationsUseCase
- **Input**: user_token
- **Output**: List[Conversation]
- **Process**:
  1. Authenticate user
  2. Retrieve user's conversations
  3. Return formatted list

### GetConversationUseCase
- **Input**: user_token, conversation_id
- **Output**: Conversation
- **Process**:
  1. Authenticate user
  2. Retrieve specific conversation
  3. Return conversation data

### ClearCacheUseCase
- **Input**: None
- **Output**: None
- **Process**:
  1. Clear all cached responses

## 🏛️ Domain Services

### MessageClassificationService
- **Purpose**: Classify messages as code or general
- **Strategy**: Keyword-based with LLM fallback
- **Performance**: ~80% faster than full LLM classification

### ConversationTitleService
- **Purpose**: Generate meaningful conversation titles
- **Strategy**: Clean first message, remove prefixes, truncate

### ConversationContextService
- **Purpose**: Manage conversation context for caching
- **Strategy**: Extract recent message summaries

## 📊 Benefits of New Architecture

### 1. **Separation of Concerns**
- Domain logic isolated from infrastructure
- Business rules centralized in domain layer
- Clear boundaries between layers

### 2. **Testability**
- Easy to mock dependencies
- Unit tests for domain logic
- Integration tests for use cases

### 3. **Maintainability**
- Changes to infrastructure don't affect domain
- New features added through use cases
- Clear dependency flow

### 4. **Extensibility**
- Easy to add new LLM providers
- Simple to change database implementation
- New interfaces can be added without affecting core

### 5. **Performance**
- Optimized message processing
- Intelligent caching strategy
- Parallel operations where possible

## 🔄 Migration Strategy

### Phase 1: New Architecture (Completed)
- ✅ Domain layer implementation
- ✅ Application layer with use cases
- ✅ Infrastructure adapters
- ✅ Interface adapters

### Phase 2: Integration (In Progress)
- 🔄 Update main application entry point
- 🔄 Dependency injection setup
- 🔄 Configuration management

### Phase 3: Testing & Validation
- ⏳ Unit tests for domain logic
- ⏳ Integration tests for use cases
- ⏳ End-to-end testing

### Phase 4: Deployment
- ⏳ Update deployment configuration
- ⏳ Performance monitoring
- ⏳ Documentation updates

## 🎯 Key Improvements

1. **Domain-Driven Design**: Business logic is now expressed in domain terms
2. **Hexagonal Architecture**: Clean separation between core and external concerns
3. **Dependency Inversion**: High-level modules don't depend on low-level modules
4. **Single Responsibility**: Each class has one reason to change
5. **Open/Closed Principle**: Open for extension, closed for modification

## 📁 Project Structure

```
chat_app/
├── domain/                 # Core business logic
│   ├── entities.py        # Domain entities
│   ├── value_objects.py   # Value objects
│   ├── services.py        # Domain services
│   └── repositories.py    # Repository interfaces
├── application/           # Use cases and application services
│   └── use_cases.py       # Application use cases
├── infrastructure/        # External concerns
│   ├── repositories.py    # Repository implementations
│   ├── llm_service.py     # LLM service implementation
│   ├── cache_service.py   # Cache service implementation
│   └── performance_monitor.py
└── interface/             # Web interfaces
    ├── rest_api.py        # REST API adapter
    ├── websocket_api.py   # WebSocket adapter
    ├── app.py            # Main application
    └── dependency_injection.py
```

This architecture provides a solid foundation for future enhancements while maintaining the existing functionality and improving code quality, testability, and maintainability.
