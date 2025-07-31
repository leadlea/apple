"""
エラーハンドリングシステムのテスト
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from error_handler import (
    ErrorHandler,
    FallbackManager,
    ErrorCategory,
    ErrorSeverity,
    ErrorInfo,
    handle_error,
    handle_model_error,
    handle_system_monitor_error,
    handle_websocket_error,
    execute_with_fallback,
    error_handler_decorator
)


class TestErrorHandler:
    """ErrorHandlerクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.error_handler = ErrorHandler()
    
    def test_handle_error_basic(self):
        """基本的なエラーハンドリングのテスト"""
        exception = ValueError("Test error")
        
        error_info = self.error_handler.handle_error(
            exception=exception,
            category=ErrorCategory.MODEL_ERROR,
            severity=ErrorSeverity.MEDIUM
        )
        
        assert error_info.category == ErrorCategory.MODEL_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.message == "Test error"
        assert "Test error" in error_info.technical_details
        assert len(error_info.suggested_actions) > 0
        assert error_info.error_id is not None
    
    def test_handle_error_with_context(self):
        """コンテキスト付きエラーハンドリングのテスト"""
        exception = RuntimeError("Runtime error")
        context = {"component": "test_component", "user_id": "test_user"}
        
        error_info = self.error_handler.handle_error(
            exception=exception,
            context=context
        )
        
        assert error_info.context == context
        assert "test_component" in str(error_info.context)
    
    def test_handle_error_custom_message(self):
        """カスタムユーザーメッセージのテスト"""
        exception = Exception("Technical error")
        custom_message = "カスタムエラーメッセージ"
        
        error_info = self.error_handler.handle_error(
            exception=exception,
            custom_user_message=custom_message
        )
        
        assert error_info.user_message == custom_message
    
    def test_handle_model_error(self):
        """モデルエラーハンドリングのテスト"""
        # タイムアウトエラー
        timeout_error = TimeoutError("Model timeout")
        error_info = self.error_handler.handle_model_error(timeout_error)
        assert error_info.severity == ErrorSeverity.MEDIUM
        
        # メモリエラー
        memory_error = MemoryError("Out of memory")
        error_info = self.error_handler.handle_model_error(memory_error)
        assert error_info.severity == ErrorSeverity.HIGH
        
        # ファイル未発見エラー
        not_found_error = FileNotFoundError("Model not found")
        error_info = self.error_handler.handle_model_error(not_found_error)
        assert error_info.severity == ErrorSeverity.CRITICAL
    
    def test_handle_system_monitor_error(self):
        """システム監視エラーハンドリングのテスト"""
        # 権限エラー
        permission_error = PermissionError("Access denied")
        error_info = self.error_handler.handle_system_monitor_error(permission_error)
        assert error_info.severity == ErrorSeverity.HIGH
        
        # ファイル未発見エラー
        not_found_error = FileNotFoundError("System file not found")
        error_info = self.error_handler.handle_system_monitor_error(not_found_error)
        assert error_info.severity == ErrorSeverity.CRITICAL
    
    def test_handle_websocket_error(self):
        """WebSocketエラーハンドリングのテスト"""
        # 切断エラー
        disconnect_error = ConnectionError("WebSocket disconnect")
        error_info = self.error_handler.handle_websocket_error(disconnect_error)
        assert error_info.severity == ErrorSeverity.MEDIUM
        
        # 接続エラー
        connection_error = ConnectionError("Connection failed")
        error_info = self.error_handler.handle_websocket_error(connection_error)
        assert error_info.severity == ErrorSeverity.HIGH
    
    def test_error_history(self):
        """エラー履歴のテスト"""
        # 初期状態
        assert len(self.error_handler.get_error_history()) == 0
        
        # エラーを追加
        for i in range(5):
            exception = ValueError(f"Error {i}")
            self.error_handler.handle_error(exception)
        
        # 履歴確認
        history = self.error_handler.get_error_history()
        assert len(history) == 5
        assert all(isinstance(error, ErrorInfo) for error in history)
    
    def test_error_statistics(self):
        """エラー統計のテスト"""
        # 異なるカテゴリとレベルのエラーを追加
        self.error_handler.handle_error(ValueError("Error 1"), ErrorCategory.MODEL_ERROR, ErrorSeverity.LOW)
        self.error_handler.handle_error(RuntimeError("Error 2"), ErrorCategory.MODEL_ERROR, ErrorSeverity.HIGH)
        self.error_handler.handle_error(ConnectionError("Error 3"), ErrorCategory.WEBSOCKET_ERROR, ErrorSeverity.MEDIUM)
        
        stats = self.error_handler.get_error_statistics()
        
        assert stats['total_errors'] == 3
        assert stats['by_category']['model_error'] == 2
        assert stats['by_category']['websocket_error'] == 1
        assert stats['by_severity']['low'] == 1
        assert stats['by_severity']['medium'] == 1
        assert stats['by_severity']['high'] == 1
    
    def test_error_callbacks(self):
        """エラーコールバックのテスト"""
        callback_called = False
        received_error = None
        
        def test_callback(error_info):
            nonlocal callback_called, received_error
            callback_called = True
            received_error = error_info
        
        # コールバックを追加
        self.error_handler.add_error_callback(test_callback)
        
        # エラーを発生させる
        exception = ValueError("Test callback error")
        error_info = self.error_handler.handle_error(exception)
        
        # コールバックが呼ばれたことを確認
        assert callback_called
        assert received_error == error_info
        
        # コールバックを削除
        self.error_handler.remove_error_callback(test_callback)
        
        # 再度エラーを発生させる
        callback_called = False
        self.error_handler.handle_error(ValueError("Another error"))
        assert not callback_called
    
    def test_clear_error_history(self):
        """エラー履歴クリアのテスト"""
        # エラーを追加
        self.error_handler.handle_error(ValueError("Error"))
        assert len(self.error_handler.get_error_history()) == 1
        
        # 履歴をクリア
        self.error_handler.clear_error_history()
        assert len(self.error_handler.get_error_history()) == 0


class TestFallbackManager:
    """FallbackManagerクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.error_handler = ErrorHandler()
        self.fallback_manager = FallbackManager(self.error_handler)
    
    @pytest.mark.asyncio
    async def test_get_fallback_system_status(self):
        """フォールバックシステム状態のテスト"""
        status = await self.fallback_manager.get_fallback_system_status()
        
        assert 'cpu_percent' in status
        assert 'memory_percent' in status
        assert 'disk_percent' in status
        assert 'timestamp' in status
        assert 'status' in status
    
    def test_get_fallback_chat_response(self):
        """フォールバックチャット応答のテスト"""
        # 一般的なメッセージ
        response = self.fallback_manager.get_fallback_chat_response("こんにちは")
        assert isinstance(response, str)
        assert len(response) > 0
        
        # システム関連のメッセージ
        system_response = self.fallback_manager.get_fallback_chat_response("システムの状態を教えて")
        assert "システム情報" in system_response
        
        # ヘルプメッセージ
        help_response = self.fallback_manager.get_fallback_chat_response("助けて")
        assert "制限" in help_response or "管理者" in help_response
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_success(self):
        """フォールバック実行（成功）のテスト"""
        async def primary_func():
            return "primary_result"
        
        async def fallback_func():
            return "fallback_result"
        
        result = await self.fallback_manager.execute_with_fallback(
            primary_func=primary_func,
            fallback_func=fallback_func,
            error_category=ErrorCategory.MODEL_ERROR
        )
        
        assert result == "primary_result"
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_failure(self):
        """フォールバック実行（失敗）のテスト"""
        async def primary_func():
            raise ValueError("Primary function failed")
        
        async def fallback_func():
            return "fallback_result"
        
        result = await self.fallback_manager.execute_with_fallback(
            primary_func=primary_func,
            fallback_func=fallback_func,
            error_category=ErrorCategory.MODEL_ERROR
        )
        
        assert result == "fallback_result"
        
        # エラーが記録されていることを確認
        history = self.error_handler.get_error_history()
        assert len(history) > 0
        assert history[-1].message == "Primary function failed"
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_both_fail(self):
        """フォールバック実行（両方失敗）のテスト"""
        async def primary_func():
            raise ValueError("Primary function failed")
        
        async def fallback_func():
            raise RuntimeError("Fallback function failed")
        
        with pytest.raises(RuntimeError, match="Fallback function failed"):
            await self.fallback_manager.execute_with_fallback(
                primary_func=primary_func,
                fallback_func=fallback_func,
                error_category=ErrorCategory.MODEL_ERROR
            )
        
        # 両方のエラーが記録されていることを確認
        history = self.error_handler.get_error_history()
        assert len(history) >= 2


class TestGlobalFunctions:
    """グローバル関数のテスト"""
    
    def test_handle_error_function(self):
        """handle_error関数のテスト"""
        exception = ValueError("Global function test")
        error_info = handle_error(exception, ErrorCategory.MODEL_ERROR, ErrorSeverity.HIGH)
        
        assert error_info.category == ErrorCategory.MODEL_ERROR
        assert error_info.severity == ErrorSeverity.HIGH
        assert error_info.message == "Global function test"
    
    def test_handle_model_error_function(self):
        """handle_model_error関数のテスト"""
        exception = TimeoutError("Model timeout")
        error_info = handle_model_error(exception)
        
        assert error_info.category == ErrorCategory.MODEL_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM
    
    def test_handle_system_monitor_error_function(self):
        """handle_system_monitor_error関数のテスト"""
        exception = PermissionError("Access denied")
        error_info = handle_system_monitor_error(exception)
        
        assert error_info.category == ErrorCategory.SYSTEM_MONITOR_ERROR
        assert error_info.severity == ErrorSeverity.HIGH
    
    def test_handle_websocket_error_function(self):
        """handle_websocket_error関数のテスト"""
        exception = ConnectionError("WebSocket error")
        error_info = handle_websocket_error(exception)
        
        assert error_info.category == ErrorCategory.WEBSOCKET_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM  # ConnectionErrorはMEDIUMレベル
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_function(self):
        """execute_with_fallback関数のテスト"""
        async def primary_func():
            return "success"
        
        async def fallback_func():
            return "fallback"
        
        result = await execute_with_fallback(
            primary_func=primary_func,
            fallback_func=fallback_func,
            error_category=ErrorCategory.MODEL_ERROR
        )
        
        assert result == "success"


class TestErrorHandlerDecorator:
    """エラーハンドリングデコレータのテスト"""
    
    def test_sync_decorator_success(self):
        """同期関数デコレータ（成功）のテスト"""
        @error_handler_decorator(ErrorCategory.MODEL_ERROR, ErrorSeverity.MEDIUM, "fallback")
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_sync_decorator_failure(self):
        """同期関数デコレータ（失敗）のテスト"""
        @error_handler_decorator(ErrorCategory.MODEL_ERROR, ErrorSeverity.MEDIUM, "fallback")
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        assert result == "fallback"
    
    @pytest.mark.asyncio
    async def test_async_decorator_success(self):
        """非同期関数デコレータ（成功）のテスト"""
        @error_handler_decorator(ErrorCategory.MODEL_ERROR, ErrorSeverity.MEDIUM, "fallback")
        async def test_function():
            return "success"
        
        result = await test_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_async_decorator_failure(self):
        """非同期関数デコレータ（失敗）のテスト"""
        @error_handler_decorator(ErrorCategory.MODEL_ERROR, ErrorSeverity.MEDIUM, "fallback")
        async def test_function():
            raise ValueError("Test error")
        
        result = await test_function()
        assert result == "fallback"


if __name__ == "__main__":
    # 基本的なテストを実行
    pytest.main([__file__, "-v"])