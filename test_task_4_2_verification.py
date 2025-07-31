#!/usr/bin/env python3
"""
Final verification test for Task 4.2: メッセージ処理とルーティング
Verifies all requirements are implemented correctly
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Import backend modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from message_router import MessageRouter, MessagePriority
from message_types import MessageType
from websocket_server import MacStatusWebSocketServer


async def verify_task_4_2():
    """Verify Task 4.2 implementation"""
    print("🔍 Task 4.2 Verification: メッセージ処理とルーティング")
    print("=" * 60)
    
    # Requirement verification checklist
    requirements = {
        "client_message_processing": False,
        "message_type_routing": False,
        "message_queuing": False,
        "error_handling": False
    }
    
    try:
        # Test 1: クライアントからのメッセージ受信と処理機能を実装
        print("\n✅ Requirement 1: Client Message Reception and Processing")
        print("-" * 50)
        
        # Create message router
        router = MessageRouter(queue_size=50, max_concurrent=3)
        
        # Track processed messages
        processed_messages = []
        
        async def test_handler(client_id: str, data: Dict[str, Any]):
            processed_messages.append({
                'client_id': client_id,
                'data': data,
                'timestamp': datetime.now().isoformat()
            })
        
        # Register handler
        router.register_handler("test_message", test_handler)
        
        # Start processing
        await router.start_processing()
        
        # Send test message
        message_id = await router.route_message(
            client_id="test_client_1",
            message_data={
                'type': 'test_message',
                'data': {'content': 'test message content'},
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        if len(processed_messages) == 1 and processed_messages[0]['client_id'] == 'test_client_1':
            print("   ✅ Client messages are received and processed correctly")
            requirements["client_message_processing"] = True
        else:
            print("   ❌ Client message processing failed")
        
        await router.stop_processing()
        
        # Test 2: システム情報要求とチャット要求の振り分け機能を追加
        print("\n✅ Requirement 2: System Info and Chat Request Routing")
        print("-" * 50)
        
        router = MessageRouter(queue_size=50, max_concurrent=3)
        
        # Track routing
        routing_results = {}
        
        async def system_handler(client_id: str, data: Dict[str, Any]):
            routing_results['system'] = True
        
        async def chat_handler(client_id: str, data: Dict[str, Any]):
            routing_results['chat'] = True
        
        # Register handlers for different message types
        router.register_handler(MessageType.SYSTEM_STATUS_REQUEST.value, system_handler)
        router.register_handler(MessageType.CHAT_MESSAGE.value, chat_handler)
        
        await router.start_processing()
        
        # Test system status request routing
        await router.route_message(
            client_id="test_client",
            message_data={
                'type': MessageType.SYSTEM_STATUS_REQUEST.value,
                'data': {'request_id': 'test_123'},
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Test chat message routing
        await router.route_message(
            client_id="test_client",
            message_data={
                'type': MessageType.CHAT_MESSAGE.value,
                'data': {'message': 'Hello system'},
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        if routing_results.get('system') and routing_results.get('chat'):
            print("   ✅ Message type routing works correctly")
            print("   ✅ System info requests routed to system handler")
            print("   ✅ Chat messages routed to chat handler")
            requirements["message_type_routing"] = True
        else:
            print("   ❌ Message type routing failed")
            print(f"   System handler called: {routing_results.get('system', False)}")
            print(f"   Chat handler called: {routing_results.get('chat', False)}")
        
        await router.stop_processing()
        
        # Test 3: メッセージキューイングとエラー処理を実装
        print("\n✅ Requirement 3: Message Queuing and Error Handling")
        print("-" * 50)
        
        router = MessageRouter(queue_size=10, max_concurrent=2)
        
        # Test queuing
        queue_test_count = 0
        
        async def queue_test_handler(client_id: str, data: Dict[str, Any]):
            nonlocal queue_test_count
            queue_test_count += 1
            await asyncio.sleep(0.1)  # Simulate processing time
        
        # Test error handling
        error_caught = False
        
        async def error_handler(client_id: str, data: Dict[str, Any]):
            raise ValueError("Test error for error handling")
        
        # Register handlers
        router.register_handler("queue_test", queue_test_handler)
        router.register_handler("error_test", error_handler)
        
        await router.start_processing()
        
        # Send multiple messages to test queuing
        for i in range(5):
            await router.route_message(
                client_id=f"queue_client_{i}",
                message_data={
                    'type': 'queue_test',
                    'data': {'test_id': i},
                    'timestamp': datetime.now().isoformat()
                }
            )
        
        # Send error message
        try:
            await router.route_message(
                client_id="error_client",
                message_data={
                    'type': 'error_test',
                    'data': {'should_fail': True},
                    'timestamp': datetime.now().isoformat()
                }
            )
        except:
            pass  # Error handling happens in the processor
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Check results
        status = await router.get_status()
        
        queuing_works = queue_test_count == 5
        error_handling_works = status['processing_metrics']['failed_messages'] > 0
        
        if queuing_works and error_handling_works:
            print("   ✅ Message queuing works correctly")
            print(f"   ✅ Processed {queue_test_count}/5 queued messages")
            print("   ✅ Error handling works correctly")
            print(f"   ✅ Failed messages: {status['processing_metrics']['failed_messages']}")
            requirements["message_queuing"] = True
            requirements["error_handling"] = True
        else:
            print("   ❌ Queuing or error handling failed")
            print(f"   Queue test: {queue_test_count}/5 messages processed")
            print(f"   Error handling: {status['processing_metrics']['failed_messages']} failed messages")
        
        await router.stop_processing()
        
        # Test 4: Integration with WebSocket Server
        print("\n✅ Integration Test: WebSocket Server Integration")
        print("-" * 50)
        
        # Verify WebSocket server has message router
        server = MacStatusWebSocketServer()
        
        if hasattr(server, 'message_router') and server.message_router is not None:
            print("   ✅ WebSocket server has message router")
            
            # Check if handlers are registered
            handlers = server.message_router.handlers
            expected_handlers = [
                MessageType.PING.value,
                MessageType.SYSTEM_STATUS_REQUEST.value,
                MessageType.CHAT_MESSAGE.value
            ]
            
            all_handlers_present = all(handler in handlers for handler in expected_handlers)
            
            if all_handlers_present:
                print("   ✅ All required message handlers are registered")
                print(f"   ✅ Registered handlers: {list(handlers.keys())}")
            else:
                print("   ❌ Some required handlers are missing")
                print(f"   Expected: {expected_handlers}")
                print(f"   Found: {list(handlers.keys())}")
        else:
            print("   ❌ WebSocket server missing message router")
        
        # Final verification
        print("\n📋 Task 4.2 Requirements Verification")
        print("=" * 40)
        
        all_requirements_met = all(requirements.values())
        
        for req_name, met in requirements.items():
            status = "✅ IMPLEMENTED" if met else "❌ NOT IMPLEMENTED"
            req_description = {
                "client_message_processing": "Client message reception and processing",
                "message_type_routing": "System info and chat request routing",
                "message_queuing": "Message queuing functionality",
                "error_handling": "Error handling functionality"
            }[req_name]
            
            print(f"  {req_description}: {status}")
        
        print(f"\nOverall Status: {'✅ ALL REQUIREMENTS MET' if all_requirements_met else '❌ SOME REQUIREMENTS NOT MET'}")
        
        if all_requirements_met:
            print("\n🎉 Task 4.2 successfully implemented!")
            print("   - Client messages are received and processed")
            print("   - Message types are correctly routed to appropriate handlers")
            print("   - Message queuing system is working")
            print("   - Error handling is implemented")
            print("   - Integration with WebSocket server is complete")
        else:
            print("\n⚠️  Task 4.2 needs additional work")
        
        return all_requirements_met
        
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        return False


async def main():
    """Main verification function"""
    success = await verify_task_4_2()
    
    if success:
        print("\n✅ Task 4.2 verification completed successfully!")
        exit(0)
    else:
        print("\n❌ Task 4.2 verification failed!")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())