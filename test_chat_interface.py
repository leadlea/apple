#!/usr/bin/env python3
"""
Test script for the chat interface functionality
"""

import asyncio
import websockets
import json
import time

async def test_websocket_connection():
    """Test WebSocket connection and basic chat functionality"""
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established")
            
            # Test sending a chat message
            test_message = {
                "type": "chat",
                "content": "CPUの使用率はどうですか？",
                "timestamp": "2025-07-30T07:26:00.000Z"
            }
            
            await websocket.send(json.dumps(test_message))
            print("✅ Message sent successfully")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)
                print(f"✅ Received response: {response_data}")
                
                if response_data.get('type') == 'response':
                    print("✅ Chat interface working correctly")
                    return True
                else:
                    print(f"❌ Unexpected response type: {response_data.get('type')}")
                    return False
                    
            except asyncio.TimeoutError:
                print("❌ No response received within timeout")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

async def main():
    print("Testing chat interface functionality...")
    print("=" * 50)
    
    # Test WebSocket connection
    success = await test_websocket_connection()
    
    if success:
        print("\n🎉 Chat interface test completed successfully!")
        print("The basic chat interface is working correctly.")
    else:
        print("\n❌ Chat interface test failed!")
        print("Please check the server logs for more details.")

if __name__ == "__main__":
    asyncio.run(main())