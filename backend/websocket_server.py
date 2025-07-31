"""
FastAPI WebSocket Server for Mac Status PWA
Handles real-time communication between frontend and backend
"""
import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Import our backend modules
import sys
import os
sys.path.append(os.path.dirname(__file__))

from system_monitor import SystemMonitor, SystemStatus
from elyza_model import ELYZAModelInterface, create_default_config
from prompt_generator import JapanesePromptGenerator, ConversationContext, PromptStyle
from response_optimizer import ResponseOptimizer, OptimizationStrategy
from message_types import MessageType, ConnectionStatus, WebSocketMessage
from message_router import MessageRouter, MessagePriority

# Import error handling
from error_handler import (
    handle_websocket_error, 
    handle_system_monitor_error,
    handle_model_error,
    execute_with_fallback, 
    ErrorCategory, 
    global_fallback_manager,
    global_error_handler
)

# Import connection management
from connection_manager import (
    ConnectionManager,
    ConnectionState,
    ReconnectionConfig,
    global_connection_manager,
    cache_system_status,
    get_offline_system_status,
    get_offline_chat_response,
    is_offline
)


@dataclass
class ClientConnection:
    """Information about a connected client"""
    client_id: str
    websocket: WebSocket
    connected_at: datetime
    last_ping: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    conversation_context: Optional[ConversationContext] = None
    
    def __post_init__(self):
        if self.conversation_context is None:
            self.conversation_context = ConversationContext()


class WebSocketConnectionManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self):
        """Initialize connection manager"""
        self.active_connections: Dict[str, ClientConnection] = {}
        self.logger = logging.getLogger(__name__)
        self._heartbeat_interval = 30  # seconds
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # 接続管理機能を統合
        self.connection_manager = global_connection_manager
        
    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None) -> str:
        """
        Accept new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            client_info: Optional client information
            
        Returns:
            Client ID
        """
        await websocket.accept()
        
        client_id = str(uuid.uuid4())
        client_connection = ClientConnection(
            client_id=client_id,
            websocket=websocket,
            connected_at=datetime.now(),
            last_ping=datetime.now(),
            user_agent=client_info.get('user_agent') if client_info else None,
            ip_address=client_info.get('ip_address') if client_info else None
        )
        
        self.active_connections[client_id] = client_connection
        
        # 接続状態を更新
        if len(self.active_connections) == 1:
            self.connection_manager.set_state(ConnectionState.CONNECTED, "first_client_connected")
        
        # Send connection confirmation
        await self.send_to_client(client_id, WebSocketMessage(
            type=MessageType.CONNECTION_STATUS.value,
            data={
                'status': ConnectionStatus.CONNECTED.value,
                'client_id': client_id,
                'server_time': datetime.now().isoformat(),
                'connection_state': self.connection_manager.get_state().value
            },
            timestamp=datetime.now().isoformat()
        ))
        
        # Start heartbeat if this is the first connection
        if len(self.active_connections) == 1 and not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        self.logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        return client_id
    
    async def disconnect(self, client_id: str):
        """
        Disconnect client
        
        Args:
            client_id: Client identifier
        """
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            
            try:
                # Send disconnect notification
                await self.send_to_client(client_id, WebSocketMessage(
                    type=MessageType.CONNECTION_STATUS.value,
                    data={
                        'status': ConnectionStatus.DISCONNECTED.value,
                        'reason': 'Server initiated disconnect'
                    },
                    timestamp=datetime.now().isoformat()
                ))
            except:
                pass  # Connection might already be closed
            
            del self.active_connections[client_id]
            self.logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
            
            # 接続状態を更新
            if len(self.active_connections) == 0:
                self.connection_manager.set_state(ConnectionState.DISCONNECTED, "all_clients_disconnected")
            
            # Stop heartbeat if no connections remain
            if len(self.active_connections) == 0 and self._heartbeat_task:
                self._heartbeat_task.cancel()
                self._heartbeat_task = None
    
    async def send_to_client(self, client_id: str, message: WebSocketMessage):
        """
        Send message to specific client
        
        Args:
            client_id: Target client ID
            message: Message to send
        """
        if client_id not in self.active_connections:
            self.logger.warning(f"Attempted to send message to non-existent client: {client_id}")
            return
        
        connection = self.active_connections[client_id]
        
        try:
            message_dict = asdict(message)
            await connection.websocket.send_text(json.dumps(message_dict))
            
        except Exception as e:
            self.logger.error(f"Error sending message to client {client_id}: {e}")
            # Remove disconnected client
            await self.disconnect(client_id)
    
    async def broadcast(self, message: WebSocketMessage, exclude_client: str = None):
        """
        Broadcast message to all connected clients
        
        Args:
            message: Message to broadcast
            exclude_client: Optional client ID to exclude from broadcast
        """
        disconnected_clients = []
        
        for client_id, connection in self.active_connections.items():
            if exclude_client and client_id == exclude_client:
                continue
                
            try:
                message_dict = asdict(message)
                await connection.websocket.send_text(json.dumps(message_dict))
                
            except Exception as e:
                self.logger.error(f"Error broadcasting to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
    
    async def _heartbeat_loop(self):
        """Heartbeat loop to check connection health"""
        while self.active_connections:
            try:
                current_time = datetime.now()
                disconnected_clients = []
                
                for client_id, connection in self.active_connections.items():
                    # Check if client hasn't responded to ping in too long
                    time_since_ping = (current_time - connection.last_ping).total_seconds()
                    
                    if time_since_ping > self._heartbeat_interval * 2:
                        # Client is unresponsive
                        disconnected_clients.append(client_id)
                    else:
                        # Send ping
                        try:
                            await self.send_to_client(client_id, WebSocketMessage(
                                type=MessageType.PING.value,
                                data={'timestamp': current_time.isoformat()},
                                timestamp=current_time.isoformat()
                            ))
                        except:
                            disconnected_clients.append(client_id)
                
                # Clean up unresponsive clients
                for client_id in disconnected_clients:
                    await self.disconnect(client_id)
                
                await asyncio.sleep(self._heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        current_time = datetime.now()
        
        connections_info = []
        for client_id, connection in self.active_connections.items():
            connection_duration = (current_time - connection.connected_at).total_seconds()
            last_ping_ago = (current_time - connection.last_ping).total_seconds()
            
            connections_info.append({
                'client_id': client_id,
                'connected_at': connection.connected_at.isoformat(),
                'connection_duration_seconds': connection_duration,
                'last_ping_seconds_ago': last_ping_ago,
                'user_agent': connection.user_agent,
                'ip_address': connection.ip_address
            })
        
        return {
            'total_connections': len(self.active_connections),
            'connections': connections_info,
            'heartbeat_interval': self._heartbeat_interval
        }


class MacStatusWebSocketServer:
    """Main WebSocket server for Mac Status PWA"""
    
    def __init__(self):
        """Initialize the WebSocket server"""
        self.app = FastAPI(title="Mac Status PWA WebSocket Server")
        self.connection_manager = WebSocketConnectionManager()
        self.logger = logging.getLogger(__name__)
        
        # Initialize backend components
        self.system_monitor = SystemMonitor(update_interval=5.0)
        self.model_interface = ELYZAModelInterface(create_default_config())
        self.prompt_generator = JapanesePromptGenerator()
        self.response_optimizer = ResponseOptimizer()
        self.message_router = MessageRouter(queue_size=1000, max_concurrent=10)
        
        # Real-time broadcasting configuration
        self.broadcast_config = {
            'min_broadcast_interval': 2.0,  # Minimum seconds between broadcasts
            'max_broadcast_interval': 30.0,  # Maximum seconds without broadcast
            'change_threshold': {
                'cpu_percent': 5.0,      # Broadcast if CPU changes by 5%
                'memory_percent': 3.0,   # Broadcast if memory changes by 3%
                'disk_percent': 1.0,     # Broadcast if disk changes by 1%
                'process_change': True   # Broadcast on top process changes
            },
            'always_broadcast_alerts': True,  # Always broadcast alerts immediately
            'throttle_identical_updates': True  # Prevent identical consecutive updates
        }
        
        # Broadcasting state tracking
        self.last_broadcast_time = 0.0
        self.last_broadcast_data = None
        self.pending_broadcast = False
        self.broadcast_queue = asyncio.Queue(maxsize=100)
        self.broadcast_task = None
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
        
        # Setup message routing
        self._setup_message_routing()
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """Main WebSocket endpoint"""
            client_info = {
                'user_agent': websocket.headers.get('user-agent'),
                'ip_address': websocket.client.host if websocket.client else None
            }
            
            client_id = await self.connection_manager.connect(websocket, client_info)
            
            try:
                while True:
                    # Receive message from client
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Route message through message router
                    try:
                        # Determine priority based on message type
                        priority = self._get_message_priority(message_data.get('type'))
                        
                        # Route message
                        await self.message_router.route_message(
                            client_id=client_id,
                            message_data=message_data,
                            priority=priority
                        )
                    except Exception as e:
                        self.logger.error(f"Error routing message: {e}")
                        await self._send_error(client_id, "Failed to process message")
                    
            except WebSocketDisconnect:
                await self.connection_manager.disconnect(client_id)
            except Exception as e:
                self.logger.error(f"WebSocket error for client {client_id}: {e}")
                await self.connection_manager.disconnect(client_id)
        
        @self.app.get("/")
        async def get_index():
            """Serve the main PWA page"""
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Mac Status PWA</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
            </head>
            <body>
                <h1>Mac Status PWA WebSocket Server</h1>
                <p>WebSocket endpoint: <code>ws://localhost:8000/ws</code></p>
                <p>Status endpoint: <code>/status</code></p>
                <p>Frontend files should be served from the frontend directory.</p>
            </body>
            </html>
            """)
        
        @self.app.get("/status")
        async def get_status():
            """Get server status"""
            return {
                'server': 'Mac Status PWA WebSocket Server',
                'status': 'running',
                'timestamp': datetime.now().isoformat(),
                'connections': self.connection_manager.get_connection_stats(),
                'system_monitor': {
                    'is_monitoring': self.system_monitor._is_monitoring,
                    'update_interval': self.system_monitor.update_interval
                },
                'model': self.model_interface.get_model_status(),
                'message_router': await self.message_router.get_status()
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
    
    def _setup_message_routing(self):
        """Setup message routing handlers"""
        # Register handlers with the message router
        self.message_router.register_handler(
            MessageType.PING.value,
            self._handle_ping_routed,
            priority=MessagePriority.HIGH,
            timeout_seconds=5.0
        )
        
        self.message_router.register_handler(
            MessageType.SYSTEM_STATUS_REQUEST.value,
            self._handle_system_status_routed,
            priority=MessagePriority.NORMAL,
            timeout_seconds=10.0
        )
        
        self.message_router.register_handler(
            MessageType.CHAT_MESSAGE.value,
            self._handle_chat_routed,
            priority=MessagePriority.NORMAL,
            timeout_seconds=30.0
        )
    
    def _get_message_priority(self, message_type: str) -> MessagePriority:
        """Determine message priority based on type"""
        priority_map = {
            MessageType.PING.value: MessagePriority.HIGH,
            MessageType.PONG.value: MessagePriority.HIGH,
            MessageType.SYSTEM_STATUS_REQUEST.value: MessagePriority.NORMAL,
            MessageType.CHAT_MESSAGE.value: MessagePriority.NORMAL,
            MessageType.ERROR.value: MessagePriority.LOW
        }
        
        return priority_map.get(message_type, MessagePriority.NORMAL)
    
    async def _handle_client_message(self, client_id: str, message_data: Dict[str, Any]):
        """
        Handle incoming client message
        
        Args:
            client_id: Client identifier
            message_data: Message data from client
        """
        try:
            message_type = message_data.get('type')
            data = message_data.get('data', {})
            
            if message_type == MessageType.PING.value:
                await self._handle_ping(client_id, data)
            
            elif message_type == MessageType.SYSTEM_STATUS_REQUEST.value:
                await self._handle_system_status_request(client_id, data)
            
            elif message_type == MessageType.CHAT_MESSAGE.value:
                await self._handle_chat_message(client_id, data)
            
            else:
                await self._send_error(client_id, f"Unknown message type: {message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message from client {client_id}: {e}")
            await self._send_error(client_id, "Internal server error")
    
    async def _handle_ping(self, client_id: str, data: Dict[str, Any]):
        """Handle ping message"""
        if client_id in self.connection_manager.active_connections:
            connection = self.connection_manager.active_connections[client_id]
            connection.last_ping = datetime.now()
            
            # Send pong response
            await self.connection_manager.send_to_client(client_id, WebSocketMessage(
                type=MessageType.PONG.value,
                data={'timestamp': datetime.now().isoformat()},
                timestamp=datetime.now().isoformat()
            ))
    
    async def _handle_system_status_request(self, client_id: str, data: Dict[str, Any]):
        """Handle system status request"""
        try:
            # Get current system status
            system_status = await self.system_monitor.get_system_info()
            
            # Convert to dictionary for JSON serialization
            status_dict = self.system_monitor.to_dict(system_status)
            
            # Send response
            await self.connection_manager.send_to_client(client_id, WebSocketMessage(
                type=MessageType.SYSTEM_STATUS_UPDATE.value,
                data={
                    'system_status': status_dict,
                    'request_id': data.get('request_id')
                },
                timestamp=datetime.now().isoformat()
            ))
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            await self._send_error(client_id, "Failed to get system status")
    
    async def _handle_chat_message(self, client_id: str, data: Dict[str, Any]):
        """Handle chat message from client"""
        try:
            user_message = data.get('message', '')
            if not user_message.strip():
                await self._send_error(client_id, "Empty message")
                return
            
            # Get client connection for conversation context
            connection = self.connection_manager.active_connections.get(client_id)
            if not connection:
                await self._send_error(client_id, "Client not found")
                return
            
            # Get current system status
            system_status = await self.system_monitor.get_system_info()
            system_data = self.system_monitor.to_dict(system_status)
            
            # Generate response using the model
            try:
                response = await self.model_interface.generate_system_response(
                    user_message=user_message,
                    system_data=system_data,
                    conversation_history=connection.conversation_context.conversation_history
                )
                
                if response:
                    # Update conversation history
                    connection.conversation_context.conversation_history.extend([
                        {'role': 'user', 'content': user_message},
                        {'role': 'assistant', 'content': response.content}
                    ])
                    
                    # Keep only recent history (last 10 exchanges = 20 messages)
                    if len(connection.conversation_context.conversation_history) > 20:
                        connection.conversation_context.conversation_history = \
                            connection.conversation_context.conversation_history[-20:]
                    
                    # Send response
                    await self.connection_manager.send_to_client(client_id, WebSocketMessage(
                        type=MessageType.CHAT_RESPONSE.value,
                        data={
                            'message': response.content,
                            'processing_time_ms': response.processing_time_ms,
                            'timestamp': response.timestamp.isoformat(),
                            'request_id': data.get('request_id')
                        },
                        timestamp=datetime.now().isoformat()
                    ))
                    
                else:
                    await self._send_error(client_id, "Failed to generate response")
                    
            except Exception as e:
                self.logger.error(f"Error generating chat response: {e}")
                await self._send_error(client_id, "Chat service temporarily unavailable")
                
        except Exception as e:
            self.logger.error(f"Error handling chat message: {e}")
            await self._send_error(client_id, "Failed to process chat message")
    
    async def _send_error(self, client_id: str, error_message: str):
        """Send error message to client"""
        await self.connection_manager.send_to_client(client_id, WebSocketMessage(
            type=MessageType.ERROR.value,
            data={'error': error_message},
            timestamp=datetime.now().isoformat()
        ))
    
    # Routed message handlers (called by message router)
    async def _handle_ping_routed(self, client_id: str, data: Dict[str, Any]):
        """Handle ping message through router"""
        await self._handle_ping(client_id, data)
    
    async def _handle_system_status_routed(self, client_id: str, data: Dict[str, Any]):
        """Handle system status request through router"""
        await self._handle_system_status_request(client_id, data)
    
    async def _handle_chat_routed(self, client_id: str, data: Dict[str, Any]):
        """Handle chat message through router"""
        await self._handle_chat_message(client_id, data)
    
    async def start_background_tasks(self):
        """Start background monitoring tasks"""
        # Start system monitoring
        await self.system_monitor.start_monitoring()
        
        # Add monitoring callback for real-time updates
        self.system_monitor.add_callback(self._system_status_callback)
        
        # Start message router
        await self.message_router.start_processing()
        
        # Initialize model (if available)
        try:
            await self.model_interface.initialize_model()
        except Exception as e:
            self.logger.warning(f"Model initialization failed: {e}")
    
    async def stop_background_tasks(self):
        """Stop background tasks"""
        await self.system_monitor.stop_monitoring()
        await self.message_router.stop_processing()
        await self.model_interface.cleanup()
        
        if self.connection_manager._heartbeat_task:
            self.connection_manager._heartbeat_task.cancel()
    
    async def _system_status_callback(self, status: SystemStatus, alerts: List[Dict], changes: List[Dict]):
        """Enhanced callback for intelligent system status broadcasting"""
        try:
            current_time = time.time()
            
            # Convert status to dictionary
            status_dict = self.system_monitor.to_dict(status)
            
            # Determine if we should broadcast this update
            should_broadcast = await self._should_broadcast_update(
                status_dict, alerts, changes, current_time
            )
            
            if should_broadcast:
                # Create broadcast data
                broadcast_data = {
                    'system_status': status_dict,
                    'alerts': alerts,
                    'changes': changes,
                    'auto_update': True,
                    'broadcast_reason': self._get_broadcast_reason(alerts, changes, current_time)
                }
                
                # Queue broadcast for processing
                try:
                    await self.broadcast_queue.put_nowait({
                        'type': MessageType.SYSTEM_STATUS_UPDATE.value,
                        'data': broadcast_data,
                        'timestamp': datetime.now().isoformat(),
                        'priority': 'high' if alerts else 'normal'
                    })
                except asyncio.QueueFull:
                    self.logger.warning("Broadcast queue full, dropping update")
                
                # Update tracking
                self.last_broadcast_time = current_time
                self.last_broadcast_data = status_dict
            
        except Exception as e:
            self.logger.error(f"Error in system status callback: {e}")
    
    async def _should_broadcast_update(self, status_dict: Dict, alerts: List[Dict], 
                                     changes: List[Dict], current_time: float) -> bool:
        """
        Determine if system status update should be broadcast
        
        Args:
            status_dict: Current system status
            alerts: System alerts
            changes: Detected changes
            current_time: Current timestamp
            
        Returns:
            True if update should be broadcast
        """
        # Always broadcast if there are alerts
        if alerts and self.broadcast_config['always_broadcast_alerts']:
            self.logger.debug("Broadcasting due to alerts")
            return True
        
        # Check minimum broadcast interval
        time_since_last = current_time - self.last_broadcast_time
        if time_since_last < self.broadcast_config['min_broadcast_interval']:
            self.logger.debug(f"Skipping broadcast - too soon ({time_since_last:.1f}s)")
            return False
        
        # Force broadcast if maximum interval exceeded
        if time_since_last > self.broadcast_config['max_broadcast_interval']:
            self.logger.debug("Broadcasting due to max interval exceeded")
            return True
        
        # Check for significant changes
        if self._has_significant_changes(status_dict, changes):
            self.logger.debug("Broadcasting due to significant changes")
            return True
        
        # Check for process changes
        if changes and self.broadcast_config['change_threshold']['process_change']:
            for change in changes:
                if change.get('type') == 'top_process_change':
                    self.logger.debug("Broadcasting due to top process change")
                    return True
        
        # Don't broadcast if no significant changes
        return False
    
    def _has_significant_changes(self, current_status: Dict, changes: List[Dict]) -> bool:
        """
        Check if there are significant changes worth broadcasting
        
        Args:
            current_status: Current system status
            changes: Detected changes
            
        Returns:
            True if changes are significant
        """
        if not self.last_broadcast_data:
            return True  # First broadcast
        
        thresholds = self.broadcast_config['change_threshold']
        
        # Check CPU change
        cpu_change = abs(current_status.get('cpu_percent', 0) - 
                        self.last_broadcast_data.get('cpu_percent', 0))
        if cpu_change >= thresholds['cpu_percent']:
            return True
        
        # Check memory change
        memory_change = abs(current_status.get('memory_percent', 0) - 
                           self.last_broadcast_data.get('memory_percent', 0))
        if memory_change >= thresholds['memory_percent']:
            return True
        
        # Check disk change
        disk_change = abs(current_status.get('disk_percent', 0) - 
                         self.last_broadcast_data.get('disk_percent', 0))
        if disk_change >= thresholds['disk_percent']:
            return True
        
        return False
    
    def _get_broadcast_reason(self, alerts: List[Dict], changes: List[Dict], 
                            current_time: float) -> str:
        """
        Get reason for broadcasting update
        
        Args:
            alerts: System alerts
            changes: Detected changes
            current_time: Current timestamp
            
        Returns:
            Reason string
        """
        if alerts:
            return f"alerts ({len(alerts)} alert{'s' if len(alerts) > 1 else ''})"
        
        if changes:
            change_types = [change.get('type', 'unknown') for change in changes]
            return f"changes ({', '.join(set(change_types))})"
        
        time_since_last = current_time - self.last_broadcast_time
        if time_since_last > self.broadcast_config['max_broadcast_interval']:
            return "periodic update"
        
        return "significant change"


# Global server instance
server_instance: Optional[MacStatusWebSocketServer] = None


async def create_server() -> MacStatusWebSocketServer:
    """Create and initialize server instance"""
    global server_instance
    
    if server_instance is None:
        server_instance = MacStatusWebSocketServer()
        await server_instance.start_background_tasks()
    
    return server_instance


async def shutdown_server():
    """Shutdown server and cleanup"""
    global server_instance
    
    if server_instance:
        await server_instance.stop_background_tasks()
        server_instance = None


# FastAPI lifespan events
async def startup_event():
    """Server startup event"""
    await create_server()


async def shutdown_event():
    """Server shutdown event"""
    await shutdown_server()


def run_server(host: str = "127.0.0.1", port: int = 8000, debug: bool = False):
    """
    Run the WebSocket server
    
    Args:
        host: Host address
        port: Port number
        debug: Debug mode
    """
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server directly
    async def run_app():
        server = await create_server()
        config = uvicorn.Config(
            app=server.app,
            host=host,
            port=port,
            log_level="debug" if debug else "info"
        )
        server_instance = uvicorn.Server(config)
        await server_instance.serve()
    
    # Run the server
    asyncio.run(run_app())


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Mac Status PWA WebSocket Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Mac Status PWA WebSocket Server")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Debug: {args.debug}")
    print(f"   WebSocket URL: ws://{args.host}:{args.port}/ws")
    
    run_server(host=args.host, port=args.port, debug=args.debug)