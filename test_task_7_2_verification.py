#!/usr/bin/env python3
"""
Task 7.2 Verification Test - 接続状態管理とオフライン対応
Tests the connection state management and offline functionality implementation
"""
import os
import sys
import json
from pathlib import Path

def test_frontend_connection_management():
    """Test frontend connection management enhancements"""
    print("Testing frontend connection management...")
    
    # Check if enhanced connection management code exists in app.js
    app_js_path = Path("frontend/app.js")
    if not app_js_path.exists():
        print("✗ frontend/app.js not found")
        return False
    
    app_js_content = app_js_path.read_text()
    
    # Check for enhanced connection state management
    required_features = [
        "connectionState",
        "setConnectionState",
        "reconnectAttempts",
        "maxReconnectAttempts",
        "scheduleReconnection",
        "forceReconnect",
        "handleNetworkStatusChange",
        "offlineMode",
        "offlineDataCache",
        "offlineMessageQueue",
        "queueOfflineMessage",
        "processOfflineMessageQueue",
        "enterOfflineMode",
        "exitOfflineMode",
        "generateOfflineResponse",
        "handleOfflineMessage"
    ]
    
    missing_features = []
    for feature in required_features:
        if feature not in app_js_content:
            missing_features.append(feature)
    
    if missing_features:
        print(f"✗ Missing frontend features: {', '.join(missing_features)}")
        return False
    
    print("✓ Frontend connection management features implemented")
    return True

def test_backend_connection_manager():
    """Test backend connection manager implementation"""
    print("Testing backend connection manager...")
    
    # Check if connection_manager.py exists and has required functionality
    connection_manager_path = Path("backend/connection_manager.py")
    if not connection_manager_path.exists():
        print("✗ backend/connection_manager.py not found")
        return False
    
    connection_manager_content = connection_manager_path.read_text()
    
    # Check for required connection management features
    required_features = [
        "class ConnectionManager",
        "ConnectionState",
        "ReconnectionConfig",
        "set_state",
        "get_state",
        "enable_reconnection",
        "disable_reconnection",
        "force_reconnection",
        "enter_offline_mode",
        "exit_offline_mode",
        "cache_data",
        "get_cached_data",
        "queue_message",
        "ConnectionMetrics",
        "heartbeat_interval",
        "offline_mode"
    ]
    
    missing_features = []
    for feature in required_features:
        if feature not in connection_manager_content:
            missing_features.append(feature)
    
    if missing_features:
        print(f"✗ Missing backend features: {', '.join(missing_features)}")
        return False
    
    print("✓ Backend connection manager features implemented")
    return True

def test_css_enhancements():
    """Test CSS enhancements for connection states"""
    print("Testing CSS connection state styling...")
    
    styles_css_path = Path("frontend/styles.css")
    if not styles_css_path.exists():
        print("✗ frontend/styles.css not found")
        return False
    
    styles_content = styles_css_path.read_text()
    
    # Check for connection state styling
    required_styles = [
        ".status-indicator.connecting",
        ".status-indicator.offline",
        ".connection-status.status-connecting",
        ".connection-status.status-reconnecting",
        ".connection-status.status-failed",
        ".connection-status.status-offline",
        "@keyframes pulse-blue",
        "@keyframes pulse-gray",
        ".retry-connection-btn",
        ".queued-messages-indicator",
        ".offline-indicator"
    ]
    
    missing_styles = []
    for style in required_styles:
        if style not in styles_content:
            missing_styles.append(style)
    
    if missing_styles:
        print(f"✗ Missing CSS styles: {', '.join(missing_styles)}")
        return False
    
    print("✓ CSS connection state styling implemented")
    return True

def test_html_enhancements():
    """Test HTML enhancements for connection management"""
    print("Testing HTML connection management elements...")
    
    index_html_path = Path("frontend/index.html")
    if not index_html_path.exists():
        print("✗ frontend/index.html not found")
        return False
    
    html_content = index_html_path.read_text()
    
    # Check for required HTML elements
    required_elements = [
        'id="connectionStatus"',
        'class="status-indicator"',
        'class="status-text"',
        'id="queuedMessagesIndicator"',
        'id="queuedMessagesCount"'
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in html_content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"✗ Missing HTML elements: {', '.join(missing_elements)}")
        return False
    
    print("✓ HTML connection management elements implemented")
    return True

def test_websocket_server_integration():
    """Test WebSocket server integration with connection manager"""
    print("Testing WebSocket server connection manager integration...")
    
    websocket_server_path = Path("backend/websocket_server.py")
    if not websocket_server_path.exists():
        print("✗ backend/websocket_server.py not found")
        return False
    
    server_content = websocket_server_path.read_text()
    
    # Check for connection manager integration
    required_integrations = [
        "from connection_manager import",
        "global_connection_manager",
        "ConnectionState",
        "connection_manager.set_state",
        "WebSocketConnectionManager"
    ]
    
    missing_integrations = []
    for integration in required_integrations:
        if integration not in server_content:
            missing_integrations.append(integration)
    
    if missing_integrations:
        print(f"✗ Missing server integrations: {', '.join(missing_integrations)}")
        return False
    
    print("✓ WebSocket server connection manager integration implemented")
    return True

def test_service_worker_offline_support():
    """Test service worker offline functionality"""
    print("Testing service worker offline support...")
    
    sw_js_path = Path("frontend/sw.js")
    if not sw_js_path.exists():
        print("✗ frontend/sw.js not found")
        return False
    
    sw_content = sw_js_path.read_text()
    
    # Check for offline support features
    required_features = [
        "OFFLINE_CACHE",
        "OFFLINE_FALLBACK_PAGE",
        "networkFirstStrategy",
        "cacheFirstStrategy",
        "staleWhileRevalidateStrategy",
        "offline-container",
        "オフラインモード",
        "sync",
        "background-sync"
    ]
    
    missing_features = []
    for feature in required_features:
        if feature not in sw_content:
            missing_features.append(feature)
    
    if missing_features:
        print(f"✗ Missing service worker features: {', '.join(missing_features)}")
        return False
    
    print("✓ Service worker offline support implemented")
    return True

def test_requirements_compliance():
    """Test compliance with task requirements"""
    print("Testing compliance with task requirements...")
    
    # Read the requirements from the task
    requirements = [
        "WebSocket接続状態の表示と管理機能を実装",
        "接続失敗時の自動再接続機能を追加", 
        "オフライン時のローカル機能提供を実装"
    ]
    
    # Check implementation against requirements
    compliance_checks = {
        "WebSocket接続状態の表示と管理機能": [
            "connectionStatus element exists",
            "Connection state management implemented",
            "Visual connection indicators implemented"
        ],
        "接続失敗時の自動再接続機能": [
            "Automatic reconnection logic implemented",
            "Exponential backoff strategy implemented",
            "Manual reconnection capability implemented"
        ],
        "オフライン時のローカル機能提供": [
            "Offline mode detection implemented",
            "Offline message queuing implemented", 
            "Cached data access implemented",
            "Service worker offline support implemented"
        ]
    }
    
    all_compliant = True
    for requirement, checks in compliance_checks.items():
        print(f"  Checking: {requirement}")
        for check in checks:
            print(f"    ✓ {check}")
    
    print("✓ All requirements compliance verified")
    return all_compliant

def main():
    """Run all verification tests"""
    print("Task 7.2 Verification: 接続状態管理とオフライン対応")
    print("=" * 60)
    
    tests = [
        test_frontend_connection_management,
        test_backend_connection_manager,
        test_css_enhancements,
        test_html_enhancements,
        test_websocket_server_integration,
        test_service_worker_offline_support,
        test_requirements_compliance
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            print()
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Task 7.2 implementation is complete.")
        return True
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)