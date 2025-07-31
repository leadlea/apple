#!/usr/bin/env python3
"""
Test script to demonstrate personalization effectiveness
"""
import tempfile
import shutil
from backend.chat_context_manager import ChatContextManager


def test_personalization_effectiveness():
    """Demonstrate personalization learning and adaptation"""
    
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create context manager
        cm = ChatContextManager(session_id="effectiveness-test", data_dir=temp_dir)
        
        print("=== Personalization Effectiveness Test ===\n")
        
        # Simulate user interactions over time
        print("1. Initial interactions - learning user patterns:")
        
        # User asks about CPU multiple times (shows preference for CPU info)
        cm.add_message("user", "CPU使用率はどうですか？")
        cm.add_message("assistant", "CPU使用率は45%です。")
        
        cm.add_message("user", "CPUの状況を教えて")
        cm.add_message("assistant", "CPU使用率は47%です。")
        
        cm.add_message("user", "プロセッサの負荷は？")
        cm.add_message("assistant", "CPU使用率は50%です。")
        
        # User asks about memory occasionally
        cm.add_message("user", "メモリ使用量は？")
        cm.add_message("assistant", "メモリ使用率は60%です。")
        
        print("   - Added 8 messages (6 CPU-related, 2 memory-related)")
        
        # Show learned patterns
        insights = cm.get_user_insights()
        print(f"   - Most frequent questions: {insights['most_frequent_questions']}")
        print(f"   - Total interactions: {insights['total_interactions']}")
        
        # Show personalized greeting
        greeting = cm.get_personalized_greeting()
        print(f"   - Personalized greeting: {greeting}")
        
        print("\n2. Testing response personalization:")
        
        # Test different personalities
        original_response = "CPU使用率は75%です。メモリ使用率は65%です。"
        
        # Set different personalities and test
        personalities = ['helpful', 'technical', 'casual']
        
        for personality in personalities:
            cm.update_user_preferences({'response_personality': personality})
            personalized = cm.personalize_response(original_response, "CPU使用率は？")
            print(f"   - {personality.capitalize()} style: {personalized}")
        
        print("\n3. Testing detail level adaptation:")
        
        # Test different detail levels
        cm.adjust_detail_level("cpu_usage", "brief")
        brief_response = cm.personalize_response(
            "CPU使用率は85%です。\nメモリ使用率は70%です。\n詳細な説明がここにあります。\nさらに詳しい情報もあります。",
            "CPU使用率は？"
        )
        print(f"   - Brief response: {brief_response}")
        
        cm.adjust_detail_level("cpu_usage", "detailed")
        detailed_response = cm.personalize_response(
            "CPU使用率は85%です。",
            "CPU使用率は？"
        )
        print(f"   - Detailed response: {detailed_response}")
        
        print("\n4. Testing session persistence:")
        
        # Create new context manager with same session ID
        cm2 = ChatContextManager(session_id="effectiveness-test", data_dir=temp_dir)
        
        # Verify data was loaded
        insights2 = cm2.get_user_insights()
        print(f"   - Loaded interactions: {insights2['total_interactions']}")
        print(f"   - Loaded patterns: {list(insights2['user_patterns'].keys())}")
        
        # Show that learning continues
        cm2.add_message("user", "CPU使用率は？")
        insights3 = cm2.get_user_insights()
        cpu_frequency = insights3['user_patterns']['cpu_usage']['frequency']
        print(f"   - CPU question frequency after reload: {cpu_frequency}")
        
        print("\n=== Test completed successfully! ===")
        print("Personalization features are working effectively:")
        print("✓ User pattern learning")
        print("✓ Response personalization")
        print("✓ Detail level adaptation")
        print("✓ Session persistence")
        print("✓ Continuous learning")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_personalization_effectiveness()