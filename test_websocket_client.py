#!/usr/bin/env python3
"""
Test WebSocket client for Mac Status PWA
Tests WebSocket server functionality
"""
import asyncio
import json
import websockets
import time
from datetime import datetime


class WebSocketTestClient:
    """Test client for WebSocket server"""
    
    def __init__(self, uri: str = "ws://localhost:8000/ws"):
        self.uri = uri
        self.websocket = None
        self.running = False
        
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            print(f"🔌 Connecting to {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            print("✅ Connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from server"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected")
    
    async def send_message(self, message_type: str, data: dict):
        """Send message to server"""
        if not self.websocket:
            print("❌ Not connected")
            return
        
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            print(f"📤 Sent: {message_type}")
        except Exception as e:
            print(f"❌ Send error: {e}")
    
    async def receive_messages(self):
        """Receive messages from server"""
        while self.running and self.websocket:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                message_type = data.get('type', 'unknown')
                timestamp = data.get('timestamp', '')
                
                print(f"📥 Received: {message_type} at {timestamp}")
                
                # Handle specific message types
                if message_type == "connection_status":
                    status = data['data'].get('status')
                    print(f"   Connection status: {status}")
                    if 'client_id' in data['data']:
                        print(f"   Client ID: {data['data']['client_id']}")
                
                elif message_type == "system_status_update":
                    system_data = data['data'].get('system_status', {})
                    cpu = system_data.get('cpu_percent', 'N/A')
                    memory = system_data.get('memory_percent', 'N/A')
                    print(f"   System: CPU {cpu}%, Memory {memory}%")
                    
                    if data['data'].get('auto_update'):
                        print("   (Auto-update)")
                
                elif message_type == "chat_response":
                    response = data['data'].get('message', '')
                    processing_time = data['data'].get('processing_time_ms', 0)
                    print(f"   Response: {response[:100]}...")
                    print(f"   Processing time: {processing_time:.1f}ms")
                
                elif message_type == "error":
                    error = data['data'].get('error', '')
                    print(f"   Error: {error}")
                
                elif message_type == "ping":
                    # Respond to ping with pong
                    await self.send_message("pong", {"timestamp": datetime.now().isoformat()})
                
            except websockets.exceptions.ConnectionClosed:
                print("🔌 Connection closed by server")
                break
            except Exception as e:
                print(f"❌ Receive error: {e}")
                break
    
    async def test_ping(self):
        """Test ping functionality"""
        print("\n🏓 Testing ping...")
        await self.send_message("ping", {"timestamp": datetime.now().isoformat()})
    
    async def test_system_status(self):
        """Test system status request"""
        print("\n📊 Testing system status request...")
        await self.send_message("system_status_request", {"request_id": f"status_{int(time.time())}"})
    
    async def test_chat(self):
        """Test chat functionality"""
        print("\n💬 Testing chat...")
        
        test_messages = [
            "こんにちは！システムの調子はどうですか？",
            "CPUの使用率を教えてください",
            "メモリの状況はいかがですか？",
            "現在のシステム状態を詳しく教えて"
        ]
        
        for message in test_messages:
            print(f"   Sending: {message}")
            await self.send_message("chat_message", {
                "message": message,
                "request_id": f"chat_{int(time.time())}"
            })
            await asyncio.sleep(2)  # Wait between messages
    
    async def run_tests(self):
        """Run all tests"""
        if not await self.connect():
            return
        
        # Start receiving messages in background
        receive_task = asyncio.create_task(self.receive_messages())
        
        try:
            # Wait a bit for connection to stabilize
            await asyncio.sleep(1)
            
            # Run tests
            await self.test_ping()
            await asyncio.sleep(2)
            
            await self.test_system_status()
            await asyncio.sleep(3)
            
            await self.test_chat()
            await asyncio.sleep(5)
            
            print("\n✅ All tests completed!")
            
        except KeyboardInterrupt:
            print("\n⏹️  Tests interrupted by user")
        
        finally:
            await self.disconnect()
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass


async def main():
    """Main test function"""
    print("🧪 WebSocket Server Test Client")
    print("=" * 40)
    
    client = WebSocketTestClient()
    await client.run_tests()


if __name__ == "__main__":
    asyncio.run(main())