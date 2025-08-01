#!/usr/bin/env python3
"""
Development Tools Functionality Test for Mac Status PWA
Tests development tools information retrieval and formatting
"""
import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from system_monitor import SystemMonitor, DevToolInfo
from prompt_generator import JapanesePromptGenerator, SystemMetricType, PromptStyle, ConversationContext


async def test_dev_tools_retrieval():
    """Test development tools information retrieval"""
    print("⚙️ Testing Development Tools Information Retrieval...")
    
    monitor = SystemMonitor()
    
    try:
        # Get system info with dev tools
        system_status = await monitor.get_system_info()
        
        print(f"✅ System info retrieved successfully")
        print(f"📊 Dev tools count: {len(system_status.dev_tools)}")
        
        if system_status.dev_tools:
            print("\n🔧 Development Tools:")
            for i, tool in enumerate(system_status.dev_tools, 1):
                print(f"   {i}. {tool.name}")
                print(f"      - Installed: {tool.is_installed}")
                if tool.is_installed:
                    print(f"      - Version: {tool.version or 'Unknown'}")
                    print(f"      - Path: {tool.path or 'Unknown'}")
                    print(f"      - Running: {tool.is_running}")
                    if tool.additional_info:
                        print(f"      - Additional: {tool.additional_info}")
        else:
            print("   - No development tools information found")
            
    except Exception as e:
        print(f"❌ Error retrieving dev tools info: {e}")


def test_dev_tools_prompt_formatting():
    """Test development tools information formatting in prompts"""
    print("\n💬 Testing Development Tools Prompt Formatting...")
    
    generator = JapanesePromptGenerator()
    
    # Test data with dev tools info
    test_dev_tools_data = {
        'timestamp': '2024-01-15 14:30:00',
        'cpu_percent': 25.5,
        'memory_percent': 60.2,
        'disk_percent': 45.8,
        'dev_tools': [
            {
                'name': 'Xcode',
                'version': '15.0',
                'path': '/Applications/Xcode.app/Contents/Developer',
                'is_installed': True,
                'is_running': True,
                'additional_info': None
            },
            {
                'name': 'Git',
                'version': '2.39.3',
                'path': '/usr/bin/git',
                'is_installed': True,
                'is_running': False,
                'additional_info': {
                    'user_name': 'Developer',
                    'user_email': 'dev@example.com'
                }
            },
            {
                'name': 'Homebrew',
                'version': '4.1.11',
                'path': '/opt/homebrew/bin/brew',
                'is_installed': True,
                'is_running': False,
                'additional_info': {
                    'prefix': '/opt/homebrew'
                }
            },
            {
                'name': 'Node.js',
                'version': 'v18.17.0',
                'path': '/opt/homebrew/bin/node',
                'is_installed': True,
                'is_running': False,
                'additional_info': {
                    'npm_version': '9.6.7'
                }
            },
            {
                'name': 'Docker',
                'version': None,
                'path': None,
                'is_installed': False,
                'is_running': False,
                'additional_info': None
            }
        ]
    }
    
    # Test different styles
    styles_to_test = [
        (PromptStyle.CASUAL, "開発ツールの状況は？"),
        (PromptStyle.FRIENDLY, "開発環境を教えて"),
        (PromptStyle.TECHNICAL, "インストール済み開発ツールの詳細"),
        (PromptStyle.PROFESSIONAL, "開発環境の状況報告")
    ]
    
    for style, query in styles_to_test:
        print(f"\n--- {style.value.upper()} Style ---")
        context = ConversationContext(preferred_style=style)
        
        prompt = generator.generate_system_prompt(
            user_query=query,
            system_data=test_dev_tools_data,
            context=context,
            focus_metric=SystemMetricType.DEV_TOOLS
        )
        
        print(f"Query: {query}")
        print("Generated prompt:")
        print(prompt[:700] + "..." if len(prompt) > 700 else prompt)


def test_dev_tools_keyword_detection():
    """Test development tools keyword detection"""
    print("\n🔍 Testing Development Tools Keyword Detection...")
    
    generator = JapanesePromptGenerator()
    
    dev_tools_queries = [
        "開発ツールの状況は？",
        "開発環境を教えて",
        "Xcodeはインストールされてる？",
        "Gitのバージョンは？",
        "Homebrewは使える？",
        "Node.jsの状況は？",
        "development tools",
        "dev environment",
        "coding tools"
    ]
    
    for query in dev_tools_queries:
        focus = generator._detect_query_focus(query)
        result = "✅ DEV_TOOLS" if focus == SystemMetricType.DEV_TOOLS else f"❌ {focus}"
        print(f"'{query}' → {result}")


def test_dev_tools_formatting_edge_cases():
    """Test development tools formatting with edge cases"""
    print("\n⚠️  Testing Development Tools Formatting Edge Cases...")
    
    generator = JapanesePromptGenerator()
    
    edge_cases = [
        # No tools
        {
            'name': 'No Tools',
            'data': {'dev_tools': []}
        },
        # All tools installed
        {
            'name': 'All Tools Installed',
            'data': {
                'dev_tools': [
                    {
                        'name': 'Xcode',
                        'version': '15.0',
                        'path': '/Applications/Xcode.app',
                        'is_installed': True,
                        'is_running': True,
                        'additional_info': None
                    },
                    {
                        'name': 'Git',
                        'version': '2.39.3',
                        'path': '/usr/bin/git',
                        'is_installed': True,
                        'is_running': False,
                        'additional_info': {'user_name': 'Developer'}
                    }
                ]
            }
        },
        # No tools installed
        {
            'name': 'No Tools Installed',
            'data': {
                'dev_tools': [
                    {
                        'name': 'Xcode',
                        'version': None,
                        'path': None,
                        'is_installed': False,
                        'is_running': False,
                        'additional_info': None
                    },
                    {
                        'name': 'Git',
                        'version': None,
                        'path': None,
                        'is_installed': False,
                        'is_running': False,
                        'additional_info': None
                    }
                ]
            }
        }
    ]
    
    for case in edge_cases:
        print(f"\n--- {case['name']} ---")
        formatted = generator._format_dev_tools_info(case['data'], PromptStyle.FRIENDLY)
        print(f"Formatted: {formatted}")


async def main():
    """Run all development tools functionality tests"""
    print("🚀 Starting Development Tools Functionality Tests\n")
    
    # Test dev tools info retrieval
    await test_dev_tools_retrieval()
    
    # Test prompt formatting
    test_dev_tools_prompt_formatting()
    
    # Test keyword detection
    test_dev_tools_keyword_detection()
    
    # Test edge cases
    test_dev_tools_formatting_edge_cases()
    
    print("\n✅ All development tools functionality tests completed!")


if __name__ == "__main__":
    asyncio.run(main())