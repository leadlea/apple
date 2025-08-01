#!/usr/bin/env python3
"""
Test thermal functionality via WebSocket
"""
import asyncio
import websockets
import json

async def test_thermal_websocket():
    """Test thermal queries via WebSocket"""
    uri = "ws://localhost:8002/ws"
    
    thermal_queries = [
        "システムの温度はどう？",
        "ファンの回転数を教えて",
        "熱くなってない？",
        "冷却状況は？",
        "サーマル情報を見せて",
        "temperature status",
        "fan speed",
        "thermal info"
    ]
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔌 Connected to WebSocket server")
            
            for query in thermal_queries:
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
    asyncio.run(test_thermal_websocket())