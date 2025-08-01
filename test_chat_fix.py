#!/usr/bin/env python3
"""
Test Chat Message Fix
チャットメッセージ修正のテスト
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_chat_message_fix():
    """チャットメッセージ修正のテスト"""
    
    print("🔍 Testing Chat Message Fix")
    print("=" * 50)
    
    uri = "ws://localhost:8002/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # 初期メッセージを受信
            try:
                initial_message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                print(f"📥 Initial message received")
            except asyncio.TimeoutError:
                print("⏰ No initial message")
            
            # テストメッセージ1: 直接message形式（fixed_index.html形式）
            print("\n--- Test 1: Direct message format ---")
            test_msg1 = {
                "type": "chat_message",
                "message": "CPUの使用率は？",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"📤 Sending: {json.dumps(test_msg1, ensure_ascii=False)}")
            await websocket.send(json.dumps(test_msg1))
            
            try:
                response1 = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print(f"📥 Response: {response1[:100]}...")
                resp_data1 = json.loads(response1)
                if resp_data1.get('type') == 'chat_response':
                    print("✅ Test 1 PASSED - Got chat response")
                else:
                    print("❌ Test 1 FAILED - Wrong response type")
            except asyncio.TimeoutError:
                print("❌ Test 1 FAILED - Timeout")
            
            await asyncio.sleep(1)
            
            # テストメッセージ2: data.message形式（ログで見られた形式）
            print("\n--- Test 2: Nested data.message format ---")
            test_msg2 = {
                "type": "chat_message",
                "data": {
                    "message": "メモリの状況は？"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"📤 Sending: {json.dumps(test_msg2, ensure_ascii=False)}")
            await websocket.send(json.dumps(test_msg2))
            
            try:
                response2 = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print(f"📥 Response: {response2[:100]}...")
                resp_data2 = json.loads(response2)
                if resp_data2.get('type') == 'chat_response':
                    print("✅ Test 2 PASSED - Got chat response")
                else:
                    print("❌ Test 2 FAILED - Wrong response type")
            except asyncio.TimeoutError:
                print("❌ Test 2 FAILED - Timeout")
            
            await asyncio.sleep(1)
            
            # テストメッセージ3: 空メッセージ（問題のケース）
            print("\n--- Test 3: Empty message test ---")
            test_msg3 = {
                "type": "chat_message",
                "message": "",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"📤 Sending: {json.dumps(test_msg3, ensure_ascii=False)}")
            await websocket.send(json.dumps(test_msg3))
            
            try:
                response3 = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print(f"📥 Response: {response3[:100]}...")
                resp_data3 = json.loads(response3)
                if resp_data3.get('type') == 'chat_response':
                    print("✅ Test 3 PASSED - Got response for empty message")
                else:
                    print("❌ Test 3 FAILED - Wrong response type")
            except asyncio.TimeoutError:
                print("❌ Test 3 FAILED - Timeout")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_message_fix())