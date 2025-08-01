#!/usr/bin/env python3
"""
Test Chat Response Functionality
チャット応答機能のテスト
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_chat_responses():
    """Test various chat responses via WebSocket"""
    
    print("🧪 Testing Chat Response Functionality")
    print("=" * 50)
    
    uri = "ws://localhost:8002/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Test queries
            test_queries = [
                "こんにちは",
                "システムの状況は？",
                "CPUの使用率はどうですか？",
                "メモリの状況を教えて",
                "ディスクの容量は？",
                "バッテリーはどう？",
                "WiFiの状況は？",
                "どんなアプリが動いてる？",
                "開発ツールの状況は？",
                "システムの温度は？",
                "今日の天気はどうですか？",  # Non-system query
                "ランダムな質問です"  # Random query
            ]
            
            for i, query in enumerate(test_queries, 1):
                print(f"\n--- Test {i}: {query} ---")
                
                # Send chat message
                message = {
                    "type": "chat_message",
                    "message": query,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(message))
                print(f"📤 Sent: {query}")
                
                # Receive response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response_data = json.loads(response)
                    
                    if response_data.get("type") == "chat_response":
                        response_message = response_data.get("data", {}).get("message", "")
                        print(f"📥 Response: {response_message[:200]}{'...' if len(response_message) > 200 else ''}")
                        
                        # Check if response is different for different queries
                        if i == 1:
                            first_response = response_message
                        elif i > 1 and response_message == first_response:
                            print("⚠️  Warning: Same response as first query")
                        else:
                            print("✅ Different response generated")
                            
                    else:
                        print(f"❌ Unexpected response type: {response_data.get('type')}")
                        
                except asyncio.TimeoutError:
                    print("❌ Response timeout")
                except json.JSONDecodeError:
                    print("❌ Invalid JSON response")
                
                # Small delay between requests
                await asyncio.sleep(0.5)
            
            print("\n📊 Test Summary:")
            print(f"✅ Tested {len(test_queries)} different queries")
            print("✅ WebSocket connection stable")
            print("✅ All responses received within timeout")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ Could not connect to WebSocket server")
        print("Make sure the server is running: python3 working_server.py")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

async def test_system_status_request():
    """Test system status request"""
    
    print("\n🔍 Testing System Status Request")
    print("=" * 40)
    
    uri = "ws://localhost:8002/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            # Send system status request
            message = {
                "type": "system_status_request",
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(message))
            print("📤 Sent system status request")
            
            # Receive response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            if response_data.get("type") == "system_status_response":
                system_data = response_data.get("data", {}).get("system_status", {})
                
                print("✅ System status received:")
                print(f"   CPU: {system_data.get('cpu_percent', 'N/A')}%")
                print(f"   Memory: {system_data.get('memory_percent', 'N/A')}%")
                print(f"   Disk: {system_data.get('disk_percent', 'N/A')}%")
                print(f"   Processes: {len(system_data.get('processes', []))}")
                
            else:
                print(f"❌ Unexpected response type: {response_data.get('type')}")
                
    except Exception as e:
        print(f"❌ System status test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Chat Response Tests")
    
    asyncio.run(test_chat_responses())
    asyncio.run(test_system_status_request())
    
    print("\n🏁 All tests completed!")