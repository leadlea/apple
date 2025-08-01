#!/usr/bin/env python3
"""
Thermal Functionality Test for Mac Status PWA
Tests thermal and fan information retrieval and formatting
"""
import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from system_monitor import SystemMonitor, ThermalInfo
from prompt_generator import JapanesePromptGenerator, SystemMetricType, PromptStyle, ConversationContext


async def test_thermal_info_retrieval():
    """Test thermal information retrieval"""
    print("🌡️ Testing Thermal Information Retrieval...")
    
    monitor = SystemMonitor()
    
    try:
        # Get system info with thermal info
        system_status = await monitor.get_system_info()
        
        print(f"✅ System info retrieved successfully")
        print(f"📊 Thermal info: {system_status.thermal_info}")
        
        if system_status.thermal_info:
            thermal = system_status.thermal_info
            print(f"   - CPU Temperature: {thermal.cpu_temperature}°C" if thermal.cpu_temperature else "   - CPU Temperature: Not available")
            print(f"   - GPU Temperature: {thermal.gpu_temperature}°C" if thermal.gpu_temperature else "   - GPU Temperature: Not available")
            print(f"   - Thermal State: {thermal.thermal_state}")
            print(f"   - Fan Count: {len(thermal.fan_speeds)}")
            
            if thermal.fan_speeds:
                for i, fan in enumerate(thermal.fan_speeds, 1):
                    print(f"     Fan {i}: {fan.get('name', 'Unknown')} - {fan.get('rpm', 0)}rpm")
            
            if thermal.power_metrics:
                print(f"   - Power Source: {thermal.power_metrics.get('power_source', 'Unknown')}")
        else:
            print("   - No thermal information available")
            
    except Exception as e:
        print(f"❌ Error retrieving thermal info: {e}")


def test_thermal_prompt_formatting():
    """Test thermal information formatting in prompts"""
    print("\n💬 Testing Thermal Prompt Formatting...")
    
    generator = JapanesePromptGenerator()
    
    # Test data with thermal info
    test_thermal_data = {
        'timestamp': '2024-01-15 14:30:00',
        'cpu_percent': 25.5,
        'memory_percent': 60.2,
        'disk_percent': 45.8,
        'thermal_info': {
            'cpu_temperature': 65.5,
            'gpu_temperature': 58.2,
            'fan_speeds': [
                {'name': 'Fan 0', 'rpm': 1800},
                {'name': 'Fan 1', 'rpm': 1650}
            ],
            'thermal_state': 'warm',
            'power_metrics': {
                'power_source': 'AC'
            }
        }
    }
    
    # Test different styles
    styles_to_test = [
        (PromptStyle.CASUAL, "システムの温度はどう？"),
        (PromptStyle.FRIENDLY, "ファンの回転数を教えて"),
        (PromptStyle.TECHNICAL, "サーマル情報の詳細"),
        (PromptStyle.PROFESSIONAL, "システム温度状況の報告")
    ]
    
    for style, query in styles_to_test:
        print(f"\n--- {style.value.upper()} Style ---")
        context = ConversationContext(preferred_style=style)
        
        prompt = generator.generate_system_prompt(
            user_query=query,
            system_data=test_thermal_data,
            context=context,
            focus_metric=SystemMetricType.THERMAL
        )
        
        print(f"Query: {query}")
        print("Generated prompt:")
        print(prompt[:600] + "..." if len(prompt) > 600 else prompt)


def test_thermal_keyword_detection():
    """Test thermal keyword detection"""
    print("\n🔍 Testing Thermal Keyword Detection...")
    
    generator = JapanesePromptGenerator()
    
    thermal_queries = [
        "システムの温度はどう？",
        "ファンの回転数を教えて",
        "熱くなってない？",
        "冷却状況は？",
        "サーマル情報を見せて",
        "temperature status",
        "fan speed",
        "thermal info",
        "system hot"
    ]
    
    for query in thermal_queries:
        focus = generator._detect_query_focus(query)
        result = "✅ THERMAL" if focus == SystemMetricType.THERMAL else f"❌ {focus}"
        print(f"'{query}' → {result}")


def test_thermal_formatting_edge_cases():
    """Test thermal formatting with edge cases"""
    print("\n⚠️  Testing Thermal Formatting Edge Cases...")
    
    generator = JapanesePromptGenerator()
    
    edge_cases = [
        # No thermal data
        {
            'name': 'No Thermal Data',
            'data': {'thermal_info': None}
        },
        # High temperature
        {
            'name': 'High Temperature',
            'data': {
                'thermal_info': {
                    'cpu_temperature': 95.0,
                    'gpu_temperature': None,
                    'fan_speeds': [
                        {'name': 'Fan 0', 'rpm': 4500}
                    ],
                    'thermal_state': 'critical',
                    'power_metrics': {'power_source': 'Battery'}
                }
            }
        },
        # Normal temperature
        {
            'name': 'Normal Temperature',
            'data': {
                'thermal_info': {
                    'cpu_temperature': 45.0,
                    'gpu_temperature': 42.0,
                    'fan_speeds': [
                        {'name': 'Fan 0', 'rpm': 1200},
                        {'name': 'Fan 1', 'rpm': 1100}
                    ],
                    'thermal_state': 'normal',
                    'power_metrics': {'power_source': 'AC'}
                }
            }
        },
        # No temperature but fan data
        {
            'name': 'Fan Data Only',
            'data': {
                'thermal_info': {
                    'cpu_temperature': None,
                    'gpu_temperature': None,
                    'fan_speeds': [
                        {'name': 'System Fan', 'rpm': 2000}
                    ],
                    'thermal_state': 'unknown',
                    'power_metrics': None
                }
            }
        }
    ]
    
    for case in edge_cases:
        print(f"\n--- {case['name']} ---")
        formatted = generator._format_thermal_info(case['data'], PromptStyle.FRIENDLY)
        print(f"Formatted: {formatted}")


async def main():
    """Run all thermal functionality tests"""
    print("🚀 Starting Thermal Functionality Tests\n")
    
    # Test thermal info retrieval
    await test_thermal_info_retrieval()
    
    # Test prompt formatting
    test_thermal_prompt_formatting()
    
    # Test keyword detection
    test_thermal_keyword_detection()
    
    # Test edge cases
    test_thermal_formatting_edge_cases()
    
    print("\n✅ All thermal functionality tests completed!")


if __name__ == "__main__":
    asyncio.run(main())