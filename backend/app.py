# backend/app.py
import uuid, json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .auth import valid_token
from .db import init_db, save_conversation, load_conversation, list_conversations
from .llm import build_chain, get_memory_stats, get_cache_key, get_cached_response, cache_response, get_conversation_context, perf_monitor

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

@app.on_event("startup")
async def startup_event():
    init_db()

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

        conversation["messages"] = load_conversation(user_id, conv_id) or conversation["messages"]
        
        # Get memory type from request (default to buffer)
        memory_type = body.get("memory_type", "buffer")
        
        # Start performance monitoring
        perf_monitor.start()
        perf_monitor.checkpoint("request_parsed")
        
        llm, conversation_chain, memory = await build_chain(conversation, user_msg, lang, memory_type)
        perf_monitor.checkpoint("chain_built")

        async def event_generator():
            accum = ""
            try:
                # Check cache first for faster responses
                conversation_context = get_conversation_context(conversation)
                cache_key = get_cache_key(user_msg, conversation_context)
                cached_response = get_cached_response(cache_key)
                
                if cached_response:
                    print(f"Using cached response for: {user_msg[:50]}...")
                    response_text = cached_response
                    perf_monitor.checkpoint("cache_hit")
                else:
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
                    import asyncio
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
                        import asyncio
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
