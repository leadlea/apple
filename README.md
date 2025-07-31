# Mac Status PWA

**プライバシー重視のMacシステム監視Progressive Web Application**

リアルタイムでMacのシステム状態を監視し、自然な日本語でAIアシスタントと対話できるPWAアプリケーションです。全ての処理がローカルで実行され、データが外部に送信されることはありません。

![Mac Status PWA](https://img.shields.io/badge/PWA-Ready-brightgreen) ![Platform](https://img.shields.io/badge/Platform-macOS-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## 🌟 主な機能

### 📊 **リアルタイムシステム監視**
- **CPU使用率**: リアルタイムでCPU使用状況を表示
- **メモリ使用量**: 使用率と詳細な容量情報
- **ディスク使用量**: ストレージの使用状況
- **プロセス監視**: 上位プロセスの表示
- **自動更新**: 2秒ごとの自動データ更新

### 🤖 **AIチャットアシスタント**
- **自然な日本語対話**: システム状態について質問可能
- **動的な応答**: 質問に応じて異なる回答を生成
- **システム分析**: パフォーマンス問題の特定と提案
- **多様な質問対応**: CPU、メモリ、ディスク、プロセス情報

### 📱 **Progressive Web App**
- **インストール可能**: ブラウザからアプリとしてインストール
- **オフライン対応**: Service Workerによるオフライン機能
- **レスポンシブデザイン**: モバイル・デスクトップ対応
- **Apple風デザイン**: macOSネイティブライクなUI

### 🔒 **プライバシー・セキュリティ**
- **完全ローカル処理**: 全てのデータがローカルで処理
- **外部通信なし**: インターネット接続不要
- **セキュアな通信**: WebSocketによる暗号化通信
- **データ保護**: 個人情報の外部流出なし

## 🚀 クイックスタート

### 必要な環境
- **macOS**: 10.15以降（推奨）
- **Python**: 3.12以降
- **メモリ**: 8GB以上（推奨）
- **ディスク容量**: 5GB以上の空き容量

### インストール

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/leadlea/apple.git
   cd apple
   ```

2. **自動セットアップ**
   ```bash
   python setup.py
   ```

3. **サーバーの起動**
   ```bash
   python working_server.py
   ```

4. **ブラウザでアクセス**
   - メイン版: http://localhost:8002
   - 修正版: http://localhost:8002/fixed （推奨）
   - デバッグ版: debug_test.html

### PWAとしてインストール

1. ブラウザでアプリを開く
2. アドレスバーのインストールアイコンをクリック
3. 「インストール」を選択
4. デスクトップアプリとして利用可能

## 📁 プロジェクト構造

```
mac-status-pwa/
├── README.md                    # このファイル
├── INSTALL.md                   # 詳細インストールガイド
├── TROUBLESHOOTING.md           # トラブルシューティング
├── working_server.py            # メインサーバー（推奨）
├── fixed_index.html             # 修正版フロントエンド（推奨）
├── debug_test.html              # デバッグ用テストページ
├── setup.py                     # 自動セットアップスクリプト
├── requirements.txt             # Python依存関係
├── frontend/                    # フロントエンドファイル
│   ├── index.html              # メインHTML
│   ├── app.js                  # JavaScript
│   ├── styles.css              # Apple風CSS
│   ├── manifest.json           # PWAマニフェスト
│   ├── sw.js                   # Service Worker
│   └── icons/                  # PWAアイコン
├── backend/                     # バックエンドコンポーネント
│   ├── main.py                 # FastAPIメインアプリ
│   ├── system_monitor.py       # システム監視
│   ├── websocket_server.py     # WebSocket通信
│   └── ...                     # その他のモジュール
├── config/                      # 設定ファイル
│   ├── production.py           # 本番設定
│   └── security.py             # セキュリティ設定
├── tests/                       # テストスイート
├── demo_data/                   # デモ用サンプルデータ
└── .github/workflows/           # CI/CD設定
```

## 💬 使用方法

### 基本的な質問例

```
「CPUの使用率はどうですか？」
「メモリの状況を教えて」
「システム全体の状況は？」
「システムが重い理由は？」
「プロセスの状況は？」
「こんにちは」
```

### システム監視

- **ダッシュボード**: 上部のカードでリアルタイム監視
- **詳細情報**: チャットで具体的な質問
- **アラート**: 使用率が高い場合の警告表示
- **履歴**: 会話履歴の保持

## 🔧 開発・カスタマイズ

### 開発環境のセットアップ

```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 依存関係のインストール
pip install -r requirements.txt

# 開発サーバーの起動
python working_server.py
```

### 設定のカスタマイズ

**config/production.py** でサーバー設定を変更：
```python
SERVER_CONFIG = {
    "host": "127.0.0.1",
    "port": 8002,
    "debug": False
}
```

**frontend/styles.css** でデザインをカスタマイズ：
- Apple風カラーパレット
- レスポンシブデザイン
- アニメーション効果

### テスト実行

```bash
# 全テストの実行
python -m pytest tests/ -v

# 統合テストの実行
python demo_system_integration.py

# WebSocket通信テスト
python test_working_server.py
```

## 📊 パフォーマンス

### システム要件
- **応答時間**: 平均2-4秒
- **メモリ使用量**: 約150-400MB
- **CPU使用率**: 通常時1-5%
- **ディスク使用量**: 約50MB

### 最適化
- **M1チップ対応**: Apple Siliconに最適化
- **効率的な監視**: 最小限のシステム負荷
- **キャッシュ機能**: 高速な応答
- **非同期処理**: ノンブロッキング動作

## 🛠️ トラブルシューティング

### よくある問題

**ダッシュボードに数値が表示されない**
```bash
# 修正版を使用
http://localhost:8002/fixed
```

**WebSocket接続エラー**
```bash
# ポートの確認
lsof -i :8002

# サーバーの再起動
python working_server.py
```

**PWAがインストールできない**
- HTTPSまたはlocalhostでアクセス
- ブラウザのPWA機能を有効化
- キャッシュをクリア

詳細は [TROUBLESHOOTING.md](TROUBLESHOOTING.md) を参照してください。

## 🧪 テスト・デバッグ

### デバッグツール

1. **デバッグテストページ**
   ```bash
   # ブラウザで開く
   file:///path/to/debug_test.html
   ```

2. **統合テスト**
   ```bash
   python demo_system_integration.py
   ```

3. **ブラウザ開発者ツール**
   - F12でコンソールを開く
   - WebSocket通信を監視
   - エラーログを確認

### テスト結果
- **テスト成功率**: 91.6% (296/323テスト)
- **統合テスト**: 全7カテゴリで動作確認
- **パフォーマンステスト**: M1 Mac最適化確認

## 📚 ドキュメント

- **[INSTALL.md](INSTALL.md)**: 詳細なインストール手順
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**: 問題解決ガイド
- **[demo_data/README.md](demo_data/README.md)**: デモデータの使用方法
- **[.kiro/specs/](./kiro/specs/)**: 設計仕様書

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Requestを作成

### 開発ガイドライン
- PEP 8スタイルガイドに従う
- 新機能にはテストを追加
- ドキュメントを更新
- 全テストが通ることを確認

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 🙏 謝辞

- **Apple**: デザインインスピレーション
- **FastAPI**: 高速なWebフレームワーク
- **psutil**: システム監視ライブラリ
- **WebSocket**: リアルタイム通信

## 📞 サポート

- **Issues**: [GitHub Issues](https://github.com/leadlea/apple/issues)
- **Discussions**: [GitHub Discussions](https://github.com/leadlea/apple/discussions)
- **Email**: プロジェクトメンテナーまで

## 🔄 更新履歴

### v1.0.0 (2024-07-31)
- ✅ 初回リリース
- ✅ リアルタイムシステム監視機能
- ✅ AIチャットアシスタント
- ✅ PWA対応
- ✅ Apple風デザイン
- ✅ 完全ローカル処理
- ✅ M1チップ最適化
- ✅ 包括的テストスイート
- ✅ 詳細ドキュメント

---

**Mac Status PWA** - プライバシーを重視するMacユーザーのための、美しく機能的なシステム監視ツール 🍎✨