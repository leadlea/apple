#!/usr/bin/env python3
"""
Simple Chat Test
シンプルなチャットテスト
"""

import asyncio
import websockets
import json
from datetime import datetime

async def simple_test():
    """Simple chat test"""
    
    print("🧪 Simple Chat Test")
    print("=" * 30)
    
    uri = "ws://localhost:8002/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Test different queries
            queries = [
                "こんにちは",
                "CPUの使用率は？",
                "メモリの状況は？",
                "今日の天気は？"
            ]
            
            for query in queries:
                print(f"\n📤 Query: {query}")
                
                message = {
                    "type": "chat_message",
                    "message": query
                }
                
                await websocket.send(json.dumps(message))
                
                # Wait for response
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data.get("type") == "chat_response":
                    response_text = response_data.get("data", {}).get("message", "")
                    print(f"📥 Response: {response_text}")
                else:
                    print(f"📥 Response type: {response_data.get('type')}")
                    print(f"📥 Data: {response_data}")
                
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(simple_test())