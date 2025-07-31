#!/usr/bin/env python3
"""
Mac Status PWA - Demo Data Preparation
デモデータ準備スクリプト

This script prepares sample data and screenshots for demonstration purposes.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random
from typing import Dict, List, Any

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

class DemoDataGenerator:
    """Generate sample data for demonstration"""
    
    def __init__(self):
        self.demo_data_dir = Path("demo_data")
        self.demo_data_dir.mkdir(exist_ok=True)
        
    def generate_sample_system_data(self) -> Dict[str, Any]:
        """Generate realistic sample system data"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": round(random.uniform(15.0, 85.0), 1),
            "memory": {
                "total": 17179869184,  # 16GB
                "available": random.randint(4000000000, 12000000000),
                "percent": round(random.uniform(30.0, 70.0), 1),
                "used": random.randint(5000000000, 13000000000)
            },
            "disk": {
                "total": 1000204886016,  # 1TB
                "used": random.randint(200000000000, 800000000000),
                "free": random.randint(200000000000, 800000000000),
                "percent": round(random.uniform(20.0, 80.0), 1)
            },
            "processes": [
                {
                    "pid": 1234,
                    "name": "Google Chrome",
                    "cpu_percent": round(random.uniform(5.0, 25.0), 1),
                    "memory_percent": round(random.uniform(10.0, 30.0), 1),
                    "status": "running"
                },
                {
                    "pid": 5678,
                    "name": "Python",
                    "cpu_percent": round(random.uniform(2.0, 15.0), 1),
                    "memory_percent": round(random.uniform(5.0, 20.0), 1),
                    "status": "running"
                },
                {
                    "pid": 9012,
                    "name": "Finder",
                    "cpu_percent": round(random.uniform(0.5, 5.0), 1),
                    "memory_percent": round(random.uniform(2.0, 8.0), 1),
                    "status": "running"
                },
                {
                    "pid": 3456,
                    "name": "Safari",
                    "cpu_percent": round(random.uniform(3.0, 20.0), 1),
                    "memory_percent": round(random.uniform(8.0, 25.0), 1),
                    "status": "running"
                },
                {
                    "pid": 7890,
                    "name": "VS Code",
                    "cpu_percent": round(random.uniform(1.0, 10.0), 1),
                    "memory_percent": round(random.uniform(5.0, 15.0), 1),
                    "status": "running"
                }
            ],
            "network": {
                "bytes_sent": random.randint(1000000, 10000000),
                "bytes_recv": random.randint(5000000, 50000000),
                "packets_sent": random.randint(1000, 10000),
                "packets_recv": random.randint(5000, 50000)
            },
            "load_average": [
                round(random.uniform(1.0, 4.0), 2),
                round(random.uniform(1.0, 4.0), 2),
                round(random.uniform(1.0, 4.0), 2)
            ]
        }
    
    def generate_sample_chat_history(self) -> List[Dict[str, Any]]:
        """Generate sample chat conversation history"""
        conversations = [
            {
                "role": "user",
                "content": "こんにちは！システムの状態を教えてください。",
                "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat()
            },
            {
                "role": "assistant",
                "content": "こんにちは！現在のMacの状態をお伝えします。\\n\\nCPU使用率: 23.4%\\nメモリ使用率: 45.2%\\nディスク使用率: 67.8%\\n\\n全体的にシステムは正常に動作しています。メモリ使用量は適正範囲内で、CPUも余裕があります。",
                "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat()
            },
            {
                "role": "user",
                "content": "メモリを多く使っているプロセスはありますか？",
                "timestamp": (datetime.now() - timedelta(minutes=8)).isoformat()
            },
            {
                "role": "assistant",
                "content": "メモリ使用量の多いプロセスをお調べしました：\\n\\n1. Google Chrome - 18.5% (約3.2GB)\\n2. Safari - 12.3% (約2.1GB)\\n3. VS Code - 8.7% (約1.5GB)\\n4. Python - 6.2% (約1.1GB)\\n5. Finder - 3.1% (約0.5GB)\\n\\nChromeが最もメモリを使用していますが、これは複数のタブを開いている場合の正常な動作です。",
                "timestamp": (datetime.now() - timedelta(minutes=8)).isoformat()
            },
            {
                "role": "user",
                "content": "システムのパフォーマンスを向上させる方法はありますか？",
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat()
            },
            {
                "role": "assistant",
                "content": "システムパフォーマンス向上のご提案です：\\n\\n🚀 即効性のある対策：\\n• 不要なブラウザタブを閉じる\\n• 使用していないアプリケーションを終了\\n• デスクトップの整理整頓\\n\\n⚙️ 定期的なメンテナンス：\\n• ディスクの空き容量を20%以上確保\\n• 定期的な再起動（週1回程度）\\n• システムアップデートの適用\\n\\n現在のシステム状態は良好ですが、これらの対策でさらに快適になります！",
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat()
            },
            {
                "role": "user",
                "content": "ありがとうございます！定期的にチェックしてもらえますか？",
                "timestamp": (datetime.now() - timedelta(minutes=2)).isoformat()
            },
            {
                "role": "assistant",
                "content": "もちろんです！定期的なシステムチェックを設定いたします。\\n\\n📊 監視項目：\\n• CPU使用率（80%超過時にアラート）\\n• メモリ使用率（85%超過時にアラート）\\n• ディスク容量（90%超過時にアラート）\\n• 異常なプロセス活動\\n\\n🔔 通知設定：\\n• リアルタイム監視: 有効\\n• アラート通知: 有効\\n• 日次レポート: 有効\\n\\nいつでもお気軽にシステム状態についてお尋ねください！",
                "timestamp": (datetime.now() - timedelta(minutes=2)).isoformat()
            }
        ]
        
        return conversations
    
    def generate_performance_metrics(self) -> Dict[str, Any]:
        """Generate sample performance metrics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "response_times": {
                "system_info_avg": round(random.uniform(0.1, 0.5), 3),
                "chat_response_avg": round(random.uniform(2.0, 4.5), 3),
                "websocket_ping_avg": round(random.uniform(0.01, 0.05), 3)
            },
            "memory_usage": {
                "application_mb": round(random.uniform(150, 400), 1),
                "model_mb": round(random.uniform(2000, 3500), 1),
                "total_mb": round(random.uniform(2200, 4000), 1)
            },
            "request_counts": {
                "system_status_requests": random.randint(50, 200),
                "chat_messages": random.randint(20, 80),
                "websocket_connections": random.randint(1, 5)
            },
            "error_rates": {
                "system_monitoring_errors": round(random.uniform(0.0, 2.0), 2),
                "chat_response_errors": round(random.uniform(0.0, 1.0), 2),
                "websocket_errors": round(random.uniform(0.0, 0.5), 2)
            }
        }
    
    def generate_user_scenarios(self) -> List[Dict[str, Any]]:
        """Generate sample user interaction scenarios"""
        scenarios = [
            {
                "scenario_name": "First Time User",
                "description": "New user exploring the PWA for the first time",
                "interactions": [
                    {"action": "open_pwa", "timestamp": "2024-01-15T09:00:00"},
                    {"action": "view_system_status", "timestamp": "2024-01-15T09:00:30"},
                    {"action": "ask_question", "message": "このアプリは何ができますか？", "timestamp": "2024-01-15T09:01:00"},
                    {"action": "install_pwa", "timestamp": "2024-01-15T09:05:00"}
                ],
                "outcome": "Successfully installed PWA and understood basic functionality"
            },
            {
                "scenario_name": "Performance Investigation",
                "description": "User investigating system performance issues",
                "interactions": [
                    {"action": "check_system_status", "timestamp": "2024-01-15T14:30:00"},
                    {"action": "ask_question", "message": "システムが重い気がします", "timestamp": "2024-01-15T14:30:30"},
                    {"action": "view_processes", "timestamp": "2024-01-15T14:31:00"},
                    {"action": "ask_question", "message": "メモリを解放する方法は？", "timestamp": "2024-01-15T14:32:00"}
                ],
                "outcome": "Identified memory-intensive processes and received optimization suggestions"
            },
            {
                "scenario_name": "Regular Monitoring",
                "description": "Daily system health check routine",
                "interactions": [
                    {"action": "open_pwa", "timestamp": "2024-01-15T08:00:00"},
                    {"action": "view_system_status", "timestamp": "2024-01-15T08:00:10"},
                    {"action": "ask_question", "message": "今日のシステム状態はどうですか？", "timestamp": "2024-01-15T08:00:30"},
                    {"action": "set_alerts", "timestamp": "2024-01-15T08:02:00"}
                ],
                "outcome": "Confirmed system health and configured monitoring alerts"
            }
        ]
        
        return scenarios
    
    def create_sample_screenshots_info(self) -> Dict[str, Any]:
        """Create information for screenshot preparation"""
        return {
            "screenshots_needed": [
                {
                    "filename": "main_interface.png",
                    "description": "Main chat interface with Apple design",
                    "viewport": "1200x800",
                    "url": "http://localhost:8000",
                    "elements_to_highlight": ["chat-container", "system-status-card"]
                },
                {
                    "filename": "system_status.png",
                    "description": "System status display with real-time metrics",
                    "viewport": "1200x800",
                    "url": "http://localhost:8000",
                    "action": "click_system_status",
                    "elements_to_highlight": ["cpu-usage", "memory-usage", "disk-usage"]
                },
                {
                    "filename": "chat_conversation.png",
                    "description": "Sample chat conversation with AI assistant",
                    "viewport": "1200x800",
                    "url": "http://localhost:8000",
                    "sample_messages": [
                        "システムの状態を教えてください",
                        "メモリ使用量が気になります"
                    ]
                },
                {
                    "filename": "pwa_install.png",
                    "description": "PWA installation prompt",
                    "viewport": "1200x800",
                    "url": "http://localhost:8000",
                    "action": "trigger_install_prompt"
                },
                {
                    "filename": "mobile_view.png",
                    "description": "Mobile responsive design",
                    "viewport": "375x667",
                    "url": "http://localhost:8000",
                    "device": "iPhone"
                },
                {
                    "filename": "process_monitoring.png",
                    "description": "Process monitoring and analysis",
                    "viewport": "1200x800",
                    "url": "http://localhost:8000",
                    "sample_message": "プロセスの状態を詳しく教えてください"
                }
            ],
            "screenshot_instructions": {
                "tools_needed": ["Playwright", "Selenium", "or manual screenshots"],
                "preparation_steps": [
                    "Start the Mac Status PWA server",
                    "Ensure ELYZA model is loaded",
                    "Prepare sample data",
                    "Use consistent browser settings",
                    "Capture at different viewport sizes"
                ],
                "post_processing": [
                    "Crop to remove browser chrome",
                    "Add subtle shadows for presentation",
                    "Ensure consistent lighting/contrast",
                    "Optimize file sizes for web"
                ]
            }
        }
    
    def generate_all_demo_data(self):
        """Generate all demo data files"""
        print("🎬 Generating Demo Data for Mac Status PWA...")
        
        # Generate system data samples
        system_samples = []
        for i in range(10):
            system_samples.append(self.generate_sample_system_data())
        
        with open(self.demo_data_dir / "sample_system_data.json", "w") as f:
            json.dump(system_samples, f, indent=2)
        print("✅ Generated sample system data")
        
        # Generate chat history
        chat_history = self.generate_sample_chat_history()
        with open(self.demo_data_dir / "sample_chat_history.json", "w") as f:
            json.dump(chat_history, f, indent=2, ensure_ascii=False)
        print("✅ Generated sample chat history")
        
        # Generate performance metrics
        performance_data = []
        for i in range(24):  # 24 hours of data
            performance_data.append(self.generate_performance_metrics())
        
        with open(self.demo_data_dir / "sample_performance_metrics.json", "w") as f:
            json.dump(performance_data, f, indent=2)
        print("✅ Generated performance metrics")
        
        # Generate user scenarios
        scenarios = self.generate_user_scenarios()
        with open(self.demo_data_dir / "user_scenarios.json", "w") as f:
            json.dump(scenarios, f, indent=2)
        print("✅ Generated user scenarios")
        
        # Create screenshot preparation info
        screenshot_info = self.create_sample_screenshots_info()
        with open(self.demo_data_dir / "screenshot_preparation.json", "w") as f:
            json.dump(screenshot_info, f, indent=2)
        print("✅ Generated screenshot preparation guide")
        
        # Create demo configuration
        demo_config = {
            "demo_version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "description": "Mac Status PWA demonstration data and configuration",
            "files": {
                "system_data": "sample_system_data.json",
                "chat_history": "sample_chat_history.json",
                "performance_metrics": "sample_performance_metrics.json",
                "user_scenarios": "user_scenarios.json",
                "screenshot_guide": "screenshot_preparation.json"
            },
            "demo_server_config": {
                "host": "localhost",
                "port": 8000,
                "demo_mode": True,
                "sample_data_enabled": True
            }
        }
        
        with open(self.demo_data_dir / "demo_config.json", "w") as f:
            json.dump(demo_config, f, indent=2)
        print("✅ Generated demo configuration")
        
        # Create README for demo data
        demo_readme = """# Demo Data for Mac Status PWA

This directory contains sample data and configuration for demonstrating the Mac Status PWA.

## Files

- `sample_system_data.json`: Sample system monitoring data
- `sample_chat_history.json`: Example chat conversations
- `sample_performance_metrics.json`: Performance benchmarking data
- `user_scenarios.json`: User interaction scenarios
- `screenshot_preparation.json`: Guide for creating screenshots
- `demo_config.json`: Demo configuration settings

## Usage

### Loading Sample Data

```python
import json

# Load system data
with open('demo_data/sample_system_data.json') as f:
    system_data = json.load(f)

# Load chat history
with open('demo_data/sample_chat_history.json') as f:
    chat_history = json.load(f)
```

### Running Demo Mode

```bash
# Start server with demo data
python backend/main.py --demo-mode

# Run integration demo
python demo_system_integration.py
```

### Screenshot Preparation

See `screenshot_preparation.json` for detailed instructions on creating demonstration screenshots.

## Demo Scenarios

The demo data includes several user scenarios:

1. **First Time User**: New user exploring the PWA
2. **Performance Investigation**: User investigating system issues
3. **Regular Monitoring**: Daily system health check routine

Each scenario includes realistic user interactions and expected outcomes.
"""
        
        with open(self.demo_data_dir / "README.md", "w") as f:
            f.write(demo_readme)
        print("✅ Generated demo data README")
        
        print(f"\n🎉 Demo data generation complete!")
        print(f"📁 Files created in: {self.demo_data_dir}")
        print(f"📊 Total files: {len(list(self.demo_data_dir.glob('*')))}")
        
        # Summary
        print("\n📋 Demo Data Summary:")
        print(f"  • System data samples: {len(system_samples)}")
        print(f"  • Chat messages: {len(chat_history)}")
        print(f"  • Performance metrics: {len(performance_data)}")
        print(f"  • User scenarios: {len(scenarios)}")
        print(f"  • Screenshot guides: {len(screenshot_info['screenshots_needed'])}")

def main():
    """Main execution"""
    generator = DemoDataGenerator()
    generator.generate_all_demo_data()
    
    print("\n🚀 Next Steps:")
    print("1. Start the Mac Status PWA server")
    print("2. Run the integration demo: python demo_system_integration.py")
    print("3. Create screenshots using the preparation guide")
    print("4. Use sample data for presentations and documentation")

if __name__ == "__main__":
    main()