#!/usr/bin/env python3
"""
Enhanced Chat Test for Mac Status PWA
"""

import asyncio
import json
import websockets

async def test_enhanced_chat():
    """Test enhanced chat functionality"""
    uri = "ws://localhost:8001/ws"
    
    test_questions = [
        "こんにちは",
        "CPUの使用率はどうですか？",
        "メモリの状況を教えて",
        "システムが重い理由は？",
        "プロセスの状況は？",
        "システム全体の状況は？"
    ]
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            
            for i, question in enumerate(test_questions, 1):
                print(f"\n📝 質問 {i}: {question}")
                
                chat_message = {
                    "type": "chat_message",
                    "message": question,
                    "timestamp": "2024-01-01T00:00:00"
                }
                
                await websocket.send(json.dumps(chat_message))
                response = await websocket.recv()
                response_data = json.loads(response)
                
                print(f"🤖 回答:")
                print(response_data['data']['message'])
                print("-" * 50)
                
                # Wait a bit between questions
                await asyncio.sleep(1)
            
            print("\n🎉 Enhanced chat test completed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_chat())