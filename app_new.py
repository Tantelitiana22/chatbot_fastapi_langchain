"""
New Application Entry Point - Hexagonal Architecture
"""
import uvicorn

from chat_app.interface.app import app

if __name__ == "__main__":
    uvicorn.run("chat_app.interface.app:app", host="0.0.0.0", port=8000, reload=True)
