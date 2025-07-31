"""
Shared message types and enums for Mac Status PWA
"""
import uuid
from datetime import datetime
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    """Types of WebSocket messages"""
    # Client to Server
    SYSTEM_STATUS_REQUEST = "system_status_request"
    CHAT_MESSAGE = "chat_message"
    PING = "ping"
    
    # Server to Client
    SYSTEM_STATUS_UPDATE = "system_status_update"
    CHAT_RESPONSE = "chat_response"
    ERROR = "error"
    PONG = "pong"
    CONNECTION_STATUS = "connection_status"


class ConnectionStatus(Enum):
    """WebSocket connection status"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """Structure for WebSocket messages"""
    type: str
    data: Dict[str, Any]
    timestamp: str
    message_id: str = None
    
    def __post_init__(self):
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())