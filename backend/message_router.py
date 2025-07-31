"""
Message Processing and Routing System for Mac Status PWA
Handles message routing, queuing, and processing logic
"""
import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import queue
from collections import defaultdict, deque

# Import our backend modules
import sys
import os
sys.path.append(os.path.dirname(__file__))

from message_types import MessageType, WebSocketMessage


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class ProcessingStatus(Enum):
    """Message processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class QueuedMessage:
    """Message in processing queue"""
    message_id: str
    client_id: str
    message_type: str
    data: Dict[str, Any]
    timestamp: datetime
    priority: MessagePriority = MessagePriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: float = 30.0
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    processing_start: Optional[datetime] = None
    processing_end: Optional[datetime] = None
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class MessageHandler:
    """Message handler configuration"""
    message_type: str
    handler_func: Callable
    priority: MessagePriority = MessagePriority.NORMAL
    timeout_seconds: float = 30.0
    max_concurrent: int = 10
    rate_limit_per_minute: int = 60


@dataclass
class ProcessingMetrics:
    """Metrics for message processing"""
    total_messages: int = 0
    processed_messages: int = 0
    failed_messages: int = 0
    timeout_messages: int = 0
    average_processing_time_ms: float = 0.0
    messages_per_minute: float = 0.0
    queue_size: int = 0
    active_processors: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_messages': self.total_messages,
            'processed_messages': self.processed_messages,
            'failed_messages': self.failed_messages,
            'timeout_messages': self.timeout_messages,
            'success_rate': (self.processed_messages / max(self.total_messages, 1)) * 100,
            'average_processing_time_ms': self.average_processing_time_ms,
            'messages_per_minute': self.messages_per_minute,
            'queue_size': self.queue_size,
            'active_processors': self.active_processors
        }


class MessageQueue:
    """Priority-based message queue with rate limiting"""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize message queue
        
        Args:
            max_size: Maximum queue size
        """
        self.max_size = max_size
        self.queues = {
            MessagePriority.URGENT: deque(),
            MessagePriority.HIGH: deque(),
            MessagePriority.NORMAL: deque(),
            MessagePriority.LOW: deque()
        }
        self.message_lookup: Dict[str, QueuedMessage] = {}
        self.rate_limits: Dict[str, deque] = defaultdict(deque)  # client_id -> timestamps
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()
    
    async def enqueue(self, message: QueuedMessage) -> bool:
        """
        Add message to queue
        
        Args:
            message: Message to enqueue
            
        Returns:
            True if enqueued successfully
        """
        async with self._lock:
            # Check queue size
            total_size = sum(len(q) for q in self.queues.values())
            if total_size >= self.max_size:
                self.logger.warning(f"Queue full, dropping message {message.message_id}")
                return False
            
            # Check rate limiting
            if not self._check_rate_limit(message.client_id):
                self.logger.warning(f"Rate limit exceeded for client {message.client_id}")
                return False
            
            # Add to appropriate priority queue
            self.queues[message.priority].append(message)
            self.message_lookup[message.message_id] = message
            
            self.logger.debug(f"Enqueued message {message.message_id} with priority {message.priority.name}")
            return True
    
    async def dequeue(self) -> Optional[QueuedMessage]:
        """
        Get next message from queue (highest priority first)
        
        Returns:
            Next message or None if queue is empty
        """
        async with self._lock:
            # Check queues in priority order
            for priority in [MessagePriority.URGENT, MessagePriority.HIGH, 
                           MessagePriority.NORMAL, MessagePriority.LOW]:
                if self.queues[priority]:
                    message = self.queues[priority].popleft()
                    return message
            
            return None
    
    async def remove_message(self, message_id: str) -> bool:
        """
        Remove message from queue
        
        Args:
            message_id: Message ID to remove
            
        Returns:
            True if removed successfully
        """
        async with self._lock:
            if message_id in self.message_lookup:
                message = self.message_lookup[message_id]
                
                # Remove from appropriate queue
                try:
                    self.queues[message.priority].remove(message)
                    del self.message_lookup[message_id]
                    return True
                except ValueError:
                    # Message not in queue (might be processing)
                    del self.message_lookup[message_id]
                    return True
            
            return False
    
    def _check_rate_limit(self, client_id: str, limit_per_minute: int = 60) -> bool:
        """
        Check if client is within rate limit
        
        Args:
            client_id: Client identifier
            limit_per_minute: Messages per minute limit
            
        Returns:
            True if within limit
        """
        now = time.time()
        minute_ago = now - 60
        
        # Clean old timestamps
        client_timestamps = self.rate_limits[client_id]
        while client_timestamps and client_timestamps[0] < minute_ago:
            client_timestamps.popleft()
        
        # Check limit
        if len(client_timestamps) >= limit_per_minute:
            return False
        
        # Add current timestamp
        client_timestamps.append(now)
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        async with self._lock:
            return {
                'total_size': sum(len(q) for q in self.queues.values()),
                'by_priority': {
                    priority.name: len(queue) 
                    for priority, queue in self.queues.items()
                },
                'max_size': self.max_size,
                'rate_limit_clients': len(self.rate_limits)
            }


class MessageProcessor:
    """Processes messages with concurrency control and error handling"""
    
    def __init__(self, max_concurrent: int = 10):
        """
        Initialize message processor
        
        Args:
            max_concurrent: Maximum concurrent processing tasks
        """
        self.max_concurrent = max_concurrent
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.processing_semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = logging.getLogger(__name__)
        
        # Metrics
        self.metrics = ProcessingMetrics()
        self.processing_times: deque = deque(maxlen=100)  # Last 100 processing times
        self.start_time = time.time()
    
    async def process_message(self, message: QueuedMessage, handler_func: Callable) -> bool:
        """
        Process a single message
        
        Args:
            message: Message to process
            handler_func: Handler function
            
        Returns:
            True if processed successfully
        """
        async with self.processing_semaphore:
            message.status = ProcessingStatus.PROCESSING
            message.processing_start = datetime.now()
            
            try:
                # Create processing task
                task = asyncio.create_task(
                    self._execute_handler(message, handler_func)
                )
                self.active_tasks[message.message_id] = task
                
                # Wait for completion with timeout
                await asyncio.wait_for(task, timeout=message.timeout_seconds)
                
                message.status = ProcessingStatus.COMPLETED
                message.processing_end = datetime.now()
                
                # Update metrics
                self._update_metrics(message, success=True)
                
                self.logger.debug(f"Successfully processed message {message.message_id}")
                return True
                
            except asyncio.TimeoutError:
                message.status = ProcessingStatus.TIMEOUT
                message.error_message = f"Processing timeout after {message.timeout_seconds}s"
                self.metrics.timeout_messages += 1
                
                self.logger.warning(f"Message {message.message_id} timed out")
                return False
                
            except Exception as e:
                message.status = ProcessingStatus.FAILED
                message.error_message = str(e)
                self.metrics.failed_messages += 1
                
                self.logger.error(f"Error processing message {message.message_id}: {e}")
                return False
                
            finally:
                # Cleanup
                if message.message_id in self.active_tasks:
                    del self.active_tasks[message.message_id]
                
                message.processing_end = datetime.now()
    
    async def _execute_handler(self, message: QueuedMessage, handler_func: Callable):
        """Execute the message handler function"""
        try:
            if asyncio.iscoroutinefunction(handler_func):
                await handler_func(message.client_id, message.data)
            else:
                handler_func(message.client_id, message.data)
        except Exception as e:
            self.logger.error(f"Handler execution failed: {e}")
            raise
    
    def _update_metrics(self, message: QueuedMessage, success: bool):
        """Update processing metrics"""
        self.metrics.total_messages += 1
        
        if success:
            self.metrics.processed_messages += 1
        
        # Calculate processing time
        if message.processing_start and message.processing_end:
            processing_time = (message.processing_end - message.processing_start).total_seconds() * 1000
            self.processing_times.append(processing_time)
            
            # Update average
            if self.processing_times:
                self.metrics.average_processing_time_ms = sum(self.processing_times) / len(self.processing_times)
        
        # Calculate messages per minute
        elapsed_minutes = (time.time() - self.start_time) / 60
        if elapsed_minutes > 0:
            self.metrics.messages_per_minute = self.metrics.total_messages / elapsed_minutes
        
        # Update active processors
        self.metrics.active_processors = len(self.active_tasks)
    
    async def cancel_message(self, message_id: str) -> bool:
        """
        Cancel processing message
        
        Args:
            message_id: Message ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        if message_id in self.active_tasks:
            task = self.active_tasks[message_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            # Remove from active tasks if still present
            if message_id in self.active_tasks:
                del self.active_tasks[message_id]
            
            self.logger.info(f"Cancelled processing for message {message_id}")
            return True
        
        return False
    
    def get_metrics(self) -> ProcessingMetrics:
        """Get current processing metrics"""
        self.metrics.queue_size = 0  # Will be updated by router
        self.metrics.active_processors = len(self.active_tasks)
        return self.metrics


class MessageRouter:
    """Main message routing and processing system"""
    
    def __init__(self, queue_size: int = 1000, max_concurrent: int = 10):
        """
        Initialize message router
        
        Args:
            queue_size: Maximum queue size
            max_concurrent: Maximum concurrent processors
        """
        self.message_queue = MessageQueue(max_size=queue_size)
        self.message_processor = MessageProcessor(max_concurrent=max_concurrent)
        self.handlers: Dict[str, MessageHandler] = {}
        self.logger = logging.getLogger(__name__)
        
        # Processing control
        self.is_running = False
        self.processing_task: Optional[asyncio.Task] = None
        
        # Default handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default message handlers"""
        # These will be overridden by the WebSocket server
        self.register_handler(
            MessageType.PING.value,
            self._default_ping_handler,
            priority=MessagePriority.HIGH,
            timeout_seconds=5.0
        )
        
        self.register_handler(
            MessageType.SYSTEM_STATUS_REQUEST.value,
            self._default_status_handler,
            priority=MessagePriority.NORMAL,
            timeout_seconds=10.0
        )
        
        self.register_handler(
            MessageType.CHAT_MESSAGE.value,
            self._default_chat_handler,
            priority=MessagePriority.NORMAL,
            timeout_seconds=30.0
        )
    
    def register_handler(self, 
                        message_type: str, 
                        handler_func: Callable,
                        priority: MessagePriority = MessagePriority.NORMAL,
                        timeout_seconds: float = 30.0,
                        max_concurrent: int = 10,
                        rate_limit_per_minute: int = 60):
        """
        Register message handler
        
        Args:
            message_type: Type of message to handle
            handler_func: Handler function
            priority: Default priority for this message type
            timeout_seconds: Processing timeout
            max_concurrent: Max concurrent processing
            rate_limit_per_minute: Rate limit
        """
        handler = MessageHandler(
            message_type=message_type,
            handler_func=handler_func,
            priority=priority,
            timeout_seconds=timeout_seconds,
            max_concurrent=max_concurrent,
            rate_limit_per_minute=rate_limit_per_minute
        )
        
        self.handlers[message_type] = handler
        self.logger.info(f"Registered handler for message type: {message_type}")
    
    async def route_message(self, 
                          client_id: str, 
                          message_data: Dict[str, Any],
                          priority: Optional[MessagePriority] = None) -> str:
        """
        Route incoming message to appropriate handler
        
        Args:
            client_id: Client identifier
            message_data: Message data
            priority: Optional priority override
            
        Returns:
            Message ID for tracking
        """
        message_type = message_data.get('type', 'unknown')
        message_id = message_data.get('message_id', str(uuid.uuid4()))
        
        # Check if handler exists
        if message_type not in self.handlers:
            self.logger.warning(f"No handler for message type: {message_type}")
            raise ValueError(f"Unknown message type: {message_type}")
        
        handler = self.handlers[message_type]
        
        # Create queued message
        queued_message = QueuedMessage(
            message_id=message_id,
            client_id=client_id,
            message_type=message_type,
            data=message_data.get('data', {}),
            timestamp=datetime.now(),
            priority=priority or handler.priority,
            timeout_seconds=handler.timeout_seconds
        )
        
        # Enqueue message
        if await self.message_queue.enqueue(queued_message):
            self.logger.debug(f"Routed message {message_id} of type {message_type}")
            return message_id
        else:
            raise RuntimeError("Failed to enqueue message (queue full or rate limited)")
    
    async def start_processing(self):
        """Start message processing loop"""
        if self.is_running:
            return
        
        self.is_running = True
        self.processing_task = asyncio.create_task(self._processing_loop())
        self.logger.info("Started message processing")
    
    async def stop_processing(self):
        """Stop message processing loop"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all active processing tasks
        for message_id in list(self.message_processor.active_tasks.keys()):
            await self.message_processor.cancel_message(message_id)
        
        self.logger.info("Stopped message processing")
    
    async def _processing_loop(self):
        """Main message processing loop"""
        while self.is_running:
            try:
                # Get next message from queue
                message = await self.message_queue.dequeue()
                
                if message is None:
                    # No messages, wait a bit
                    await asyncio.sleep(0.1)
                    continue
                
                # Get handler
                if message.message_type not in self.handlers:
                    self.logger.error(f"No handler for message type: {message.message_type}")
                    continue
                
                handler = self.handlers[message.message_type]
                
                # Process message (non-blocking)
                asyncio.create_task(
                    self.message_processor.process_message(message, handler.handler_func)
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(1)  # Wait before retrying
    
    async def get_status(self) -> Dict[str, Any]:
        """Get router status and metrics"""
        queue_stats = await self.message_queue.get_stats()
        processing_metrics = self.message_processor.get_metrics()
        processing_metrics.queue_size = queue_stats['total_size']
        
        return {
            'is_running': self.is_running,
            'queue_stats': queue_stats,
            'processing_metrics': processing_metrics.to_dict(),
            'registered_handlers': list(self.handlers.keys()),
            'active_tasks': len(self.message_processor.active_tasks)
        }
    
    # Default handlers (to be overridden)
    async def _default_ping_handler(self, client_id: str, data: Dict[str, Any]):
        """Default ping handler"""
        self.logger.debug(f"Ping from client {client_id}")
    
    async def _default_status_handler(self, client_id: str, data: Dict[str, Any]):
        """Default system status handler"""
        self.logger.debug(f"System status request from client {client_id}")
    
    async def _default_chat_handler(self, client_id: str, data: Dict[str, Any]):
        """Default chat handler"""
        self.logger.debug(f"Chat message from client {client_id}: {data.get('message', '')}")


# Utility functions for message routing
def create_message_router(queue_size: int = 1000, max_concurrent: int = 10) -> MessageRouter:
    """
    Create and configure message router
    
    Args:
        queue_size: Maximum queue size
        max_concurrent: Maximum concurrent processors
        
    Returns:
        Configured MessageRouter instance
    """
    router = MessageRouter(queue_size=queue_size, max_concurrent=max_concurrent)
    return router


async def test_message_router():
    """Test message router functionality"""
    print("🧪 Testing Message Router")
    print("=" * 40)
    
    # Create router
    router = create_message_router(queue_size=100, max_concurrent=5)
    
    # Test message counter
    message_count = {'ping': 0, 'status': 0, 'chat': 0}
    
    # Custom handlers for testing
    async def test_ping_handler(client_id: str, data: Dict[str, Any]):
        message_count['ping'] += 1
        print(f"  Ping from {client_id}")
        await asyncio.sleep(0.1)  # Simulate processing
    
    async def test_status_handler(client_id: str, data: Dict[str, Any]):
        message_count['status'] += 1
        print(f"  Status request from {client_id}")
        await asyncio.sleep(0.2)  # Simulate processing
    
    async def test_chat_handler(client_id: str, data: Dict[str, Any]):
        message_count['chat'] += 1
        message = data.get('message', '')
        print(f"  Chat from {client_id}: {message[:30]}...")
        await asyncio.sleep(0.3)  # Simulate processing
    
    # Register test handlers
    router.register_handler(MessageType.PING.value, test_ping_handler, priority=MessagePriority.HIGH)
    router.register_handler(MessageType.SYSTEM_STATUS_REQUEST.value, test_status_handler)
    router.register_handler(MessageType.CHAT_MESSAGE.value, test_chat_handler)
    
    # Start processing
    await router.start_processing()
    
    try:
        # Test messages
        test_messages = [
            (MessageType.PING.value, {'timestamp': datetime.now().isoformat()}),
            (MessageType.SYSTEM_STATUS_REQUEST.value, {'request_id': 'test_123'}),
            (MessageType.CHAT_MESSAGE.value, {'message': 'Hello, how is the system?'}),
            (MessageType.PING.value, {'timestamp': datetime.now().isoformat()}),
            (MessageType.CHAT_MESSAGE.value, {'message': 'What is the CPU usage?'}),
        ]
        
        print("\n📤 Sending test messages...")
        
        # Send messages
        for msg_type, data in test_messages:
            message_data = {
                'type': msg_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                message_id = await router.route_message('test_client', message_data)
                print(f"  Routed {msg_type}: {message_id}")
            except Exception as e:
                print(f"  Failed to route {msg_type}: {e}")
        
        # Wait for processing
        print("\n⏳ Processing messages...")
        await asyncio.sleep(2)
        
        # Get status
        status = await router.get_status()
        print(f"\n📊 Router Status:")
        print(f"  Queue size: {status['queue_stats']['total_size']}")
        print(f"  Processed: {status['processing_metrics']['processed_messages']}")
        print(f"  Success rate: {status['processing_metrics']['success_rate']:.1f}%")
        print(f"  Avg processing time: {status['processing_metrics']['average_processing_time_ms']:.1f}ms")
        
        print(f"\n📈 Message Counts:")
        print(f"  Ping: {message_count['ping']}")
        print(f"  Status: {message_count['status']}")
        print(f"  Chat: {message_count['chat']}")
        
        print("\n✅ Message router test completed!")
        
    finally:
        await router.stop_processing()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run test
    asyncio.run(test_message_router())