"""
Main Application Entry Point - Dependency Injection and Configuration
"""
from fastapi import FastAPI, WebSocket

from chat_app.interface.rest_api import ChatAPI
from chat_app.interface.websocket_api import WebSocketChatHandler


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""

    # Initialize API handlers
    chat_api = ChatAPI()
    websocket_handler = WebSocketChatHandler()

    # Create FastAPI app
    app = chat_api.create_app()

    # Add WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket_handler.handle_websocket(websocket)

    return app


# Create the app instance
app = create_app()
