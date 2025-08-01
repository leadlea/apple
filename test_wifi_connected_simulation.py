#!/usr/bin/env python3
"""
WiFi Connected State Simulation Test
Tests WiFi functionality with simulated connected state
"""
import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from prompt_generator import JapanesePromptGenerator, SystemMetricType, PromptStyle, ConversationContext


def simulate_wifi_responses():
    """Simulate WiFi responses for different connection states"""
    print("🌐 Simulating WiFi Connection States\n")
    
    generator = JapanesePromptGenerator()
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Excellent 5GHz Connection',
            'data': {
                'wifi': {
                    'ssid': 'MyHome-5G',
                    'signal_strength': -35,
                    'signal_quality': 'excellent',
                    'channel': 149,
                    'frequency': 5.0,
                    'security': 'WPA3(PSK/AES)',
                    'link_speed': 1200,
                    'is_connected': True,
                    'interface_name': 'en0'
                }
            },
            'queries': ['WiFiの調子はどう？', 'ネットワークの状況は？']
        },
        {
            'name': 'Good 2.4GHz Connection',
            'data': {
                'wifi': {
                    'ssid': 'CoffeeShop-WiFi',
                    'signal_strength': -55,
                    'signal_quality': 'good',
                    'channel': 6,
                    'frequency': 2.4,
                    'security': 'WPA2(PSK/AES)',
                    'link_speed': 300,
                    'is_connected': True,
                    'interface_name': 'en0'
                }
            },
            'queries': ['信号強度を教えて', '接続速度はどのくらい？']
        },
        {
            'name': 'Poor Connection',
            'data': {
                'wifi': {
                    'ssid': 'DistantRouter',
                    'signal_strength': -85,
                    'signal_quality': 'poor',
                    'channel': 11,
                    'frequency': 2.4,
                    'security': 'WPA2(PSK/AES)',
                    'link_speed': 54,
                    'is_connected': True,
                    'interface_name': 'en0'
                }
            },
            'queries': ['電波の状態は？', 'wifi status']
        },
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
            },
            'queries': ['WiFiに接続してる？', 'network connection']
        }
    ]
    
    for scenario in scenarios:
        print(f"📊 {scenario['name']}")
        print("=" * 50)
        
        for query in scenario['queries']:
            print(f"\n🗣️  Query: {query}")
            
            # Test different styles
            for style in [PromptStyle.CASUAL, PromptStyle.FRIENDLY]:
                context = ConversationContext(preferred_style=style)
                
                # Generate formatted WiFi info
                wifi_formatted = generator._format_wifi_info(scenario['data'], style)
                
                print(f"   {style.value}: {wifi_formatted}")
        
        print("\n")


def simulate_chat_responses():
    """Simulate actual chat responses"""
    print("💬 Simulating Chat Responses\n")
    
    # Simulate working_server.py style responses
    scenarios = [
        {
            'ssid': 'MyHome-5G',
            'signal_strength': -35,
            'channel': 149,
            'security': 'WPA3(PSK/AES)'
        },
        {
            'ssid': 'CoffeeShop',
            'signal_strength': -65,
            'channel': 6,
            'security': 'WPA2(PSK/AES)'
        },
        {
            'ssid': 'WeakSignal',
            'signal_strength': -88,
            'channel': 11,
            'security': 'WPA2(PSK/AES)'
        }
    ]
    
    for i, wifi_info in enumerate(scenarios, 1):
        print(f"📶 Scenario {i}: {wifi_info['ssid']}")
        print("-" * 40)
        
        # Simulate server response format
        response_text = f"📶 WiFi接続情報\n\n"
        response_text += f"🌐 ネットワーク: {wifi_info['ssid']}\n"
        
        signal_strength = wifi_info['signal_strength']
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
        response_text += f"📻 チャンネル: {wifi_info['channel']}\n"
        response_text += f"🔒 セキュリティ: {wifi_info['security']}\n"
        
        # Add connection quality assessment
        if signal_strength >= -50:
            response_text += "\n✅ 接続品質は良好です。"
        elif signal_strength >= -70:
            response_text += "\n⚠️ 接続品質は普通です。"
        else:
            response_text += "\n🔴 接続品質が低下しています。ルーターに近づくことをお勧めします。"
        
        print(response_text)
        print()


async def main():
    """Run WiFi simulation tests"""
    print("🚀 Starting WiFi Connection Simulation Tests\n")
    
    # Test prompt formatting
    simulate_wifi_responses()
    
    # Test chat responses
    simulate_chat_responses()
    
    print("✅ All WiFi simulation tests completed!")


if __name__ == "__main__":
    asyncio.run(main())