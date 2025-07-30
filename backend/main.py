"""
Mac Status PWA - Main FastAPI Application
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
from typing import List
import uvicorn

app = FastAPI(title="Mac Status PWA", version="1.0.0")

# Mount static files for PWA
app.mount("/static", StaticFiles(directory="frontend"), name="static")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def get():
    """Serve the PWA main page"""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Echo back for now - will be replaced with actual processing
            response = {
                "type": "response",
                "content": f"Received: {message_data.get('content', '')}"
            }
            await manager.send_personal_message(json.dumps(response), websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Mac Status PWA"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)