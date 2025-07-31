#!/usr/bin/env python3
"""
Test script for connection management and offline functionality
"""
import asyncio
import json
import time
import websockets
from datetime import datetime

async def test_connection_management():
    """Test connection management features"""
    print("Testing connection management and offline functionality...")
    
    # Test 1: Basic connection
    print("\n1. Testing basic WebSocket connection...")
    try:
        async with websockets.connect("ws://localhost:8000/ws") as websocket:
            print("✓ WebSocket connection established")
            
            # Send ping
            ping_message = {
                "type": "ping",
                "data": {"timestamp": datetime.now().isoformat()},
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(ping_message))
            
            # Wait for pong
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            if data.get("type") == "pong":
                print("✓ Ping-pong test successful")
            else:
                print(f"✗ Unexpected response: {data}")
                
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
    
    # Test 2: Connection interruption simulation
    print("\n2. Testing connection interruption handling...")
    try:
        websocket = await websockets.connect("ws://localhost:8000/ws")
        print("✓ Initial connection established")
        
        # Send a message
        chat_message = {
            "type": "chat_message",
            "data": {"message": "テスト接続メッセージ"},
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(chat_message))
        print("✓ Message sent")
        
        # Simulate connection drop by closing
        await websocket.close()
        print("✓ Connection closed (simulating network interruption)")
        
    except Exception as e:
        print(f"✗ Connection interruption test failed: {e}")
    
    # Test 3: System status request
    print("\n3. Testing system status request...")
    try:
        async with websockets.connect("ws://localhost:8000/ws") as websocket:
            status_request = {
                "type": "system_status_request",
                "data": {"request_id": "test_request_123"},
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(status_request))
            
            # Wait for system status response
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            data = json.loads(response)
            
            if data.get("type") == "system_status_update":
                print("✓ System status request successful")
                system_status = data.get("data", {}).get("system_status", {})
                print(f"  CPU: {system_status.get('cpu_percent', 0):.1f}%")
                print(f"  Memory: {system_status.get('memory_percent', 0):.1f}%")
                print(f"  Disk: {system_status.get('disk_percent', 0):.1f}%")
            else:
                print(f"✗ Unexpected response: {data}")
                
    except Exception as e:
        print(f"✗ System status test failed: {e}")
    
    # Test 4: Multiple connection handling
    print("\n4. Testing multiple connections...")
    try:
        connections = []
        for i in range(3):
            ws = await websockets.connect("ws://localhost:8000/ws")
            connections.append(ws)
            print(f"✓ Connection {i+1} established")
        
        # Send messages from all connections
        for i, ws in enumerate(connections):
            message = {
                "type": "ping",
                "data": {"client_id": f"client_{i+1}"},
                "timestamp": datetime.now().isoformat()
            }
            await ws.send(json.dumps(message))
        
        print("✓ Messages sent from all connections")
        
        # Close all connections
        for ws in connections:
            await ws.close()
        
        print("✓ All connections closed")
        
    except Exception as e:
        print(f"✗ Multiple connections test failed: {e}")
    
    print("\nConnection management tests completed!")

async def test_server_status():
    """Test server status endpoint"""
    print("\n5. Testing server status endpoint...")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✓ Server status endpoint accessible")
                    print(f"  Server: {data.get('server')}")
                    print(f"  Status: {data.get('status')}")
                    print(f"  Connections: {data.get('connections', {}).get('total_connections', 0)}")
                else:
                    print(f"✗ Server status returned {response.status}")
    except ImportError:
        print("⚠ aiohttp not available, skipping HTTP status test")
    except Exception as e:
        print(f"✗ Server status test failed: {e}")

if __name__ == "__main__":
    print("Mac Status PWA - Connection Management Test")
    print("=" * 50)
    
    try:
        asyncio.run(test_connection_management())
        asyncio.run(test_server_status())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")