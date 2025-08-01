#!/usr/bin/env python3
"""
Battery Functionality Test for Mac Status PWA
Tests battery information retrieval and formatting
"""
import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from system_monitor import SystemMonitor, BatteryInfo
from prompt_generator import JapanesePromptGenerator, SystemMetricType, PromptStyle, ConversationContext


async def test_battery_info_retrieval():
    """Test battery information retrieval"""
    print("🔋 Testing Battery Information Retrieval...")
    
    monitor = SystemMonitor()
    
    try:
        # Get system info with battery
        system_status = await monitor.get_system_info()
        
        print(f"✅ System info retrieved successfully")
        print(f"📊 Battery info: {system_status.battery}")
        
        if system_status.battery:
            battery = system_status.battery
            print(f"   - Percent: {battery.percent}%")
            print(f"   - Power plugged: {battery.power_plugged}")
            print(f"   - Status: {battery.status}")
            if battery.secsleft:
                hours = battery.secsleft // 3600
                minutes = (battery.secsleft % 3600) // 60
                print(f"   - Time remaining: {hours}h {minutes}m")
        else:
            print("   - No battery detected (desktop Mac)")
            
    except Exception as e:
        print(f"❌ Error retrieving battery info: {e}")


def test_battery_prompt_formatting():
    """Test battery information formatting in prompts"""
    print("\n💬 Testing Battery Prompt Formatting...")
    
    generator = JapanesePromptGenerator()
    
    # Test data with battery info
    test_battery_data = {
        'timestamp': '2024-01-15 14:30:00',
        'cpu_percent': 25.5,
        'memory_percent': 60.2,
        'disk_percent': 45.8,
        'battery': {
            'percent': 78.5,
            'power_plugged': False,
            'secsleft': 10800,  # 3 hours
            'status': 'discharging'
        }
    }
    
    # Test different styles
    styles_to_test = [
        (PromptStyle.CASUAL, "バッテリーはどのくらい？"),
        (PromptStyle.FRIENDLY, "バッテリーの残量を教えて"),
        (PromptStyle.TECHNICAL, "バッテリーの詳細情報"),
        (PromptStyle.PROFESSIONAL, "バッテリー状況の報告")
    ]
    
    for style, query in styles_to_test:
        print(f"\n--- {style.value.upper()} Style ---")
        context = ConversationContext(preferred_style=style)
        
        prompt = generator.generate_system_prompt(
            user_query=query,
            system_data=test_battery_data,
            context=context,
            focus_metric=SystemMetricType.BATTERY
        )
        
        print(f"Query: {query}")
        print("Generated prompt:")
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)


def test_battery_keyword_detection():
    """Test battery keyword detection"""
    print("\n🔍 Testing Battery Keyword Detection...")
    
    generator = JapanesePromptGenerator()
    
    battery_queries = [
        "バッテリーはどう？",
        "電池の残量は？",
        "充電はあとどのくらい？",
        "battery status",
        "power remaining",
        "あと何時間使える？"
    ]
    
    for query in battery_queries:
        focus = generator._detect_query_focus(query)
        result = "✅ BATTERY" if focus == SystemMetricType.BATTERY else f"❌ {focus}"
        print(f"'{query}' → {result}")


async def main():
    """Run all battery functionality tests"""
    print("🚀 Starting Battery Functionality Tests\n")
    
    # Test battery info retrieval
    await test_battery_info_retrieval()
    
    # Test prompt formatting
    test_battery_prompt_formatting()
    
    # Test keyword detection
    test_battery_keyword_detection()
    
    print("\n✅ All battery functionality tests completed!")


if __name__ == "__main__":
    asyncio.run(main())