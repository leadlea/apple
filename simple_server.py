#!/usr/bin/env python3
"""
Simple Mac Status PWA Server for Testing
シンプルなMac Status PWAサーバー（テスト用）
"""

import asyncio
import json
import psutil
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Create FastAPI app
app = FastAPI(title="Mac Status PWA - Simple")

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

def get_system_info():
    """Get current system information"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Top processes
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage and get top 5
        processes = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:5]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            },
            "processes": processes
        }
    except Exception as e:
        return {"error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    print("WebSocket client connected")
    
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
                    # Enhanced chat response with real-time system data
                    user_message = message.get("message", "").lower()
                    system_info = get_system_info()
                    
                    # Get current system metrics
                    cpu_usage = system_info.get("cpu_percent", 0)
                    memory_percent = system_info.get("memory", {}).get("percent", 0)
                    memory_used_gb = system_info.get("memory", {}).get("used", 0) / (1024**3)
                    memory_total_gb = system_info.get("memory", {}).get("total", 0) / (1024**3)
                    disk_percent = system_info.get("disk", {}).get("percent", 0)
                    disk_used_gb = system_info.get("disk", {}).get("used", 0) / (1024**3)
                    disk_total_gb = system_info.get("disk", {}).get("total", 0) / (1024**3)
                    top_processes = system_info.get("processes", [])[:3]
                    
                    # Generate contextual responses
                    if "cpu" in user_message or "プロセッサ" in user_message or "使用率" in user_message:
                        response_text = f"🖥️ 現在のCPU使用率は **{cpu_usage:.1f}%** です。\n\n"
                        if cpu_usage > 80:
                            response_text += "⚠️ CPU使用率が高めです。重い処理が実行されている可能性があります。"
                        elif cpu_usage > 50:
                            response_text += "📊 CPU使用率は中程度です。通常の動作範囲内です。"
                        else:
                            response_text += "✅ CPU使用率は低く、システムに余裕があります。"
                        
                        if top_processes:
                            response_text += f"\n\n**上位プロセス:**\n"
                            for i, proc in enumerate(top_processes, 1):
                                response_text += f"{i}. {proc['name']}: {proc['cpu_percent']:.1f}%\n"
                    
                    elif "メモリ" in user_message or "memory" in user_message or "ram" in user_message:
                        response_text = f"💾 現在のメモリ使用状況:\n\n"
                        response_text += f"**使用率:** {memory_percent:.1f}%\n"
                        response_text += f"**使用量:** {memory_used_gb:.1f}GB / {memory_total_gb:.1f}GB\n"
                        response_text += f"**空き容量:** {(memory_total_gb - memory_used_gb):.1f}GB\n\n"
                        
                        if memory_percent > 85:
                            response_text += "🔴 メモリ使用率が高いです。アプリケーションを閉じることを検討してください。"
                        elif memory_percent > 70:
                            response_text += "🟡 メモリ使用率がやや高めです。"
                        else:
                            response_text += "🟢 メモリ使用率は正常範囲内です。"
                    
                    elif "ディスク" in user_message or "disk" in user_message or "storage" in user_message:
                        response_text = f"💿 現在のディスク使用状況:\n\n"
                        response_text += f"**使用率:** {disk_percent:.1f}%\n"
                        response_text += f"**使用量:** {disk_used_gb:.0f}GB / {disk_total_gb:.0f}GB\n"
                        response_text += f"**空き容量:** {(disk_total_gb - disk_used_gb):.0f}GB\n\n"
                        
                        if disk_percent > 90:
                            response_text += "🔴 ディスク容量が不足しています。ファイルの整理が必要です。"
                        elif disk_percent > 80:
                            response_text += "🟡 ディスク使用率が高めです。不要なファイルの削除を検討してください。"
                        else:
                            response_text += "🟢 ディスク容量に余裕があります。"
                    
                    elif "プロセス" in user_message or "process" in user_message or "アプリ" in user_message:
                        response_text = f"🔄 現在実行中の主要プロセス:\n\n"
                        for i, proc in enumerate(top_processes, 1):
                            cpu_val = proc.get('cpu_percent', 0) or 0
                            mem_val = proc.get('memory_percent', 0) or 0
                            response_text += f"**{i}. {proc['name']}**\n"
                            response_text += f"   CPU: {cpu_val:.1f}% | メモリ: {mem_val:.1f}%\n\n"
                    
                    elif "システム" in user_message or "status" in user_message or "全体" in user_message or "状況" in user_message:
                        response_text = f"📊 **システム全体の状況**\n\n"
                        response_text += f"🖥️ **CPU:** {cpu_usage:.1f}%\n"
                        response_text += f"💾 **メモリ:** {memory_percent:.1f}% ({memory_used_gb:.1f}GB/{memory_total_gb:.1f}GB)\n"
                        response_text += f"💿 **ディスク:** {disk_percent:.1f}% ({disk_used_gb:.0f}GB/{disk_total_gb:.0f}GB)\n\n"
                        
                        # Overall health assessment
                        issues = []
                        if cpu_usage > 80:
                            issues.append("CPU使用率が高い")
                        if memory_percent > 85:
                            issues.append("メモリ不足")
                        if disk_percent > 90:
                            issues.append("ディスク容量不足")
                        
                        if issues:
                            response_text += f"⚠️ **注意事項:** {', '.join(issues)}"
                        else:
                            response_text += "✅ **システムは正常に動作しています**"
                    
                    elif "重い" in user_message or "遅い" in user_message or "パフォーマンス" in user_message:
                        response_text = f"🔍 **パフォーマンス分析**\n\n"
                        
                        bottlenecks = []
                        if cpu_usage > 70:
                            bottlenecks.append(f"CPU使用率が高い ({cpu_usage:.1f}%)")
                        if memory_percent > 80:
                            bottlenecks.append(f"メモリ使用率が高い ({memory_percent:.1f}%)")
                        
                        if bottlenecks:
                            response_text += f"**検出された問題:**\n"
                            for issue in bottlenecks:
                                response_text += f"• {issue}\n"
                            response_text += f"\n**推奨対策:**\n"
                            response_text += f"• 不要なアプリケーションを終了\n"
                            response_text += f"• ブラウザのタブを整理\n"
                            response_text += f"• システムの再起動を検討\n"
                        else:
                            response_text += "✅ 現在のシステムパフォーマンスは良好です。"
                        
                        if top_processes:
                            response_text += f"\n\n**リソース使用量の多いプロセス:**\n"
                            for proc in top_processes:
                                cpu_val = proc.get('cpu_percent', 0) or 0
                                if cpu_val > 5:  # Only show processes using >5% CPU
                                    response_text += f"• {proc['name']}: {cpu_val:.1f}%\n"
                    
                    elif "こんにちは" in user_message or "hello" in user_message or "はじめまして" in user_message:
                        response_text = f"👋 こんにちは！Mac Status PWAへようこそ！\n\n"
                        response_text += f"現在のシステム状況をお知らせします：\n"
                        response_text += f"🖥️ CPU: {cpu_usage:.1f}%\n"
                        response_text += f"💾 メモリ: {memory_percent:.1f}%\n"
                        response_text += f"💿 ディスク: {disk_percent:.1f}%\n\n"
                        response_text += f"何かご質問があれば、お気軽にお聞きください！"
                    
                    else:
                        # Default response with current system info
                        response_text = f"🤖 「{message.get('message', '')}」についてお答えします。\n\n"
                        response_text += f"現在のシステム状況：\n"
                        response_text += f"🖥️ CPU: {cpu_usage:.1f}%\n"
                        response_text += f"💾 メモリ: {memory_percent:.1f}%\n"
                        response_text += f"💿 ディスク: {disk_percent:.1f}%\n\n"
                        response_text += f"具体的な質問例：\n"
                        response_text += f"• 「CPUの使用率は？」\n"
                        response_text += f"• 「メモリの状況を教えて」\n"
                        response_text += f"• 「システムが重い理由は？」\n"
                        response_text += f"• 「プロセスの状況は？」"
                    
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
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Mac Status PWA Simple Server...")
    print("📱 Open your browser to: http://localhost:8001")
    print("🔧 Press Ctrl+C to stop")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    )