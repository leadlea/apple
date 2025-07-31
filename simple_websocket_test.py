#!/usr/bin/env python3
"""
Simple WebSocket server test
"""
import asyncio
import json
import logging
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    
    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_status",
            "data": {"status": "connected"},
            "timestamp": datetime.now().isoformat()
        }))
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.info(f"Received: {message.get('type', 'unknown')}")
            
            # Echo back with response
            response = {
                "type": "echo",
                "data": {"original": message},
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

@app.get("/")
async def root():
    return {"message": "WebSocket test server running"}

if __name__ == "__main__":
    print("🚀 Starting simple WebSocket test server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)