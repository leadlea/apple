"""
Unit tests for MessageRouter system
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Import the classes we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from message_router import (
    MessageRouter,
    MessageQueue,
    MessageProcessor,
    QueuedMessage,
    MessageHandler,
    MessagePriority,
    ProcessingStatus,
    ProcessingMetrics,
    create_message_router
)


class TestQueuedMessage:
    """Test cases for QueuedMessage"""
    
    def test_queued_message_creation(self):
        """Test QueuedMessage creation"""
        message = QueuedMessage(
            message_id="test_123",
            client_id="client_456",
            message_type="test_message",
            data={"key": "value"},
            timestamp=datetime.now()
        )
        
        assert message.message_id == "test_123"
        assert message.client_id == "client_456"
        assert message.message_type == "test_message"
        assert message.data == {"key": "value"}
        assert message.priority == MessagePriority.NORMAL
        assert message.status == ProcessingStatus.PENDING
    
    def test_queued_message_with_custom_values(self):
        """Test QueuedMessage with custom values"""
        message = QueuedMessage(
            message_id="test_123",
            client_id="client_456",
            message_type="urgent_message",
            data={},
            timestamp=datetime.now(),
            priority=MessagePriority.URGENT,
            timeout_seconds=60.0,
            max_retries=5
        )
        
        assert message.priority == MessagePriority.URGENT
        assert message.timeout_seconds == 60.0
        assert message.max_retries == 5


class TestMessageHandler:
    """Test cases for MessageHandler"""
    
    def test_message_handler_creation(self):
        """Test MessageHandler creation"""
        def dummy_handler():
            pass
        
        handler = MessageHandler(
            message_type="test_type",
            handler_func=dummy_handler,
            priority=MessagePriority.HIGH,
            timeout_seconds=15.0
        )
        
        assert handler.message_type == "test_type"
        assert handler.handler_func == dummy_handler
        assert handler.priority == MessagePriority.HIGH
        assert handler.timeout_seconds == 15.0


class TestProcessingMetrics:
    """Test cases for ProcessingMetrics"""
    
    def test_processing_metrics_creation(self):
        """Test ProcessingMetrics creation"""
        metrics = ProcessingMetrics(
            total_messages=100,
            processed_messages=95,
            failed_messages=3,
            timeout_messages=2
        )
        
        assert metrics.total_messages == 100
        assert metrics.processed_messages == 95
        assert metrics.failed_messages == 3
        assert metrics.timeout_messages == 2
    
    def test_processing_metrics_to_dict(self):
        """Test ProcessingMetrics to_dict conversion"""
        metrics = ProcessingMetrics(
            total_messages=100,
            processed_messages=90,
            failed_messages=5,
            timeout_messages=5
        )
        
        result = metrics.to_dict()
        
        assert result['total_messages'] == 100
        assert result['processed_messages'] == 90
        assert result['success_rate'] == 90.0
        assert 'average_processing_time_ms' in result
        assert 'queue_size' in result


class TestMessageQueue:
    """Test cases for MessageQueue"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.queue = MessageQueue(max_size=10)
    
    @pytest.mark.asyncio
    async def test_enqueue_message(self):
        """Test enqueuing messages"""
        message = QueuedMessage(
            message_id="test_1",
            client_id="client_1",
            message_type="test",
            data={},
            timestamp=datetime.now()
        )
        
        result = await self.queue.enqueue(message)
        assert result is True
        
        # Check message is in lookup
        assert "test_1" in self.queue.message_lookup
    
    @pytest.mark.asyncio
    async def test_dequeue_message(self):
        """Test dequeuing messages"""
        # Enqueue messages with different priorities
        high_priority = QueuedMessage(
            message_id="high_1",
            client_id="client_1",
            message_type="test",
            data={},
            timestamp=datetime.now(),
            priority=MessagePriority.HIGH
        )
        
        normal_priority = QueuedMessage(
            message_id="normal_1",
            client_id="client_1",
            message_type="test",
            data={},
            timestamp=datetime.now(),
            priority=MessagePriority.NORMAL
        )
        
        # Enqueue normal first, then high
        await self.queue.enqueue(normal_priority)
        await self.queue.enqueue(high_priority)
        
        # Dequeue should return high priority first
        message = await self.queue.dequeue()
        assert message.message_id == "high_1"
        
        # Next should be normal priority
        message = await self.queue.dequeue()
        assert message.message_id == "normal_1"
    
    @pytest.mark.asyncio
    async def test_dequeue_empty_queue(self):
        """Test dequeuing from empty queue"""
        message = await self.queue.dequeue()
        assert message is None
    
    @pytest.mark.asyncio
    async def test_queue_size_limit(self):
        """Test queue size limit"""
        # Fill queue to max size
        for i in range(10):
            message = QueuedMessage(
                message_id=f"test_{i}",
                client_id="client_1",
                message_type="test",
                data={},
                timestamp=datetime.now()
            )
            result = await self.queue.enqueue(message)
            assert result is True
        
        # Try to add one more (should fail)
        overflow_message = QueuedMessage(
            message_id="overflow",
            client_id="client_1",
            message_type="test",
            data={},
            timestamp=datetime.now()
        )
        
        result = await self.queue.enqueue(overflow_message)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_remove_message(self):
        """Test removing message from queue"""
        message = QueuedMessage(
            message_id="remove_test",
            client_id="client_1",
            message_type="test",
            data={},
            timestamp=datetime.now()
        )
        
        await self.queue.enqueue(message)
        assert "remove_test" in self.queue.message_lookup
        
        result = await self.queue.remove_message("remove_test")
        assert result is True
        assert "remove_test" not in self.queue.message_lookup
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting queue statistics"""
        # Add some messages
        for i in range(3):
            message = QueuedMessage(
                message_id=f"stats_test_{i}",
                client_id="client_1",
                message_type="test",
                data={},
                timestamp=datetime.now(),
                priority=MessagePriority.HIGH if i == 0 else MessagePriority.NORMAL
            )
            await self.queue.enqueue(message)
        
        stats = await self.queue.get_stats()
        
        assert stats['total_size'] == 3
        assert stats['by_priority']['HIGH'] == 1
        assert stats['by_priority']['NORMAL'] == 2
        assert stats['max_size'] == 10


class TestMessageProcessor:
    """Test cases for MessageProcessor"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.processor = MessageProcessor(max_concurrent=3)
    
    @pytest.mark.asyncio
    async def test_process_message_success(self):
        """Test successful message processing"""
        processed_data = []
        
        async def test_handler(client_id: str, data: dict):
            processed_data.append((client_id, data))
            await asyncio.sleep(0.1)  # Simulate processing
        
        message = QueuedMessage(
            message_id="process_test",
            client_id="client_1",
            message_type="test",
            data={"test": "data"},
            timestamp=datetime.now()
        )
        
        result = await self.processor.process_message(message, test_handler)
        
        assert result is True
        assert message.status == ProcessingStatus.COMPLETED
        assert len(processed_data) == 1
        assert processed_data[0] == ("client_1", {"test": "data"})
    
    @pytest.mark.asyncio
    async def test_process_message_timeout(self):
        """Test message processing timeout"""
        async def slow_handler(client_id: str, data: dict):
            await asyncio.sleep(2.0)  # Longer than timeout
        
        message = QueuedMessage(
            message_id="timeout_test",
            client_id="client_1",
            message_type="test",
            data={},
            timestamp=datetime.now(),
            timeout_seconds=0.5  # Short timeout
        )
        
        result = await self.processor.process_message(message, slow_handler)
        
        assert result is False
        assert message.status == ProcessingStatus.TIMEOUT
        assert "timeout" in message.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_process_message_error(self):
        """Test message processing error"""
        async def error_handler(client_id: str, data: dict):
            raise ValueError("Test error")
        
        message = QueuedMessage(
            message_id="error_test",
            client_id="client_1",
            message_type="test",
            data={},
            timestamp=datetime.now()
        )
        
        result = await self.processor.process_message(message, error_handler)
        
        assert result is False
        assert message.status == ProcessingStatus.FAILED
        assert "Test error" in message.error_message
    
    @pytest.mark.asyncio
    async def test_cancel_message(self):
        """Test cancelling message processing"""
        async def long_handler(client_id: str, data: dict):
            await asyncio.sleep(5.0)  # Long processing
        
        message = QueuedMessage(
            message_id="cancel_test",
            client_id="client_1",
            message_type="test",
            data={},
            timestamp=datetime.now()
        )
        
        # Start processing
        process_task = asyncio.create_task(
            self.processor.process_message(message, long_handler)
        )
        
        # Wait a bit then cancel
        await asyncio.sleep(0.1)
        cancel_result = await self.processor.cancel_message("cancel_test")
        
        assert cancel_result is True
        
        # Wait for task to complete
        try:
            await process_task
        except:
            pass  # Task might be cancelled
    
    def test_get_metrics(self):
        """Test getting processing metrics"""
        metrics = self.processor.get_metrics()
        
        assert isinstance(metrics, ProcessingMetrics)
        assert metrics.total_messages >= 0
        assert metrics.processed_messages >= 0
        assert metrics.active_processors >= 0


class TestMessageRouter:
    """Test cases for MessageRouter"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.router = MessageRouter(queue_size=50, max_concurrent=5)
    
    def test_router_initialization(self):
        """Test router initialization"""
        assert self.router.message_queue is not None
        assert self.router.message_processor is not None
        assert len(self.router.handlers) > 0  # Default handlers
        assert not self.router.is_running
    
    def test_register_handler(self):
        """Test registering message handler"""
        def test_handler():
            pass
        
        self.router.register_handler(
            "custom_message",
            test_handler,
            priority=MessagePriority.HIGH,
            timeout_seconds=20.0
        )
        
        assert "custom_message" in self.router.handlers
        handler = self.router.handlers["custom_message"]
        assert handler.handler_func == test_handler
        assert handler.priority == MessagePriority.HIGH
        assert handler.timeout_seconds == 20.0
    
    @pytest.mark.asyncio
    async def test_route_message(self):
        """Test routing message"""
        # Register test handler
        processed_messages = []
        
        async def test_handler(client_id: str, data: dict):
            processed_messages.append((client_id, data))
        
        self.router.register_handler("test_route", test_handler)
        
        # Start processing
        await self.router.start_processing()
        
        try:
            # Route message
            message_data = {
                'type': 'test_route',
                'data': {'test': 'routing'},
                'timestamp': datetime.now().isoformat()
            }
            
            message_id = await self.router.route_message('test_client', message_data)
            assert message_id is not None
            
            # Wait for processing
            await asyncio.sleep(0.5)
            
            # Check if message was processed
            assert len(processed_messages) == 1
            assert processed_messages[0] == ('test_client', {'test': 'routing'})
            
        finally:
            await self.router.stop_processing()
    
    @pytest.mark.asyncio
    async def test_route_unknown_message_type(self):
        """Test routing unknown message type"""
        message_data = {
            'type': 'unknown_type',
            'data': {},
            'timestamp': datetime.now().isoformat()
        }
        
        with pytest.raises(ValueError, match="Unknown message type"):
            await self.router.route_message('test_client', message_data)
    
    @pytest.mark.asyncio
    async def test_start_stop_processing(self):
        """Test starting and stopping processing"""
        assert not self.router.is_running
        
        # Start processing
        await self.router.start_processing()
        assert self.router.is_running
        assert self.router.processing_task is not None
        
        # Stop processing
        await self.router.stop_processing()
        assert not self.router.is_running
    
    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting router status"""
        status = await self.router.get_status()
        
        assert 'is_running' in status
        assert 'queue_stats' in status
        assert 'processing_metrics' in status
        assert 'registered_handlers' in status
        assert 'active_tasks' in status
        
        assert isinstance(status['registered_handlers'], list)
        assert len(status['registered_handlers']) > 0  # Default handlers


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_message_router(self):
        """Test creating message router"""
        router = create_message_router(queue_size=100, max_concurrent=8)
        
        assert isinstance(router, MessageRouter)
        assert router.message_queue.max_size == 100
        assert router.message_processor.max_concurrent == 8


class TestMessageRouterIntegration:
    """Integration tests for message router"""
    
    @pytest.mark.asyncio
    async def test_full_message_flow(self):
        """Test complete message flow from routing to processing"""
        router = create_message_router(queue_size=10, max_concurrent=2)
        
        # Track processed messages
        processed_messages = []
        processing_times = []
        
        async def tracking_handler(client_id: str, data: dict):
            start_time = time.time()
            await asyncio.sleep(0.1)  # Simulate processing
            end_time = time.time()
            
            processed_messages.append({
                'client_id': client_id,
                'data': data,
                'processing_time': end_time - start_time
            })
            processing_times.append(end_time - start_time)
        
        # Register handler
        router.register_handler(
            "integration_test",
            tracking_handler,
            priority=MessagePriority.NORMAL,
            timeout_seconds=5.0
        )
        
        # Start processing
        await router.start_processing()
        
        try:
            # Send multiple messages
            message_ids = []
            for i in range(5):
                message_data = {
                    'type': 'integration_test',
                    'data': {'message_number': i},
                    'timestamp': datetime.now().isoformat()
                }
                
                message_id = await router.route_message(f'client_{i}', message_data)
                message_ids.append(message_id)
            
            # Wait for all messages to be processed
            await asyncio.sleep(1.0)
            
            # Verify all messages were processed
            assert len(processed_messages) == 5
            
            # Check processing times are reasonable
            assert all(0.05 < t < 0.5 for t in processing_times)
            
            # Get final status
            status = await router.get_status()
            assert status['processing_metrics']['processed_messages'] == 5
            assert status['processing_metrics']['success_rate'] == 100.0
            
        finally:
            await router.stop_processing()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])