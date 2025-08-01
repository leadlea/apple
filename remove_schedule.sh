#!/bin/bash

# Mac Status PWA 自動スケジュール削除スクリプト

echo "🗑️ Mac Status PWA 自動スケジュールを削除します..."

LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

# ジョブを停止・削除
echo "⏹️ スケジュールを停止中..."
launchctl unload "$LAUNCH_AGENTS_DIR/com.macstatus.pwa.plist" 2>/dev/null || true
launchctl unload "$LAUNCH_AGENTS_DIR/com.macstatus.pwa.stop.plist" 2>/dev/null || true

# plistファイルを削除
echo "🗂️ plistファイルを削除中..."
rm -f "$LAUNCH_AGENTS_DIR/com.macstatus.pwa.plist"
rm -f "$LAUNCH_AGENTS_DIR/com.macstatus.pwa.stop.plist"

# 実行中のサーバーを停止
echo "🔌 実行中のサーバーを停止中..."
pkill -f "python3.*working_server.py" 2>/dev/null || true

echo "✅ 削除完了！"
echo "📋 確認: launchctl list | grep macstatus"