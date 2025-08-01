#!/usr/bin/env python3
"""
Disk Details Functionality Test for Mac Status PWA
Tests disk details information retrieval and formatting
"""
import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from system_monitor import SystemMonitor, DiskInfo
from prompt_generator import JapanesePromptGenerator, SystemMetricType, PromptStyle, ConversationContext


async def test_disk_details_retrieval():
    """Test disk details information retrieval"""
    print("💾 Testing Disk Details Information Retrieval...")
    
    monitor = SystemMonitor()
    
    try:
        # Get system info with disk details
        system_status = await monitor.get_system_info()
        
        print(f"✅ System info retrieved successfully")
        print(f"📊 Disk details count: {len(system_status.disk_details)}")
        
        if system_status.disk_details:
            print("\n💿 Disk Details:")
            for i, disk in enumerate(system_status.disk_details, 1):
                print(f"   {i}. {disk.label or disk.mountpoint}")
                print(f"      - Device: {disk.device}")
                print(f"      - Mount: {disk.mountpoint}")
                print(f"      - Type: {disk.fstype}")
                print(f"      - Size: {disk.total_gb:.1f}GB")
                print(f"      - Used: {disk.used_gb:.1f}GB ({disk.percent:.1f}%)")
                print(f"      - Free: {disk.free_gb:.1f}GB")
                print(f"      - System: {disk.is_system}")
                print(f"      - Removable: {disk.is_removable}")
        else:
            print("   - No disk details found")
            
    except Exception as e:
        print(f"❌ Error retrieving disk details: {e}")


def test_disk_details_prompt_formatting():
    """Test disk details information formatting in prompts"""
    print("\n💬 Testing Disk Details Prompt Formatting...")
    
    generator = JapanesePromptGenerator()
    
    # Test data with disk details info
    test_disk_data = {
        'timestamp': '2024-01-15 14:30:00',
        'cpu_percent': 25.5,
        'memory_percent': 60.2,
        'disk_percent': 45.8,
        'disk_details': [
            {
                'device': '/dev/disk3s1',
                'mountpoint': '/',
                'fstype': 'apfs',
                'label': 'Macintosh HD',
                'total_gb': 500.0,
                'used_gb': 230.0,
                'free_gb': 270.0,
                'percent': 46.0,
                'is_removable': False,
                'is_system': True
            },
            {
                'device': '/dev/disk4s1',
                'mountpoint': '/Volumes/External SSD',
                'fstype': 'exfat',
                'label': 'External SSD',
                'total_gb': 1000.0,
                'used_gb': 650.0,
                'free_gb': 350.0,
                'percent': 65.0,
                'is_removable': True,
                'is_system': False
            },
            {
                'device': '/dev/disk5s1',
                'mountpoint': '/Volumes/Backup Drive',
                'fstype': 'hfs',
                'label': 'Backup Drive',
                'total_gb': 2000.0,
                'used_gb': 1200.0,
                'free_gb': 800.0,
                'percent': 60.0,
                'is_removable': True,
                'is_system': False
            }
        ]
    }
    
    # Test different styles
    styles_to_test = [
        (PromptStyle.CASUAL, "ディスクの詳細を教えて"),
        (PromptStyle.FRIENDLY, "外付けドライブの状況は？"),
        (PromptStyle.TECHNICAL, "パーティション情報の詳細"),
        (PromptStyle.PROFESSIONAL, "ストレージ使用状況の報告")
    ]
    
    for style, query in styles_to_test:
        print(f"\n--- {style.value.upper()} Style ---")
        context = ConversationContext(preferred_style=style)
        
        prompt = generator.generate_system_prompt(
            user_query=query,
            system_data=test_disk_data,
            context=context,
            focus_metric=SystemMetricType.DISK_DETAILS
        )
        
        print(f"Query: {query}")
        print("Generated prompt:")
        print(prompt[:700] + "..." if len(prompt) > 700 else prompt)


def test_disk_details_keyword_detection():
    """Test disk details keyword detection"""
    print("\n🔍 Testing Disk Details Keyword Detection...")
    
    generator = JapanesePromptGenerator()
    
    disk_queries = [
        "ディスクの詳細を教えて",
        "パーティション情報は？",
        "外付けドライブの状況は？",
        "ボリュームの一覧を見せて",
        "ストレージの詳細情報",
        "disk details",
        "partition info",
        "external drives",
        "volume list",
        "/Volumes/"
    ]
    
    for query in disk_queries:
        focus = generator._detect_query_focus(query)
        result = "✅ DISK_DETAILS" if focus == SystemMetricType.DISK_DETAILS else f"❌ {focus}"
        print(f"'{query}' → {result}")


def test_disk_details_formatting_edge_cases():
    """Test disk details formatting with edge cases"""
    print("\n⚠️  Testing Disk Details Formatting Edge Cases...")
    
    generator = JapanesePromptGenerator()
    
    edge_cases = [
        # No disks
        {
            'name': 'No Disks',
            'data': {'disk_details': []}
        },
        # Single large disk
        {
            'name': 'Single Large Disk',
            'data': {
                'disk_details': [
                    {
                        'device': '/dev/disk1s1',
                        'mountpoint': '/',
                        'fstype': 'apfs',
                        'label': 'Macintosh HD',
                        'total_gb': 2048.0,
                        'used_gb': 1024.0,
                        'free_gb': 1024.0,
                        'percent': 50.0,
                        'is_removable': False,
                        'is_system': True
                    }
                ]
            }
        },
        # Multiple external drives
        {
            'name': 'Multiple External Drives',
            'data': {
                'disk_details': [
                    {
                        'device': '/dev/disk2s1',
                        'mountpoint': '/Volumes/USB Drive 1',
                        'fstype': 'exfat',
                        'label': 'USB Drive 1',
                        'total_gb': 64.0,
                        'used_gb': 32.0,
                        'free_gb': 32.0,
                        'percent': 50.0,
                        'is_removable': True,
                        'is_system': False
                    },
                    {
                        'device': '/dev/disk3s1',
                        'mountpoint': '/Volumes/USB Drive 2',
                        'fstype': 'fat32',
                        'label': 'USB Drive 2',
                        'total_gb': 128.0,
                        'used_gb': 96.0,
                        'free_gb': 32.0,
                        'percent': 75.0,
                        'is_removable': True,
                        'is_system': False
                    }
                ]
            }
        }
    ]
    
    for case in edge_cases:
        print(f"\n--- {case['name']} ---")
        formatted = generator._format_disk_details_info(case['data'], PromptStyle.FRIENDLY)
        print(f"Formatted: {formatted}")


async def main():
    """Run all disk details functionality tests"""
    print("🚀 Starting Disk Details Functionality Tests\n")
    
    # Test disk details info retrieval
    await test_disk_details_retrieval()
    
    # Test prompt formatting
    test_disk_details_prompt_formatting()
    
    # Test keyword detection
    test_disk_details_keyword_detection()
    
    # Test edge cases
    test_disk_details_formatting_edge_cases()
    
    print("\n✅ All disk details functionality tests completed!")


if __name__ == "__main__":
    asyncio.run(main())