#!/usr/bin/env python3
"""
Debug Chat Response Issues
チャット応答問題のデバッグ
"""

import asyncio
import websockets
import json
from datetime import datetime

async def debug_chat_responses():
    """Debug chat response functionality with detailed logging"""
    
    print("🔍 Debugging Chat Response Issues")
    print("=" * 50)
    
    uri = "ws://localhost:8002/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Test different types of queries to see actual responses
            test_queries = [
                "こんにちは",
                "CPUの使用率は？",
                "cpu",
                "メモリの状況は？",
                "memory",
                "ディスクの容量は？",
                "disk",
                "システムの状況は？",
                "system",
                "今日の天気は？",
                "使用中のアプリは？"
            ]
            
            responses = []
            
            for i, query in enumerate(test_queries, 1):
                print(f"\n--- Test {i}: '{query}' ---")
                
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
                    
                    print(f"📥 Raw response type: {response_data.get('type')}")
                    
                    if response_data.get("type") == "chat_response":
                        response_message = response_data.get("data", {}).get("message", "")
                        print(f"📥 Response length: {len(response_message)} chars")
                        print(f"📥 Response preview: {response_message[:100]}...")
                        
                        # Store for comparison
                        responses.append({
                            'query': query,
                            'response': response_message,
                            'length': len(response_message)
                        })
                        
                    else:
                        print(f"📥 Unexpected response: {response_data}")
                        
                except asyncio.TimeoutError:
                    print("❌ Response timeout")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                
                # Small delay between requests
                await asyncio.sleep(1)
            
            # Analyze responses for patterns
            print("\n" + "="*50)
            print("📊 Response Analysis")
            print("="*50)
            
            # Check for identical responses
            unique_responses = set()
            identical_pairs = []
            
            for i, resp in enumerate(responses):
                for j, other_resp in enumerate(responses[i+1:], i+1):
                    if resp['response'] == other_resp['response']:
                        identical_pairs.append((resp['query'], other_resp['query']))
                
                unique_responses.add(resp['response'])
            
            print(f"Total queries: {len(responses)}")
            print(f"Unique responses: {len(unique_responses)}")
            print(f"Identical response pairs: {len(identical_pairs)}")
            
            if identical_pairs:
                print("\n⚠️ Found identical responses:")
                for pair in identical_pairs[:5]:  # Show first 5
                    print(f"  '{pair[0]}' == '{pair[1]}'")
            
            # Show response lengths
            print(f"\nResponse lengths:")
            for resp in responses:
                print(f"  '{resp['query']}': {resp['length']} chars")
            
            # Check for keyword detection
            print(f"\nKeyword detection test:")
            cpu_queries = [r for r in responses if 'cpu' in r['query'].lower()]
            memory_queries = [r for r in responses if 'メモリ' in r['query'] or 'memory' in r['query'].lower()]
            
            print(f"CPU queries: {len(cpu_queries)}")
            print(f"Memory queries: {len(memory_queries)}")
            
            if cpu_queries:
                print(f"CPU response sample: {cpu_queries[0]['response'][:100]}...")
            if memory_queries:
                print(f"Memory response sample: {memory_queries[0]['response'][:100]}...")
                
    except websockets.exceptions.ConnectionRefused:
        print("❌ Could not connect to WebSocket server")
        print("Make sure the server is running: python3 working_server.py")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

async def test_server_direct():
    """Test server response generation directly"""
    
    print("\n🔧 Testing Server Response Generation Directly")
    print("=" * 50)
    
    try:
        # Import server functions directly
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        
        from working_server import generate_fallback_response, get_system_info
        
        # Get system info
        system_info = get_system_info()
        print(f"✅ System info retrieved: CPU {system_info.get('cpu_percent')}%")
        
        # Test different queries
        test_queries = [
            "こんにちは",
            "CPUの使用率は？",
            "メモリの状況は？",
            "今日の天気は？"
        ]
        
        for query in test_queries:
            response = generate_fallback_response(query, system_info)
            print(f"\nQuery: '{query}'")
            print(f"Response length: {len(response)} chars")
            print(f"Response preview: {response[:100]}...")
            
    except Exception as e:
        print(f"❌ Direct test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Chat Response Debug")
    
    asyncio.run(debug_chat_responses())
    asyncio.run(test_server_direct())
    
    print("\n🏁 Debug completed!")