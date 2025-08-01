#!/usr/bin/env python3
"""
Test development tools functionality via WebSocket
"""
import asyncio
import websockets
import json

async def test_dev_tools_websocket():
    """Test development tools queries via WebSocket"""
    uri = "ws://localhost:8002/ws"
    
    dev_tools_queries = [
        "開発ツールの状況は？",
        "開発環境を教えて",
        "Xcodeはインストールされてる？",
        "Gitのバージョンは？",
        "Homebrewは使える？",
        "Node.jsの状況は？",
        "development tools",
        "dev environment"
    ]
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔌 Connected to WebSocket server")
            
            for query in dev_tools_queries:
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
    asyncio.run(test_dev_tools_websocket())