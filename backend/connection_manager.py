"""
接続状態管理とオフライン対応システム
WebSocket接続の監視、自動再接続、オフライン機能を提供
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, asdict
import json

from error_handler import (
    handle_websocket_error,
    ErrorCategory,
    ErrorSeverity,
    global_error_handler
)


class ConnectionState(Enum):
    """接続状態の定義"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    OFFLINE = "offline"


class ReconnectionStrategy(Enum):
    """再接続戦略"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_INTERVAL = "fixed_interval"
    IMMEDIATE = "immediate"
    NONE = "none"


@dataclass
class ConnectionMetrics:
    """接続メトリクス"""
    total_connections: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    reconnection_attempts: int = 0
    total_uptime_seconds: float = 0.0
    total_downtime_seconds: float = 0.0
    last_connected_at: Optional[datetime] = None
    last_disconnected_at: Optional[datetime] = None
    average_connection_duration: float = 0.0
    connection_success_rate: float = 0.0


@dataclass
class ReconnectionConfig:
    """再接続設定"""
    strategy: ReconnectionStrategy = ReconnectionStrategy.EXPONENTIAL_BACKOFF
    max_attempts: int = 10
    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff_multiplier: float = 2.0
    timeout_seconds: float = 10.0
    enable_jitter: bool = True


class ConnectionManager:
    """WebSocket接続状態管理クラス"""
    
    def __init__(self, reconnection_config: ReconnectionConfig = None):
        """
        接続マネージャーを初期化
        
        Args:
            reconnection_config: 再接続設定
        """
        self.logger = logging.getLogger(__name__)
        self.reconnection_config = reconnection_config or ReconnectionConfig()
        
        # 接続状態
        self.current_state = ConnectionState.DISCONNECTED
        self.previous_state = ConnectionState.DISCONNECTED
        self.state_changed_at = datetime.now()
        
        # 再接続管理
        self.reconnection_task: Optional[asyncio.Task] = None
        self.reconnection_attempts = 0
        self.is_reconnection_enabled = True
        
        # メトリクス
        self.metrics = ConnectionMetrics()
        self.connection_history: List[Dict[str, Any]] = []
        
        # コールバック
        self.state_change_callbacks: List[Callable] = []
        self.connection_callbacks: List[Callable] = []
        self.disconnection_callbacks: List[Callable] = []
        
        # ハートビート
        self.heartbeat_interval = 30.0  # seconds
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.last_heartbeat_received = None
        self.heartbeat_timeout = 60.0  # seconds
        
        # オフライン機能
        self.offline_mode = False
        self.offline_data_cache: Dict[str, Any] = {}
        self.offline_message_queue: List[Dict[str, Any]] = []
        
    def set_state(self, new_state: ConnectionState, reason: str = ""):
        """
        接続状態を変更
        
        Args:
            new_state: 新しい接続状態
            reason: 状態変更の理由
        """
        if new_state == self.current_state:
            return
        
        old_state = self.current_state
        self.previous_state = old_state
        self.current_state = new_state
        self.state_changed_at = datetime.now()
        
        # メトリクス更新
        self._update_metrics(old_state, new_state)
        
        # 履歴に記録
        self.connection_history.append({
            'timestamp': self.state_changed_at.isoformat(),
            'old_state': old_state.value,
            'new_state': new_state.value,
            'reason': reason,
            'reconnection_attempts': self.reconnection_attempts
        })
        
        # 履歴サイズ制限
        if len(self.connection_history) > 100:
            self.connection_history = self.connection_history[-100:]
        
        self.logger.info(f"Connection state changed: {old_state.value} -> {new_state.value} ({reason})")
        
        # コールバック実行
        self._execute_state_change_callbacks(old_state, new_state, reason)
        
        # 状態別処理
        if new_state == ConnectionState.CONNECTED:
            self.reconnection_attempts = 0
            self._execute_connection_callbacks()
            self._start_heartbeat()
            self._process_offline_queue()
        elif new_state == ConnectionState.DISCONNECTED:
            self._execute_disconnection_callbacks()
            self._stop_heartbeat()
            if self.is_reconnection_enabled:
                self._schedule_reconnection()
        elif new_state == ConnectionState.OFFLINE:
            self.offline_mode = True
            self._stop_heartbeat()
    
    def get_state(self) -> ConnectionState:
        """現在の接続状態を取得"""
        return self.current_state
    
    def get_state_info(self) -> Dict[str, Any]:
        """接続状態の詳細情報を取得"""
        return {
            'current_state': self.current_state.value,
            'previous_state': self.previous_state.value,
            'state_changed_at': self.state_changed_at.isoformat(),
            'reconnection_attempts': self.reconnection_attempts,
            'is_reconnection_enabled': self.is_reconnection_enabled,
            'offline_mode': self.offline_mode,
            'heartbeat_active': self.heartbeat_task is not None,
            'last_heartbeat': self.last_heartbeat_received.isoformat() if self.last_heartbeat_received else None,
            'queued_messages': len(self.offline_message_queue)
        }
    
    def enable_reconnection(self):
        """自動再接続を有効化"""
        self.is_reconnection_enabled = True
        self.logger.info("Automatic reconnection enabled")
    
    def disable_reconnection(self):
        """自動再接続を無効化"""
        self.is_reconnection_enabled = False
        if self.reconnection_task:
            self.reconnection_task.cancel()
            self.reconnection_task = None
        self.logger.info("Automatic reconnection disabled")
    
    def force_reconnection(self):
        """強制的に再接続を試行"""
        if self.reconnection_task:
            self.reconnection_task.cancel()
        
        self.reconnection_attempts = 0
        self.set_state(ConnectionState.RECONNECTING, "forced_reconnection")
        self._schedule_reconnection(immediate=True)
    
    def _schedule_reconnection(self, immediate: bool = False):
        """再接続をスケジュール"""
        if not self.is_reconnection_enabled:
            return
        
        if self.reconnection_attempts >= self.reconnection_config.max_attempts:
            self.set_state(ConnectionState.FAILED, "max_reconnection_attempts_exceeded")
            return
        
        delay = 0.0 if immediate else self._calculate_reconnection_delay()
        
        self.logger.info(f"Scheduling reconnection in {delay:.1f}s (attempt {self.reconnection_attempts + 1})")
        
        self.reconnection_task = asyncio.create_task(self._reconnection_worker(delay))
    
    def _calculate_reconnection_delay(self) -> float:
        """再接続遅延時間を計算"""
        if self.reconnection_config.strategy == ReconnectionStrategy.IMMEDIATE:
            return 0.0
        elif self.reconnection_config.strategy == ReconnectionStrategy.FIXED_INTERVAL:
            delay = self.reconnection_config.initial_delay
        elif self.reconnection_config.strategy == ReconnectionStrategy.EXPONENTIAL_BACKOFF:
            delay = min(
                self.reconnection_config.initial_delay * (
                    self.reconnection_config.backoff_multiplier ** self.reconnection_attempts
                ),
                self.reconnection_config.max_delay
            )
        else:
            delay = self.reconnection_config.initial_delay
        
        # ジッターを追加（接続の集中を避ける）
        if self.reconnection_config.enable_jitter:
            import random
            jitter = delay * 0.1 * random.random()
            delay += jitter
        
        return delay
    
    async def _reconnection_worker(self, delay: float):
        """再接続ワーカー"""
        try:
            if delay > 0:
                await asyncio.sleep(delay)
            
            self.reconnection_attempts += 1
            self.set_state(ConnectionState.CONNECTING, f"reconnection_attempt_{self.reconnection_attempts}")
            
            # 実際の再接続処理は外部から提供される
            # ここでは状態管理のみ行う
            
        except asyncio.CancelledError:
            self.logger.info("Reconnection cancelled")
        except Exception as e:
            error_info = handle_websocket_error(
                e, 
                {'component': 'reconnection_worker', 'attempt': self.reconnection_attempts}
            )
            self.logger.error(f"[{error_info.error_id}] Reconnection worker error: {e}")
    
    def _start_heartbeat(self):
        """ハートビート監視を開始"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        self.heartbeat_task = asyncio.create_task(self._heartbeat_worker())
        self.logger.debug("Heartbeat monitoring started")
    
    def _stop_heartbeat(self):
        """ハートビート監視を停止"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None
        self.logger.debug("Heartbeat monitoring stopped")
    
    async def _heartbeat_worker(self):
        """ハートビート監視ワーカー"""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                
                # ハートビートタイムアウトチェック
                if self.last_heartbeat_received:
                    time_since_heartbeat = (datetime.now() - self.last_heartbeat_received).total_seconds()
                    if time_since_heartbeat > self.heartbeat_timeout:
                        self.logger.warning(f"Heartbeat timeout: {time_since_heartbeat:.1f}s")
                        self.set_state(ConnectionState.DISCONNECTED, "heartbeat_timeout")
                        break
                
        except asyncio.CancelledError:
            self.logger.debug("Heartbeat worker cancelled")
        except Exception as e:
            error_info = handle_websocket_error(
                e, 
                {'component': 'heartbeat_worker'}
            )
            self.logger.error(f"[{error_info.error_id}] Heartbeat worker error: {e}")
    
    def on_heartbeat_received(self):
        """ハートビート受信時の処理"""
        self.last_heartbeat_received = datetime.now()
        self.logger.debug("Heartbeat received")
    
    def _update_metrics(self, old_state: ConnectionState, new_state: ConnectionState):
        """メトリクスを更新"""
        now = datetime.now()
        
        if new_state == ConnectionState.CONNECTED:
            self.metrics.total_connections += 1
            self.metrics.successful_connections += 1
            self.metrics.last_connected_at = now
        elif old_state == ConnectionState.CONNECTED and new_state != ConnectionState.CONNECTED:
            self.metrics.last_disconnected_at = now
            
            # 接続時間を計算
            if self.metrics.last_connected_at:
                connection_duration = (now - self.metrics.last_connected_at).total_seconds()
                self.metrics.total_uptime_seconds += connection_duration
                
                # 平均接続時間を更新
                if self.metrics.successful_connections > 0:
                    self.metrics.average_connection_duration = (
                        self.metrics.total_uptime_seconds / self.metrics.successful_connections
                    )
        
        if new_state == ConnectionState.FAILED:
            self.metrics.failed_connections += 1
        
        if new_state in [ConnectionState.RECONNECTING, ConnectionState.CONNECTING]:
            self.metrics.reconnection_attempts += 1
        
        # 成功率を計算
        if self.metrics.total_connections > 0:
            self.metrics.connection_success_rate = (
                self.metrics.successful_connections / self.metrics.total_connections
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """接続メトリクスを取得"""
        return asdict(self.metrics)
    
    def get_connection_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """接続履歴を取得"""
        return self.connection_history[-limit:]
    
    # オフライン機能
    def enter_offline_mode(self):
        """オフラインモードに移行"""
        self.offline_mode = True
        self.set_state(ConnectionState.OFFLINE, "manual_offline_mode")
        self.logger.info("Entered offline mode")
    
    def exit_offline_mode(self):
        """オフラインモードを終了"""
        self.offline_mode = False
        if self.current_state == ConnectionState.OFFLINE:
            self.set_state(ConnectionState.DISCONNECTED, "exit_offline_mode")
        self.logger.info("Exited offline mode")
    
    def cache_data(self, key: str, data: Any, ttl_seconds: int = 300):
        """データをオフラインキャッシュに保存"""
        self.offline_data_cache[key] = {
            'data': data,
            'cached_at': datetime.now(),
            'ttl_seconds': ttl_seconds
        }
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """オフラインキャッシュからデータを取得"""
        if key not in self.offline_data_cache:
            return None
        
        cached_item = self.offline_data_cache[key]
        cached_at = cached_item['cached_at']
        ttl_seconds = cached_item['ttl_seconds']
        
        # TTLチェック
        if (datetime.now() - cached_at).total_seconds() > ttl_seconds:
            del self.offline_data_cache[key]
            return None
        
        return cached_item['data']
    
    def queue_message(self, message: Dict[str, Any]):
        """メッセージをオフラインキューに追加"""
        message['queued_at'] = datetime.now().isoformat()
        self.offline_message_queue.append(message)
        
        # キューサイズ制限
        if len(self.offline_message_queue) > 100:
            self.offline_message_queue = self.offline_message_queue[-100:]
        
        self.logger.debug(f"Message queued for offline processing: {len(self.offline_message_queue)} messages in queue")
    
    def _process_offline_queue(self):
        """オフラインキューのメッセージを処理"""
        if not self.offline_message_queue:
            return
        
        self.logger.info(f"Processing {len(self.offline_message_queue)} queued messages")
        
        # キューのメッセージを処理（実際の送信は外部で実装）
        processed_messages = self.offline_message_queue.copy()
        self.offline_message_queue.clear()
        
        # コールバックで処理を通知
        for callback in self.connection_callbacks:
            try:
                if hasattr(callback, '__call__'):
                    callback({'type': 'offline_queue_processing', 'messages': processed_messages})
            except Exception as e:
                self.logger.error(f"Error in offline queue processing callback: {e}")
    
    def clear_offline_cache(self):
        """オフラインキャッシュをクリア"""
        self.offline_data_cache.clear()
        self.offline_message_queue.clear()
        self.logger.info("Offline cache cleared")
    
    # コールバック管理
    def add_state_change_callback(self, callback: Callable):
        """状態変更コールバックを追加"""
        if callback not in self.state_change_callbacks:
            self.state_change_callbacks.append(callback)
    
    def remove_state_change_callback(self, callback: Callable):
        """状態変更コールバックを削除"""
        if callback in self.state_change_callbacks:
            self.state_change_callbacks.remove(callback)
    
    def add_connection_callback(self, callback: Callable):
        """接続コールバックを追加"""
        if callback not in self.connection_callbacks:
            self.connection_callbacks.append(callback)
    
    def add_disconnection_callback(self, callback: Callable):
        """切断コールバックを追加"""
        if callback not in self.disconnection_callbacks:
            self.disconnection_callbacks.append(callback)
    
    def _execute_state_change_callbacks(self, old_state: ConnectionState, new_state: ConnectionState, reason: str):
        """状態変更コールバックを実行"""
        for callback in self.state_change_callbacks:
            try:
                callback(old_state, new_state, reason)
            except Exception as e:
                self.logger.error(f"Error in state change callback: {e}")
    
    def _execute_connection_callbacks(self):
        """接続コールバックを実行"""
        for callback in self.connection_callbacks:
            try:
                callback({'type': 'connected', 'timestamp': datetime.now().isoformat()})
            except Exception as e:
                self.logger.error(f"Error in connection callback: {e}")
    
    def _execute_disconnection_callbacks(self):
        """切断コールバックを実行"""
        for callback in self.disconnection_callbacks:
            try:
                callback({'type': 'disconnected', 'timestamp': datetime.now().isoformat()})
            except Exception as e:
                self.logger.error(f"Error in disconnection callback: {e}")
    
    async def cleanup(self):
        """リソースをクリーンアップ"""
        self.disable_reconnection()
        self._stop_heartbeat()
        self.clear_offline_cache()
        
        # コールバックをクリア
        self.state_change_callbacks.clear()
        self.connection_callbacks.clear()
        self.disconnection_callbacks.clear()
        
        self.logger.info("Connection manager cleaned up")


class OfflineDataManager:
    """オフライン時のデータ管理クラス"""
    
    def __init__(self):
        """オフラインデータマネージャーを初期化"""
        self.logger = logging.getLogger(__name__)
        self.local_storage: Dict[str, Any] = {}
        self.last_system_status: Optional[Dict[str, Any]] = None
        self.cached_responses: Dict[str, str] = {}
        
        # デフォルトのオフライン応答
        self.default_responses = {
            'system_status': 'オフラインモードです。最後に取得したシステム情報を表示しています。',
            'chat_general': 'オフラインモードのため、AIアシスタント機能は利用できません。',
            'chat_system': 'オフラインモードです。基本的なシステム情報のみ表示できます。',
            'error': 'オフラインモードのため、この機能は利用できません。'
        }
    
    def store_system_status(self, status: Dict[str, Any]):
        """システム状態をローカルに保存"""
        self.last_system_status = status.copy()
        self.last_system_status['offline_cached_at'] = datetime.now().isoformat()
        self.logger.debug("System status cached for offline use")
    
    def get_offline_system_status(self) -> Dict[str, Any]:
        """オフライン用システム状態を取得"""
        if self.last_system_status:
            offline_status = self.last_system_status.copy()
            offline_status['offline_mode'] = True
            offline_status['message'] = self.default_responses['system_status']
            return offline_status
        else:
            return {
                'offline_mode': True,
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'disk_percent': 0.0,
                'timestamp': datetime.now().isoformat(),
                'message': 'オフラインモードです。システム情報は利用できません。'
            }
    
    def get_offline_chat_response(self, user_message: str) -> str:
        """オフライン用チャット応答を生成"""
        user_message_lower = user_message.lower()
        
        # システム関連の質問
        if any(keyword in user_message for keyword in ['システム', 'CPU', 'メモリ', 'ディスク']):
            if self.last_system_status:
                return f"{self.default_responses['chat_system']}\n\n最後に取得した情報:\nCPU: {self.last_system_status.get('cpu_percent', 0):.1f}%\nメモリ: {self.last_system_status.get('memory_percent', 0):.1f}%"
            else:
                return self.default_responses['chat_system']
        
        # 一般的な質問
        return self.default_responses['chat_general']
    
    def cache_response(self, key: str, response: str):
        """応答をキャッシュ"""
        self.cached_responses[key] = response
    
    def get_cached_response(self, key: str) -> Optional[str]:
        """キャッシュされた応答を取得"""
        return self.cached_responses.get(key)
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self.local_storage.clear()
        self.cached_responses.clear()
        self.last_system_status = None
        self.logger.info("Offline data cache cleared")


# グローバルインスタンス
global_connection_manager = ConnectionManager()
global_offline_data_manager = OfflineDataManager()


# 便利な関数
def get_connection_state() -> ConnectionState:
    """現在の接続状態を取得"""
    return global_connection_manager.get_state()


def is_online() -> bool:
    """オンライン状態かどうかを確認"""
    return global_connection_manager.get_state() == ConnectionState.CONNECTED


def is_offline() -> bool:
    """オフライン状態かどうかを確認"""
    return global_connection_manager.offline_mode or global_connection_manager.get_state() == ConnectionState.OFFLINE


def enable_offline_mode():
    """オフラインモードを有効化"""
    global_connection_manager.enter_offline_mode()


def disable_offline_mode():
    """オフラインモードを無効化"""
    global_connection_manager.exit_offline_mode()


def cache_system_status(status: Dict[str, Any]):
    """システム状態をキャッシュ"""
    global_offline_data_manager.store_system_status(status)


def get_offline_system_status() -> Dict[str, Any]:
    """オフライン用システム状態を取得"""
    return global_offline_data_manager.get_offline_system_status()


def get_offline_chat_response(user_message: str) -> str:
    """オフライン用チャット応答を取得"""
    return global_offline_data_manager.get_offline_chat_response(user_message)