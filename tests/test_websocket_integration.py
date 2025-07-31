"""
WebSocket通信の統合テスト
WebSocketサーバーとクライアント間の通信を包括的にテスト
"""
import pytest
import asyncio
import json
import websockets
import time
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# Import backend components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from websocket_server import MacStatusWebSocketServer
from connection_manager import ConnectionManager
from message_router import MessageRouter
from system_monitor import SystemMonitor
from elyza_model import ELYZAModelInterface, ModelConfig
from chat_context_manager import ChatContextManager


class TestWebSocketIntegration:
    """WebSocket通信の統合テスト"""
    
    def setup_method(self):
        """各テストメソッドのセットアップ"""
        self.server_port = 8001  # テスト用ポート
        self.server_uri = f"ws://localhost:{self.server_port}/ws"
        self.server = None
        self.server_task = None
        
        # モックコンポーネント
        self.mock_system_monitor = Mock(spec=SystemMonitor)
        self.mock_model_interface = Mock(spec=ELYZAModelInterface)
        self.mock_chat_context = Mock(spec=ChatContextManager)
        
        # サンプルシステムデータ
        self.sample_system_data = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': 45.2,
            'memory_percent': 68.5,
            'disk_percent': 72.1,
            'top_processes': [
                {'name': 'Google Chrome', 'cpu_percent': 25.3, 'memory_percent': 18.2},
                {'name': 'Xcode', 'cpu_percent': 12.8, 'memory_percent': 15.6}
            ]
        }
    
    async def start_test_server(self):
        """テスト用WebSocketサーバーを起動"""
        # モックの設定
        self.mock_system_monitor.get_system_info.return_value = self.sample_system_data
        self.mock_model_interface.generate_system_response = AsyncMock(
            return_value=Mock(
                content="システムは正常に動作しています。CPUは45.2%、メモリは68.5%使用中です。",
                processing_time_ms=150.0
            )
        )
        
        # WebSocketサーバーの作成
        connection_manager = ConnectionManager()
        message_router = MessageRouter(
            system_monitor=self.mock_system_monitor,
            model_interface=self.mock_model_interface,
            chat_context_manager=self.mock_chat_context
        )
        
        self.server = MacStatusWebSocketServer()
        
        # バックグラウンドタスクを開始
        await self.server.start_background_tasks()
        
        # サーバーを非同期で起動
        import uvicorn
        config = uvicorn.Config(self.server.app, host="127.0.0.1", port=self.server_port, log_level="error")
        server = uvicorn.Server(config)
        self.server_task = asyncio.create_task(server.serve())
        await asyncio.sleep(1.0)  # サーバー起動待機
    
    async def stop_test_server(self):
        """テスト用サーバーを停止"""
        if self.server:
            await self.server.stop_background_tasks()
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self):
        """WebSocket接続のライフサイクルテスト"""
        await self.start_test_server()
        
        try:
            # 接続テスト
            websocket = await websockets.connect(self.server_uri)
            
            # 接続確認メッセージを受信
            welcome_message = await websocket.recv()
            welcome_data = json.loads(welcome_message)
            
            assert welcome_data['type'] == 'connection_status'
            assert welcome_data['data']['status'] == 'connected'
            assert 'client_id' in welcome_data['data']
            
            # 正常切断
            await websocket.close()
            
        finally:
            await self.stop_test_server()
    
    @pytest.mark.asyncio
    async def test_system_status_request_response(self):
        """システムステータス要求・応答テスト"""
        await self.start_test_server()
        
        try:
            websocket = await websockets.connect(self.server_uri)
            
            # 接続確認メッセージをスキップ
            await websocket.recv()
            
            # システムステータス要求
            request = {
                'type': 'system_status_request',
                'data': {'request_id': 'test_status_001'},
                'timestamp': datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(request))
            
            # 応答を受信
            response_message = await websocket.recv()
            response_data = json.loads(response_message)
            
            # 応答検証
            assert response_data['type'] == 'system_status_update'
            assert 'system_status' in response_data['data']
            assert response_data['data']['system_status']['cpu_percent'] == 45.2
            assert response_data['data']['system_status']['memory_percent'] == 68.5
            
            await websocket.close()
            
        finally:
            await self.stop_test_server()
    
    @pytest.mark.asyncio
    async def test_chat_message_processing(self):
        """チャットメッセージ処理テスト"""
        await self.start_test_server()
        
        try:
            websocket = await websockets.connect(self.server_uri)
            
            # 接続確認メッセージをスキップ
            await websocket.recv()
            
            # チャットメッセージ送信
            chat_request = {
                'type': 'chat_message',
                'data': {
                    'message': 'システムの状況を教えてください',
                    'request_id': 'test_chat_001'
                },
                'timestamp': datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(chat_request))
            
            # チャット応答を受信
            response_message = await websocket.recv()
            response_data = json.loads(response_message)
            
            # 応答検証
            assert response_data['type'] == 'chat_response'
            assert 'message' in response_data['data']
            assert 'processing_time_ms' in response_data['data']
            assert response_data['data']['request_id'] == 'test_chat_001'
            assert 'システム' in response_data['data']['message']
            
            await websocket.close()
            
        finally:
            await self.stop_test_server()
    
    @pytest.mark.asyncio
    async def test_multiple_client_connections(self):
        """複数クライアント接続テスト"""
        await self.start_test_server()
        
        try:
            # 3つのクライアント接続を作成
            clients = []
            for i in range(3):
                client = await websockets.connect(self.server_uri)
                clients.append(client)
                
                # 接続確認メッセージを受信
                welcome_message = await client.recv()
                welcome_data = json.loads(welcome_message)
                assert welcome_data['type'] == 'connection_status'
            
            # 各クライアントからメッセージ送信
            for i, client in enumerate(clients):
                request = {
                    'type': 'system_status_request',
                    'data': {'request_id': f'multi_client_{i}'},
                    'timestamp': datetime.now().isoformat()
                }
                await client.send(json.dumps(request))
            
            # 各クライアントで応答を受信
            for i, client in enumerate(clients):
                response_message = await client.recv()
                response_data = json.loads(response_message)
                assert response_data['type'] == 'system_status_update'
                assert response_data['data']['request_id'] == f'multi_client_{i}'
            
            # 全クライアント切断
            for client in clients:
                await client.close()
            
        finally:
            await self.stop_test_server()
    
    @pytest.mark.asyncio
    async def test_auto_status_updates(self):
        """自動ステータス更新テスト"""
        await self.start_test_server()
        
        try:
            websocket = await websockets.connect(self.server_uri)
            
            # 接続確認メッセージをスキップ
            await websocket.recv()
            
            # 自動更新を有効化
            enable_request = {
                'type': 'enable_auto_updates',
                'data': {'interval_seconds': 1},
                'timestamp': datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(enable_request))
            
            # 自動更新メッセージを複数回受信
            auto_updates = []
            for _ in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    if data['type'] == 'system_status_update' and data['data'].get('auto_update'):
                        auto_updates.append(data)
                except asyncio.TimeoutError:
                    break
            
            # 自動更新が機能していることを確認
            assert len(auto_updates) >= 2
            for update in auto_updates:
                assert update['data']['auto_update'] is True
                assert 'system_status' in update['data']
            
            await websocket.close()
            
        finally:
            await self.stop_test_server()
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """エラーハンドリングテスト"""
        await self.start_test_server()
        
        try:
            websocket = await websockets.connect(self.server_uri)
            
            # 接続確認メッセージをスキップ
            await websocket.recv()
            
            # 無効なメッセージ形式を送信
            invalid_messages = [
                "invalid json",
                json.dumps({"type": "unknown_type"}),
                json.dumps({"data": "missing_type"}),
                json.dumps({"type": "chat_message", "data": {}})  # 必須フィールド不足
            ]
            
            for invalid_msg in invalid_messages:
                await websocket.send(invalid_msg)
                
                # エラー応答を受信
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    response_data = json.loads(response)
                    
                    # エラーメッセージまたは無視されることを確認
                    if response_data.get('type') == 'error':
                        assert 'error' in response_data['data']
                        
                except asyncio.TimeoutError:
                    # メッセージが無視される場合もある
                    pass
            
            await websocket.close()
            
        finally:
            await self.stop_test_server()
    
    @pytest.mark.asyncio
    async def test_ping_pong_mechanism(self):
        """Ping-Pongメカニズムテスト"""
        await self.start_test_server()
        
        try:
            websocket = await websockets.connect(self.server_uri)
            
            # 接続確認メッセージをスキップ
            await websocket.recv()
            
            # Pingメッセージ送信
            ping_request = {
                'type': 'ping',
                'data': {'timestamp': datetime.now().isoformat()},
                'timestamp': datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(ping_request))
            
            # Pong応答を受信
            pong_response = await websocket.recv()
            pong_data = json.loads(pong_response)
            
            assert pong_data['type'] == 'pong'
            assert 'timestamp' in pong_data['data']
            
            await websocket.close()
            
        finally:
            await self.stop_test_server()
    
    @pytest.mark.asyncio
    async def test_connection_recovery(self):
        """接続回復テスト"""
        await self.start_test_server()
        
        try:
            # 最初の接続
            websocket1 = await websockets.connect(self.server_uri)
            await websocket1.recv()  # 接続確認メッセージ
            
            # 接続を強制切断
            await websocket1.close()
            
            # 少し待機
            await asyncio.sleep(0.5)
            
            # 再接続
            websocket2 = await websockets.connect(self.server_uri)
            welcome_message = await websocket2.recv()
            welcome_data = json.loads(welcome_message)
            
            # 再接続が成功することを確認
            assert welcome_data['type'] == 'connection_status'
            assert welcome_data['data']['status'] == 'connected'
            
            # 再接続後も正常に機能することを確認
            request = {
                'type': 'system_status_request',
                'data': {'request_id': 'reconnect_test'},
                'timestamp': datetime.now().isoformat()
            }
            
            await websocket2.send(json.dumps(request))
            response = await websocket2.recv()
            response_data = json.loads(response)
            
            assert response_data['type'] == 'system_status_update'
            
            await websocket2.close()
            
        finally:
            await self.stop_test_server()
    
    @pytest.mark.asyncio
    async def test_message_ordering(self):
        """メッセージ順序保証テスト"""
        await self.start_test_server()
        
        try:
            websocket = await websockets.connect(self.server_uri)
            await websocket.recv()  # 接続確認メッセージ
            
            # 複数のメッセージを順次送信
            request_ids = []
            for i in range(5):
                request_id = f'order_test_{i}'
                request_ids.append(request_id)
                
                request = {
                    'type': 'system_status_request',
                    'data': {'request_id': request_id},
                    'timestamp': datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(request))
                await asyncio.sleep(0.1)  # 少し間隔を空ける
            
            # 応答を順次受信
            received_ids = []
            for _ in range(5):
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data['type'] == 'system_status_update':
                    received_ids.append(response_data['data']['request_id'])
            
            # 順序が保たれていることを確認
            assert received_ids == request_ids
            
            await websocket.close()
            
        finally:
            await self.stop_test_server()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])