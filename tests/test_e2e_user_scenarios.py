"""
ユーザーシナリオ全体のE2Eテスト
実際のユーザー使用パターンを模擬した包括的なテスト
"""
import pytest
import asyncio
import json
import websockets
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any
import tempfile
import os
from pathlib import Path

# Import backend components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from websocket_server import MacStatusWebSocketServer
from connection_manager import ConnectionManager
from message_router import MessageRouter
from system_monitor import SystemMonitor
from elyza_model import ELYZAModelInterface, ModelConfig, ModelResponse
from chat_context_manager import ChatContextManager


class TestE2EUserScenarios:
    """ユーザーシナリオ全体のE2Eテスト"""
    
    def setup_method(self):
        """各テストメソッドのセットアップ"""
        self.server_port = 8002  # E2Eテスト用ポート
        self.server_uri = f"ws://localhost:{self.server_port}/ws"
        self.server = None
        self.server_task = None
        
        # モックコンポーネントの設定
        self.setup_mock_components()
        
        # テスト用データ
        self.setup_test_data()
    
    def setup_mock_components(self):
        """モックコンポーネントのセットアップ"""
        self.mock_system_monitor = Mock(spec=SystemMonitor)
        self.mock_model_interface = Mock(spec=ELYZAModelInterface)
        self.mock_chat_context = Mock(spec=ChatContextManager)
        
        # システム監視データの動的変化をシミュレート
        self.system_data_sequence = [
            {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': 35.2,
                'memory_percent': 62.1,
                'disk_percent': 68.4,
                'top_processes': [
                    {'name': 'Safari', 'cpu_percent': 15.3, 'memory_percent': 12.2},
                    {'name': 'Finder', 'cpu_percent': 8.1, 'memory_percent': 5.4}
                ]
            },
            {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': 78.5,  # CPU使用率が急上昇
                'memory_percent': 85.3,  # メモリ使用率も上昇
                'disk_percent': 68.4,
                'top_processes': [
                    {'name': 'Xcode', 'cpu_percent': 45.2, 'memory_percent': 35.8},
                    {'name': 'Google Chrome', 'cpu_percent': 25.1, 'memory_percent': 28.4}
                ]
            },
            {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': 42.1,  # 正常レベルに戻る
                'memory_percent': 71.2,
                'disk_percent': 68.4,
                'top_processes': [
                    {'name': 'Google Chrome', 'cpu_percent': 18.3, 'memory_percent': 22.1},
                    {'name': 'Terminal', 'cpu_percent': 12.4, 'memory_percent': 8.7}
                ]
            }
        ]
        
        self.data_index = 0
        
        def get_dynamic_system_data():
            data = self.system_data_sequence[self.data_index % len(self.system_data_sequence)]
            self.data_index += 1
            return data
        
        self.mock_system_monitor.get_system_info.side_effect = get_dynamic_system_data
        
        # モデル応答のシミュレート
        self.setup_model_responses()
    
    def setup_model_responses(self):
        """モデル応答のセットアップ"""
        response_patterns = {
            'greeting': "こんにちは！Mac Status PWAへようこそ。システムの監視についてお手伝いします。",
            'system_status': "現在のシステム状況をお伝えします。CPUは{cpu}%、メモリは{memory}%使用中です。",
            'cpu_high': "CPUの使用率が{cpu}%と高めです。{top_process}が多くのリソースを使用しています。",
            'memory_concern': "メモリ使用率が{memory}%です。必要に応じてアプリケーションを終了することをお勧めします。",
            'normal_status': "システムは正常に動作しています。特に問題はありません。",
            'process_info': "現在、{top_process}が最もリソースを使用しています。CPU: {process_cpu}%、メモリ: {process_memory}%です。"
        }
        
        async def generate_contextual_response(user_message, system_data, conversation_history=None):
            await asyncio.sleep(0.2)  # 応答時間をシミュレート
            
            cpu = system_data.get('cpu_percent', 0)
            memory = system_data.get('memory_percent', 0)
            top_process = system_data.get('top_processes', [{}])[0]
            
            # ユーザーメッセージに基づく応答選択
            message_lower = user_message.lower()
            
            if any(word in message_lower for word in ['こんにちは', 'はじめまして', 'hello']):
                content = response_patterns['greeting']
            elif cpu > 70:
                content = response_patterns['cpu_high'].format(
                    cpu=cpu, 
                    top_process=top_process.get('name', 'Unknown')
                )
            elif memory > 80:
                content = response_patterns['memory_concern'].format(memory=memory)
            elif any(word in message_lower for word in ['プロセス', 'アプリ', 'process']):
                content = response_patterns['process_info'].format(
                    top_process=top_process.get('name', 'Unknown'),
                    process_cpu=top_process.get('cpu_percent', 0),
                    process_memory=top_process.get('memory_percent', 0)
                )
            elif any(word in message_lower for word in ['状況', '状態', 'ステータス', 'status']):
                if cpu < 50 and memory < 70:
                    content = response_patterns['normal_status']
                else:
                    content = response_patterns['system_status'].format(cpu=cpu, memory=memory)
            else:
                content = response_patterns['system_status'].format(cpu=cpu, memory=memory)
            
            return ModelResponse(
                content=content,
                timestamp=datetime.now(),
                processing_time_ms=200.0,
                token_count=len(content.split()),
                model_info={'model': 'test_elyza'}
            )
        
        self.mock_model_interface.generate_system_response = AsyncMock(
            side_effect=generate_contextual_response
        )
    
    def setup_test_data(self):
        """テストデータのセットアップ"""
        self.user_scenarios = [
            {
                'name': '初回ユーザー体験',
                'messages': [
                    'こんにちは',
                    'システムの状況を教えてください',
                    'CPUの使用率はどうですか？',
                    'ありがとうございました'
                ]
            },
            {
                'name': 'システム監視セッション',
                'messages': [
                    'システムの詳細な状況を教えて',
                    'メモリの使用状況は？',
                    'どのプロセスが一番リソースを使っていますか？',
                    '問題があれば教えてください'
                ]
            },
            {
                'name': 'パフォーマンス問題調査',
                'messages': [
                    'Macが重く感じます',
                    'CPUの状況を確認してください',
                    'メモリ不足でしょうか？',
                    '対処法を教えてください'
                ]
            }
        ]
    
    async def start_test_server(self):
        """テスト用サーバーの起動"""
        self.server = MacStatusWebSocketServer()
        
        # モックコンポーネントを注入
        self.server.system_monitor = self.mock_system_monitor
        self.server.model_interface = self.mock_model_interface
        
        # バックグラウンドタスクを開始
        await self.server.start_background_tasks()
        
        # サーバーを非同期で起動
        import uvicorn
        config = uvicorn.Config(self.server.app, host="127.0.0.1", port=self.server_port, log_level="error")
        server = uvicorn.Server(config)
        self.server_task = asyncio.create_task(server.serve())
        await asyncio.sleep(1.0)  # サーバー起動待機
    
    async def stop_test_server(self):
        """テスト用サーバーの停止"""
        if self.server:
            await self.server.stop_background_tasks()
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_first_time_user_experience(self):
        """初回ユーザー体験のE2Eテスト"""
        await self.start_test_server()
        
        try:
            websocket = await websockets.connect(self.server_uri)
            
            # 接続確認
            welcome_message = await websocket.recv()
            welcome_data = json.loads(welcome_message)
            assert welcome_data['type'] == 'connection_status'
            
            scenario = self.user_scenarios[0]  # 初回ユーザー体験
            responses = []
            
            for message in scenario['messages']:
                # チャットメッセージ送信
                chat_request = {
                    'type': 'chat_message',
                    'data': {
                        'message': message,
                        'request_id': f'first_user_{len(responses)}'
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(chat_request))
                
                # 応答受信
                response_message = await websocket.recv()
                response_data = json.loads(response_message)
                
                assert response_data['type'] == 'chat_response'
                assert 'message' in response_data['data']
                
                responses.append({
                    'user_message': message,
                    'assistant_response': response_data['data']['message'],
                    'processing_time': response_data['data'].get('processing_time_ms', 0)
                })
                
                await asyncio.sleep(0.5)  # 自然な会話間隔
            
            # 初回ユーザー体験の検証
            assert len(responses) == len(scenario['messages'])
            
            # 挨拶への適切な応答
            first_response = responses[0]['assistant_response']
            assert any(word in first_response for word in ['こんにちは', 'ようこそ', 'お手伝い'])
            
            # システム情報への応答
            system_response = responses[1]['assistant_response']
            assert any(word in system_response for word in ['CPU', 'メモリ', 'システム'])
            
            # 応答時間の確認
            for response in responses:
                assert response['processing_time'] < 5000  # 5秒以内
            
            await websocket.close()
            
        finally:
            await self.stop_test_server()
    
    @pytest.mark.asyncio
    async def test_system_monitoring_session(self):
        """システム監視セッションのE2Eテスト"""
        await self.start_test_server()
        
        try:
            websocket = await websockets.connect(self.server_uri)
            await websocket.recv()  # 接続確認メッセージをスキップ
            
            scenario = self.user_scenarios[1]  # システム監視セッション
            session_data = {
                'start_time': datetime.now(),
                'messages': [],
                'system_snapshots': []
            }
            
            for i, message in enumerate(scenario['messages']):
                # システムステータスも同時に取得
                status_request = {
                    'type': 'system_status_request',
                    'data': {'request_id': f'monitoring_{i}'},
                    'timestamp': datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(status_request))
                status_response = await websocket.recv()
                status_data = json.loads(status_response)
                
                session_data['system_snapshots'].append(status_data['data']['system_status'])
                
                # チャットメッセージ送信
                chat_request = {
                    'type': 'chat_message',
                    'data': {
                        'message': message,
                        'request_id': f'monitoring_chat_{i}'
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(chat_request))
                chat_response = await websocket.recv()
                chat_data = json.loads(chat_response)
                
                session_data['messages'].append({
                    'user': message,
                    'assistant': chat_data['data']['message'],
                    'timestamp': datetime.now(),
                    'system_context': status_data['data']['system_status']
                })
                
                await asyncio.sleep(1)  # 監視間隔
            
            # セッションデータの検証
            assert len(session_data['messages']) == len(scenario['messages'])
            assert len(session_data['system_snapshots']) == len(scenario['messages'])
            
            # システム状態の変化を検証
            cpu_values = [snap['cpu_percent'] for snap in session_data['system_snapshots']]
            assert len(set(cpu_values)) > 1, "CPU values should change during monitoring"
            
            # 応答がシステム状態を反映していることを確認
            for msg_data in session_data['messages']:
                response = msg_data['assistant']
                system_ctx = msg_data['system_context']
                
                # 高CPU使用率時の適切な応答
                if system_ctx['cpu_percent'] > 70:
                    assert any(word in response for word in ['高め', '多く', 'リソース'])
                
                # システム情報が含まれていることを確認
                assert any(str(int(system_ctx['cpu_percent'])) in response or 
                          str(int(system_ctx['memory_percent'])) in response
                          for _ in [None])  # At least one should be true
            
            await websocket.close()
            
        finally:
            await self.stop_test_server()
    
    @pytest.mark.asyncio
    async def test_performance_issue_investigation(self):
        """パフォーマンス問題調査のE2Eテスト"""
        await self.start_test_server()
        
        try:
            websocket = await websockets.connect(self.server_uri)
            await websocket.recv()  # 接続確認メッセージをスキップ
            
            scenario = self.user_scenarios[2]  # パフォーマンス問題調査
            investigation_log = []
            
            for message in scenario['messages']:
                # 問題調査のタイムスタンプ記録
                investigation_start = time.time()
                
                # チャットメッセージ送信
                chat_request = {
                    'type': 'chat_message',
                    'data': {
                        'message': message,
                        'request_id': f'investigation_{len(investigation_log)}'
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(chat_request))
                
                # 応答受信
                response_message = await websocket.recv()
                response_data = json.loads(response_message)
                
                investigation_end = time.time()
                response_time = (investigation_end - investigation_start) * 1000
                
                investigation_log.append({
                    'query': message,
                    'response': response_data['data']['message'],
                    'response_time_ms': response_time,
                    'timestamp': datetime.now()
                })
                
                await asyncio.sleep(0.8)  # 調査間隔
            
            # 調査プロセスの検証
            assert len(investigation_log) == len(scenario['messages'])
            
            # 問題報告への適切な応答
            first_query = investigation_log[0]
            assert '重く' in first_query['query']
            # 応答に診断的な内容が含まれていることを確認
            first_response = first_query['response']
            assert any(word in first_response for word in ['CPU', 'メモリ', 'リソース', 'プロセス'])
            
            # CPU確認要求への応答
            cpu_query = investigation_log[1]
            cpu_response = cpu_query['response']
            assert any(word in cpu_response for word in ['CPU', '%', '使用'])
            
            # 全ての応答時間が適切であることを確認
            for log_entry in investigation_log:
                assert log_entry['response_time_ms'] < 5000  # 5秒以内
            
            # 調査の進行が論理的であることを確認
            responses_text = ' '.join([log['response'] for log in investigation_log])
            assert 'CPU' in responses_text and 'メモリ' in responses_text
            
            await websocket.close()
            
        finally:
            await self.stop_test_server()
    
    @pytest.mark.asyncio
    async def test_concurrent_users_scenario(self):
        """複数ユーザー同時使用のE2Eテスト"""
        await self.start_test_server()
        
        try:
            # 3人のユーザーを同時にシミュレート
            user_tasks = []
            
            for user_id in range(3):
                task = self.simulate_user_session(user_id)
                user_tasks.append(task)
            
            # 全ユーザーセッションを並行実行
            user_results = await asyncio.gather(*user_tasks, return_exceptions=True)
            
            # 結果の検証
            successful_sessions = [r for r in user_results if not isinstance(r, Exception)]
            assert len(successful_sessions) == 3, "All user sessions should complete successfully"
            
            # 各ユーザーセッションの検証
            for user_result in successful_sessions:
                assert user_result['completed'] is True
                assert len(user_result['messages']) > 0
                assert all(msg['response_time_ms'] < 5000 for msg in user_result['messages'])
            
        finally:
            await self.stop_test_server()
    
    async def simulate_user_session(self, user_id: int) -> Dict[str, Any]:
        """個別ユーザーセッションのシミュレート"""
        websocket = await websockets.connect(self.server_uri)
        await websocket.recv()  # 接続確認メッセージをスキップ
        
        session_result = {
            'user_id': user_id,
            'completed': False,
            'messages': []
        }
        
        try:
            # ユーザー固有のメッセージパターン
            user_messages = [
                f'ユーザー{user_id}です。システム状況を教えてください',
                f'CPU使用率はどうですか？',
                f'メモリの状況も確認したいです'
            ]
            
            for i, message in enumerate(user_messages):
                start_time = time.time()
                
                chat_request = {
                    'type': 'chat_message',
                    'data': {
                        'message': message,
                        'request_id': f'user_{user_id}_msg_{i}'
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(chat_request))
                response_message = await websocket.recv()
                response_data = json.loads(response_message)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                session_result['messages'].append({
                    'message': message,
                    'response': response_data['data']['message'],
                    'response_time_ms': response_time
                })
                
                await asyncio.sleep(0.5)  # ユーザー間の自然な間隔
            
            session_result['completed'] = True
            
        finally:
            await websocket.close()
        
        return session_result
    
    @pytest.mark.asyncio
    async def test_long_running_session(self):
        """長時間セッションのE2Eテスト"""
        await self.start_test_server()
        
        try:
            websocket = await websockets.connect(self.server_uri)
            await websocket.recv()  # 接続確認メッセージをスキップ
            
            session_duration = 30  # 30秒間のセッション
            session_start = time.time()
            message_count = 0
            responses = []
            
            while (time.time() - session_start) < session_duration:
                # 定期的なシステム状況確認
                message = f'システム状況確認 #{message_count + 1}'
                
                chat_request = {
                    'type': 'chat_message',
                    'data': {
                        'message': message,
                        'request_id': f'long_session_{message_count}'
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(chat_request))
                response_message = await websocket.recv()
                response_data = json.loads(response_message)
                
                responses.append({
                    'message_id': message_count,
                    'response': response_data['data']['message'],
                    'timestamp': datetime.now()
                })
                
                message_count += 1
                await asyncio.sleep(3)  # 3秒間隔
            
            # 長時間セッションの検証
            assert message_count >= 8, "Should have multiple messages in long session"
            assert len(responses) == message_count
            
            # 接続が安定していることを確認
            response_times = [
                (responses[i]['timestamp'] - responses[i-1]['timestamp']).total_seconds()
                for i in range(1, len(responses))
            ]
            
            # 応答間隔が一定範囲内であることを確認
            for interval in response_times:
                assert 2.5 <= interval <= 4.0, "Response intervals should be consistent"
            
            await websocket.close()
            
        finally:
            await self.stop_test_server()
    
    @pytest.mark.asyncio
    async def test_error_recovery_scenario(self):
        """エラー回復シナリオのE2Eテスト"""
        await self.start_test_server()
        
        try:
            websocket = await websockets.connect(self.server_uri)
            await websocket.recv()  # 接続確認メッセージをスキップ
            
            # 正常なメッセージ
            normal_request = {
                'type': 'chat_message',
                'data': {
                    'message': '正常なメッセージです',
                    'request_id': 'normal_msg'
                },
                'timestamp': datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(normal_request))
            normal_response = await websocket.recv()
            normal_data = json.loads(normal_response)
            
            assert normal_data['type'] == 'chat_response'
            
            # 無効なメッセージを送信
            invalid_messages = [
                "invalid json format",
                json.dumps({"type": "unknown_type"}),
                json.dumps({"data": "missing_type_field"})
            ]
            
            for invalid_msg in invalid_messages:
                await websocket.send(invalid_msg)
                
                # エラー応答または無視を確認
                try:
                    error_response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    error_data = json.loads(error_response)
                    
                    if error_data.get('type') == 'error':
                        assert 'error' in error_data['data']
                        
                except asyncio.TimeoutError:
                    # メッセージが無視される場合もある
                    pass
            
            # エラー後も正常に動作することを確認
            recovery_request = {
                'type': 'chat_message',
                'data': {
                    'message': 'エラー後の回復テスト',
                    'request_id': 'recovery_msg'
                },
                'timestamp': datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(recovery_request))
            recovery_response = await websocket.recv()
            recovery_data = json.loads(recovery_response)
            
            assert recovery_data['type'] == 'chat_response'
            assert 'message' in recovery_data['data']
            
            await websocket.close()
            
        finally:
            await self.stop_test_server()
    
    @pytest.mark.asyncio
    async def test_complete_user_journey(self):
        """完全なユーザージャーニーのE2Eテスト"""
        await self.start_test_server()
        
        try:
            websocket = await websockets.connect(self.server_uri)
            await websocket.recv()  # 接続確認メッセージをスキップ
            
            # 完全なユーザージャーニー
            journey_steps = [
                {
                    'action': 'greeting',
                    'message': 'こんにちは、初めて使います',
                    'expected_keywords': ['こんにちは', 'ようこそ', 'お手伝い']
                },
                {
                    'action': 'system_overview',
                    'message': 'システム全体の状況を教えてください',
                    'expected_keywords': ['CPU', 'メモリ', 'システム']
                },
                {
                    'action': 'specific_inquiry',
                    'message': 'CPUの詳細な使用状況は？',
                    'expected_keywords': ['CPU', '%', '使用']
                },
                {
                    'action': 'process_check',
                    'message': 'どのアプリが一番リソースを使っていますか？',
                    'expected_keywords': ['プロセス', 'アプリ', 'リソース']
                },
                {
                    'action': 'problem_inquiry',
                    'message': '何か問題はありませんか？',
                    'expected_keywords': ['問題', '正常', '状況']
                },
                {
                    'action': 'farewell',
                    'message': 'ありがとうございました',
                    'expected_keywords': ['ありがとう', 'また', 'お疲れ']
                }
            ]
            
            journey_log = []
            
            for step in journey_steps:
                step_start = time.time()
                
                # メッセージ送信
                request = {
                    'type': 'chat_message',
                    'data': {
                        'message': step['message'],
                        'request_id': f"journey_{step['action']}"
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(request))
                response_message = await websocket.recv()
                response_data = json.loads(response_message)
                
                step_end = time.time()
                step_duration = (step_end - step_start) * 1000
                
                # ステップ結果の記録
                step_result = {
                    'action': step['action'],
                    'user_message': step['message'],
                    'assistant_response': response_data['data']['message'],
                    'duration_ms': step_duration,
                    'keywords_found': []
                }
                
                # 期待されるキーワードの確認
                response_text = response_data['data']['message']
                for keyword in step['expected_keywords']:
                    if keyword in response_text:
                        step_result['keywords_found'].append(keyword)
                
                journey_log.append(step_result)
                
                await asyncio.sleep(1)  # 自然な会話間隔
            
            # ジャーニー全体の検証
            assert len(journey_log) == len(journey_steps)
            
            # 各ステップの検証
            for i, step_result in enumerate(journey_log):
                expected_step = journey_steps[i]
                
                # 応答時間の確認
                assert step_result['duration_ms'] < 5000, \
                    f"Step {step_result['action']} took too long"
                
                # キーワードの確認
                assert len(step_result['keywords_found']) > 0, \
                    f"Step {step_result['action']} should contain expected keywords"
            
            # ジャーニーの一貫性確認
            all_responses = ' '.join([step['assistant_response'] for step in journey_log])
            assert 'システム' in all_responses, "Journey should include system information"
            assert 'CPU' in all_responses, "Journey should include CPU information"
            
            await websocket.close()
            
        finally:
            await self.stop_test_server()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])