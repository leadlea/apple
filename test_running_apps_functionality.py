#!/usr/bin/env python3
"""
Running Apps Functionality Test for Mac Status PWA
Tests running applications information retrieval and formatting
"""
import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from system_monitor import SystemMonitor, RunningAppInfo
from prompt_generator import JapanesePromptGenerator, SystemMetricType, PromptStyle, ConversationContext


async def test_running_apps_retrieval():
    """Test running applications information retrieval"""
    print("🖥️ Testing Running Apps Information Retrieval...")
    
    monitor = SystemMonitor()
    
    try:
        # Get system info with running apps
        system_status = await monitor.get_system_info()
        
        print(f"✅ System info retrieved successfully")
        print(f"📊 Running apps count: {len(system_status.running_apps)}")
        
        if system_status.running_apps:
            print("\n🔝 Top Running Apps:")
            for i, app in enumerate(system_status.running_apps[:5], 1):
                print(f"   {i}. {app.name}")
                print(f"      - PID: {app.pid}")
                print(f"      - CPU: {app.cpu_percent:.1f}%")
                print(f"      - Memory: {app.memory_mb:.1f}MB ({app.memory_percent:.1f}%)")
                print(f"      - Status: {app.status}")
                print(f"      - Windows: {app.window_count}")
                print(f"      - GUI App: {app.is_gui_app}")
        else:
            print("   - No running GUI applications found")
            
    except Exception as e:
        print(f"❌ Error retrieving running apps info: {e}")


def test_running_apps_prompt_formatting():
    """Test running apps information formatting in prompts"""
    print("\n💬 Testing Running Apps Prompt Formatting...")
    
    generator = JapanesePromptGenerator()
    
    # Test data with running apps info
    test_apps_data = {
        'timestamp': '2024-01-15 14:30:00',
        'cpu_percent': 25.5,
        'memory_percent': 60.2,
        'disk_percent': 45.8,
        'running_apps': [
            {
                'name': 'Google Chrome',
                'pid': 1234,
                'cpu_percent': 15.2,
                'memory_percent': 8.5,
                'memory_mb': 680.5,
                'status': 'active',
                'window_count': 3,
                'is_gui_app': True,
                'bundle_id': 'com.google.Chrome',
                'launch_time': 1642248000
            },
            {
                'name': 'Visual Studio Code',
                'pid': 5678,
                'cpu_percent': 8.7,
                'memory_percent': 4.2,
                'memory_mb': 336.8,
                'status': 'active',
                'window_count': 2,
                'is_gui_app': True,
                'bundle_id': 'com.microsoft.VSCode',
                'launch_time': 1642248100
            },
            {
                'name': 'Finder',
                'pid': 9012,
                'cpu_percent': 0.5,
                'memory_percent': 1.2,
                'memory_mb': 96.4,
                'status': 'background',
                'window_count': 0,
                'is_gui_app': True,
                'bundle_id': 'com.apple.finder',
                'launch_time': 1642247000
            },
            {
                'name': 'Slack',
                'pid': 3456,
                'cpu_percent': 2.1,
                'memory_percent': 3.8,
                'memory_mb': 304.2,
                'status': 'active',
                'window_count': 1,
                'is_gui_app': True,
                'bundle_id': 'com.tinyspeck.slackmacgap',
                'launch_time': 1642248200
            }
        ]
    }
    
    # Test different styles
    styles_to_test = [
        (PromptStyle.CASUAL, "どんなアプリが開いてる？"),
        (PromptStyle.FRIENDLY, "実行中のアプリケーションを教えて"),
        (PromptStyle.TECHNICAL, "実行中プロセスの詳細情報"),
        (PromptStyle.PROFESSIONAL, "アプリケーション使用状況の報告")
    ]
    
    for style, query in styles_to_test:
        print(f"\n--- {style.value.upper()} Style ---")
        context = ConversationContext(preferred_style=style)
        
        prompt = generator.generate_system_prompt(
            user_query=query,
            system_data=test_apps_data,
            context=context,
            focus_metric=SystemMetricType.APPS
        )
        
        print(f"Query: {query}")
        print("Generated prompt:")
        print(prompt[:600] + "..." if len(prompt) > 600 else prompt)


def test_running_apps_keyword_detection():
    """Test running apps keyword detection"""
    print("\n🔍 Testing Running Apps Keyword Detection...")
    
    generator = JapanesePromptGenerator()
    
    app_queries = [
        "どんなアプリが開いてる？",
        "実行中のアプリケーションは？",
        "動いてるプログラムを教えて",
        "Chromeは起動してる？",
        "重いアプリは何？",
        "running applications",
        "open apps",
        "what programs are running"
    ]
    
    for query in app_queries:
        focus = generator._detect_query_focus(query)
        result = "✅ APPS" if focus == SystemMetricType.APPS else f"❌ {focus}"
        print(f"'{query}' → {result}")


def test_running_apps_formatting_edge_cases():
    """Test running apps formatting with edge cases"""
    print("\n⚠️  Testing Running Apps Formatting Edge Cases...")
    
    generator = JapanesePromptGenerator()
    
    edge_cases = [
        # No apps
        {
            'name': 'No Apps',
            'data': {'running_apps': []}
        },
        # Single heavy app
        {
            'name': 'Single Heavy App',
            'data': {
                'running_apps': [
                    {
                        'name': 'Heavy App',
                        'pid': 1234,
                        'cpu_percent': 45.0,
                        'memory_percent': 15.0,
                        'memory_mb': 1200.0,
                        'status': 'active',
                        'window_count': 1,
                        'is_gui_app': True
                    }
                ]
            }
        },
        # Many light apps
        {
            'name': 'Many Light Apps',
            'data': {
                'running_apps': [
                    {
                        'name': f'LightApp{i}',
                        'pid': 1000 + i,
                        'cpu_percent': 0.1,
                        'memory_percent': 0.5,
                        'memory_mb': 40.0,
                        'status': 'background',
                        'window_count': 0,
                        'is_gui_app': True
                    } for i in range(10)
                ]
            }
        }
    ]
    
    for case in edge_cases:
        print(f"\n--- {case['name']} ---")
        formatted = generator._format_running_apps_info(case['data'], PromptStyle.FRIENDLY)
        print(f"Formatted: {formatted}")


async def main():
    """Run all running apps functionality tests"""
    print("🚀 Starting Running Apps Functionality Tests\n")
    
    # Test running apps info retrieval
    await test_running_apps_retrieval()
    
    # Test prompt formatting
    test_running_apps_prompt_formatting()
    
    # Test keyword detection
    test_running_apps_keyword_detection()
    
    # Test edge cases
    test_running_apps_formatting_edge_cases()
    
    print("\n✅ All running apps functionality tests completed!")


if __name__ == "__main__":
    asyncio.run(main())