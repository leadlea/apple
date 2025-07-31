#!/usr/bin/env python3
"""
Integration test for Message Processing and Routing (Task 4.2)
Tests the specific requirements:
1. クライアントからのメッセージ受信と処理機能を実装
2. システム情報要求とチャット要求の振り分け機能を追加  
3. メッセージキューイングとエラー処理を実装
"""
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Import backend modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from message_router import MessageRouter, MessagePriority, create_message_router
from message_types import MessageType


class MessageRoutingIntegrationTest:
    """Integration test for message routing functionality"""
    
    def __init__(self):
        self.router = None
        self.processed_messages: List[Dict[str, Any]] = []
        self.error_messages: List[Dict[str, Any]] = []
        
    async def setup(self):
        """Setup test environment"""
        print("🔧 Setting up message routing test...")
        
        # Create message router
        self.router = create_message_router(queue_size=100, max_concurrent=5)
        
        # Register custom handlers for testing
        await self._register_test_handlers()
        
        # Start processing
        await self.router.start_processing()
        
        print("✅ Setup complete")
    
    async def teardown(self):
        """Cleanup test environment"""
        if self.router:
            await self.router.stop_processing()
        print("🧹 Cleanup complete")
    
    async def _register_test_handlers(self):
        """Register test message handlers"""
        
        # System status request handler
        async def system_status_handler(client_id: str, data: Dict[str, Any]):
            print(f"   📊 Processing system status request from {client_id}")
            await asyncio.sleep(0.2)  # Simulate system data collection
            
            self.processed_messages.append({
                'type': 'system_status_request',
                'client_id': client_id,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'processing_time': 0.2
            })
            
            print(f"   ✅ System status processed for {client_id}")
        
        # Chat message handler
        async def chat_handler(client_id: str, data: Dict[str, Any]):
            message = data.get('message', '')
            print(f"   💬 Processing chat from {client_id}: {message[:50]}...")
            await asyncio.sleep(0.5)  # Simulate AI processing
            
            self.processed_messages.append({
                'type': 'chat_message',
                'client_id': client_id,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'processing_time': 0.5
            })
            
            print(f"   ✅ Chat processed for {client_id}")
        
        # Ping handler
        async def ping_handler(client_id: str, data: Dict[str, Any]):
            print(f"   🏓 Processing ping from {client_id}")
            
            self.processed_messages.append({
                'type': 'ping',
                'client_id': client_id,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'processing_time': 0.01
            })
        
        # Error handler for testing error handling
        async def error_handler(client_id: str, data: Dict[str, Any]):
            print(f"   ❌ Simulating error for {client_id}")
            raise ValueError("Test error for error handling")
        
        # Register handlers
        self.router.register_handler(
            MessageType.SYSTEM_STATUS_REQUEST.value,
            system_status_handler,
            priority=MessagePriority.NORMAL,
            timeout_seconds=10.0
        )
        
        self.router.register_handler(
            MessageType.CHAT_MESSAGE.value,
            chat_handler,
            priority=MessagePriority.NORMAL,
            timeout_seconds=30.0
        )
        
        self.router.register_handler(
            MessageType.PING.value,
            ping_handler,
            priority=MessagePriority.HIGH,
            timeout_seconds=5.0
        )
        
        # Register error handler for testing
        self.router.register_handler(
            "error_test",
            error_handler,
            priority=MessagePriority.NORMAL,
            timeout_seconds=5.0
        )
        
        print("   📝 Registered test handlers")
    
    async def test_client_message_reception_and_processing(self):
        """Test requirement 1: クライアントからのメッセージ受信と処理機能を実装"""
        print("\n📥 Test 1: Client Message Reception and Processing")
        print("-" * 50)
        
        # Test different types of client messages
        test_messages = [
            {
                'type': MessageType.PING.value,
                'data': {'timestamp': datetime.now().isoformat()},
                'client': 'client_1'
            },
            {
                'type': MessageType.SYSTEM_STATUS_REQUEST.value,
                'data': {'request_id': 'status_001'},
                'client': 'client_2'
            },
            {
                'type': MessageType.CHAT_MESSAGE.value,
                'data': {'message': 'システムの状態を教えてください'},
                'client': 'client_3'
            }
        ]
        
        initial_count = len(self.processed_messages)
        
        # Send messages
        for msg in test_messages:
            try:
                message_id = await self.router.route_message(
                    client_id=msg['client'],
                    message_data={
                        'type': msg['type'],
                        'data': msg['data'],
                        'timestamp': datetime.now().isoformat()
                    }
                )
                print(f"   📤 Routed {msg['type']} from {msg['client']}: {message_id}")
            except Exception as e:
                print(f"   ❌ Failed to route {msg['type']}: {e}")
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Verify processing
        processed_count = len(self.processed_messages) - initial_count
        print(f"   📊 Processed {processed_count}/3 messages")
        
        if processed_count == 3:
            print("   ✅ Test 1 PASSED: All messages received and processed")
        else:
            print("   ❌ Test 1 FAILED: Not all messages processed")
        
        return processed_count == 3
    
    async def test_message_type_routing(self):
        """Test requirement 2: システム情報要求とチャット要求の振り分け機能を追加"""
        print("\n🔀 Test 2: Message Type Routing (System Info vs Chat)")
        print("-" * 50)
        
        # Test routing different message types to appropriate handlers
        routing_tests = [
            {
                'type': MessageType.SYSTEM_STATUS_REQUEST.value,
                'data': {'request_id': 'routing_test_1'},
                'expected_handler': 'system_status_request'
            },
            {
                'type': MessageType.CHAT_MESSAGE.value,
                'data': {'message': 'CPUの使用率はどのくらいですか？'},
                'expected_handler': 'chat_message'
            },
            {
                'type': MessageType.SYSTEM_STATUS_REQUEST.value,
                'data': {'request_id': 'routing_test_2', 'detailed': True},
                'expected_handler': 'system_status_request'
            },
            {
                'type': MessageType.CHAT_MESSAGE.value,
                'data': {'message': 'メモリの状況を詳しく教えて'},
                'expected_handler': 'chat_message'
            }
        ]
        
        initial_count = len(self.processed_messages)
        
        # Send routing test messages
        for i, test in enumerate(routing_tests):
            try:
                message_id = await self.router.route_message(
                    client_id=f'routing_client_{i}',
                    message_data={
                        'type': test['type'],
                        'data': test['data'],
                        'timestamp': datetime.now().isoformat()
                    }
                )
                print(f"   📤 Routed {test['type']}: {message_id}")
            except Exception as e:
                print(f"   ❌ Failed to route {test['type']}: {e}")
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # Verify correct routing (messages may complete out of order due to concurrency)
        new_messages = self.processed_messages[initial_count:]
        routing_correct = True
        
        # Count expected vs actual message types
        expected_counts = {}
        actual_counts = {}
        
        for test in routing_tests:
            expected_type = test['expected_handler']
            expected_counts[expected_type] = expected_counts.get(expected_type, 0) + 1
        
        for msg in new_messages:
            msg_type = msg['type']
            actual_counts[msg_type] = actual_counts.get(msg_type, 0) + 1
        
        # Verify counts match
        for expected_type, expected_count in expected_counts.items():
            actual_count = actual_counts.get(expected_type, 0)
            if actual_count == expected_count:
                print(f"   ✅ {expected_type}: {actual_count}/{expected_count} messages (correct)")
            else:
                print(f"   ❌ {expected_type}: {actual_count}/{expected_count} messages (incorrect)")
                routing_correct = False
        
        # Check total count
        if len(new_messages) != len(routing_tests):
            print(f"   ❌ Total messages: {len(new_messages)}/{len(routing_tests)} (incorrect)")
            routing_correct = False
        else:
            print(f"   ✅ Total messages: {len(new_messages)}/{len(routing_tests)} (correct)")
        
        if routing_correct:
            print("   ✅ Test 2 PASSED: Message routing works correctly")
        else:
            print("   ❌ Test 2 FAILED: Message routing issues detected")
        
        return routing_correct
    
    async def test_message_queuing_and_error_handling(self):
        """Test requirement 3: メッセージキューイングとエラー処理を実装"""
        print("\n📋 Test 3: Message Queuing and Error Handling")
        print("-" * 50)
        
        # Test 3a: Message Queuing
        print("   📋 Testing message queuing...")
        
        # Send multiple messages rapidly to test queuing
        queue_test_messages = []
        for i in range(10):
            message_data = {
                'type': MessageType.PING.value,
                'data': {'test_id': f'queue_test_{i}'},
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                message_id = await self.router.route_message(
                    client_id=f'queue_client_{i}',
                    message_data=message_data
                )
                queue_test_messages.append(message_id)
            except Exception as e:
                print(f"   ❌ Failed to queue message {i}: {e}")
        
        print(f"   📤 Queued {len(queue_test_messages)} messages")
        
        # Check queue status
        status = await self.router.get_status()
        queue_size = status['queue_stats']['total_size']
        print(f"   📊 Current queue size: {queue_size}")
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Test 3b: Error Handling
        print("   ❌ Testing error handling...")
        
        initial_error_count = len(self.error_messages)
        
        # Send message that will cause error
        try:
            error_message_id = await self.router.route_message(
                client_id='error_test_client',
                message_data={
                    'type': 'error_test',
                    'data': {'should_fail': True},
                    'timestamp': datetime.now().isoformat()
                }
            )
            print(f"   📤 Sent error test message: {error_message_id}")
        except Exception as e:
            print(f"   ❌ Failed to send error test: {e}")
        
        # Wait for error processing
        await asyncio.sleep(2)
        
        # Check final status
        final_status = await self.router.get_status()
        failed_messages = final_status['processing_metrics']['failed_messages']
        
        print(f"   📊 Failed messages: {failed_messages}")
        
        # Test results
        queuing_works = len(queue_test_messages) == 10
        error_handling_works = failed_messages > 0
        
        if queuing_works and error_handling_works:
            print("   ✅ Test 3 PASSED: Queuing and error handling work correctly")
        else:
            print("   ❌ Test 3 FAILED:")
            if not queuing_works:
                print("     - Queuing issues detected")
            if not error_handling_works:
                print("     - Error handling not working")
        
        return queuing_works and error_handling_works
    
    async def test_performance_and_metrics(self):
        """Test performance and metrics collection"""
        print("\n📈 Test 4: Performance and Metrics")
        print("-" * 50)
        
        # Send a batch of messages and measure performance
        start_time = time.time()
        batch_size = 20
        
        for i in range(batch_size):
            message_type = [
                MessageType.PING.value,
                MessageType.SYSTEM_STATUS_REQUEST.value,
                MessageType.CHAT_MESSAGE.value
            ][i % 3]
            
            message_data = {
                'type': message_type,
                'data': {'batch_test': i, 'message': f'Performance test message {i}'},
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                await self.router.route_message(
                    client_id=f'perf_client_{i}',
                    message_data=message_data
                )
            except Exception as e:
                print(f"   ❌ Failed to send batch message {i}: {e}")
        
        # Wait for processing
        await asyncio.sleep(5)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Get final metrics
        status = await self.router.get_status()
        metrics = status['processing_metrics']
        
        print(f"   📊 Performance Metrics:")
        print(f"     - Total messages: {metrics['total_messages']}")
        print(f"     - Processed messages: {metrics['processed_messages']}")
        print(f"     - Success rate: {metrics['success_rate']:.1f}%")
        print(f"     - Average processing time: {metrics['average_processing_time_ms']:.1f}ms")
        print(f"     - Messages per minute: {metrics['messages_per_minute']:.1f}")
        print(f"     - Total test time: {total_time:.2f}s")
        
        # Performance criteria
        success_rate_ok = metrics['success_rate'] >= 90
        avg_time_ok = metrics['average_processing_time_ms'] < 1000  # Less than 1 second
        
        if success_rate_ok and avg_time_ok:
            print("   ✅ Test 4 PASSED: Performance metrics are acceptable")
        else:
            print("   ❌ Test 4 FAILED: Performance issues detected")
        
        return success_rate_ok and avg_time_ok
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🧪 Message Processing and Routing Integration Test")
        print("=" * 60)
        print("Testing Task 4.2 Requirements:")
        print("1. クライアントからのメッセージ受信と処理機能を実装")
        print("2. システム情報要求とチャット要求の振り分け機能を追加")
        print("3. メッセージキューイングとエラー処理を実装")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Run tests
            test_results = []
            
            test_results.append(await self.test_client_message_reception_and_processing())
            test_results.append(await self.test_message_type_routing())
            test_results.append(await self.test_message_queuing_and_error_handling())
            test_results.append(await self.test_performance_and_metrics())
            
            # Summary
            print("\n📋 Test Summary")
            print("=" * 30)
            
            passed_tests = sum(test_results)
            total_tests = len(test_results)
            
            test_names = [
                "Message Reception & Processing",
                "Message Type Routing",
                "Queuing & Error Handling",
                "Performance & Metrics"
            ]
            
            for i, (name, result) in enumerate(zip(test_names, test_results)):
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"  {i+1}. {name}: {status}")
            
            print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
            
            if passed_tests == total_tests:
                print("🎉 ALL TESTS PASSED - Task 4.2 requirements implemented successfully!")
            else:
                print("⚠️  Some tests failed - review implementation")
            
            return passed_tests == total_tests
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
        
        finally:
            await self.teardown()


async def main():
    """Main test execution"""
    test = MessageRoutingIntegrationTest()
    success = await test.run_all_tests()
    
    if success:
        print("\n✅ Task 4.2 implementation verified successfully!")
        exit(0)
    else:
        print("\n❌ Task 4.2 implementation needs review")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())