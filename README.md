# Mac Status PWA – Ollama 対応版 README

このリポジトリは **macOS のシステム状況を PWA で可視化**し、チャット欄から
- 日常会話（スモールトーク）
- CPU/メモリ/ディスク/プロセスなどの**システム質問**

に答える **FastAPI + WebSocket** サーバです。  
LLM は **Ollama（llama3.1:8b-instruct-q4_K_M）** を利用し、失敗時は**安全なフォールバック応答**に切替わります。

---

## 今回の主な更新（2025-08）

- **ELYZA 依存を削除**し、**Ollama** へ完全移行
- 「おはよう」等の**雑談は `/api/chat`** で軽量応答、
  **システム質問は `/api/generate`** で状況（CPU/メモリ等）を織り込んで回答
- **起動時ウォームアップ**（1トークン生成 + `/api/tags` Ping）で初回タイムアウトを回避
- **段階的タイムアウト & 自動リトライ**を実装（デフォルト：180s → 360s で再試行）
- 依存関係を整理（`fastapi[standard]`, `requests`, `psutil`）
- `README.md` を全面更新（このファイル）

> **注**: cred の自動生成等で環境変数を変更したくないケースを考慮し、**環境変数は必須ではありません**。すべて既定値で動作します。

---

## 動作要件

- macOS / Linux（ローカル想定）
- Python **3.12** 以上推奨
- [Ollama](https://ollama.com/) が動作していること
- モデル `llama3.1:8b-instruct-q4_K_M` を Pull 済み

```bash
ollama pull llama3.1:8b-instruct-q4_K_M
```

---

## セットアップ

```bash
cd ~/apple
python3.12 -m venv venv
source venv/bin/activate

python -m pip install -U pip
python -m pip install "fastapi[standard]" psutil requests
```

> まとめて入れる場合は `requirements.txt` を利用：
> ```txt
> fastapi[standard]
> psutil
> requests
> ```
> ```bash
> python -m pip install -r requirements.txt
> ```

---

## 起動

```bash
python working_server.py
# デフォルト: 0.0.0.0:8002 で待受
```

- 初回は **自動ウォームアップ** を行います（`/api/tags` → 1トークン生成）。
- ブラウザで `http://localhost:8002` または `http://localhost:8002/fixed` にアクセス。

---

## 使い方

### 1) 雑談（スモールトーク）
- 例：「おはよう！」「ありがとう」「了解です」など短い一言
- 内部では **`/api/chat`** を使用して自然な返答（1〜4文程度）を生成します。

### 2) システム質問
- 例：「CPUの状況は？」「実行中のアプリは？」「メモリは？」「ディスク容量は？」
- 内部では **`/api/generate`** を使用し、**現在の CPU/メモリ/ディスク/上位プロセス**をプロンプトに埋め込んで回答します。

### 3) フォールバック
- LLM がタイムアウト/失敗した場合でも、**定型の有用な回答**を返します（安全動作）。

---

## ウォームアップ & タイムアウト設計

- 起動時に **`/api/tags`** Ping と **1トークン生成**を自動実行 → モデル初回ロードの待ち時間を短縮
- 生成呼び出しは **段階的タイムアウト**（既定 180s → 360s に再試行）+ リトライ（既定 1 回）
- さらに手動でウォームアップしたい場合：

```bash
curl -sS http://127.0.0.1:11434/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"model":"llama3.1:8b-instruct-q4_K_M","prompt":"OK","options":{"num_predict":1},"stream":false}' >/dev/null
```

> **環境変数は未設定でOK**（cred への影響を避けるため）。既定値のままでも実運用可能。

---

## API / メッセージ仕様（クライアント ↔ サーバ）

### WebSocket: `/ws`

- `ping` … サーバ応答: `pong`
- `system_status_request` … サーバ応答: `system_status_response`
- `chat_message` … 入力例
  ```json
  {
    "type": "chat_message",
    "data": { "message": "CPUの状況を教えて" }
  }
  ```
  サーバ応答: `chat_response` に `"data.message"` としてテキストが返る

### ブロードキャスト
- 2秒間隔で `system_status_update` を全接続へ送信

---

## よくあるトラブルと対処

### `ModuleNotFoundError: No module named 'fastapi'`
```bash
python -m pip install "fastapi[standard]" psutil requests
```

### `Read timed out`（Ollama）
- 自動ウォームアップ完了まで待つ or 上記の **手動ウォームアップ**を一度実行
- モデルが Pull 済みか確認：`ollama pull llama3.1:8b-instruct-q4_K_M`

### `psutil` 未導入
```bash
python -m pip install psutil
```

### venv が効いていない
```bash
which python
python -c "import sys; print(sys.executable)"
# .../apple/venv/bin/python であればOK
```

---

## 正しい `jq + curl` の例（スマートクオート禁止）

> “ ” ‘ ’ の **スマートクオートは使用しない**でください。**半角の ' と " のみ**を使います。

```bash
jq -n --arg p '量子コンピューターについて小学生向けに説明して' \
'{
  model: "llama3.1:8b-instruct-q4_K_M",
  prompt: $p,
  options: { num_predict: 80, temperature: 0.2, top_p: 0.9, repeat_penalty: 1.1, stop: ["\n\n"] },
  keep_alive: "10m",
  stream: false
}' \
| curl -sS -H 'Content-Type: application/json' --data-binary @- http://127.0.0.1:11434/api/generate \
| jq -r '.response // .error'
```

---

## ファイル構成（抜粋）

```
apple/
├─ working_server.py        # サーバ本体（Ollama + Smalltalk + Warmup + Fallback）
├─ frontend/                # PWA フロント（/static にマウント）
├─ fixed_index.html         # 固定版 UI（/fixed で配信）
└─ README.md                # このファイル
```

---

## ランタイム既定値（参考）

コード内既定値（環境変数未使用でも可）

- `OLLAMA_BASE = "http://127.0.0.1:11434"`
- `OLLAMA_MODEL = "llama3.1:8b-instruct-q4_K_M"`
- `OLLAMA_TIMEOUT_SEC = 180` / `OLLAMA_MAX_TIMEOUT_SEC = 360`
- `OLLAMA_RETRIES = 2`
- `keep_alive = "30m"`

> どうしても変更したい場合のみ、起動前に環境変数を設定してください（**通常は不要**）。

---

## ライセンス / 注意
- 本実装はローカル開発用途を想定。外部公開時は認証/レート制限等の追加実装を推奨。
- システム情報の収集は `psutil` でローカルマシン内に完結します。

---

### 更新履歴
- 2025-08: Ollama 完全移行、雑談チャット導入、ウォームアップ/リトライ実装、README更新
