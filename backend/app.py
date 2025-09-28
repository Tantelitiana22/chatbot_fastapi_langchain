# backend/app.py
import uuid, json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .auth import valid_token
from .db import init_db, save_conversation, load_conversation, list_conversations
from .llm import build_chain, get_memory_stats, get_cache_key, get_cached_response, cache_response, get_conversation_context, perf_monitor
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount tests directory
app.mount("/tests", StaticFiles(directory="tests"), name="tests")

# Thread pool for parallel processing
thread_pool = ThreadPoolExecutor(max_workers=4)

@app.on_event("startup")
async def startup_event():
    init_db()

# Message preprocessing functions
def preprocess_message(user_msg: str) -> dict:
    """Preprocess and validate user message for faster processing"""
    # Clean and validate message
    cleaned_msg = user_msg.strip()
    
    # Quick validation
    if not cleaned_msg:
        return {"error": "Empty message", "processed": False}
    
    if len(cleaned_msg) > 4000:
        return {"error": "Message too long", "processed": False}
    
    # Detect message type for optimization
    msg_type = "simple" if len(cleaned_msg) < 50 else "complex"
    
    # Detect if it's a question
    is_question = cleaned_msg.endswith('?') or any(word in cleaned_msg.lower() for word in ['how', 'what', 'why', 'when', 'where', 'who'])
    
    # Detect if it's a code request
    code_indicators = ['code', 'function', 'class', 'python', 'javascript', 'html', 'css', 'sql', 'api', 'debug', 'error']
    is_code_request = any(indicator in cleaned_msg.lower() for indicator in code_indicators)
    
    # Quick response patterns for instant answers
    quick_responses = {
        "hello": "Hello! How can I help you today?",
        "hi": "Hi there! What would you like to know?",
        "thanks": "You're welcome! Is there anything else I can help with?",
        "thank you": "You're welcome! Feel free to ask if you need more help.",
        "bye": "Goodbye! Have a great day!",
        "goodbye": "See you later! Take care!"
    }
    
    has_quick_response = cleaned_msg.lower() in quick_responses
    
    return {
        "processed": True,
        "message": cleaned_msg,
        "type": msg_type,
        "is_question": is_question,
        "is_code_request": is_code_request,
        "length": len(cleaned_msg),
        "has_quick_response": has_quick_response,
        "quick_response": quick_responses.get(cleaned_msg.lower(), None)
    }

async def parallel_conversation_loading(user_id: str, conv_id: str) -> dict:
    """Load conversation data in parallel with other operations"""
    loop = asyncio.get_event_loop()
    conversation_data = await loop.run_in_executor(thread_pool, load_conversation, user_id, conv_id)
    return {"id": conv_id, "messages": conversation_data or []}

async def parallel_cache_check(user_msg: str, conversation_context: str) -> tuple:
    """Check cache in parallel with other operations"""
    loop = asyncio.get_event_loop()
    cache_key = await loop.run_in_executor(thread_pool, get_cache_key, user_msg, conversation_context)
    cached_response = await loop.run_in_executor(thread_pool, get_cached_response, cache_key)
    return cache_key, cached_response

# Root endpoint to serve the main page
@app.get("/")
async def read_root():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Server is running"}

# ---------- SSE ----------
@app.post("/api/chat/stream")
async def chat_stream(request: Request):
    print(f"Received POST request to /api/chat/stream")
    print(f"Request method: {request.method}")
    print(f"Request headers: {dict(request.headers)}")
    
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = valid_token(token)
    if not user_id:
        print(f"Invalid token: {token}")
        return StreamingResponse(iter(["Unauthorized"]), media_type="text/plain")

    try:
        body = await request.json()
        print(f"Request body: {body}")
        user_msg = body.get("message", "")
        lang = body.get("lang", "fr")
        conversation = body.get("conversation", {"id": str(uuid.uuid4()), "messages": []})
        conv_id = conversation["id"]
        memory_type = body.get("memory_type", "buffer")
        
        # Start performance monitoring
        perf_monitor.start()
        perf_monitor.checkpoint("request_parsed")
        
        # Preprocess message for optimization
        preprocessed = preprocess_message(user_msg)
        if not preprocessed["processed"]:
            return StreamingResponse(iter([f"Error: {preprocessed['error']}"]), media_type="text/plain")
        
        user_msg = preprocessed["message"]
        perf_monitor.checkpoint("message_preprocessed")
        
        # Parallel operations for faster processing
        conversation_task = parallel_conversation_loading(user_id, conv_id)
        
        # Wait for conversation loading
        conversation_data = await conversation_task
        conversation["messages"] = conversation_data["messages"]
        perf_monitor.checkpoint("conversation_loaded")
        
        # Build chain with optimized parameters based on message type
        llm, conversation_chain, memory = await build_chain(conversation, user_msg, lang, memory_type, preprocessed)
        perf_monitor.checkpoint("chain_built")

        async def event_generator():
            accum = ""
            try:
                # Parallel cache check for faster responses
                conversation_context = get_conversation_context(conversation)
                cache_key, cached_response = await parallel_cache_check(user_msg, conversation_context)
                
                if cached_response:
                    print(f"Using cached response for: {user_msg[:50]}...")
                    response_text = cached_response
                    perf_monitor.checkpoint("cache_hit")
                elif preprocessed["has_quick_response"]:
                    # Instant response for common greetings
                    print(f"Using quick response for: {user_msg[:50]}...")
                    response_text = preprocessed["quick_response"]
                    perf_monitor.checkpoint("quick_response")
                else:
                    # Early response for simple messages
                    if preprocessed["type"] == "simple" and preprocessed["is_question"]:
                        # Send immediate acknowledgment for simple questions
                        yield f"data: {json.dumps({'content': '🤔 ', 'done': False})}\n\n"
                        await asyncio.sleep(0.01)
                    
                    # Use conversation chain with memory for streaming
                    # Note: ConversationChain.astream might not work as expected, so we'll use invoke and simulate streaming
                    response = await conversation_chain.ainvoke({"input": user_msg})
                    perf_monitor.checkpoint("llm_response")
                    
                    # Simulate streaming by sending the response in chunks
                    response_text = response.get('response', '') if isinstance(response, dict) else str(response)
                    
                    # Cache the response for future use
                    cache_response(cache_key, response_text)
                    perf_monitor.checkpoint("response_cached")
                
                # Optimized chunking for faster perceived response
                chunk_size = 20  # Larger chunks for faster delivery
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i + chunk_size]
                    accum += chunk
                    yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                    # Reduced delay for faster streaming
                    await asyncio.sleep(0.02)  # Faster streaming
                
                # Send completion signal with memory stats
                memory_stats = get_memory_stats(memory)
                perf_monitor.checkpoint("streaming_complete")
                perf_monitor.log_performance(f"Chat response for: {user_msg[:30]}...")
                
                yield f"data: {json.dumps({'content': '', 'done': True, 'memory_stats': memory_stats})}\n\n"
                
                # Update conversation with new messages
                conversation["messages"].append({"role": "user", "content": user_msg})
                conversation["messages"].append({"role": "assistant", "content": accum})
                save_conversation(user_id, conv_id, conversation["messages"])
            except Exception as e:
                print(f"Error in event_generator: {e}")
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        print(f"Error in chat_stream: {e}")
        return StreamingResponse(iter([f"Error: {str(e)}"]), media_type="text/plain")

# ---------- WebSocket ----------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    lang = websocket.query_params.get("lang", "fr")
    user_id = valid_token(token)
    if not user_id:
        await websocket.close(code=1008)
        return
    await websocket.accept()

    stop_flag = False
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "stop":
                stop_flag = True
                await websocket.send_text(json.dumps({"type": "stopped"}))
                continue

            if msg.get("type") == "user_message":
                text = msg.get("text", "")
                conversation = msg.get("conversation", {"id": str(uuid.uuid4()), "messages": []})
                conv_id = conversation["id"]

                conversation["messages"] = load_conversation(user_id, conv_id) or conversation["messages"]
                
                # Get memory type from WebSocket data (default to buffer)
                memory_type = msg.get("memory_type", "buffer")
                
                llm, conversation_chain, memory = await build_chain(conversation, text, lang, memory_type)

                accum = ""
                try:
                    # Use conversation chain with memory for streaming
                    # Note: ConversationChain.astream might not work as expected, so we'll use invoke and simulate streaming
                    response = await conversation_chain.ainvoke({"input": text})
                    
                    # Simulate streaming by sending the response in chunks
                    response_text = response.get('response', '') if isinstance(response, dict) else str(response)
                    
                    # Send response in chunks for smooth streaming
                    chunk_size = 10  # Characters per chunk
                    for i in range(0, len(response_text), chunk_size):
                        if stop_flag:
                            stop_flag = False
                            break
                        
                        chunk = response_text[i:i + chunk_size]
                        accum += chunk
                        await websocket.send_text(json.dumps({"type": "chunk", "content": chunk, "done": False}))
                        # Small delay to simulate streaming
                        await asyncio.sleep(0.05)
                    
                    # Send completion signal with memory stats
                    memory_stats = get_memory_stats(memory)
                    await websocket.send_text(json.dumps({"type": "final", "content": "", "done": True, "memory_stats": memory_stats}))
                    
                    # Update conversation with new messages
                    conversation["messages"].append({"role": "user", "content": text})
                    conversation["messages"].append({"role": "assistant", "content": accum})
                    save_conversation(user_id, conv_id, conversation["messages"])
                except Exception as e:
                    print(f"Error in WebSocket streaming: {e}")
                    await websocket.send_text(json.dumps({"type": "error", "content": str(e), "done": True}))
    except WebSocketDisconnect:
        print("WS disconnected")

# ---------- Memory Management ----------
@app.post("/api/memory/settings")
async def set_memory_settings(request: Request):
    """Set memory configuration for a conversation"""
    try:
        body = await request.json()
        user_id = valid_token(request.headers.get("Authorization", ""))
        if not user_id:
            return {"error": "Invalid token"}
        
        memory_type = body.get("memory_type", "buffer")
        conversation_id = body.get("conversation_id")
        
        if memory_type not in ["buffer", "summary", "token_buffer"]:
            return {"error": "Invalid memory type"}
        
        # Store memory settings (you could extend the database schema for this)
        return {
            "success": True,
            "memory_type": memory_type,
            "conversation_id": conversation_id,
            "message": f"Memory type set to {memory_type}"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/memory/types")
async def get_memory_types():
    """Get available memory types and their descriptions"""
    return {
        "memory_types": {
            "buffer": {
                "name": "Conversation Buffer",
                "description": "Stores all conversation history in memory. Best for short conversations.",
                "pros": ["Complete context", "No information loss"],
                "cons": ["Memory usage grows", "Slower with long conversations"]
            },
            "summary": {
                "name": "Conversation Summary",
                "description": "Summarizes older messages to maintain context while reducing memory usage.",
                "pros": ["Efficient memory usage", "Good for long conversations"],
                "cons": ["May lose some details", "Requires LLM for summarization"]
            },
            "token_buffer": {
                "name": "Token Buffer",
                "description": "Keeps recent messages within a token limit, discarding older ones.",
                "pros": ["Predictable memory usage", "Fast performance"],
                "cons": ["May lose older context", "Fixed token limit"]
            }
        }
    }

# ---------- Conversations ----------
@app.get("/api/conversations")
async def get_conversations(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = valid_token(token)
    if not user_id:
        return []
    return list_conversations(user_id)

@app.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: str, request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = valid_token(token)
    if not user_id:
        return {}
    return {"id": conv_id, "messages": load_conversation(user_id, conv_id)}
