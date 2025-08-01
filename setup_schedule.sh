#!/bin/bash

# Mac Status PWA 自動スケジュール設定スクリプト

echo "🚀 Mac Status PWA 自動スケジュール設定を開始します..."

# ログディレクトリ作成
mkdir -p logs

# LaunchAgents ディレクトリ確認・作成
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS_DIR"

# plistファイルをLaunchAgentsにコピー
echo "📋 plistファイルをコピー中..."
cp com.macstatus.pwa.plist "$LAUNCH_AGENTS_DIR/"
cp com.macstatus.pwa.stop.plist "$LAUNCH_AGENTS_DIR/"

# 既存のジョブを停止・削除（エラーを無視）
echo "🔄 既存のスケジュールをクリア中..."
launchctl unload "$LAUNCH_AGENTS_DIR/com.macstatus.pwa.plist" 2>/dev/null || true
launchctl unload "$LAUNCH_AGENTS_DIR/com.macstatus.pwa.stop.plist" 2>/dev/null || true

# 新しいジョブを登録
echo "⏰ 新しいスケジュールを登録中..."
launchctl load "$LAUNCH_AGENTS_DIR/com.macstatus.pwa.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.macstatus.pwa.stop.plist"

echo "✅ 設定完了！"
echo ""
echo "📅 スケジュール:"
echo "   🌅 09:00 - サーバー自動起動"
echo "   🌆 18:00 - サーバー自動停止"
echo ""
echo "🔍 確認コマンド:"
echo "   launchctl list | grep macstatus"
echo ""
echo "🗂️ ログファイル:"
echo "   📄 通常ログ: $(pwd)/logs/macstatus.log"
echo "   ❌ エラーログ: $(pwd)/logs/macstatus_error.log"
echo ""
echo "🌐 PWAアクセス: http://localhost:8002/fixed"