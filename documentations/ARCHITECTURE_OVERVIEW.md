ffer # 🏗️ Architecture Overview

This document provides a text-based overview of the message flow architecture and the models used.

## 🤖 Models Used

### Model Selection by Memory Type

#### **🧠 Buffer complet (Complete Buffer)**
**Classification Model: Mistral**
```
Purpose: Message classification (code vs general)
Parameters: Temperature 0.1, Context 512, Prediction 10
Optimization: Keyword-based with LLM fallback
Performance: ~80% faster than full LLM classification
```

**Generation Models**

**deepseek-coder** (Code Generation)
```
Trigger: Code-related content detected
Parameters: Temperature 0.3, Context 4096, Prediction 1024
Use Cases: Programming, debugging, code examples
Optimization: Precision-focused for accurate code generation
```

**llama3** (General Conversation)
```
Trigger: General content detected
Parameters: Temperature 0.7, Context 4096, Prediction 2048
Use Cases: Questions, explanations, discussions
Optimization: Balanced creativity and accuracy
```

#### **📝 Résumé intelligent (Smart Summary)**
**Single Model: Mistral**
```
Purpose: All interactions (no classification)
Parameters: Temperature 0.7, Context 2048, Prediction 1024
Use Cases: General conversation, summaries, all content types
Optimization: Balanced parameters for general use
Performance: No classification overhead
```

#### **⚡ Buffer limité (Limited Buffer)**
**Single Model: Mistral**
```
Purpose: All interactions (no classification)
Parameters: Temperature 0.7, Context 2048, Prediction 1024
Use Cases: General conversation, limited context, all content types
Optimization: Balanced parameters for general use
Performance: No classification overhead
```

## 📊 Message Flow Architecture

```
User Message
    ↓
Request Reception
    ↓
Message Preprocessing
    ↓
Message Validation
    ↓
Memory Type Check
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│   Buffer        │   Summary        │   Token Buffer   │
│   Complet       │   Intelligent    │   Limité         │
└─────────────────┴─────────────────┴─────────────────┘
    ↓                     ↓                     ↓
Classification        Direct to            Direct to
Model: Mistral        Mistral              Mistral
    ↓                     ↓                     ↓
┌─────────────────┬─────────────────┬─────────────────┐
│   Code?         │   Mistral       │   Mistral       │
│   deepseek-coder│   Generation    │   Generation    │
│   General?      │   (All Types)   │   (All Types)   │
│   llama3        │                 │                 │
└─────────────────┴─────────────────┴─────────────────┘
    ↓                     ↓                     ↓
Quick Response Check ←───┴─────────────────────┘
    ↓
┌─────────────────┬─────────────────┐
│   Found?        │   No: Build     │
│   Instant       │   Optimized     │
│   Response      │   Chain         │
└─────────────────┴─────────────────┘
    ↓                     ↓
Dynamic Parameter Optimization
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│   Mistral:      │   Simple:       │   Code/Complex: │
│   temp=0.7      │   temp=0.5      │   temp=0.3/0.7  │
│   tokens=1024   │   tokens=512   │   tokens=1024/  │
│   ctx=2048      │   ctx=2048      │   2048/4096     │
└─────────────────┴─────────────────┴─────────────────┘
    ↓
LLM Generation (Mistral OR deepseek-coder OR llama3)
    ↓
Response Processing
    ↓
Cache Response
    ↓
Stream Response
    ↓
Performance Monitoring
    ↓
Response Complete
```

## ⚡ Performance Paths

### 1. Quick Response Path (Instant)
```
User: "Hello"
→ Preprocess → Quick Response → Stream
Time: ~100ms
```

### 2. Cached Response Path (Very Fast)
```
User: "What is machine learning?"
→ Preprocess → Cache Hit → Stream
Time: ~150ms
```

### 3. Optimized Generation Path (Fast)
```
User: "How do I implement binary search in Python?"
→ Preprocess → Mistral Classification → deepseek-coder → Generate → Stream
Time: ~1500ms
```

### 4. Simple Question Path (Very Fast)
```
User: "What is Python?"
→ Preprocess → Early Acknowledgment → llama3 → Generate → Stream
Time: ~800ms
```

## 🔧 Key Components

### Message Preprocessing
- **Validation**: Length, content checks
- **Type Detection**: Simple/complex classification
- **Intent Recognition**: Question, code request detection

### Classification System
- **Primary**: Keyword-based classification (fast)
- **Fallback**: Mistral model classification (accurate)
- **Optimization**: 80% faster than full LLM classification

### Dynamic Model Selection
- **Code Content**: → deepseek-coder (precision-focused)
- **General Content**: → llama3 (balanced)
- **Parameters**: Optimized based on content type

### Parallel Processing
- **Cache Check**: Concurrent with conversation loading
- **Thread Pool**: 4 worker threads
- **Connection Pool**: 3 connections

### Performance Monitoring
- **9 Checkpoints**: Detailed timing tracking
- **Real-time Metrics**: Live performance data
- **Optimization Insights**: Data-driven improvements

## 📈 Expected Performance

| Message Type | Model Used | Response Time | Improvement |
|-------------|------------|---------------|-------------|
| Greetings | Quick Response | ~100ms | 95% faster |
| Cached | Cached Response | ~150ms | 90% faster |
| Simple Questions | llama3 (optimized) | ~800ms | 70% faster |
| Code Requests | deepseek-coder | ~1500ms | 40% faster |
| Complex Messages | llama3 (balanced) | ~2000ms | 35% faster |

## 🎯 Model Selection Logic

```
Message Input
    ↓
Keyword Check (Fast)
    ↓
┌─────────────────┬─────────────────┐
│   Code Keywords │   General        │
│   Found?        │   Keywords       │
│   ↓             │   ↓             │
│   deepseek-coder│   llama3         │
└─────────────────┴─────────────────┘
    ↓
Mistral Classification (Fallback)
    ↓
┌─────────────────┬─────────────────┐
│   "code"        │   "general"     │
│   ↓             │   ↓             │
│   deepseek-coder│   llama3         │
└─────────────────┴─────────────────┘
```

---

**Note**: This architecture ensures optimal model selection and performance for each type of user query, with the Mistral model serving as the intelligent classifier for routing requests to the most appropriate generation model.
