#!/usr/bin/env python3
"""
Test Working Server
"""

import asyncio
import json
import websockets

async def test_working_server():
    """Test the working server"""
    uri = "ws://localhost:8002/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            
            # Wait for initial system status
            print("\n📊 Waiting for initial system status...")
            initial_response = await websocket.recv()
            initial_data = json.loads(initial_response)
            print(f"Initial response type: {initial_data.get('type')}")
            
            if initial_data.get('type') == 'system_status_response':
                system_data = initial_data['data']['system_status']
                print(f"  CPU: {system_data['cpu_percent']}%")
                print(f"  Memory: {system_data['memory_percent']}%")
                print(f"  Disk: {system_data['disk_percent']}%")
            
            # Test chat
            print("\n💬 Testing chat...")
            chat_message = {
                "type": "chat_message",
                "message": "こんにちは",
                "timestamp": "2024-01-01T00:00:00"
            }
            await websocket.send(json.dumps(chat_message))
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Chat response: {response_data['data']['message'][:100]}...")
            
            print("\n🎉 Working server test completed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_working_server())