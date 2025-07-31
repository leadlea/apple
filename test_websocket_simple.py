#!/usr/bin/env python3
"""
Simple WebSocket Test for Mac Status PWA
"""

import asyncio
import json
import websockets

async def test_websocket():
    """Test WebSocket connection and functionality"""
    uri = "ws://localhost:8001/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            
            # Test 1: Ping
            print("\n🏓 Testing ping...")
            ping_message = {
                "type": "ping",
                "timestamp": "2024-01-01T00:00:00"
            }
            await websocket.send(json.dumps(ping_message))
            response = await websocket.recv()
            print(f"Response: {response}")
            
            # Test 2: System Status Request
            print("\n📊 Testing system status request...")
            status_message = {
                "type": "system_status_request",
                "timestamp": "2024-01-01T00:00:00"
            }
            await websocket.send(json.dumps(status_message))
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"System Status Response:")
            print(f"  CPU: {response_data['data']['system_status']['cpu_percent']:.1f}%")
            print(f"  Memory: {response_data['data']['system_status']['memory']['percent']:.1f}%")
            print(f"  Disk: {response_data['data']['system_status']['disk']['percent']:.1f}%")
            
            # Test 3: Chat Message
            print("\n💬 Testing chat message...")
            chat_message = {
                "type": "chat_message",
                "message": "CPUの使用率はどうですか？",
                "timestamp": "2024-01-01T00:00:00"
            }
            await websocket.send(json.dumps(chat_message))
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Chat Response: {response_data['data']['message']}")
            
            print("\n🎉 All tests passed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())