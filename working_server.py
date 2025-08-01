#!/usr/bin/env python3
"""
Working Mac Status PWA Server
動作確認済みのMac Status PWAサーバー
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
app = FastAPI(title="Mac Status PWA - Working")

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
                    user_message = message.get("message", "").lower()
                    system_info = get_system_info()
                    
                    # Get current system metrics
                    cpu_usage = system_info.get("cpu_percent", 0)
                    memory_percent = system_info.get("memory_percent", 0)
                    memory_used_gb = system_info.get("memory_used", 0) / (1024**3)
                    memory_total_gb = system_info.get("memory_total", 1) / (1024**3)
                    disk_percent = system_info.get("disk_percent", 0)
                    disk_used_gb = system_info.get("disk_used", 0) / (1024**3)
                    disk_total_gb = system_info.get("disk_total", 1) / (1024**3)
                    top_processes = system_info.get("processes", [])[:3]
                    
                    # Generate contextual responses
                    if "cpu" in user_message or "プロセッサ" in user_message or "使用率" in user_message:
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
                    
                    elif "メモリ" in user_message or "memory" in user_message or "ram" in user_message:
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
                    
                    elif "ディスク" in user_message or "disk" in user_message or "storage" in user_message:
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
                    
                    elif "バッテリー" in user_message or "電池" in user_message or "充電" in user_message or "battery" in user_message or "power" in user_message or "残量" in user_message or "時間" in user_message:
                        # Get battery information
                        try:
                            battery = psutil.sensors_battery()
                            if battery is None:
                                response_text = "🖥️ このMacにはバッテリーが搭載されていません（デスクトップMac）。"
                            else:
                                percent = battery.percent
                                power_plugged = battery.power_plugged
                                secsleft = battery.secsleft
                                
                                if power_plugged:
                                    if percent >= 100:
                                        response_text = f"🔋 バッテリーは満充電です ({percent:.0f}%)\n\n✅ 電源に接続されています。"
                                    else:
                                        response_text = f"🔌 充電中です ({percent:.0f}%)\n\n⚡ 電源に接続されています。"
                                else:
                                    response_text = f"🔋 バッテリー残量は {percent:.0f}% です\n\n"
                                    if secsleft and secsleft != psutil.POWER_TIME_UNLIMITED:
                                        hours = secsleft // 3600
                                        minutes = (secsleft % 3600) // 60
                                        if hours > 0:
                                            response_text += f"⏰ あと約 {hours}時間{minutes}分 使用可能です"
                                        else:
                                            response_text += f"⏰ あと約 {minutes}分 使用可能です"
                                    else:
                                        response_text += "⏰ 残り時間は計算中です"
                                    
                                    # Battery level warnings
                                    if percent <= 10:
                                        response_text += "\n\n🔴 バッテリー残量が少なくなっています。充電してください。"
                                    elif percent <= 20:
                                        response_text += "\n\n🟡 バッテリー残量が少なめです。充電を検討してください。"
                                    else:
                                        response_text += "\n\n🟢 バッテリー残量は十分です。"
                        except Exception as e:
                            response_text = f"❌ バッテリー情報の取得に失敗しました: {str(e)}"
                    
                    elif any(keyword in user_message for keyword in ["wifi", "ワイファイ", "ネットワーク", "接続", "信号", "電波", "ssid", "速度", "チャンネル"]):
                        # Get WiFi information using macOS commands
                        try:
                            import subprocess
                            
                            # Get WiFi info using airport command
                            airport_result = subprocess.run([
                                '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport',
                                '-I'
                            ], capture_output=True, text=True, timeout=10)
                            
                            if airport_result.returncode != 0:
                                response_text = "📶❌ WiFi情報を取得できませんでした。WiFiがオフになっているか、接続されていない可能性があります。"
                            else:
                                # Parse airport output
                                wifi_data = {}
                                for line in airport_result.stdout.split('\n'):
                                    if ':' in line:
                                        key, value = line.split(':', 1)
                                        wifi_data[key.strip()] = value.strip()
                                
                                ssid = wifi_data.get('SSID', 'Unknown')
                                signal_strength = None
                                channel = None
                                security = wifi_data.get('link auth', 'Unknown')
                                
                                # Parse signal strength
                                if 'agrCtlRSSI' in wifi_data:
                                    try:
                                        signal_strength = int(wifi_data['agrCtlRSSI'])
                                    except ValueError:
                                        pass
                                
                                # Parse channel
                                if 'channel' in wifi_data:
                                    try:
                                        channel_info = wifi_data['channel']
                                        if '(' in channel_info:
                                            channel = int(channel_info.split('(')[0].strip())
                                        else:
                                            channel = int(channel_info)
                                    except (ValueError, IndexError):
                                        pass
                                
                                if ssid and ssid != 'Unknown':
                                    response_text = f"📶 WiFi接続情報\n\n"
                                    response_text += f"🌐 ネットワーク: {ssid}\n"
                                    
                                    if signal_strength is not None:
                                        # Determine signal quality
                                        if signal_strength >= -30:
                                            quality = "非常に良好 🟢"
                                        elif signal_strength >= -50:
                                            quality = "良好 🟡"
                                        elif signal_strength >= -70:
                                            quality = "普通 🟠"
                                        elif signal_strength >= -90:
                                            quality = "弱い 🔴"
                                        else:
                                            quality = "非常に弱い 🔴"
                                        
                                        response_text += f"📡 信号強度: {signal_strength}dBm ({quality})\n"
                                    
                                    if channel:
                                        response_text += f"📻 チャンネル: {channel}\n"
                                    
                                    if security and security != 'Unknown':
                                        response_text += f"🔒 セキュリティ: {security}\n"
                                    
                                    # Add connection quality assessment
                                    if signal_strength is not None:
                                        if signal_strength >= -50:
                                            response_text += "\n✅ 接続品質は良好です。"
                                        elif signal_strength >= -70:
                                            response_text += "\n⚠️ 接続品質は普通です。"
                                        else:
                                            response_text += "\n🔴 接続品質が低下しています。ルーターに近づくことをお勧めします。"
                                else:
                                    response_text = "📶❌ WiFiに接続されていません。"
                        
                        except Exception as e:
                            response_text = f"❌ WiFi情報の取得に失敗しました: {str(e)}"
                    
                    elif any(keyword in user_message for keyword in ["アプリ", "アプリケーション", "開いてる", "実行中", "動いてる", "プログラム", "app", "application", "running", "chrome", "safari", "finder"]):
                        # Get running applications using AppleScript
                        try:
                            import subprocess
                            
                            # Get GUI applications using simpler AppleScript
                            applescript_cmd = '''
                            tell application "System Events"
                                get name of every process whose background only is false
                            end tell
                            '''
                            
                            result = subprocess.run([
                                'osascript', '-e', applescript_cmd
                            ], capture_output=True, text=True, timeout=15)
                            
                            if result.returncode != 0:
                                response_text = "🖥️❌ アプリケーション情報を取得できませんでした。"
                            else:
                                # Parse AppleScript output - simple app names list
                                gui_app_names = []
                                if result.stdout.strip():
                                    output = result.stdout.strip()
                                    # Parse comma-separated app names
                                    app_names = [name.strip() for name in output.split(',')]
                                    gui_app_names = app_names
                                
                                # Get detailed process information
                                running_apps = []
                                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                                    try:
                                        pinfo = proc.info
                                        proc_name = pinfo['name']
                                        
                                        # Check if this process matches a GUI app
                                        if any(gui_name.lower() in proc_name.lower() or proc_name.lower() in gui_name.lower() 
                                              for gui_name in gui_app_names):
                                            memory_mb = 0
                                            if pinfo['memory_info']:
                                                memory_mb = pinfo['memory_info'].rss / (1024 * 1024)
                                            
                                            running_apps.append({
                                                'name': proc_name,
                                                'cpu_percent': pinfo['cpu_percent'] or 0.0,
                                                'memory_mb': memory_mb,
                                                'window_count': 1  # Assume GUI apps have windows
                                            })
                                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                                        continue
                                
                                # Sort by CPU usage
                                running_apps.sort(key=lambda x: x['cpu_percent'], reverse=True)
                                
                                if running_apps:
                                    response_text = f"🖥️ 実行中のアプリケーション ({len(running_apps)}個)\n\n"
                                    
                                    # Show top apps
                                    for i, app in enumerate(running_apps[:8], 1):
                                        name = app['name']
                                        cpu = app['cpu_percent']
                                        memory_mb = app['memory_mb']
                                        windows = app['window_count']
                                        
                                        status_icon = "🟢" if windows > 0 else "⚪"
                                        
                                        response_text += f"{i}. {status_icon} {name}\n"
                                        
                                        if cpu > 1:
                                            response_text += f"   CPU: {cpu:.1f}%"
                                        if memory_mb > 50:
                                            response_text += f" | メモリ: {memory_mb:.0f}MB"
                                        if windows > 0:
                                            response_text += f" | ウィンドウ: {windows}個"
                                        response_text += "\n"
                                    
                                    # Add summary
                                    total_cpu = sum(app['cpu_percent'] for app in running_apps)
                                    total_memory = sum(app['memory_mb'] for app in running_apps)
                                    active_apps = len([app for app in running_apps if app['window_count'] > 0])
                                    
                                    response_text += f"\n📊 合計: CPU {total_cpu:.1f}%, メモリ {total_memory:.0f}MB"
                                    response_text += f"\n🟢 アクティブ: {active_apps}個, ⚪ バックグラウンド: {len(running_apps) - active_apps}個"
                                else:
                                    response_text = "🖥️ 実行中のGUIアプリケーションが見つかりませんでした。"
                        
                        except Exception as e:
                            response_text = f"❌ アプリケーション情報の取得に失敗しました: {str(e)}"
                    
                    elif any(keyword in user_message for keyword in ["ディスク詳細", "パーティション", "外付け", "ドライブ", "ボリューム", "volumes", "partition", "external", "drive"]):
                        # Get detailed disk information
                        try:
                            import psutil
                            
                            # Get all disk partitions
                            partitions = psutil.disk_partitions()
                            disk_info_list = []
                            
                            for partition in partitions:
                                try:
                                    usage = psutil.disk_usage(partition.mountpoint)
                                    
                                    # Convert bytes to GB
                                    total_gb = usage.total / (1024**3)
                                    used_gb = usage.used / (1024**3)
                                    free_gb = usage.free / (1024**3)
                                    percent = (usage.used / usage.total) * 100 if usage.total > 0 else 0
                                    
                                    # Skip very small partitions
                                    if total_gb < 0.1:
                                        continue
                                    
                                    # Determine disk type
                                    is_removable = '/Volumes/' in partition.mountpoint and partition.mountpoint != '/'
                                    is_system = partition.mountpoint == '/' or partition.mountpoint.startswith('/System')
                                    
                                    # Get disk label
                                    label = None
                                    if partition.mountpoint.startswith('/Volumes/'):
                                        label = partition.mountpoint.split('/Volumes/')[-1]
                                    elif partition.mountpoint == '/':
                                        label = 'Macintosh HD'
                                    else:
                                        label = partition.mountpoint
                                    
                                    disk_info_list.append({
                                        'device': partition.device,
                                        'mountpoint': partition.mountpoint,
                                        'fstype': partition.fstype,
                                        'label': label,
                                        'total_gb': total_gb,
                                        'used_gb': used_gb,
                                        'free_gb': free_gb,
                                        'percent': percent,
                                        'is_removable': is_removable,
                                        'is_system': is_system
                                    })
                                    
                                except (PermissionError, OSError):
                                    continue
                            
                            # Sort by system disks first, then by size
                            disk_info_list.sort(key=lambda x: (not x['is_system'], -x['total_gb']))
                            
                            if disk_info_list:
                                response_text = f"💾 ディスク詳細情報 ({len(disk_info_list)}個)\n\n"
                                
                                for i, disk in enumerate(disk_info_list, 1):
                                    label = disk['label'] or disk['mountpoint']
                                    total_gb = disk['total_gb']
                                    used_gb = disk['used_gb']
                                    free_gb = disk['free_gb']
                                    percent = disk['percent']
                                    fstype = disk['fstype']
                                    is_system = disk['is_system']
                                    is_removable = disk['is_removable']
                                    
                                    # Disk type icon
                                    if is_system:
                                        icon = "💾"
                                        disk_type = "システム"
                                    elif is_removable:
                                        icon = "🔌"
                                        disk_type = "外付け"
                                    else:
                                        icon = "💿"
                                        disk_type = "内蔵"
                                    
                                    # Size formatting
                                    if total_gb > 1000:
                                        size_text = f"{total_gb/1000:.1f}TB"
                                        used_text = f"{used_gb/1000:.1f}TB"
                                        free_text = f"{free_gb/1000:.1f}TB"
                                    else:
                                        size_text = f"{total_gb:.0f}GB"
                                        used_text = f"{used_gb:.0f}GB"
                                        free_text = f"{free_gb:.0f}GB"
                                    
                                    response_text += f"{i}. {icon} {label} ({disk_type})\n"
                                    response_text += f"   容量: {used_text}/{size_text} ({percent:.1f}%使用)\n"
                                    response_text += f"   空き: {free_text} | ファイルシステム: {fstype}\n"
                                    response_text += f"   マウント: {disk['mountpoint']}\n\n"
                                
                                # Add summary
                                total_capacity = sum(d['total_gb'] for d in disk_info_list)
                                total_used = sum(d['used_gb'] for d in disk_info_list)
                                total_free = sum(d['free_gb'] for d in disk_info_list)
                                system_count = len([d for d in disk_info_list if d['is_system']])
                                external_count = len([d for d in disk_info_list if d['is_removable']])
                                
                                if total_capacity > 1000:
                                    capacity_text = f"{total_capacity/1000:.1f}TB"
                                    used_text = f"{total_used/1000:.1f}TB"
                                    free_text = f"{total_free/1000:.1f}TB"
                                else:
                                    capacity_text = f"{total_capacity:.0f}GB"
                                    used_text = f"{total_used:.0f}GB"
                                    free_text = f"{total_free:.0f}GB"
                                
                                response_text += f"📊 合計容量: {capacity_text} (使用: {used_text}, 空き: {free_text})\n"
                                response_text += f"💾 システム: {system_count}個, 🔌 外付け: {external_count}個"
                            else:
                                response_text = "💾 アクセス可能なディスク情報が見つかりませんでした。"
                        
                        except Exception as e:
                            response_text = f"❌ ディスク情報の取得に失敗しました: {str(e)}"
                    
                    elif any(keyword in user_message for keyword in ["開発ツール", "開発環境", "xcode", "git", "homebrew", "node", "python", "docker", "code", "brew", "npm", "pip", "development", "dev tools"]):
                        # Get development tools information
                        try:
                            import subprocess
                            
                            # Define tools to check
                            tools_to_check = [
                                {'name': 'Xcode', 'command': ['xcode-select', '--print-path'], 'version_cmd': ['xcodebuild', '-version']},
                                {'name': 'Git', 'command': ['which', 'git'], 'version_cmd': ['git', '--version']},
                                {'name': 'Homebrew', 'command': ['which', 'brew'], 'version_cmd': ['brew', '--version']},
                                {'name': 'Node.js', 'command': ['which', 'node'], 'version_cmd': ['node', '--version']},
                                {'name': 'Python', 'command': ['which', 'python3'], 'version_cmd': ['python3', '--version']},
                                {'name': 'Docker', 'command': ['which', 'docker'], 'version_cmd': ['docker', '--version']},
                                {'name': 'VS Code', 'command': ['which', 'code'], 'version_cmd': ['code', '--version']}
                            ]
                            
                            installed_tools = []
                            not_installed_tools = []
                            
                            for tool in tools_to_check:
                                try:
                                    # Check if tool is installed
                                    result = subprocess.run(tool['command'], capture_output=True, text=True, timeout=5)
                                    
                                    if result.returncode == 0:
                                        # Tool is installed, get version
                                        version = "不明"
                                        path = result.stdout.strip()
                                        
                                        if tool.get('version_cmd'):
                                            try:
                                                version_result = subprocess.run(tool['version_cmd'], capture_output=True, text=True, timeout=5)
                                                if version_result.returncode == 0:
                                                    version_output = version_result.stdout.strip()
                                                    
                                                    # Parse version based on tool
                                                    if tool['name'] == 'Git' and 'git version' in version_output:
                                                        version = version_output.split('git version')[1].split()[0]
                                                    elif tool['name'] == 'Homebrew' and 'Homebrew' in version_output:
                                                        version = version_output.split('\n')[0].split('Homebrew')[1].strip()
                                                    elif tool['name'] == 'Node.js':
                                                        version = version_output.strip()
                                                    elif tool['name'] == 'Python' and 'Python' in version_output:
                                                        version = version_output.split('Python')[1].strip()
                                                    elif tool['name'] == 'Docker' and 'Docker version' in version_output:
                                                        version = version_output.split('Docker version')[1].split(',')[0].strip()
                                                    elif tool['name'] == 'VS Code':
                                                        version = version_output.split('\n')[0].strip()
                                                    elif tool['name'] == 'Xcode' and 'Xcode' in version_output:
                                                        for line in version_output.split('\n'):
                                                            if 'Xcode' in line:
                                                                version = line.split('Xcode')[1].strip()
                                                                break
                                                    else:
                                                        version = version_output.split('\n')[0].strip()
                                            except Exception:
                                                pass
                                        
                                        installed_tools.append({
                                            'name': tool['name'],
                                            'version': version,
                                            'path': path
                                        })
                                    else:
                                        not_installed_tools.append(tool['name'])
                                        
                                except Exception:
                                    not_installed_tools.append(tool['name'])
                            
                            if installed_tools or not_installed_tools:
                                response_text = f"⚙️ 開発ツール情報\n\n"
                                
                                if installed_tools:
                                    response_text += f"✅ インストール済み ({len(installed_tools)}個):\n\n"
                                    
                                    for i, tool in enumerate(installed_tools, 1):
                                        name = tool['name']
                                        version = tool['version']
                                        path = tool['path']
                                        
                                        response_text += f"{i}. 🟢 {name}\n"
                                        response_text += f"   バージョン: {version}\n"
                                        
                                        # Add path for important tools
                                        if name in ['Xcode', 'Homebrew']:
                                            response_text += f"   パス: {path}\n"
                                        
                                        # Add additional info for specific tools
                                        if name == 'Git':
                                            try:
                                                user_result = subprocess.run(['git', 'config', '--global', 'user.name'], capture_output=True, text=True, timeout=3)
                                                if user_result.returncode == 0:
                                                    response_text += f"   ユーザー: {user_result.stdout.strip()}\n"
                                            except Exception:
                                                pass
                                        elif name == 'Node.js':
                                            try:
                                                npm_result = subprocess.run(['npm', '--version'], capture_output=True, text=True, timeout=3)
                                                if npm_result.returncode == 0:
                                                    response_text += f"   npm: v{npm_result.stdout.strip()}\n"
                                            except Exception:
                                                pass
                                        elif name == 'Python':
                                            try:
                                                pip_result = subprocess.run(['pip3', '--version'], capture_output=True, text=True, timeout=3)
                                                if pip_result.returncode == 0:
                                                    pip_version = pip_result.stdout.strip().split()[1]
                                                    response_text += f"   pip: v{pip_version}\n"
                                            except Exception:
                                                pass
                                        
                                        response_text += "\n"
                                
                                if not_installed_tools:
                                    response_text += f"❌ 未インストール ({len(not_installed_tools)}個):\n"
                                    response_text += f"   {', '.join(not_installed_tools)}\n\n"
                                
                                # Add summary
                                response_text += f"📊 合計: {len(installed_tools)}個インストール済み, {len(not_installed_tools)}個未インストール"
                            else:
                                response_text = "⚙️ 開発ツール情報を取得できませんでした。"
                        
                        except Exception as e:
                            response_text = f"❌ 開発ツール情報の取得に失敗しました: {str(e)}"
                    
                    elif any(keyword in user_message for keyword in ["温度", "熱", "ファン", "冷却", "発熱", "サーマル", "回転数", "temperature", "thermal", "fan", "cooling", "暑い", "熱い", "hot"]):
                        # Get thermal and fan information
                        try:
                            import subprocess
                            
                            cpu_temperature = None
                            gpu_temperature = None
                            fan_speeds = []
                            thermal_state = "不明"
                            
                            # Try to get temperature using istats (if installed)
                            try:
                                istats_result = subprocess.run(['istats', 'cpu', 'temp'], capture_output=True, text=True, timeout=5)
                                if istats_result.returncode == 0:
                                    output = istats_result.stdout.strip()
                                    if '°C' in output:
                                        temp_str = output.split(':')[1].strip().replace('°C', '').strip()
                                        cpu_temperature = float(temp_str)
                            except (subprocess.TimeoutExpired, FileNotFoundError):
                                pass
                            
                            # Try to get fan information using istats
                            try:
                                istats_fan_result = subprocess.run(['istats', 'fan'], capture_output=True, text=True, timeout=5)
                                if istats_fan_result.returncode == 0:
                                    for line in istats_fan_result.stdout.split('\n'):
                                        if 'Fan' in line and 'RPM' in line:
                                            try:
                                                parts = line.split(':')
                                                if len(parts) >= 2:
                                                    fan_name = parts[0].strip()
                                                    rpm_str = parts[1].strip().replace('RPM', '').strip()
                                                    rpm = int(float(rpm_str))
                                                    fan_speeds.append({'name': fan_name, 'rpm': rpm})
                                            except (ValueError, IndexError):
                                                pass
                            except (subprocess.TimeoutExpired, FileNotFoundError):
                                pass
                            
                            # Try to get thermal state using pmset
                            try:
                                pmset_result = subprocess.run(['pmset', '-g', 'therm'], capture_output=True, text=True, timeout=5)
                                if pmset_result.returncode == 0:
                                    output = pmset_result.stdout.lower()
                                    if 'cpu_speed_limit' in output:
                                        thermal_state = "サーマルスロットリング中"
                                    elif cpu_temperature:
                                        if cpu_temperature < 60:
                                            thermal_state = "正常"
                                        elif cpu_temperature < 75:
                                            thermal_state = "やや高温"
                                        elif cpu_temperature < 90:
                                            thermal_state = "高温"
                                        else:
                                            thermal_state = "危険"
                                    else:
                                        thermal_state = "正常"
                            except (subprocess.TimeoutExpired, FileNotFoundError):
                                pass
                            
                            # Build response
                            if cpu_temperature or fan_speeds or thermal_state != "不明":
                                response_text = f"🌡️ システム温度・ファン情報\n\n"
                                
                                # Temperature information
                                if cpu_temperature:
                                    if cpu_temperature > 85:
                                        temp_icon = "🔥"
                                        temp_status = "高温"
                                    elif cpu_temperature > 70:
                                        temp_icon = "🌡️"
                                        temp_status = "やや高温"
                                    elif cpu_temperature > 50:
                                        temp_icon = "✅"
                                        temp_status = "正常"
                                    else:
                                        temp_icon = "❄️"
                                        temp_status = "低温"
                                    
                                    response_text += f"{temp_icon} CPU温度: {cpu_temperature:.1f}°C ({temp_status})\n"
                                else:
                                    response_text += "🌡️ CPU温度: 取得できません\n"
                                
                                # Fan information
                                if fan_speeds:
                                    response_text += f"\n💨 ファン情報 ({len(fan_speeds)}個):\n"
                                    for i, fan in enumerate(fan_speeds, 1):
                                        name = fan['name']
                                        rpm = fan['rpm']
                                        
                                        if rpm > 3000:
                                            fan_icon = "💨"
                                            fan_status = "高速"
                                        elif rpm > 1500:
                                            fan_icon = "🌀"
                                            fan_status = "中速"
                                        elif rpm > 500:
                                            fan_icon = "💨"
                                            fan_status = "低速"
                                        else:
                                            fan_icon = "⏸️"
                                            fan_status = "停止"
                                        
                                        response_text += f"{i}. {fan_icon} {name}: {rpm}rpm ({fan_status})\n"
                                else:
                                    response_text += "\n💨 ファン情報: 取得できません\n"
                                
                                # Thermal state
                                response_text += f"\n🔥 サーマル状態: {thermal_state}\n"
                                
                                # Add recommendations
                                if cpu_temperature and cpu_temperature > 80:
                                    response_text += "\n⚠️ 推奨事項:\n"
                                    response_text += "- 重い処理を一時停止してください\n"
                                    response_text += "- 通気口の清掃を検討してください\n"
                                    response_text += "- 涼しい場所でMacを使用してください"
                                elif thermal_state == "正常":
                                    response_text += "\n✅ システムは正常な温度で動作しています"
                                
                                # Note about limitations
                                if not cpu_temperature and not fan_speeds:
                                    response_text += "\n📝 注意: macOSでは詳細な温度・ファン情報の取得に制限があります。\n"
                                    response_text += "より詳細な情報を取得するには、iStat Menusなどのサードパーティアプリをご利用ください。"
                            else:
                                response_text = "🌡️ 温度・ファン情報を取得できませんでした。\n\n"
                                response_text += "macOSでは、詳細な温度・ファン情報の取得に制限があります。\n"
                                response_text += "より詳細な情報を取得するには、以下の方法をお試しください：\n\n"
                                response_text += "1. iStat Menus などのサードパーティアプリを使用\n"
                                response_text += "2. ターミナルで 'istats' コマンドをインストール (brew install istat-menus)\n"
                                response_text += "3. システム環境設定でアクセス許可を確認"
                        
                        except Exception as e:
                            response_text = f"❌ 温度・ファン情報の取得に失敗しました: {str(e)}"
                    
                    elif "システム" in user_message or "status" in user_message or "全体" in user_message or "状況" in user_message:
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
                    
                    elif "こんにちは" in user_message or "hello" in user_message:
                        response_text = f"👋 こんにちは！Mac Status PWAへようこそ！\n\n"
                        response_text += f"現在のシステム状況:\n"
                        response_text += f"🖥️ CPU: {cpu_usage}%\n"
                        response_text += f"💾 メモリ: {memory_percent}%\n"
                        response_text += f"💿 ディスク: {disk_percent}%\n\n"
                        response_text += f"何かご質問があれば、お気軽にお聞きください！"
                    
                    else:
                        # Generate varied default responses
                        import random
                        
                        responses = [
                            f"🤖 ご質問ありがとうございます。現在のシステム状況をお知らせします：\n🖥️ CPU: {cpu_usage}%\n💾 メモリ: {memory_percent}%\n💿 ディスク: {disk_percent}%",
                            f"📊 システム監視中です。現在の状態：\nCPU使用率: {cpu_usage}%\nメモリ使用率: {memory_percent}%\nディスク使用率: {disk_percent}%\n\n他に何かお聞きしたいことはありますか？",
                            f"🔍 システムをチェックしました。\n• CPU: {cpu_usage}% {'(正常)' if cpu_usage < 70 else '(高め)' if cpu_usage < 85 else '(注意)'}\n• メモリ: {memory_percent}% {'(正常)' if memory_percent < 75 else '(高め)' if memory_percent < 90 else '(注意)'}\n• ディスク: {disk_percent}% {'(正常)' if disk_percent < 80 else '(高め)' if disk_percent < 95 else '(注意)'}",
                            f"💻 Macの状態を確認しました。\nCPU: {cpu_usage}%、メモリ: {memory_percent}%、ディスク: {disk_percent}%\n\n詳しい情報が必要でしたら、「CPUの詳細」「メモリの詳細」などとお聞きください。"
                        ]
                        
                        response_text = random.choice(responses)
                    
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
    except Exception as e:
        connected_clients.discard(websocket)
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Mac Status PWA Working Server...")
    print("📱 Open your browser to: http://localhost:8002")
    print("🔧 Press Ctrl+C to stop")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8002,
        log_level="info"
    )