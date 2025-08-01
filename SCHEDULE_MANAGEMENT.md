# Mac Status PWA - スケジュール管理 ⏰

Mac Status PWAの自動起動・停止スケジュール管理機能について説明します。

## 🎯 **概要**

スケジュール管理機能により、勤務時間中（09:00-18:00）に自動でサーバーを起動・停止できます。これにより、必要な時間帯のみアプリケーションを動作させ、システムリソースを効率的に使用できます。

## 🚀 **クイックセットアップ**

### **自動スケジュール設定**
```bash
# 実行権限を付与
chmod +x setup_schedule.sh remove_schedule.sh

# 自動スケジュール設定
./setup_schedule.sh

# 設定確認
launchctl list | grep macstatus
```

### **スケジュール削除**
```bash
# スケジュール削除
./remove_schedule.sh

# 削除確認
launchctl list | grep macstatus
```

## 📋 **設定ファイル詳細**

### **起動スケジュール (com.macstatus.pwa.plist)**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.macstatus.pwa</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/mac-status-pwa/working_server.py</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>WorkingDirectory</key>
    <string>/path/to/mac-status-pwa</string>
    
    <key>StandardOutPath</key>
    <string>/path/to/mac-status-pwa/logs/macstatus.log</string>
    
    <key>StandardErrorPath</key>
    <string>/path/to/mac-status-pwa/logs/macstatus_error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

### **停止スケジュール (com.macstatus.pwa.stop.plist)**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.macstatus.pwa.stop</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>pkill -f "python.*working_server.py"</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

## 🔧 **手動設定方法**

### **1. plistファイルの作成**
```bash
# 起動用plistファイル作成
cat > ~/Library/LaunchAgents/com.macstatus.pwa.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.macstatus.pwa</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$(pwd)/working_server.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>$(pwd)</string>
    <key>StandardOutPath</key>
    <string>$(pwd)/logs/macstatus.log</string>
    <key>StandardErrorPath</key>
    <string>$(pwd)/logs/macstatus_error.log</string>
</dict>
</plist>
EOF

# 停止用plistファイル作成
cat > ~/Library/LaunchAgents/com.macstatus.pwa.stop.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.macstatus.pwa.stop</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>pkill -f "python.*working_server.py"</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
EOF
```

### **2. launchctlに登録**
```bash
# 起動スケジュール登録
launchctl load ~/Library/LaunchAgents/com.macstatus.pwa.plist

# 停止スケジュール登録
launchctl load ~/Library/LaunchAgents/com.macstatus.pwa.stop.plist

# 登録確認
launchctl list | grep macstatus
```

### **3. ログディレクトリ作成**
```bash
# ログディレクトリ作成
mkdir -p logs

# ログファイルの権限設定
touch logs/macstatus.log logs/macstatus_error.log
chmod 644 logs/macstatus.log logs/macstatus_error.log
```

## ⚙️ **カスタマイズ**

### **時間の変更**
```bash
# 起動時間を8:30に変更
sed -i '' 's/<integer>9<\/integer>/<integer>8<\/integer>/' ~/Library/LaunchAgents/com.macstatus.pwa.plist
sed -i '' 's/<integer>0<\/integer>/<integer>30<\/integer>/' ~/Library/LaunchAgents/com.macstatus.pwa.plist

# 停止時間を19:00に変更
sed -i '' 's/<integer>18<\/integer>/<integer>19<\/integer>/' ~/Library/LaunchAgents/com.macstatus.pwa.stop.plist

# 設定を再読み込み
launchctl unload ~/Library/LaunchAgents/com.macstatus.pwa.plist
launchctl load ~/Library/LaunchAgents/com.macstatus.pwa.plist
```

### **平日のみ実行**
```xml
<!-- 平日のみ実行する場合 -->
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Weekday</key>
        <integer>1</integer> <!-- 月曜日 -->
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Weekday</key>
        <integer>2</integer> <!-- 火曜日 -->
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <!-- 水曜日から金曜日も同様に追加 -->
</array>
```

### **複数回起動**
```xml
<!-- 1日に複数回起動する場合 -->
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>13</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</array>
```

## 📊 **監視とログ**

### **スケジュール状態確認**
```bash
# 登録済みスケジュール一覧
launchctl list | grep macstatus

# 特定スケジュールの詳細
launchctl list com.macstatus.pwa

# スケジュールの実行履歴
log show --predicate 'subsystem == "com.apple.launchd"' --info | grep macstatus
```

### **ログ監視**
```bash
# リアルタイムログ監視
tail -f logs/macstatus.log

# エラーログ確認
tail -f logs/macstatus_error.log

# ログローテーション設定
cat > logs/logrotate.conf << 'EOF'
logs/macstatus.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
EOF
```

### **プロセス監視**
```bash
# Mac Status PWAプロセス確認
ps aux | grep "python.*working_server.py"

# ポート使用状況確認
lsof -i :8002

# システムリソース使用量
top -pid $(pgrep -f "python.*working_server.py")
```

## 🚨 **トラブルシューティング**

### **よくある問題**

**1. スケジュールが実行されない**
```bash
# plistファイルの構文確認
plutil -lint ~/Library/LaunchAgents/com.macstatus.pwa.plist

# 権限確認
ls -la ~/Library/LaunchAgents/com.macstatus.pwa*

# launchd設定確認
launchctl print gui/$(id -u)/com.macstatus.pwa
```

**2. Pythonパスが見つからない**
```bash
# Pythonパス確認
which python3

# plistファイルのPythonパス修正
sed -i '' 's|/usr/bin/python3|$(which python3)|' ~/Library/LaunchAgents/com.macstatus.pwa.plist
```

**3. 作業ディレクトリエラー**
```bash
# 作業ディレクトリ確認
pwd

# plistファイルのパス修正
sed -i '' "s|/path/to/mac-status-pwa|$(pwd)|g" ~/Library/LaunchAgents/com.macstatus.pwa.plist
```

**4. 権限エラー**
```bash
# ファイル権限修正
chmod 644 ~/Library/LaunchAgents/com.macstatus.pwa*
chmod +x working_server.py

# ログディレクトリ権限修正
chmod 755 logs
chmod 644 logs/*
```

### **デバッグ方法**

**1. 手動実行テスト**
```bash
# スケジュールを手動実行
launchctl start com.macstatus.pwa

# 実行状況確認
launchctl list com.macstatus.pwa
```

**2. 詳細ログ有効化**
```xml
<!-- plistファイルにデバッグ設定追加 -->
<key>Debug</key>
<true/>

<key>StandardOutPath</key>
<string>/path/to/mac-status-pwa/logs/macstatus_debug.log</string>
```

**3. システムログ確認**
```bash
# システムログでlaunchd関連エラー確認
log show --predicate 'subsystem == "com.apple.launchd"' --last 1h | grep macstatus

# Console.appでGUIログ確認
open /Applications/Utilities/Console.app
```

## 🔄 **アップデート・メンテナンス**

### **スケジュール更新**
```bash
# 既存スケジュール停止
launchctl unload ~/Library/LaunchAgents/com.macstatus.pwa.plist
launchctl unload ~/Library/LaunchAgents/com.macstatus.pwa.stop.plist

# plistファイル更新
# （設定変更）

# スケジュール再開
launchctl load ~/Library/LaunchAgents/com.macstatus.pwa.plist
launchctl load ~/Library/LaunchAgents/com.macstatus.pwa.stop.plist
```

### **ログメンテナンス**
```bash
# 古いログファイル削除
find logs -name "*.log" -mtime +30 -delete

# ログサイズ確認
du -sh logs/

# ログ圧縮
gzip logs/macstatus.log.old
```

### **完全削除**
```bash
# スケジュール停止・削除
launchctl unload ~/Library/LaunchAgents/com.macstatus.pwa.plist
launchctl unload ~/Library/LaunchAgents/com.macstatus.pwa.stop.plist

# plistファイル削除
rm ~/Library/LaunchAgents/com.macstatus.pwa.plist
rm ~/Library/LaunchAgents/com.macstatus.pwa.stop.plist

# プロセス強制終了
pkill -f "python.*working_server.py"
```

## 📚 **参考情報**

### **launchd関連コマンド**
```bash
# 全スケジュール一覧
launchctl list

# 特定スケジュール詳細
launchctl print gui/$(id -u)/com.macstatus.pwa

# スケジュール手動実行
launchctl start com.macstatus.pwa

# スケジュール停止
launchctl stop com.macstatus.pwa
```

### **時間指定フォーマット**
- **Hour**: 0-23 (24時間形式)
- **Minute**: 0-59
- **Weekday**: 0=日曜日, 1=月曜日, ..., 6=土曜日
- **Day**: 1-31 (月の日)
- **Month**: 1-12

### **環境変数設定**
```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin</string>
    <key>PYTHONPATH</key>
    <string>/path/to/mac-status-pwa</string>
    <key>HOME</key>
    <string>/Users/username</string>
</dict>
```

---

**スケジュール管理により、Mac Status PWAを効率的に運用しましょう！** ⏰✨