"""
REST API Interface - FastAPI adapters
"""
import asyncio
import json
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from chat_app.application.use_cases import (
    ChatRequest,
    ClearCacheUseCase,
    GetConversationsUseCase,
    GetConversationUseCase,
)
from chat_app.domain.value_objects import Language, MemoryType
from chat_app.infrastructure.performance_monitor import perf_monitor
from chat_app.interface.base_handler import BaseHandler


class ChatAPI(BaseHandler):
    """REST API adapter for chat functionality"""

    def __init__(self):
        super().__init__()
        self.get_conversations_use_case = GetConversationsUseCase(
            self.user_repository, self.conversation_repository
        )
        self.get_conversation_use_case = GetConversationUseCase(
            self.user_repository, self.conversation_repository
        )
        self.clear_cache_use_case = ClearCacheUseCase(self.cache_service)

    def create_app(self) -> FastAPI:
        """Create FastAPI application with routes"""
        app = FastAPI(title="ChatGPT-like API", version="2.0.0")

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Mount static files
        app.mount("/static", StaticFiles(directory="static"), name="static")
        app.mount("/tests", StaticFiles(directory="tests"), name="tests")

        # Routes
        @app.get("/")
        async def read_root():
            return FileResponse("static/index.html")

        @app.get("/api/health")
        async def health_check():
            return {"status": "ok", "message": "Server is running"}

        @app.post("/api/chat/stream")
        async def chat_stream(request: Request):
            return await self._handle_chat_stream(request)

        @app.post("/api/clear-cache")
        async def clear_response_cache():
            await self.clear_cache_use_case.execute()
            return {"status": "ok", "message": "Cache cleared"}

        @app.get("/api/conversations")
        async def get_conversations(request: Request):
            return await self._handle_get_conversations(request)

        @app.get("/api/conversations/{conv_id}")
        async def get_conversation(conv_id: str, request: Request):
            return await self._handle_get_conversation(conv_id, request)

        return app

    async def _handle_chat_stream(self, request: Request) -> StreamingResponse:
        """Handle chat streaming request"""
        try:
            # Extract token from headers
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                return StreamingResponse(
                    iter(["Unauthorized"]), media_type="text/plain"
                )

            # Parse request body
            body = await request.json()
            user_msg = body.get("message", "")
            lang = body.get("lang", "fr")
            conversation = body.get(
                "conversation", {"id": str(uuid.uuid4()), "messages": []}
            )
            memory_type = body.get("memory_type", "buffer")

            # Start performance monitoring
            perf_monitor.start()
            perf_monitor.checkpoint("request_parsed")

            # Create chat request
            chat_request = ChatRequest(
                user_token=token,
                message_content=user_msg,
                conversation_id=conversation.get("id"),
                language=Language(lang),
                memory_type=MemoryType(memory_type),
            )

            perf_monitor.checkpoint("request_created")

            # Execute chat use case
            chat_response = await self.chat_use_case.execute(chat_request)

            perf_monitor.checkpoint("use_case_executed")

            # Create streaming response
            async def event_generator():
                try:
                    # Update performance metrics
                    chat_response.performance_metrics = perf_monitor.get_metrics(
                        f"Chat response for: {user_msg[:30]}..."
                    )

                    # Stream response content
                    response_text = chat_response.response_content
                    chunk_size = 20

                    for i in range(0, len(response_text), chunk_size):
                        chunk = response_text[i : i + chunk_size]
                        yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                        await asyncio.sleep(0.02)

                    # Send completion signal
                    yield f"data: {json.dumps({'content': '', 'done': True, 'memory_stats': chat_response.memory_stats.to_dict()})}\n\n"

                except Exception as e:
                    print(f"Error in event_generator: {e}")
                    yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

            return StreamingResponse(event_generator(), media_type="text/event-stream")

        except Exception as e:
            print(f"Error in chat_stream: {e}")
            return StreamingResponse(
                iter([f"Error: {str(e)}"]), media_type="text/plain"
            )

    async def _handle_get_conversations(self, request: Request) -> list:
        """Handle get conversations request"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                raise HTTPException(status_code=401, detail="Invalid token")

            conversations = await self.get_conversations_use_case.execute(token)

            # Convert to API format
            result = []
            for conv in conversations:
                result.append(
                    {
                        "id": conv.conversation_id.value,
                        "title": conv.title,
                        "messages": [
                            {
                                "role": msg.role,
                                "content": msg.content,
                                "timestamp": msg.timestamp.isoformat(),
                            }
                            for msg in conv.messages
                        ],
                        "created_at": conv.created_at.isoformat(),
                        "updated_at": conv.updated_at.isoformat(),
                        "message_count": conv.get_message_count(),
                    }
                )

            return result

        except Exception as e:
            print(f"Error in get_conversations: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _handle_get_conversation(self, conv_id: str, request: Request) -> dict:
        """Handle get conversation request"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                raise HTTPException(status_code=401, detail="Invalid token")

            conversation = await self.get_conversation_use_case.execute(token, conv_id)

            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

            return {
                "id": conversation.conversation_id.value,
                "title": conversation.title,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                    }
                    for msg in conversation.messages
                ],
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "message_count": conversation.get_message_count(),
            }

        except Exception as e:
            print(f"Error in get_conversation: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# Import asyncio for the streaming response
