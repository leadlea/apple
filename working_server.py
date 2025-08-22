#!/usr/bin/env python3
"""
Working Mac Status PWA Server - Ollama + Smalltalk Chat + Warmup
- 雑談は /api/chat で軽量応答
- システム質問は /api/generate（従来どおり）でコンテキスト付き応答
- 起動時ウォームアップ + 段階的タイムアウト + リトライ
"""

import asyncio
import json
import psutil
from datetime import datetime
import os
import sys
import time
import requests

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# ===== Ollama endpoints/config =====
# 基本URL（PORT/ホストを環境変数で差し替え可能）
OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "http://127.0.0.1:11434")
OLLAMA_GENERATE_URL = os.environ.get("OLLAMA_URL", f"{OLLAMA_BASE}/api/generate")
OLLAMA_CHAT_URL = os.environ.get("OLLAMA_CHAT_URL", f"{OLLAMA_BASE}/api/chat")
OLLAMA_TAGS_URL = f"{OLLAMA_BASE}/api/tags"

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M")
OLLAMA_NUM_PREDICT = int(os.environ.get("OLLAMA_NUM_PREDICT", "80"))
OLLAMA_TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.2"))
OLLAMA_TOP_P = float(os.environ.get("OLLAMA_TOP_P", "0.9"))
OLLAMA_REPEAT_PENALTY = float(os.environ.get("OLLAMA_REPEAT_PENALTY", "1.1"))
OLLAMA_STOP = os.environ.get("OLLAMA_STOP", "\\n\\n").encode("utf-8").decode("unicode_escape")
# 初回ロードが重いことがあるため広めの既定（段階的に延ばす）
OLLAMA_TIMEOUT_SEC = int(os.environ.get("OLLAMA_TIMEOUT_SEC", "180"))
OLLAMA_MAX_TIMEOUT_SEC = int(os.environ.get("OLLAMA_MAX_TIMEOUT_SEC", "360"))
OLLAMA_RETRIES = int(os.environ.get("OLLAMA_RETRIES", "2"))  # リトライ回数（失敗後にもう一度）

# ===== FastAPI =====
app = FastAPI(title="Mac Status PWA - Ollama")

app.mount("/static", StaticFiles(directory="frontend"), name="static")

connected_clients = set()

# ====== System info ======
def get_system_info():
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                if info['cpu_percent'] is not None and info['cpu_percent'] > 0:
                    processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        processes = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:5]

        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": round(cpu_percent, 1),
            "memory_percent": round(memory.percent, 1),
            "memory_used": memory.used,
            "memory_total": memory.total,
            "disk_percent": round((disk.used / disk.total) * 100, 1),
            "disk_used": disk.used,
            "disk_total": disk.total,
            "processes": processes
        }
    except Exception as e:
        print(f"Error getting system info: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_used": 0,
            "memory_total": 1,
            "disk_percent": 0,
            "disk_used": 0,
            "disk_total": 1,
            "processes": [],
            "error": str(e)
        }

# ===== Broadcast loop =====
async def broadcast_system_status():
    while True:
        if connected_clients:
            system_info = get_system_info()
            message = {
                "type": "system_status_update",
                "data": system_info,
                "timestamp": datetime.now().isoformat()
            }
            disconnected = set()
            for ws in connected_clients:
                try:
                    await ws.send_text(json.dumps(message))
                except:
                    disconnected.add(ws)
            connected_clients.difference_update(disconnected)
        await asyncio.sleep(2)

# ===== Warmup =====
def _ollama_ping():
    try:
        requests.get(OLLAMA_TAGS_URL, timeout=10)
    except Exception as e:
        print(f"[warmup] tags ping error: {e}")

def _ollama_one_token_warmup():
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": "OK",
        "options": {"num_predict": 1},
        "keep_alive": "30m",
        "stream": False
    }
    try:
        requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=60)
        print("[warmup] one-token generate done")
    except Exception as e:
        print(f"[warmup] one-token generate error: {e}")

async def warmup_ollama():
    print("🧊 Warmup Ollama ...")
    await asyncio.to_thread(_ollama_ping)
    await asyncio.to_thread(_ollama_one_token_warmup)
    print("🔥 Warmup finished")

# ===== Startup =====
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_system_status())
    asyncio.create_task(warmup_ollama())
    print(f"🧠 OLLAMA_BASE : {OLLAMA_BASE}")
    print(f"🧩 MODEL       : {OLLAMA_MODEL}")

# ===== LLM helpers =====
def _ollama_post(url: str, payload: dict) -> str:
    """段階的タイムアウト + リトライ。成功ならテキスト、失敗は空文字。"""
    timeouts = [OLLAMA_TIMEOUT_SEC]
    if OLLAMA_RETRIES > 0:
        timeouts.append(min(OLLAMA_MAX_TIMEOUT_SEC, OLLAMA_TIMEOUT_SEC * 2))

    for i, t in enumerate(timeouts):
        try:
            r = requests.post(url, json=payload, timeout=t)
            r.raise_for_status()
            data = r.json()
            # /api/generate は 'response'、/api/chat は 'message' 内 'content'
            if "response" in data:
                return (data.get("response") or "").strip()
            if "message" in data and isinstance(data["message"], dict):
                return (data["message"].get("content") or "").strip()
            # chat の stream=False でも messages 配列が返る場合がある
            if "messages" in data and data["messages"]:
                last = data["messages"][-1]
                if isinstance(last, dict):
                    return (last.get("content") or "").strip()
            return ""
        except requests.exceptions.ReadTimeout as e:
            print(f"[Ollama timeout {t}s try#{i+1}] {e}")
            if i == 0:
                # 1発目で詰まったら軽くウォームアップを再実行
                try:
                    _ollama_one_token_warmup()
                except Exception:
                    pass
            continue
        except Exception as e:
            print(f"[Ollama error try#{i+1}] {e}")
            time.sleep(0.2)
            continue
    return ""

def build_system_prompt(user_query: str, system_metrics: dict) -> str:
    cpu = system_metrics.get("cpu_percent", 0)
    mem = system_metrics.get("memory_percent", 0)
    mem_used_gb = system_metrics.get("memory_used", 0) / (1024**3)
    mem_total_gb = system_metrics.get("memory_total", 1) / (1024**3)
    disk = system_metrics.get("disk_percent", 0)
    disk_used_gb = system_metrics.get("disk_used", 0) / (1024**3)
    disk_total_gb = system_metrics.get("disk_total", 1) / (1024**3)
    top = system_metrics.get("processes", [])[:3]

    top_lines = []
    for i, p in enumerate(top, 1):
        top_lines.append(f"{i}. {p.get('name','?')} | CPU {p.get('cpu_percent',0):.1f}% / MEM {p.get('memory_percent',0):.1f}%")
    top_block = "\n".join(top_lines) if top_lines else "（上位プロセス情報なし）"

    prompt = (
        "あなたは macOS の軽量システムアシスタントです。専門用語を避け、日本語で簡潔・要点のみで答えてください。\n"
        "取得できない情報は『未対応』と述べ、代替の確認手段を1〜2個だけ提案してください。絵文字は最小限。\n\n"
        "=== 現在のシステム状況 ===\n"
        f"- CPU使用率: {cpu:.1f}%\n"
        f"- メモリ: {mem:.1f}%（{mem_used_gb:.1f}GB / {mem_total_gb:.1f}GB）\n"
        f"- ディスク: {disk:.1f}%（{disk_used_gb:.0f}GB / {disk_total_gb:.0f}GB）\n"
        f"- 上位プロセス:\n{top_block}\n"
        "=========================\n\n"
        f"ユーザーの質問: {user_query}\n"
        "回答は2〜6行程度で。"
    )
    return prompt

def generate_with_ollama_generate(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "options": {
            "num_predict": OLLAMA_NUM_PREDICT,
            "temperature": OLLAMA_TEMPERATURE,
            "top_p": OLLAMA_TOP_P,
            "repeat_penalty": OLLAMA_REPEAT_PENALTY,
            "stop": [OLLAMA_STOP] if OLLAMA_STOP else []
        },
        "keep_alive": "30m",
        "stream": False
    }
    return _ollama_post(OLLAMA_GENERATE_URL, payload)

def build_smalltalk_messages(user_text: str):
    system = (
        "あなたはフレンドリーな会話相手です。日本語で丁寧だが堅すぎない調子で、1〜4文で返答。"
        "状況に応じて短い相づちや1つだけ簡単な質問でラリーを続けてもOK。絵文字は最小限。"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_text}
    ]

def generate_with_ollama_chat(messages) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "options": {
            "num_predict": max(48, OLLAMA_NUM_PREDICT),  # 雑談は少し長めでもOK
            "temperature": 0.5,  # 雑談は少し自然さ優先
            "top_p": 0.9,
            "repeat_penalty": 1.05
        },
        "keep_alive": "30m",
        "stream": False
    }
    return _ollama_post(OLLAMA_CHAT_URL, payload)

def is_smalltalk(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    greetings = ["こんにちは", "こんばんは", "おはよう", "やあ", "はろー", "hi", "hello"]
    pleasantries = ["ありがとう", "助かった", "助かります", "おつかれ", "お疲れ", "元気", "どうも", "なるほど", "了解", "りょうかい"]
    sys_keywords = ["cpu", "メモリ", "memory", "ram", "ディスク", "disk", "storage",
                    "wifi", "wi-fi", "ネット", "インターネット", "プロセス", "温度", "fan", "バッテリー", "battery"]

    if any(k in t for k in greetings) or any(k in t for k in pleasantries):
        return True
    if any(k in t.lower() for k in sys_keywords):
        return False
    # 短い発話は雑談とみなす
    return len(t) <= 40

# ===== Fallback (従来どおり) =====
def generate_fallback_response(user_message: str, system_info: dict) -> str:
    user_message_lower = (user_message or "").lower()
    cpu_usage = system_info.get("cpu_percent", 0)
    memory_percent = system_info.get("memory_percent", 0)
    memory_used_gb = system_info.get("memory_used", 0) / (1024**3)
    memory_total_gb = system_info.get("memory_total", 1) / (1024**3)
    disk_percent = system_info.get("disk_percent", 0)
    disk_used_gb = system_info.get("disk_used", 0) / (1024**3)
    disk_total_gb = system_info.get("disk_total", 1) / (1024**3)
    top_processes = system_info.get("processes", [])[:3]

    def contains(text, kws): return any(k in text for k in kws)

    if contains(user_message_lower, ["バッテリー", "battery", "電池", "充電"]):
        import random
        return random.choice([
            "🔋 現在バッテリー情報の取得は未対応です。メニューバーのバッテリーアイコンや設定>バッテリーをご確認ください。",
            "🔋 バッテリー監視は未実装です。設定>バッテリー、もしくはアクティビティモニタ>エネルギーを参照してください。"
        ])

    elif contains(user_message_lower, ["アプリ", "app", "プロセス", "process", "実行中", "起動中", "動いている"]):
        s = "📱 **現在実行中の主要プロセス:**\n\n"
        if top_processes:
            for i, p in enumerate(top_processes, 1):
                s += f"**{i}. {p.get('name')}**  CPU {p.get('cpu_percent',0):.1f}% / MEM {p.get('memory_percent',0):.1f}%\n"
        else:
            s += "取得できませんでした。\n"
        s += f"\n📊 全体: CPU {cpu_usage}% / メモリ {memory_percent}%"
        return s

    elif contains(user_message_lower, ["wifi", "wi-fi", "ワイファイ", "無線", "ネット", "インターネット", "接続"]):
        return f"📶 Wi-Fi詳細取得は未対応です。設定>ネットワークやメニューバーのWi-Fiから確認してください。\n現在: CPU {cpu_usage}% / MEM {memory_percent}%"

    elif contains(user_message_lower, ["cpu", "プロセッサ", "使用率", "処理"]):
        s = f"🖥️ 現在のCPU使用率は {cpu_usage}% です。\n"
        if cpu_usage > 80: s += "⚠️ 高負荷の可能性があります。"
        elif cpu_usage > 50: s += "📊 中程度の負荷です。"
        else: s += "✅ 低負荷です。"
        return s

    elif contains(user_message_lower, ["メモリ", "memory", "ram", "使用量"]):
        s = (f"💾 メモリ使用率: {memory_percent}%\n"
             f"使用量: {memory_used_gb:.1f}GB / {memory_total_gb:.1f}GB")
        return s

    elif contains(user_message_lower, ["ディスク", "disk", "storage", "容量"]):
        s = (f"💿 ディスク使用率: {disk_percent}%\n"
             f"使用量: {disk_used_gb:.0f}GB / {disk_total_gb:.0f}GB")
        return s

    elif contains(user_message_lower, ["システム", "status", "全体", "状況"]):
        return (f"📊 システム全体\n"
                f"CPU {cpu_usage}%, メモリ {memory_percent}%, ディスク {disk_percent}%")

    elif contains(user_message_lower, ["こんにちは", "hello", "はじめまして", "おはよう", "こんばんは"]):
        return (f"👋 こんにちは！現在の状況: CPU {cpu_usage}%, メモリ {memory_percent}%, ディスク {disk_percent}%\n"
                "気になる項目があればどうぞ。")

    else:
        return (f"🔍 状態: CPU {cpu_usage}% / メモリ {memory_percent}% / ディスク {disk_percent}%\n"
                "『CPUの詳細』『実行中のアプリ』など具体的にどうぞ。")

# ===== Routes =====
@app.get("/")
async def serve_pwa():
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse("<h1>Mac Status PWA</h1><p>Frontend files not found</p>", status_code=200)

@app.get("/fixed")
async def serve_fixed_pwa():
    try:
        with open("fixed_index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse("<h1>Fixed Mac Status PWA</h1><p>Fixed version not found</p>", status_code=200)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ===== WebSocket =====
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    print(f"WebSocket client connected. Total: {len(connected_clients)}")

    # 初回ステータス
    try:
        system_info = get_system_info()
        await websocket.send_text(json.dumps({
            "type": "system_status_response",
            "data": {"system_status": system_info},
            "timestamp": datetime.now().isoformat()
        }))
    except Exception as e:
        print(f"Error sending initial status: {e}")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received: {data}")
            try:
                msg = json.loads(data)
                t = msg.get("type", "")

                if t == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}))

                elif t == "system_status_request":
                    system_info = get_system_info()
                    await websocket.send_text(json.dumps({
                        "type": "system_status_response",
                        "data": {"system_status": system_info},
                        "timestamp": datetime.now().isoformat()
                    }))

                elif t == "chat_message":
                    # 互換: data.message or message
                    user_message = ""
                    if "data" in msg and isinstance(msg["data"], dict):
                        user_message = msg["data"].get("message", "")
                    else:
                        user_message = msg.get("message", "")

                    print(f"🔍 chat: '{user_message}'")
                    system_info = get_system_info()

                    # 雑談かどうかで分岐
                    try_text = ""
                    if is_smalltalk(user_message):
                        # 軽量な雑談は /api/chat
                        messages = build_smalltalk_messages(user_message)
                        try_text = generate_with_ollama_chat(messages)
                        if not try_text:
                            # 念のため generate でも試す
                            prompt = f"ユーザー: {user_message}\n自然な日本語で1〜4文で返答。"
                            try_text = generate_with_ollama_generate(prompt)
                    else:
                        # システム質問は generate + コンテキスト
                        prompt = build_system_prompt(user_message, system_info)
                        try_text = generate_with_ollama_generate(prompt)

                    if not try_text:
                        try_text = generate_fallback_response(user_message, system_info)
                        print(f"✅ fallback used ({len(try_text)} chars)")
                    else:
                        print(f"✅ llm used ({len(try_text)} chars)")

                    await websocket.send_text(json.dumps({
                        "type": "chat_response",
                        "data": {"message": try_text},
                        "timestamp": datetime.now().isoformat()
                    }))

                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {"message": f"Unknown message type: {t}"},
                        "timestamp": datetime.now().isoformat()
                    }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid JSON format"},
                    "timestamp": datetime.now().isoformat()
                }))

    except WebSocketDisconnect:
        connected_clients.discard(websocket)
        print(f"WebSocket client disconnected. Total: {len(connected_clients)}")

# ===== Main =====
if __name__ == "__main__":
    print("🚀 Starting Mac Status PWA Server (Ollama+Chat)")
    print(f"BASE   : {OLLAMA_BASE}")
    print(f"MODEL  : {OLLAMA_MODEL}")
    print(f"TIMEOUT: {OLLAMA_TIMEOUT_SEC}s (max {OLLAMA_MAX_TIMEOUT_SEC}s) RETRIES: {OLLAMA_RETRIES}")
    uvicorn.run(app, host="0.0.0.0", port=8002)
