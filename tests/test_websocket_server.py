"""
Unit tests for WebSocket server
"""
import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

# Import the classes we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from websocket_server import (
    MacStatusWebSocketServer,
    WebSocketConnectionManager,
    WebSocketMessage,
    ClientConnection,
    MessageType,
    ConnectionStatus
)


class TestWebSocketMessage:
    """Test cases for WebSocketMessage"""
    
    def test_websocket_message_creation(self):
        """Test WebSocketMessage creation"""
        message = WebSocketMessage(
            type="test_type",
            data={"key": "value"},
            timestamp="2023-01-01T00:00:00"
        )
        
        assert message.type == "test_type"
        assert message.data == {"key": "value"}
        assert message.timestamp == "2023-01-01T00:00:00"
        assert message.message_id is not None  # Auto-generated
    
    def test_websocket_message_with_id(self):
        """Test WebSocketMessage with custom ID"""
        message = WebSocketMessage(
            type="test_type",
            data={},
            timestamp="2023-01-01T00:00:00",
            message_id="custom_id"
        )
        
        assert message.message_id == "custom_id"


class TestClientConnection:
    """Test cases for ClientConnection"""
    
    def test_client_connection_creation(self):
        """Test ClientConnection creation"""
        mock_websocket = Mock(spec=WebSocket)
        connection_time = datetime.now()
        
        connection = ClientConnection(
            client_id="test_client",
            websocket=mock_websocket,
            connected_at=connection_time,
            last_ping=connection_time
        )
        
        assert connection.client_id == "test_client"
        assert connection.websocket == mock_websocket
        assert connection.connected_at == connection_time
        assert connection.conversation_context is not None  # Auto-created


class TestWebSocketConnectionManager:
    """Test cases for WebSocketConnectionManager"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.manager = WebSocketConnectionManager()
    
    @pytest.mark.asyncio
    async def test_connect_client(self):
        """Test client connection"""
        mock_websocket = AsyncMock(spec=WebSocket)
        
        client_id = await self.manager.connect(mock_websocket)
        
        assert client_id in self.manager.active_connections
        assert len(self.manager.active_connections) == 1
        
        # Verify websocket.accept was called
        mock_websocket.accept.assert_called_once()
        
        # Verify connection status message was sent
        mock_websocket.send_text.assert_called()
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data['type'] == MessageType.CONNECTION_STATUS.value
    
    @pytest.mark.asyncio
    async def test_disconnect_client(self):
        """Test client disconnection"""
        mock_websocket = AsyncMock(spec=WebSocket)
        
        # Connect client first
        client_id = await self.manager.connect(mock_websocket)
        assert len(self.manager.active_connections) == 1
        
        # Disconnect client
        await self.manager.disconnect(client_id)
        assert len(self.manager.active_connections) == 0
    
    @pytest.mark.asyncio
    async def test_send_to_client(self):
        """Test sending message to specific client"""
        mock_websocket = AsyncMock(spec=WebSocket)
        
        # Connect client
        client_id = await self.manager.connect(mock_websocket)
        
        # Send message
        message = WebSocketMessage(
            type="test_message",
            data={"test": "data"},
            timestamp=datetime.now().isoformat()
        )
        
        await self.manager.send_to_client(client_id, message)
        
        # Verify message was sent (2 calls: connection status + our message)
        assert mock_websocket.send_text.call_count == 2
    
    @pytest.mark.asyncio
    async def test_send_to_nonexistent_client(self):
        """Test sending message to non-existent client"""
        message = WebSocketMessage(
            type="test_message",
            data={},
            timestamp=datetime.now().isoformat()
        )
        
        # Should not raise exception
        await self.manager.send_to_client("nonexistent_id", message)
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Test broadcasting message to all clients"""
        # Connect multiple clients
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        
        client_id1 = await self.manager.connect(mock_websocket1)
        client_id2 = await self.manager.connect(mock_websocket2)
        
        # Broadcast message
        message = WebSocketMessage(
            type="broadcast_test",
            data={"broadcast": True},
            timestamp=datetime.now().isoformat()
        )
        
        await self.manager.broadcast(message)
        
        # Both clients should receive the message
        assert mock_websocket1.send_text.call_count == 2  # connection + broadcast
        assert mock_websocket2.send_text.call_count == 2  # connection + broadcast
    
    @pytest.mark.asyncio
    async def test_broadcast_with_exclusion(self):
        """Test broadcasting with client exclusion"""
        # Connect multiple clients
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        
        client_id1 = await self.manager.connect(mock_websocket1)
        client_id2 = await self.manager.connect(mock_websocket2)
        
        # Broadcast message excluding client1
        message = WebSocketMessage(
            type="broadcast_test",
            data={},
            timestamp=datetime.now().isoformat()
        )
        
        await self.manager.broadcast(message, exclude_client=client_id1)
        
        # Only client2 should receive the broadcast message
        assert mock_websocket1.send_text.call_count == 1  # only connection message
        assert mock_websocket2.send_text.call_count == 2  # connection + broadcast
    
    def test_get_connection_stats(self):
        """Test getting connection statistics"""
        stats = self.manager.get_connection_stats()
        
        assert 'total_connections' in stats
        assert 'connections' in stats
        assert 'heartbeat_interval' in stats
        assert stats['total_connections'] == 0
        assert len(stats['connections']) == 0


class TestMacStatusWebSocketServer:
    """Test cases for MacStatusWebSocketServer"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Mock the backend components to avoid initialization issues
        with patch('websocket_server.SystemMonitor'), \
             patch('websocket_server.ELYZAModelInterface'), \
             patch('websocket_server.JapanesePromptGenerator'), \
             patch('websocket_server.ResponseOptimizer'):
            
            self.server = MacStatusWebSocketServer()
    
    def test_server_initialization(self):
        """Test server initialization"""
        assert self.server.app is not None
        assert self.server.connection_manager is not None
        assert hasattr(self.server, 'system_monitor')
        assert hasattr(self.server, 'model_interface')
    
    def test_fastapi_app_creation(self):
        """Test FastAPI app creation"""
        # Test that routes are set up
        routes = [route.path for route in self.server.app.routes]
        
        assert "/" in routes
        assert "/status" in routes
        assert "/health" in routes
        assert "/ws" in [route.path for route in self.server.app.routes if hasattr(route, 'path')]
    
    @pytest.mark.asyncio
    async def test_handle_ping_message(self):
        """Test handling ping message"""
        # Mock connection
        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = await self.server.connection_manager.connect(mock_websocket)
        
        # Handle ping
        await self.server._handle_ping(client_id, {'timestamp': datetime.now().isoformat()})
        
        # Should update last_ping time
        connection = self.server.connection_manager.active_connections[client_id]
        assert connection.last_ping is not None
    
    @pytest.mark.asyncio
    async def test_handle_system_status_request(self):
        """Test handling system status request"""
        # Mock system monitor
        mock_status = Mock()
        mock_status_dict = {'cpu_percent': 50.0, 'memory_percent': 60.0}
        
        self.server.system_monitor.get_system_info = AsyncMock(return_value=mock_status)
        self.server.system_monitor.to_dict = Mock(return_value=mock_status_dict)
        
        # Mock connection
        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = await self.server.connection_manager.connect(mock_websocket)
        
        # Handle request
        await self.server._handle_system_status_request(client_id, {'request_id': 'test_123'})
        
        # Verify system monitor was called
        self.server.system_monitor.get_system_info.assert_called_once()
        self.server.system_monitor.to_dict.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_chat_message(self):
        """Test handling chat message"""
        # Mock model interface
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_response.processing_time_ms = 100.0
        mock_response.timestamp = datetime.now()
        
        self.server.model_interface.generate_system_response = AsyncMock(return_value=mock_response)
        self.server.system_monitor.get_system_info = AsyncMock(return_value=Mock())
        self.server.system_monitor.to_dict = Mock(return_value={})
        
        # Mock connection
        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = await self.server.connection_manager.connect(mock_websocket)
        
        # Handle chat message
        await self.server._handle_chat_message(client_id, {
            'message': 'Hello, how is the system?',
            'request_id': 'chat_123'
        })
        
        # Verify model was called
        self.server.model_interface.generate_system_response.assert_called_once()
        
        # Verify conversation history was updated
        connection = self.server.connection_manager.active_connections[client_id]
        assert len(connection.conversation_context.conversation_history) == 2  # user + assistant
    
    @pytest.mark.asyncio
    async def test_handle_empty_chat_message(self):
        """Test handling empty chat message"""
        # Mock connection
        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = await self.server.connection_manager.connect(mock_websocket)
        
        # Handle empty message
        await self.server._handle_chat_message(client_id, {'message': ''})
        
        # Should send error message
        # Verify error was sent (connection message + error message)
        assert mock_websocket.send_text.call_count == 2
    
    @pytest.mark.asyncio
    async def test_send_error(self):
        """Test sending error message"""
        # Mock connection
        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = await self.server.connection_manager.connect(mock_websocket)
        
        # Send error
        await self.server._send_error(client_id, "Test error message")
        
        # Verify error message was sent
        assert mock_websocket.send_text.call_count == 2  # connection + error
        
        # Check error message content
        error_call = mock_websocket.send_text.call_args_list[1]
        error_data = json.loads(error_call[0][0])
        assert error_data['type'] == MessageType.ERROR.value
        assert error_data['data']['error'] == "Test error message"
    
    @pytest.mark.asyncio
    async def test_system_status_callback(self):
        """Test system status callback for broadcasting"""
        # Mock system status
        mock_status = Mock()
        mock_status_dict = {'cpu_percent': 75.0}
        
        self.server.system_monitor.to_dict = Mock(return_value=mock_status_dict)
        
        # Connect clients
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        
        await self.server.connection_manager.connect(mock_websocket1)
        await self.server.connection_manager.connect(mock_websocket2)
        
        # Trigger callback
        alerts = [{'type': 'cpu_high', 'message': 'High CPU usage'}]
        changes = [{'type': 'cpu_change', 'change': 10.0}]
        
        await self.server._system_status_callback(mock_status, alerts, changes)
        
        # Both clients should receive the broadcast
        assert mock_websocket1.send_text.call_count == 2  # connection + status update
        assert mock_websocket2.send_text.call_count == 2  # connection + status update


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality"""
    
    @pytest.mark.asyncio
    async def test_client_message_flow(self):
        """Test complete client message flow"""
        # This would require a more complex setup with actual WebSocket connections
        # For now, we test the message handling logic
        
        with patch('websocket_server.SystemMonitor'), \
             patch('websocket_server.ELYZAModelInterface'), \
             patch('websocket_server.JapanesePromptGenerator'), \
             patch('websocket_server.ResponseOptimizer'):
            
            server = MacStatusWebSocketServer()
            
            # Mock connection
            mock_websocket = AsyncMock(spec=WebSocket)
            client_id = await server.connection_manager.connect(mock_websocket)
            
            # Test different message types
            test_messages = [
                {
                    'type': MessageType.PING.value,
                    'data': {'timestamp': datetime.now().isoformat()}
                },
                {
                    'type': MessageType.SYSTEM_STATUS_REQUEST.value,
                    'data': {'request_id': 'status_123'}
                }
            ]
            
            for message in test_messages:
                await server._handle_client_message(client_id, message)
            
            # Verify messages were processed (no exceptions raised)
            assert client_id in server.connection_manager.active_connections
    
    def test_message_type_enum(self):
        """Test MessageType enum values"""
        assert MessageType.PING.value == "ping"
        assert MessageType.PONG.value == "pong"
        assert MessageType.CHAT_MESSAGE.value == "chat_message"
        assert MessageType.CHAT_RESPONSE.value == "chat_response"
        assert MessageType.SYSTEM_STATUS_REQUEST.value == "system_status_request"
        assert MessageType.SYSTEM_STATUS_UPDATE.value == "system_status_update"
        assert MessageType.ERROR.value == "error"
        assert MessageType.CONNECTION_STATUS.value == "connection_status"
    
    def test_connection_status_enum(self):
        """Test ConnectionStatus enum values"""
        assert ConnectionStatus.CONNECTING.value == "connecting"
        assert ConnectionStatus.CONNECTED.value == "connected"
        assert ConnectionStatus.DISCONNECTED.value == "disconnected"
        assert ConnectionStatus.ERROR.value == "error"


class TestWebSocketServerHTTPEndpoints:
    """Test HTTP endpoints of the WebSocket server"""
    
    def setup_method(self):
        """Setup test client"""
        with patch('websocket_server.SystemMonitor'), \
             patch('websocket_server.ELYZAModelInterface'), \
             patch('websocket_server.JapanesePromptGenerator'), \
             patch('websocket_server.ResponseOptimizer'):
            
            server = MacStatusWebSocketServer()
            self.client = TestClient(server.app)
    
    def test_index_endpoint(self):
        """Test index endpoint"""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "Mac Status PWA WebSocket Server" in response.text
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_status_endpoint(self):
        """Test status endpoint"""
        response = self.client.get("/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data['server'] == 'Mac Status PWA WebSocket Server'
        assert data['status'] == 'running'
        assert 'connections' in data
        assert 'system_monitor' in data
        assert 'model' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])