#!/usr/bin/env python3
"""
Test Improved Chat Responses
改善されたチャット応答のテスト
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_improved_responses():
    """改善されたチャット応答のテスト"""
    
    print("🔍 Testing Improved Chat Responses")
    print("=" * 50)
    
    uri = "ws://localhost:8002/ws"
    
    test_questions = [
        "開いてるアプリは？",
        "バッテリーは？", 
        "Wi-Fiは？",
        "CPUの使用率は？",
        "メモリの状況は？",
        "ディスクの容量は？",
        "システムの状況は？",
        "こんにちは",
        "温度は？",
        "ネットワークの速度は？"
    ]
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # 初期メッセージを受信
            try:
                initial_message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                print("📥 Initial message received")
            except asyncio.TimeoutError:
                print("⏰ No initial message")
            
            for i, question in enumerate(test_questions, 1):
                print(f"\n--- Test {i}: '{question}' ---")
                
                test_msg = {
                    "type": "chat_message",
                    "message": question,
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"📤 Sending: {question}")
                await websocket.send(json.dumps(test_msg))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    resp_data = json.loads(response)
                    
                    if resp_data.get('type') == 'chat_response':
                        message = resp_data.get('data', {}).get('message', '')
                        print(f"📥 Response ({len(message)} chars): {message[:100]}...")
                        print("✅ PASSED")
                    else:
                        print("❌ FAILED - Wrong response type")
                        
                except asyncio.TimeoutError:
                    print("❌ FAILED - Timeout")
                
                await asyncio.sleep(0.5)  # Short delay between tests
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_improved_responses())