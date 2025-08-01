#!/usr/bin/env python3
"""
Test WiFi functionality via WebSocket
"""
import asyncio
import websockets
import json

async def test_wifi_websocket():
    """Test WiFi queries via WebSocket"""
    uri = "ws://localhost:8002/ws"
    
    wifi_queries = [
        "WiFiの調子はどう？",
        "ネットワークの状況は？",
        "接続速度はどのくらい？",
        "信号強度を教えて",
        "電波の状態は？",
        "wifi status",
        "network connection"
    ]
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔌 Connected to WebSocket server")
            
            for query in wifi_queries:
                print(f"\n📤 Sending: {query}")
                
                # Send message
                message = {
                    "type": "chat_message",
                    "message": query
                }
                await websocket.send(json.dumps(message))
                
                # Wait for response
                response = await websocket.recv()
                response_data = json.loads(response)
                
                # Extract response message based on type
                if response_data.get('type') == 'chat_response':
                    message = response_data.get('data', {}).get('message', 'No message')
                    print(f"📥 Response: {message}")
                else:
                    print(f"📥 Response: {response_data}")
                
                # Wait a bit between queries
                await asyncio.sleep(2)
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_wifi_websocket())