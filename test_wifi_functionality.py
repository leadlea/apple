#!/usr/bin/env python3
"""
WiFi Functionality Test for Mac Status PWA
Tests WiFi information retrieval and formatting
"""
import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from system_monitor import SystemMonitor, WiFiInfo
from prompt_generator import JapanesePromptGenerator, SystemMetricType, PromptStyle, ConversationContext


async def test_wifi_info_retrieval():
    """Test WiFi information retrieval"""
    print("📶 Testing WiFi Information Retrieval...")
    
    monitor = SystemMonitor()
    
    try:
        # Get system info with WiFi
        system_status = await monitor.get_system_info()
        
        print(f"✅ System info retrieved successfully")
        print(f"📊 WiFi info: {system_status.wifi}")
        
        if system_status.wifi:
            wifi = system_status.wifi
            print(f"   - Connected: {wifi.is_connected}")
            if wifi.is_connected:
                print(f"   - SSID: {wifi.ssid}")
                print(f"   - Signal strength: {wifi.signal_strength}dBm")
                print(f"   - Signal quality: {wifi.signal_quality}")
                print(f"   - Channel: {wifi.channel}")
                print(f"   - Frequency: {wifi.frequency}GHz" if wifi.frequency else "   - Frequency: Unknown")
                print(f"   - Security: {wifi.security}")
                print(f"   - Link speed: {wifi.link_speed}Mbps" if wifi.link_speed else "   - Link speed: Unknown")
                print(f"   - Interface: {wifi.interface_name}")
        else:
            print("   - No WiFi information available")
            
    except Exception as e:
        print(f"❌ Error retrieving WiFi info: {e}")


def test_wifi_prompt_formatting():
    """Test WiFi information formatting in prompts"""
    print("\n💬 Testing WiFi Prompt Formatting...")
    
    generator = JapanesePromptGenerator()
    
    # Test data with WiFi info
    test_wifi_data = {
        'timestamp': '2024-01-15 14:30:00',
        'cpu_percent': 25.5,
        'memory_percent': 60.2,
        'disk_percent': 45.8,
        'wifi': {
            'ssid': 'MyWiFi-5G',
            'signal_strength': -45,
            'signal_quality': 'good',
            'channel': 149,
            'frequency': 5.0,
            'security': 'WPA2(PSK/AES)',
            'link_speed': 866,
            'is_connected': True,
            'interface_name': 'en0'
        }
    }
    
    # Test different styles
    styles_to_test = [
        (PromptStyle.CASUAL, "WiFiの調子はどう？"),
        (PromptStyle.FRIENDLY, "ネットワークの状況を教えて"),
        (PromptStyle.TECHNICAL, "WiFiの詳細情報"),
        (PromptStyle.PROFESSIONAL, "ネットワーク接続状況の報告")
    ]
    
    for style, query in styles_to_test:
        print(f"\n--- {style.value.upper()} Style ---")
        context = ConversationContext(preferred_style=style)
        
        prompt = generator.generate_system_prompt(
            user_query=query,
            system_data=test_wifi_data,
            context=context,
            focus_metric=SystemMetricType.WIFI
        )
        
        print(f"Query: {query}")
        print("Generated prompt:")
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)


def test_wifi_keyword_detection():
    """Test WiFi keyword detection"""
    print("\n🔍 Testing WiFi Keyword Detection...")
    
    generator = JapanesePromptGenerator()
    
    wifi_queries = [
        "WiFiの調子はどう？",
        "ネットワークの状況は？",
        "接続速度はどのくらい？",
        "信号強度を教えて",
        "電波の状態は？",
        "SSIDは何？",
        "wifi status",
        "network connection",
        "signal strength"
    ]
    
    for query in wifi_queries:
        focus = generator._detect_query_focus(query)
        result = "✅ WIFI" if focus == SystemMetricType.WIFI else f"❌ {focus}"
        print(f"'{query}' → {result}")


def test_wifi_formatting_edge_cases():
    """Test WiFi formatting with edge cases"""
    print("\n⚠️  Testing WiFi Formatting Edge Cases...")
    
    generator = JapanesePromptGenerator()
    
    edge_cases = [
        # Not connected
        {
            'name': 'Not Connected',
            'data': {
                'wifi': {
                    'ssid': None,
                    'signal_strength': None,
                    'signal_quality': 'no_signal',
                    'channel': None,
                    'frequency': None,
                    'security': None,
                    'link_speed': None,
                    'is_connected': False,
                    'interface_name': 'en0'
                }
            }
        },
        # Excellent signal
        {
            'name': 'Excellent Signal',
            'data': {
                'wifi': {
                    'ssid': 'HomeWiFi',
                    'signal_strength': -25,
                    'signal_quality': 'excellent',
                    'channel': 6,
                    'frequency': 2.4,
                    'security': 'WPA3(PSK/AES)',
                    'link_speed': 300,
                    'is_connected': True,
                    'interface_name': 'en0'
                }
            }
        },
        # Poor signal
        {
            'name': 'Poor Signal',
            'data': {
                'wifi': {
                    'ssid': 'DistantWiFi',
                    'signal_strength': -85,
                    'signal_quality': 'poor',
                    'channel': 11,
                    'frequency': 2.4,
                    'security': 'WPA2(PSK/AES)',
                    'link_speed': 54,
                    'is_connected': True,
                    'interface_name': 'en0'
                }
            }
        },
        # No WiFi data
        {
            'name': 'No WiFi Data',
            'data': {'wifi': None}
        }
    ]
    
    for case in edge_cases:
        print(f"\n--- {case['name']} ---")
        formatted = generator._format_wifi_info(case['data'], PromptStyle.FRIENDLY)
        print(f"Formatted: {formatted}")


async def main():
    """Run all WiFi functionality tests"""
    print("🚀 Starting WiFi Functionality Tests\n")
    
    # Test WiFi info retrieval
    await test_wifi_info_retrieval()
    
    # Test prompt formatting
    test_wifi_prompt_formatting()
    
    # Test keyword detection
    test_wifi_keyword_detection()
    
    # Test edge cases
    test_wifi_formatting_edge_cases()
    
    print("\n✅ All WiFi functionality tests completed!")


if __name__ == "__main__":
    asyncio.run(main())