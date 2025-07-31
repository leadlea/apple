"""
包括的エラーハンドリングシステム
Mac Status PWA用のエラー処理、ユーザーフレンドリーなメッセージ、フォールバック機能を提供
"""
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio


class ErrorSeverity(Enum):
    """エラーの重要度レベル"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """エラーのカテゴリ"""
    MODEL_ERROR = "model_error"
    SYSTEM_MONITOR_ERROR = "system_monitor_error"
    WEBSOCKET_ERROR = "websocket_error"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    CONFIGURATION_ERROR = "configuration_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ErrorInfo:
    """エラー情報を格納するデータクラス"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    technical_details: str
    timestamp: datetime
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    suggested_actions: List[str] = None
    
    def __post_init__(self):
        if self.suggested_actions is None:
            self.suggested_actions = []


class ErrorHandler:
    """包括的エラーハンドリングクラス"""
    
    def __init__(self):
        """エラーハンドラーを初期化"""
        self.logger = logging.getLogger(__name__)
        self.error_callbacks: List[Callable] = []
        self.error_history: List[ErrorInfo] = []
        self.max_history_size = 100
        
        # エラーメッセージのマッピング
        self.user_messages = {
            ErrorCategory.MODEL_ERROR: {
                ErrorSeverity.LOW: "AIモデルで軽微な問題が発生しました。",
                ErrorSeverity.MEDIUM: "AIモデルの処理に時間がかかっています。",
                ErrorSeverity.HIGH: "AIモデルが一時的に利用できません。",
                ErrorSeverity.CRITICAL: "AIモデルが利用できません。システム管理者にお問い合わせください。"
            },
            ErrorCategory.SYSTEM_MONITOR_ERROR: {
                ErrorSeverity.LOW: "システム情報の取得で軽微な問題が発生しました。",
                ErrorSeverity.MEDIUM: "一部のシステム情報が取得できません。",
                ErrorSeverity.HIGH: "システム監視機能に問題が発生しています。",
                ErrorSeverity.CRITICAL: "システム監視機能が停止しています。"
            },
            ErrorCategory.WEBSOCKET_ERROR: {
                ErrorSeverity.LOW: "通信で軽微な問題が発生しました。",
                ErrorSeverity.MEDIUM: "接続が不安定になっています。",
                ErrorSeverity.HIGH: "接続に問題が発生しています。再接続を試行中です。",
                ErrorSeverity.CRITICAL: "サーバーとの接続が失われました。"
            },
            ErrorCategory.NETWORK_ERROR: {
                ErrorSeverity.LOW: "ネットワークで軽微な問題が発生しました。",
                ErrorSeverity.MEDIUM: "ネットワーク接続が不安定です。",
                ErrorSeverity.HIGH: "ネットワーク接続に問題があります。",
                ErrorSeverity.CRITICAL: "ネットワーク接続が利用できません。"
            },
            ErrorCategory.VALIDATION_ERROR: {
                ErrorSeverity.LOW: "入力データに軽微な問題があります。",
                ErrorSeverity.MEDIUM: "入力データの形式に問題があります。",
                ErrorSeverity.HIGH: "入力データが無効です。",
                ErrorSeverity.CRITICAL: "入力データの検証に失敗しました。"
            },
            ErrorCategory.CONFIGURATION_ERROR: {
                ErrorSeverity.LOW: "設定で軽微な問題が発見されました。",
                ErrorSeverity.MEDIUM: "設定に問題があります。",
                ErrorSeverity.HIGH: "設定エラーにより一部機能が利用できません。",
                ErrorSeverity.CRITICAL: "設定エラーによりシステムが正常に動作しません。"
            },
            ErrorCategory.RESOURCE_ERROR: {
                ErrorSeverity.LOW: "リソース使用量が高くなっています。",
                ErrorSeverity.MEDIUM: "リソース不足により処理が遅くなっています。",
                ErrorSeverity.HIGH: "リソース不足により一部機能が制限されています。",
                ErrorSeverity.CRITICAL: "リソース不足によりシステムが不安定です。"
            },
            ErrorCategory.UNKNOWN_ERROR: {
                ErrorSeverity.LOW: "予期しない問題が発生しました。",
                ErrorSeverity.MEDIUM: "システムで問題が発生しています。",
                ErrorSeverity.HIGH: "システムエラーが発生しました。",
                ErrorSeverity.CRITICAL: "重大なシステムエラーが発生しました。"
            }
        }
        
        # 推奨アクションのマッピング
        self.suggested_actions_map = {
            ErrorCategory.MODEL_ERROR: [
                "しばらく待ってから再試行してください",
                "モデルファイルが正しく配置されているか確認してください",
                "システムリソースに十分な空きがあるか確認してください"
            ],
            ErrorCategory.SYSTEM_MONITOR_ERROR: [
                "システム監視機能を再起動してください",
                "管理者権限で実行されているか確認してください",
                "psutilライブラリが正しくインストールされているか確認してください"
            ],
            ErrorCategory.WEBSOCKET_ERROR: [
                "ページを再読み込みしてください",
                "ネットワーク接続を確認してください",
                "ファイアウォール設定を確認してください"
            ],
            ErrorCategory.NETWORK_ERROR: [
                "インターネット接続を確認してください",
                "VPN接続を確認してください",
                "プロキシ設定を確認してください"
            ],
            ErrorCategory.VALIDATION_ERROR: [
                "入力内容を確認してください",
                "必要な項目がすべて入力されているか確認してください",
                "文字数制限を確認してください"
            ],
            ErrorCategory.CONFIGURATION_ERROR: [
                "設定ファイルを確認してください",
                "環境変数が正しく設定されているか確認してください",
                "必要なファイルが存在するか確認してください"
            ],
            ErrorCategory.RESOURCE_ERROR: [
                "不要なアプリケーションを終了してください",
                "システムリソースの使用状況を確認してください",
                "ディスク容量を確認してください"
            ],
            ErrorCategory.UNKNOWN_ERROR: [
                "システムを再起動してください",
                "ログファイルを確認してください",
                "システム管理者にお問い合わせください"
            ]
        }
    
    def handle_error(self, 
                    exception: Exception, 
                    category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    context: Dict[str, Any] = None,
                    custom_user_message: str = None) -> ErrorInfo:
        """
        エラーを処理してErrorInfoオブジェクトを返す
        
        Args:
            exception: 発生した例外
            category: エラーのカテゴリ
            severity: エラーの重要度
            context: エラーのコンテキスト情報
            custom_user_message: カスタムユーザーメッセージ
            
        Returns:
            ErrorInfo: エラー情報オブジェクト
        """
        import uuid
        
        error_id = str(uuid.uuid4())[:8]
        
        # ユーザーメッセージを決定
        if custom_user_message:
            user_message = custom_user_message
        else:
            user_message = self.user_messages.get(category, {}).get(
                severity, "システムで問題が発生しました。"
            )
        
        # 推奨アクションを取得
        suggested_actions = self.suggested_actions_map.get(category, [
            "しばらく待ってから再試行してください",
            "問題が続く場合はシステム管理者にお問い合わせください"
        ])
        
        # エラー情報を作成
        error_info = ErrorInfo(
            error_id=error_id,
            category=category,
            severity=severity,
            message=str(exception),
            user_message=user_message,
            technical_details=f"{type(exception).__name__}: {str(exception)}",
            timestamp=datetime.now(),
            context=context or {},
            stack_trace=traceback.format_exc(),
            suggested_actions=suggested_actions
        )
        
        # ログに記録
        self._log_error(error_info)
        
        # 履歴に追加
        self._add_to_history(error_info)
        
        # コールバックを実行
        self._execute_callbacks(error_info)
        
        return error_info
    
    def handle_model_error(self, exception: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """モデル関連エラーの処理"""
        # エラーの種類に基づいて重要度を決定
        if "timeout" in str(exception).lower():
            severity = ErrorSeverity.MEDIUM
        elif "memory" in str(exception).lower() or "resource" in str(exception).lower():
            severity = ErrorSeverity.HIGH
        elif "not found" in str(exception).lower() or "missing" in str(exception).lower():
            severity = ErrorSeverity.CRITICAL
        else:
            severity = ErrorSeverity.MEDIUM
        
        return self.handle_error(
            exception=exception,
            category=ErrorCategory.MODEL_ERROR,
            severity=severity,
            context=context
        )
    
    def handle_system_monitor_error(self, exception: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """システム監視エラーの処理"""
        # エラーの種類に基づいて重要度を決定
        if "permission" in str(exception).lower() or "access" in str(exception).lower():
            severity = ErrorSeverity.HIGH
        elif "not found" in str(exception).lower():
            severity = ErrorSeverity.CRITICAL
        else:
            severity = ErrorSeverity.MEDIUM
        
        return self.handle_error(
            exception=exception,
            category=ErrorCategory.SYSTEM_MONITOR_ERROR,
            severity=severity,
            context=context
        )
    
    def handle_websocket_error(self, exception: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """WebSocket関連エラーの処理"""
        # エラーの種類に基づいて重要度を決定
        if "disconnect" in str(exception).lower():
            severity = ErrorSeverity.MEDIUM
        elif "connection" in str(exception).lower():
            severity = ErrorSeverity.HIGH
        else:
            severity = ErrorSeverity.MEDIUM
        
        return self.handle_error(
            exception=exception,
            category=ErrorCategory.WEBSOCKET_ERROR,
            severity=severity,
            context=context
        )
    
    def add_error_callback(self, callback: Callable[[ErrorInfo], None]):
        """エラー発生時のコールバック関数を追加"""
        if callback not in self.error_callbacks:
            self.error_callbacks.append(callback)
    
    def remove_error_callback(self, callback: Callable[[ErrorInfo], None]):
        """エラーコールバック関数を削除"""
        if callback in self.error_callbacks:
            self.error_callbacks.remove(callback)
    
    def get_error_history(self, limit: int = 50) -> List[ErrorInfo]:
        """エラー履歴を取得"""
        return self.error_history[-limit:]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計情報を取得"""
        if not self.error_history:
            return {
                'total_errors': 0,
                'by_category': {},
                'by_severity': {},
                'recent_errors': 0
            }
        
        # カテゴリ別統計
        by_category = {}
        for error in self.error_history:
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        # 重要度別統計
        by_severity = {}
        for error in self.error_history:
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # 最近のエラー（過去1時間）
        from datetime import timedelta
        recent_threshold = datetime.now() - timedelta(hours=1)
        recent_errors = sum(1 for error in self.error_history 
                          if error.timestamp > recent_threshold)
        
        return {
            'total_errors': len(self.error_history),
            'by_category': by_category,
            'by_severity': by_severity,
            'recent_errors': recent_errors
        }
    
    def clear_error_history(self):
        """エラー履歴をクリア"""
        self.error_history.clear()
        self.logger.info("Error history cleared")
    
    def _log_error(self, error_info: ErrorInfo):
        """エラーをログに記録"""
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_info.severity, logging.ERROR)
        
        self.logger.log(
            log_level,
            f"[{error_info.error_id}] {error_info.category.value}: {error_info.message}",
            extra={
                'error_id': error_info.error_id,
                'category': error_info.category.value,
                'severity': error_info.severity.value,
                'context': error_info.context
            }
        )
    
    def _add_to_history(self, error_info: ErrorInfo):
        """エラーを履歴に追加"""
        self.error_history.append(error_info)
        
        # 履歴サイズを制限
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    def _execute_callbacks(self, error_info: ErrorInfo):
        """エラーコールバックを実行"""
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.logger.error(f"Error in error callback: {e}")


class FallbackManager:
    """フォールバック機能管理クラス"""
    
    def __init__(self, error_handler: ErrorHandler):
        """フォールバックマネージャーを初期化"""
        self.error_handler = error_handler
        self.logger = logging.getLogger(__name__)
        self.fallback_data = {
            'system_status': {
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'disk_percent': 0.0,
                'timestamp': datetime.now().isoformat(),
                'status': 'unavailable'
            },
            'chat_responses': [
                "申し訳ございませんが、現在AIモデルが利用できません。",
                "システム情報の取得に問題が発生しています。しばらくお待ちください。",
                "一時的にサービスが利用できません。後ほど再試行してください。"
            ]
        }
    
    async def get_fallback_system_status(self) -> Dict[str, Any]:
        """システム状態のフォールバックデータを取得"""
        try:
            # 基本的なシステム情報を取得を試行
            import psutil
            
            fallback_status = {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'timestamp': datetime.now().isoformat(),
                'status': 'limited',
                'message': 'システム監視機能が制限モードで動作しています'
            }
            
            return fallback_status
            
        except Exception as e:
            self.error_handler.handle_system_monitor_error(
                e, {'context': 'fallback_system_status'}
            )
            
            # 完全なフォールバック
            return {
                **self.fallback_data['system_status'],
                'message': 'システム情報を取得できません'
            }
    
    def get_fallback_chat_response(self, user_message: str = None) -> str:
        """チャット応答のフォールバックメッセージを取得"""
        import random
        
        if user_message and "システム" in user_message:
            return "申し訳ございませんが、現在システム情報の詳細な分析ができません。基本的な情報のみ表示されています。"
        elif user_message and ("助けて" in user_message or "ヘルプ" in user_message):
            return "現在AIアシスタント機能が制限されています。システム管理者にお問い合わせいただくか、しばらく時間をおいて再試行してください。"
        else:
            return random.choice(self.fallback_data['chat_responses'])
    
    async def execute_with_fallback(self, 
                                  primary_func: Callable,
                                  fallback_func: Callable,
                                  error_category: ErrorCategory,
                                  context: Dict[str, Any] = None) -> Any:
        """
        プライマリ機能を実行し、失敗時にフォールバック機能を実行
        
        Args:
            primary_func: メイン機能
            fallback_func: フォールバック機能
            error_category: エラーカテゴリ
            context: コンテキスト情報
            
        Returns:
            プライマリまたはフォールバック機能の結果
        """
        try:
            # プライマリ機能を実行
            if asyncio.iscoroutinefunction(primary_func):
                return await primary_func()
            else:
                return primary_func()
                
        except Exception as e:
            # エラーを処理
            self.error_handler.handle_error(
                exception=e,
                category=error_category,
                context=context or {}
            )
            
            # フォールバック機能を実行
            try:
                if asyncio.iscoroutinefunction(fallback_func):
                    return await fallback_func()
                else:
                    return fallback_func()
            except Exception as fallback_error:
                self.error_handler.handle_error(
                    exception=fallback_error,
                    category=error_category,
                    severity=ErrorSeverity.CRITICAL,
                    context={**(context or {}), 'fallback_failed': True}
                )
                raise fallback_error


# グローバルエラーハンドラーインスタンス
global_error_handler = ErrorHandler()
global_fallback_manager = FallbackManager(global_error_handler)


# 便利な関数
def handle_error(exception: Exception, 
                category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR,
                severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                context: Dict[str, Any] = None) -> ErrorInfo:
    """グローバルエラーハンドラーを使用してエラーを処理"""
    return global_error_handler.handle_error(exception, category, severity, context)


def handle_model_error(exception: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
    """モデルエラーを処理"""
    return global_error_handler.handle_model_error(exception, context)


def handle_system_monitor_error(exception: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
    """システム監視エラーを処理"""
    return global_error_handler.handle_system_monitor_error(exception, context)


def handle_websocket_error(exception: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
    """WebSocketエラーを処理"""
    return global_error_handler.handle_websocket_error(exception, context)


async def execute_with_fallback(primary_func: Callable,
                               fallback_func: Callable,
                               error_category: ErrorCategory,
                               context: Dict[str, Any] = None) -> Any:
    """フォールバック付きで関数を実行"""
    return await global_fallback_manager.execute_with_fallback(
        primary_func, fallback_func, error_category, context
    )


# エラーハンドリングデコレータ
def error_handler_decorator(category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR,
                          severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                          fallback_value: Any = None):
    """エラーハンドリングデコレータ"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                global_error_handler.handle_error(e, category, severity)
                return fallback_value
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                global_error_handler.handle_error(e, category, severity)
                return fallback_value
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator