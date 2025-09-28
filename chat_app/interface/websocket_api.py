"""
WebSocket API Interface - Real-time chat
"""
import asyncio
import json
import uuid
from typing import Any, Dict

from fastapi import WebSocket, WebSocketDisconnect

from chat_app.application.use_cases import ChatRequest
from chat_app.domain.value_objects import Language, MemoryType
from chat_app.interface.base_handler import BaseHandler


class WebSocketChatHandler(BaseHandler):
    """WebSocket handler for real-time chat"""

    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection"""
        # Extract parameters
        token = websocket.query_params.get("token")
        lang = websocket.query_params.get("lang", "fr")

        if not token:
            await websocket.close(code=1008, reason="No token provided")
            return

        # Authenticate user
        user = await self.user_repository.find_by_token(token)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return

        await websocket.accept()

        stop_flag = False

        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                msg = json.loads(data)

                # Handle stop command
                if msg.get("type") == "stop":
                    stop_flag = True
                    await websocket.send_text(json.dumps({"type": "stopped"}))
                    continue

                # Handle user message
                if msg.get("type") == "user_message":
                    await self._handle_user_message(websocket, msg, lang, stop_flag)

        except WebSocketDisconnect:
            print("WebSocket disconnected")
        except Exception as e:
            print(f"WebSocket error: {e}")
            try:
                await websocket.send_text(
                    json.dumps({"type": "error", "content": str(e), "done": True})
                )
            except:
                pass

    async def _handle_user_message(
        self, websocket: WebSocket, msg: Dict[str, Any], lang: str, stop_flag: bool
    ):
        """Handle user message in WebSocket"""
        try:
            text = msg.get("text", "")
            conversation = msg.get(
                "conversation", {"id": str(uuid.uuid4()), "messages": []}
            )
            memory_type = msg.get("memory_type", "buffer")

            # Create chat request
            chat_request = ChatRequest(
                user_token=msg.get("token", ""),
                message_content=text,
                conversation_id=conversation.get("id"),
                language=Language(lang),
                memory_type=MemoryType(memory_type),
            )

            # Execute chat use case
            chat_response = await self.chat_use_case.execute(chat_request)

            # Stream response
            response_text = chat_response.response_content
            chunk_size = 10

            for i in range(0, len(response_text), chunk_size):
                if stop_flag:
                    stop_flag = False
                    break

                chunk = response_text[i : i + chunk_size]
                await websocket.send_text(
                    json.dumps({"type": "chunk", "content": chunk, "done": False})
                )
                await asyncio.sleep(0.05)

            # Send completion signal
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "final",
                        "content": "",
                        "done": True,
                        "memory_stats": chat_response.memory_stats.to_dict(),
                    }
                )
            )

        except Exception as e:
            print(f"Error handling user message: {e}")
            await websocket.send_text(
                json.dumps({"type": "error", "content": str(e), "done": True})
            )
