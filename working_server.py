#!/usr/bin/env python3
"""
Working Mac Status PWA Server - Fixed Version
動作確認済みのMac Status PWAサーバー（修正版）
"""

import asyncio
import json
import psutil
from datetime import datetime
from pathlib import Path
import os
import sys

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import ELYZA model interface
try:
    from elyza_model import ELYZAModelInterface, ModelConfig
    from prompt_generator import PromptGenerator
    ELYZA_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ELYZA model not available: {e}")
    ELYZA_AVAILABLE = False

# Create FastAPI app
app = FastAPI(title="Mac Status PWA - Working")

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialize ELYZA model
elyza_model = None
prompt_generator = None

async def initialize_elyza_model():
    """Initialize ELYZA model if available"""
    global elyza_model, prompt_generator
    
    if not ELYZA_AVAILABLE:
        print("ELYZA model not available, using fallback responses")
        return False
    
    try:
        # Model configuration
        model_path = "models/elyza7b/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf"
        
        if not os.path.exists(model_path):
            print(f"Model file not found: {model_path}")
            print("Using fallback responses")
            return False
        
        config = ModelConfig(
            model_path=model_path,
            n_ctx=1024,  # Reduced for better performance
            n_gpu_layers=-1,  # Use all Metal layers on M1
            n_threads=4,
            temperature=0.7,
            max_tokens=256
        )
        
        elyza_model = ELYZAModelInterface(config)
        success = await elyza_model.initialize_model()
        
        if success:
            prompt_generator = PromptGenerator()
            print("✅ ELYZA model initialized successfully")
            return True
        else:
            print("❌ ELYZA model initialization failed")
            return False
            
    except Exception as e:
        print(f"Error initializing ELYZA model: {e}")
        return False

@app.get("/")
async def serve_pwa():
    """Serve the PWA main page"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Mac Status PWA</h1><p>Frontend files not found</p>",
            status_code=200
        )

@app.get("/fixed")
async def serve_fixed_pwa():
    """Serve the fixed PWA version"""
    try:
        with open("fixed_index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Fixed Mac Status PWA</h1><p>Fixed version not found</p>",
            status_code=200
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

def get_system_info():
    """Get current system information"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Top processes
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                if info['cpu_percent'] is not None and info['cpu_percent'] > 0:
                    processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage and get top 5
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

# Store connected clients
connected_clients = set()

async def broadcast_system_status():
    """Broadcast system status to all connected clients"""
    while True:
        if connected_clients:
            system_info = get_system_info()
            message = {
                "type": "system_status_update",
                "data": system_info,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to all connected clients
            disconnected_clients = set()
            for websocket in connected_clients:
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    disconnected_clients.add(websocket)
            
            # Remove disconnected clients
            connected_clients -= disconnected_clients
        
        await asyncio.sleep(2)  # Update every 2 seconds

# Start background task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_system_status())
    # Initialize ELYZA model in background
    asyncio.create_task(initialize_elyza_model())

def generate_fallback_response(user_message: str, system_info: dict) -> str:
    """Generate fallback response when ELYZA model is not available"""
    
    user_message_lower = user_message.lower()
    
    # Get current system metrics
    cpu_usage = system_info.get("cpu_percent", 0)
    memory_percent = system_info.get("memory_percent", 0)
    memory_used_gb = system_info.get("memory_used", 0) / (1024**3)
    memory_total_gb = system_info.get("memory_total", 1) / (1024**3)
    disk_percent = system_info.get("disk_percent", 0)
    disk_used_gb = system_info.get("disk_used", 0) / (1024**3)
    disk_total_gb = system_info.get("disk_total", 1) / (1024**3)
    top_processes = system_info.get("processes", [])[:3]
    
    # Generate contextual responses based on keywords
    if "cpu" in user_message_lower or "プロセッサ" in user_message_lower or "使用率" in user_message_lower:
        response_text = f"🖥️ 現在のCPU使用率は {cpu_usage}% です。\n\n"
        if cpu_usage > 80:
            response_text += "⚠️ CPU使用率が高めです。重い処理が実行されている可能性があります。"
        elif cpu_usage > 50:
            response_text += "📊 CPU使用率は中程度です。通常の動作範囲内です。"
        else:
            response_text += "✅ CPU使用率は低く、システムに余裕があります。"
        
        if top_processes:
            response_text += f"\n\n上位プロセス:\n"
            for i, proc in enumerate(top_processes, 1):
                cpu_val = proc.get('cpu_percent', 0) or 0
                response_text += f"{i}. {proc['name']}: {cpu_val:.1f}%\n"
        
        return response_text
    
    elif "メモリ" in user_message_lower or "memory" in user_message_lower or "ram" in user_message_lower:
        response_text = f"💾 現在のメモリ使用状況:\n\n"
        response_text += f"使用率: {memory_percent}%\n"
        response_text += f"使用量: {memory_used_gb:.1f}GB / {memory_total_gb:.1f}GB\n"
        response_text += f"空き容量: {(memory_total_gb - memory_used_gb):.1f}GB\n\n"
        
        if memory_percent > 85:
            response_text += "🔴 メモリ使用率が高いです。アプリケーションを閉じることを検討してください。"
        elif memory_percent > 70:
            response_text += "🟡 メモリ使用率がやや高めです。"
        else:
            response_text += "🟢 メモリ使用率は正常範囲内です。"
        
        return response_text
    
    elif "ディスク" in user_message_lower or "disk" in user_message_lower or "storage" in user_message_lower:
        response_text = f"💿 現在のディスク使用状況:\n\n"
        response_text += f"使用率: {disk_percent}%\n"
        response_text += f"使用量: {disk_used_gb:.0f}GB / {disk_total_gb:.0f}GB\n"
        response_text += f"空き容量: {(disk_total_gb - disk_used_gb):.0f}GB\n\n"
        
        if disk_percent > 90:
            response_text += "🔴 ディスク容量が不足しています。ファイルの整理が必要です。"
        elif disk_percent > 80:
            response_text += "🟡 ディスク使用率が高めです。不要なファイルの削除を検討してください。"
        else:
            response_text += "🟢 ディスク容量に余裕があります。"
        
        return response_text
    
    elif "システム" in user_message_lower or "status" in user_message_lower or "全体" in user_message_lower or "状況" in user_message_lower:
        response_text = f"📊 システム全体の状況\n\n"
        response_text += f"🖥️ CPU: {cpu_usage}%\n"
        response_text += f"💾 メモリ: {memory_percent}% ({memory_used_gb:.1f}GB/{memory_total_gb:.1f}GB)\n"
        response_text += f"💿 ディスク: {disk_percent}% ({disk_used_gb:.0f}GB/{disk_total_gb:.0f}GB)\n\n"
        
        # Overall health assessment
        issues = []
        if cpu_usage > 80:
            issues.append("CPU使用率が高い")
        if memory_percent > 85:
            issues.append("メモリ不足")
        if disk_percent > 90:
            issues.append("ディスク容量不足")
        
        if issues:
            response_text += f"⚠️ 注意事項: {', '.join(issues)}"
        else:
            response_text += "✅ システムは正常に動作しています"
        
        return response_text
    
    elif "こんにちは" in user_message_lower or "hello" in user_message_lower:
        response_text = f"👋 こんにちは！Mac Status PWAへようこそ！\n\n"
        response_text += f"現在のシステム状況:\n"
        response_text += f"🖥️ CPU: {cpu_usage}%\n"
        response_text += f"💾 メモリ: {memory_percent}%\n"
        response_text += f"💿 ディスク: {disk_percent}%\n\n"
        response_text += f"何かご質問があれば、お気軽にお聞きください！"
        
        return response_text
    
    else:
        # Generate varied default responses
        import random
        
        responses = [
            f"🤖 ご質問ありがとうございます。現在のシステム状況をお知らせします：\n🖥️ CPU: {cpu_usage}%\n💾 メモリ: {memory_percent}%\n💿 ディスク: {disk_percent}%",
            f"📊 システム監視中です。現在の状態：\nCPU使用率: {cpu_usage}%\nメモリ使用率: {memory_percent}%\nディスク使用率: {disk_percent}%\n\n他に何かお聞きしたいことはありますか？",
            f"🔍 システムをチェックしました。\n• CPU: {cpu_usage}% {'(正常)' if cpu_usage < 70 else '(高め)' if cpu_usage < 85 else '(注意)'}\n• メモリ: {memory_percent}% {'(正常)' if memory_percent < 75 else '(高め)' if memory_percent < 90 else '(注意)'}\n• ディスク: {disk_percent}% {'(正常)' if disk_percent < 80 else '(高め)' if disk_percent < 95 else '(注意)'}",
            f"💻 Macの状態を確認しました。\nCPU: {cpu_usage}%、メモリ: {memory_percent}%、ディスク: {disk_percent}%\n\n詳しい情報が必要でしたら、「CPUの詳細」「メモリの詳細」などとお聞きください。"
        ]
        
        return random.choice(responses)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    connected_clients.add(websocket)
    print(f"WebSocket client connected. Total clients: {len(connected_clients)}")
    
    # Send initial system status
    try:
        system_info = get_system_info()
        initial_message = {
            "type": "system_status_response",
            "data": {
                "system_status": system_info
            },
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(initial_message))
    except Exception as e:
        print(f"Error sending initial status: {e}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            print(f"Received: {data}")
            
            try:
                message = json.loads(data)
                message_type = message.get("type", "")
                
                if message_type == "ping":
                    # Respond to ping
                    response = {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_text(json.dumps(response))
                
                elif message_type == "system_status_request":
                    # Get system information
                    system_info = get_system_info()
                    response = {
                        "type": "system_status_response",
                        "data": {
                            "system_status": system_info
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_text(json.dumps(response))
                
                elif message_type == "chat_message":
                    # Enhanced chat response
                    user_message = message.get("message", "")
                    system_info = get_system_info()
                    
                    response_text = None
                    
                    # Try to use ELYZA model first
                    if elyza_model and elyza_model.is_initialized and prompt_generator:
                        try:
                            # Generate prompt with system context
                            prompt = prompt_generator.generate_system_status_prompt(
                                user_query=user_message,
                                system_metrics={
                                    'cpu_percent': system_info.get("cpu_percent", 0),
                                    'memory_percent': system_info.get("memory_percent", 0),
                                    'memory_used_gb': system_info.get("memory_used", 0) / (1024**3),
                                    'memory_total_gb': system_info.get("memory_total", 1) / (1024**3),
                                    'disk_percent': system_info.get("disk_percent", 0),
                                    'disk_used_gb': system_info.get("disk_used", 0) / (1024**3),
                                    'disk_total_gb': system_info.get("disk_total", 1) / (1024**3),
                                    'top_processes': system_info.get("processes", [])[:3]
                                }
                            )
                            
                            # Get response from ELYZA model
                            model_response = await elyza_model.generate_response(prompt)
                            if model_response and model_response.content.strip():
                                response_text = model_response.content.strip()
                                print(f"✅ ELYZA response generated: {len(response_text)} chars")
                            else:
                                print("⚠️ ELYZA returned empty response, using fallback")
                                
                        except Exception as e:
                            print(f"❌ ELYZA model error: {e}")
                    
                    # If ELYZA model failed or not available, use fallback responses
                    if not response_text:
                        response_text = generate_fallback_response(user_message, system_info)
                        print(f"✅ Fallback response generated: {len(response_text)} chars")
                    
                    response = {
                        "type": "chat_response",
                        "data": {
                            "message": response_text
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_text(json.dumps(response))
                
                else:
                    # Unknown message type
                    response = {
                        "type": "error",
                        "data": {
                            "message": f"Unknown message type: {message_type}"
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_text(json.dumps(response))
                    
            except json.JSONDecodeError:
                # Invalid JSON
                response = {
                    "type": "error",
                    "data": {
                        "message": "Invalid JSON format"
                    },
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(response))
                
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
        print(f"WebSocket client disconnected. Total clients: {len(connected_clients)}")

if __name__ == "__main__":
    print("🚀 Starting Mac Status PWA Server (Fixed Version)")
    print("ELYZA model available:", ELYZA_AVAILABLE)
    uvicorn.run(app, host="0.0.0.0", port=8002)