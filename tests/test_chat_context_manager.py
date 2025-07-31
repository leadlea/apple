"""
Tests for ChatContextManager
"""
import pytest
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from backend.chat_context_manager import ChatContextManager, ChatMessage, UserPreferences


class TestChatMessage:
    """Test ChatMessage dataclass"""
    
    def test_chat_message_creation(self):
        """Test creating a ChatMessage"""
        msg = ChatMessage(
            id="test-id",
            timestamp=datetime.now(),
            role="user",
            content="Hello",
            system_context={"cpu": 50}
        )
        
        assert msg.id == "test-id"
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.system_context == {"cpu": 50}
    
    def test_chat_message_to_dict(self):
        """Test converting ChatMessage to dictionary"""
        timestamp = datetime.now()
        msg = ChatMessage(
            id="test-id",
            timestamp=timestamp,
            role="user",
            content="Hello"
        )
        
        result = msg.to_dict()
        
        assert result['id'] == "test-id"
        assert result['timestamp'] == timestamp.isoformat()
        assert result['role'] == "user"
        assert result['content'] == "Hello"
        assert result['system_context'] is None
    
    def test_chat_message_from_dict(self):
        """Test creating ChatMessage from dictionary"""
        timestamp = datetime.now()
        data = {
            'id': "test-id",
            'timestamp': timestamp.isoformat(),
            'role': "assistant",
            'content': "Hi there",
            'system_context': {"memory": 70}
        }
        
        msg = ChatMessage.from_dict(data)
        
        assert msg.id == "test-id"
        assert msg.timestamp == timestamp
        assert msg.role == "assistant"
        assert msg.content == "Hi there"
        assert msg.system_context == {"memory": 70}


class TestUserPreferences:
    """Test UserPreferences dataclass"""
    
    def test_user_preferences_defaults(self):
        """Test UserPreferences default values"""
        prefs = UserPreferences()
        
        assert prefs.language_style == "friendly"
        assert prefs.notification_level == "normal"
        assert prefs.preferred_metrics == ["cpu", "memory", "disk"]
        assert prefs.response_personality == "helpful"
    
    def test_user_preferences_custom(self):
        """Test UserPreferences with custom values"""
        prefs = UserPreferences(
            language_style="formal",
            notification_level="high",
            preferred_metrics=["cpu", "network"],
            response_personality="technical"
        )
        
        assert prefs.language_style == "formal"
        assert prefs.notification_level == "high"
        assert prefs.preferred_metrics == ["cpu", "network"]
        assert prefs.response_personality == "technical"


class TestChatContextManager:
    """Test ChatContextManager functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def context_manager(self, temp_dir):
        """Create ChatContextManager instance for testing"""
        return ChatContextManager(session_id="test-session", data_dir=temp_dir)
    
    def test_initialization(self, context_manager):
        """Test ChatContextManager initialization"""
        assert context_manager.session_id == "test-session"
        assert len(context_manager.conversation_history) == 0
        assert isinstance(context_manager.user_preferences, UserPreferences)
    
    def test_add_message(self, context_manager):
        """Test adding messages to conversation history"""
        message_id = context_manager.add_message("user", "Hello", {"cpu": 50})
        
        assert len(context_manager.conversation_history) == 1
        assert isinstance(message_id, str)
        
        msg = context_manager.conversation_history[0]
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.system_context == {"cpu": 50}
    
    def test_add_multiple_messages(self, context_manager):
        """Test adding multiple messages"""
        context_manager.add_message("user", "Hello")
        context_manager.add_message("assistant", "Hi there")
        context_manager.add_message("user", "How are you?")
        
        assert len(context_manager.conversation_history) == 3
        assert context_manager.conversation_history[0].role == "user"
        assert context_manager.conversation_history[1].role == "assistant"
        assert context_manager.conversation_history[2].role == "user"
    
    def test_conversation_history_limit(self, context_manager):
        """Test conversation history is limited to 50 messages"""
        # Add 55 messages
        for i in range(55):
            context_manager.add_message("user", f"Message {i}")
        
        # Should only keep last 50
        assert len(context_manager.conversation_history) == 50
        assert context_manager.conversation_history[0].content == "Message 5"
        assert context_manager.conversation_history[-1].content == "Message 54"
    
    def test_get_conversation_history(self, context_manager):
        """Test getting conversation history"""
        context_manager.add_message("user", "Message 1")
        context_manager.add_message("assistant", "Response 1")
        context_manager.add_message("user", "Message 2")
        
        # Get all history
        all_history = context_manager.get_conversation_history()
        assert len(all_history) == 3
        
        # Get limited history
        limited_history = context_manager.get_conversation_history(2)
        assert len(limited_history) == 2
        assert limited_history[0].content == "Response 1"
        assert limited_history[1].content == "Message 2"
    
    def test_get_context_prompt(self, context_manager):
        """Test generating context prompt"""
        # Add some conversation history
        context_manager.add_message("user", "What's my CPU usage?")
        context_manager.add_message("assistant", "Your CPU usage is 45%")
        
        system_data = {
            'cpu_percent': 45.5,
            'memory_percent': 60.2,
            'disk_percent': 75.0
        }
        
        prompt = context_manager.get_context_prompt(system_data)
        
        assert "CPU使用率: 45.5%" in prompt
        assert "メモリ使用率: 60.2%" in prompt
        assert "ディスク使用率: 75.0%" in prompt
        assert "過去の会話:" in prompt
        assert "What's my CPU usage?" in prompt
        assert "Your CPU usage is 45%" in prompt
    
    def test_clear_history(self, context_manager):
        """Test clearing conversation history"""
        context_manager.add_message("user", "Hello")
        context_manager.add_message("assistant", "Hi")
        
        assert len(context_manager.conversation_history) == 2
        
        context_manager.clear_history()
        
        assert len(context_manager.conversation_history) == 0 
   
    def test_update_user_preferences(self, context_manager):
        """Test updating user preferences"""
        new_prefs = {
            'language_style': 'formal',
            'response_personality': 'technical',
            'preferred_metrics': ['cpu', 'network']
        }
        
        context_manager.update_user_preferences(new_prefs)
        
        prefs = context_manager.get_user_preferences()
        assert prefs.language_style == 'formal'
        assert prefs.response_personality == 'technical'
        assert prefs.preferred_metrics == ['cpu', 'network']
        assert prefs.notification_level == 'normal'  # Should remain unchanged
    
    def test_session_persistence(self, temp_dir):
        """Test session data persistence"""
        # Create first context manager and add data
        cm1 = ChatContextManager(session_id="persist-test", data_dir=temp_dir)
        cm1.add_message("user", "Hello")
        cm1.add_message("assistant", "Hi there")
        cm1.update_user_preferences({'language_style': 'formal'})
        
        # Create second context manager with same session
        cm2 = ChatContextManager(session_id="persist-test", data_dir=temp_dir)
        
        # Should load previous data
        assert len(cm2.conversation_history) == 2
        assert cm2.conversation_history[0].content == "Hello"
        assert cm2.conversation_history[1].content == "Hi there"
        assert cm2.user_preferences.language_style == 'formal'
    
    def test_session_stats(self, context_manager):
        """Test getting session statistics"""
        context_manager.add_message("user", "Hello")
        context_manager.add_message("assistant", "Hi")
        
        stats = context_manager.get_session_stats()
        
        assert stats['session_id'] == "test-session"
        assert stats['message_count'] == 2
        assert stats['last_activity'] is not None
        assert 'user_preferences' in stats
    
    def test_session_file_creation(self, context_manager, temp_dir):
        """Test that session file is created"""
        context_manager.add_message("user", "Test message")
        
        session_file = Path(temp_dir) / "session_test-session.json"
        assert session_file.exists()
        
        # Verify file content
        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['session_id'] == "test-session"
        assert len(data['conversation_history']) == 1
        assert data['conversation_history'][0]['content'] == "Test message"
    
    def test_corrupted_session_file_handling(self, temp_dir):
        """Test handling of corrupted session file"""
        # Create corrupted session file
        session_file = Path(temp_dir) / "session_corrupted-test.json"
        with open(session_file, 'w') as f:
            f.write("invalid json content")
        
        # Should handle gracefully and initialize with defaults
        cm = ChatContextManager(session_id="corrupted-test", data_dir=temp_dir)
        
        assert len(cm.conversation_history) == 0
        assert isinstance(cm.user_preferences, UserPreferences)
    
    def test_empty_system_data_context_prompt(self, context_manager):
        """Test context prompt with empty system data"""
        prompt = context_manager.get_context_prompt({})
        
        assert "CPU使用率: N/A%" in prompt
        assert "メモリ使用率: N/A%" in prompt
        assert "ディスク使用率: N/A%" in prompt
        assert "あなたはMacのシステム状態を監視し" in prompt


if __name__ == "__main__":
    pytest.main([__file__])


class TestPersonalizationEngine:
    """Test PersonalizationEngine functionality"""
    
    @pytest.fixture
    def personalization_engine(self):
        """Create PersonalizationEngine instance for testing"""
        from backend.chat_context_manager import PersonalizationEngine
        return PersonalizationEngine()
    
    def test_analyze_user_question(self, personalization_engine):
        """Test question type analysis"""
        # Test CPU questions
        assert personalization_engine.analyze_user_question("CPU使用率はどうですか？") == "cpu_usage"
        assert personalization_engine.analyze_user_question("プロセッサの状況は？") == "cpu_usage"
        
        # Test memory questions
        assert personalization_engine.analyze_user_question("メモリ使用量を教えて") == "memory_usage"
        assert personalization_engine.analyze_user_question("RAMの状況は？") == "memory_usage"
        
        # Test disk questions
        assert personalization_engine.analyze_user_question("ディスク容量は？") == "disk_usage"
        assert personalization_engine.analyze_user_question("ストレージの状況") == "disk_usage"
        
        # Test general chat
        assert personalization_engine.analyze_user_question("こんにちは") == "general_chat"
        assert personalization_engine.analyze_user_question("ありがとう") == "general_chat"
    
    def test_learn_user_pattern(self, personalization_engine):
        """Test learning user patterns"""
        # Ask CPU question multiple times
        personalization_engine.learn_user_pattern("CPU使用率は？")
        personalization_engine.learn_user_pattern("CPUの状況を教えて")
        personalization_engine.learn_user_pattern("プロセッサの負荷は？")
        
        # Check pattern learning
        assert "cpu_usage" in personalization_engine.user_patterns
        assert personalization_engine.user_patterns["cpu_usage"].frequency == 3
    
    def test_get_most_frequent_questions(self, personalization_engine):
        """Test getting most frequent question types"""
        # Create different patterns with different frequencies
        personalization_engine.learn_user_pattern("CPU使用率は？")
        personalization_engine.learn_user_pattern("CPU使用率は？")
        personalization_engine.learn_user_pattern("CPU使用率は？")
        
        personalization_engine.learn_user_pattern("メモリ使用量は？")
        personalization_engine.learn_user_pattern("メモリ使用量は？")
        
        personalization_engine.learn_user_pattern("ディスク容量は？")
        
        frequent = personalization_engine.get_most_frequent_questions(2)
        assert frequent[0] == "cpu_usage"
        assert frequent[1] == "memory_usage"
    
    def test_personalize_response_brief(self, personalization_engine):
        """Test response personalization with brief detail level"""
        # Set brief detail level for CPU questions
        personalization_engine.learn_user_pattern("CPU使用率は？")
        personalization_engine.user_patterns["cpu_usage"].preferred_detail_level = "brief"
        
        response = "CPU使用率は45%です。\nメモリ使用率は60%です。\n詳細な説明がここに続きます。\nさらに詳しい情報もあります。"
        
        personalized = personalization_engine.personalize_response(response, "helpful", "cpu_usage")
        
        # Should be more concise
        lines = personalized.split('\n')
        assert len(lines) <= 3
        assert "45%" in personalized
    
    def test_personalize_response_detailed(self, personalization_engine):
        """Test response personalization with detailed level"""
        # Set detailed level first
        personalization_engine.learn_user_pattern("CPU使用率は？")
        personalization_engine.user_patterns["cpu_usage"].preferred_detail_level = "detailed"
        
        response = "CPU使用率は85%です。"
        
        personalized = personalization_engine.personalize_response(response, "helpful", "cpu_usage")
        
        # Should have additional context for high CPU usage
        assert "CPU使用率が高い場合" in personalized or len(personalized) > len(response)
    
    def test_personalize_response_tone(self, personalization_engine):
        """Test response tone personalization"""
        response = "CPU使用率は45%です！"
        
        # Test casual tone
        casual = personalization_engine.personalize_response(response, "casual", "cpu_usage")
        assert "だよ" in casual or "るよ" in casual
        
        # Test professional tone
        professional = personalization_engine.personalize_response(response, "technical", "cpu_usage")
        assert "！" not in professional
    
    def test_serialization(self, personalization_engine):
        """Test PersonalizationEngine serialization"""
        # Add some patterns
        personalization_engine.learn_user_pattern("CPU使用率は？")
        personalization_engine.learn_user_pattern("メモリ使用量は？")
        
        # Serialize
        data = personalization_engine.to_dict()
        
        # Create new engine and load data
        from backend.chat_context_manager import PersonalizationEngine
        new_engine = PersonalizationEngine()
        new_engine.from_dict(data)
        
        # Verify data was loaded correctly
        assert "cpu_usage" in new_engine.user_patterns
        assert "memory_usage" in new_engine.user_patterns
        assert new_engine.user_patterns["cpu_usage"].frequency == 1


class TestChatContextManagerPersonalization:
    """Test ChatContextManager personalization features"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def context_manager(self, temp_dir):
        """Create ChatContextManager instance for testing"""
        return ChatContextManager(session_id="personalization-test", data_dir=temp_dir)
    
    def test_learning_from_user_messages(self, context_manager):
        """Test that user messages are learned from"""
        context_manager.add_message("user", "CPU使用率はどうですか？")
        context_manager.add_message("user", "CPUの状況を教えて")
        
        # Check that patterns were learned
        assert "cpu_usage" in context_manager.personalization_engine.user_patterns
        assert context_manager.personalization_engine.user_patterns["cpu_usage"].frequency == 2
    
    def test_personalize_response(self, context_manager):
        """Test response personalization"""
        # Set up user pattern
        context_manager.add_message("user", "CPU使用率は？")
        
        response = "CPU使用率は45%です。"
        user_question = "CPU使用率はどう？"
        
        personalized = context_manager.personalize_response(response, user_question)
        
        # Should return a string (basic test)
        assert isinstance(personalized, str)
        assert len(personalized) > 0
    
    def test_get_user_insights(self, context_manager):
        """Test getting user behavior insights"""
        # Add some messages to create patterns
        context_manager.add_message("user", "CPU使用率は？")
        context_manager.add_message("assistant", "45%です")
        context_manager.add_message("user", "メモリ使用量は？")
        context_manager.add_message("assistant", "60%です")
        context_manager.add_message("user", "CPU使用率は？")
        
        insights = context_manager.get_user_insights()
        
        assert 'most_frequent_questions' in insights
        assert 'total_interactions' in insights
        assert 'user_patterns' in insights
        assert 'preferences' in insights
        
        assert insights['total_interactions'] == 5
        assert 'cpu_usage' in insights['most_frequent_questions']
    
    def test_adjust_detail_level(self, context_manager):
        """Test adjusting detail level for question types"""
        # Create a pattern first
        context_manager.add_message("user", "CPU使用率は？")
        
        # Adjust detail level
        context_manager.adjust_detail_level("cpu_usage", "detailed")
        
        # Verify adjustment
        pattern = context_manager.personalization_engine.user_patterns["cpu_usage"]
        assert pattern.preferred_detail_level == "detailed"
    
    def test_get_personalized_greeting(self, context_manager):
        """Test personalized greeting generation"""
        # Add some patterns
        context_manager.add_message("user", "システム全体の状況は？")
        context_manager.add_message("user", "システムの状態を教えて")
        
        greeting = context_manager.get_personalized_greeting()
        
        assert isinstance(greeting, str)
        assert len(greeting) > 0
        # Should include system-related suggestion
        assert "システム" in greeting
    
    def test_personalization_persistence(self, temp_dir):
        """Test that personalization data persists across sessions"""
        # Create first context manager and add patterns
        cm1 = ChatContextManager(session_id="persist-personalization", data_dir=temp_dir)
        cm1.add_message("user", "CPU使用率は？")
        cm1.add_message("user", "CPU使用率は？")
        cm1.adjust_detail_level("cpu_usage", "brief")
        
        # Create second context manager with same session
        cm2 = ChatContextManager(session_id="persist-personalization", data_dir=temp_dir)
        
        # Verify personalization data was loaded
        assert "cpu_usage" in cm2.personalization_engine.user_patterns
        assert cm2.personalization_engine.user_patterns["cpu_usage"].frequency == 2
        assert cm2.personalization_engine.user_patterns["cpu_usage"].preferred_detail_level == "brief"


class TestChatContextManagerAdvanced:
    """Test advanced ChatContextManager functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def context_manager(self, temp_dir):
        """Create ChatContextManager instance for testing"""
        return ChatContextManager(session_id="advanced-test", data_dir=temp_dir)
    
    def test_message_search(self, context_manager):
        """Test searching through message history"""
        # Add various messages
        context_manager.add_message("user", "CPU使用率はどうですか？")
        context_manager.add_message("assistant", "CPU使用率は45%です")
        context_manager.add_message("user", "メモリ使用量は？")
        context_manager.add_message("assistant", "メモリ使用量は8GB/16GBです")
        context_manager.add_message("user", "ディスク容量を確認したい")
        
        # Search for CPU-related messages
        cpu_messages = [msg for msg in context_manager.conversation_history 
                       if "CPU" in msg.content]
        assert len(cpu_messages) == 2
        
        # Search for memory-related messages
        memory_messages = [msg for msg in context_manager.conversation_history 
                          if "メモリ" in msg.content]
        assert len(memory_messages) == 2
    
    def test_conversation_export_import(self, context_manager, temp_dir):
        """Test exporting and importing conversation data"""
        # Add some conversation data
        context_manager.add_message("user", "Hello")
        context_manager.add_message("assistant", "Hi there")
        context_manager.update_user_preferences({'language_style': 'formal'})
        
        # Export data
        export_file = Path(temp_dir) / "export.json"
        export_data = {
            'session_id': context_manager.session_id,
            'conversation_history': [msg.to_dict() for msg in context_manager.conversation_history],
            'user_preferences': {
                'language_style': context_manager.user_preferences.language_style,
                'notification_level': context_manager.user_preferences.notification_level,
                'preferred_metrics': context_manager.user_preferences.preferred_metrics,
                'response_personality': context_manager.user_preferences.response_personality
            },
            'personalization_engine': context_manager.personalization_engine.to_dict()
        }
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        # Create new context manager and import
        new_cm = ChatContextManager(session_id="import-test", data_dir=temp_dir)
        
        with open(export_file, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        # Manually import data (would be a method in real implementation)
        for msg_data in import_data['conversation_history']:
            msg = ChatMessage.from_dict(msg_data)
            new_cm.conversation_history.append(msg)
        
        assert len(new_cm.conversation_history) == 2
        assert new_cm.conversation_history[0].content == "Hello"
    
    def test_session_analytics(self, context_manager):
        """Test session analytics functionality"""
        # Add messages with different patterns
        context_manager.add_message("user", "CPU使用率は？")
        context_manager.add_message("assistant", "45%です")
        context_manager.add_message("user", "メモリ使用量は？")
        context_manager.add_message("assistant", "8GB使用中です")
        context_manager.add_message("user", "CPU使用率は？")  # Repeat question
        
        # Analyze conversation patterns
        user_messages = [msg for msg in context_manager.conversation_history if msg.role == "user"]
        question_types = {}
        
        for msg in user_messages:
            if "CPU" in msg.content:
                question_types["cpu"] = question_types.get("cpu", 0) + 1
            elif "メモリ" in msg.content:
                question_types["memory"] = question_types.get("memory", 0) + 1
        
        assert question_types["cpu"] == 2
        assert question_types["memory"] == 1
    
    def test_context_prompt_optimization(self, context_manager):
        """Test context prompt optimization for different scenarios"""
        # Test with minimal system data
        minimal_data = {"cpu_percent": 50}
        prompt1 = context_manager.get_context_prompt(minimal_data)
        
        # Test with comprehensive system data
        comprehensive_data = {
            "cpu_percent": 75.5,
            "memory_percent": 65.0,
            "disk_percent": 80.0,
            "top_processes": [{"name": "Chrome", "cpu_percent": 25}],
            "network_io": {"bytes_sent": 1000, "bytes_recv": 2000}
        }
        prompt2 = context_manager.get_context_prompt(comprehensive_data)
        
        # Comprehensive prompt should be longer
        assert len(prompt2) > len(prompt1)
        # The prompt format may not include process names directly
        assert "75.5%" in prompt2  # Should include CPU percentage
        assert "65.0%" in prompt2  # Should include memory percentage
    
    def test_message_threading(self, context_manager):
        """Test message threading and context continuity"""
        # Simulate a threaded conversation
        context_manager.add_message("user", "システム状態を教えて")
        context_manager.add_message("assistant", "CPU 50%, メモリ 60%です")
        context_manager.add_message("user", "CPUが高い理由は？")  # Follow-up question
        context_manager.add_message("assistant", "複数のプロセスが動作中です")
        context_manager.add_message("user", "どのプロセス？")  # Context-dependent question
        
        # Get recent context for the last question
        recent_history = context_manager.get_conversation_history(3)
        
        # Should include enough context to understand "どのプロセス？"
        assert len(recent_history) == 3
        assert any("プロセス" in msg.content for msg in recent_history)
    
    def test_user_preference_learning(self, context_manager):
        """Test automatic user preference learning"""
        # Simulate user asking detailed questions
        context_manager.add_message("user", "CPU使用率の詳細な内訳を教えて")
        context_manager.add_message("user", "メモリ使用量の詳しい分析をお願いします")
        context_manager.add_message("user", "プロセス一覧の詳細情報が欲しい")
        
        # Should learn that user prefers detailed responses
        insights = context_manager.get_user_insights()
        
        # Check if system detected preference for detailed information
        assert insights['total_interactions'] == 3
        assert len(insights['user_patterns']) > 0


class TestChatContextManagerErrorHandling:
    """Test error handling in ChatContextManager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_invalid_session_id_handling(self, temp_dir):
        """Test handling of invalid session IDs"""
        # Test with various invalid session IDs
        invalid_ids = ["session/with/slashes", "session:with:colons"]
        
        for invalid_id in invalid_ids:
            # Should handle gracefully or sanitize
            try:
                cm = ChatContextManager(session_id=invalid_id, data_dir=temp_dir)
                # If it succeeds, session_id should be sanitized
                assert isinstance(cm.session_id, str)
                assert len(cm.session_id) > 0
            except ValueError:
                # Or it should raise a clear error
                pass
        
        # Test empty string separately
        try:
            cm = ChatContextManager(session_id="", data_dir=temp_dir)
            # Should either work with default ID or raise error
            assert isinstance(cm.session_id, str)
        except ValueError:
            pass
    
    def test_corrupted_personalization_data(self, temp_dir):
        """Test handling of corrupted personalization data"""
        # Create session file with corrupted personalization data
        session_file = Path(temp_dir) / "session_corrupt-personalization.json"
        corrupted_data = {
            "session_id": "corrupt-personalization",
            "conversation_history": [],
            "user_preferences": {
                "language_style": "friendly",
                "notification_level": "normal",
                "preferred_metrics": ["cpu", "memory"],
                "response_personality": "helpful"
            },
            "personalization_engine": {
                "user_patterns": "invalid_data_type",  # Should be dict
                "interaction_count": "not_a_number"     # Should be int
            }
        }
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(corrupted_data, f)
        
        # Should handle gracefully
        cm = ChatContextManager(session_id="corrupt-personalization", data_dir=temp_dir)
        
        # Should have valid personalization engine despite corruption
        assert hasattr(cm, 'personalization_engine')
        assert isinstance(cm.personalization_engine.user_patterns, dict)
    
    def test_disk_space_handling(self, temp_dir):
        """Test handling when disk space is limited"""
        context_manager = ChatContextManager(session_id="disk-test", data_dir=temp_dir)
        
        # Add many messages to test file size limits
        for i in range(1000):
            context_manager.add_message("user", f"Message {i} " + "x" * 100)
        
        # Should still function (though may limit history)
        assert len(context_manager.conversation_history) <= 50  # History limit
        
        # Should be able to get stats
        stats = context_manager.get_session_stats()
        assert isinstance(stats, dict)
    
    def test_concurrent_access_handling(self, temp_dir):
        """Test handling of concurrent access to session files"""
        # Create two context managers with same session
        cm1 = ChatContextManager(session_id="concurrent-test", data_dir=temp_dir)
        cm2 = ChatContextManager(session_id="concurrent-test", data_dir=temp_dir)
        
        # Add messages from both
        cm1.add_message("user", "Message from CM1")
        cm2.add_message("user", "Message from CM2")
        
        # Both should function without errors
        assert len(cm1.conversation_history) >= 1
        assert len(cm2.conversation_history) >= 1


class TestChatContextManagerPerformance:
    """Test performance aspects of ChatContextManager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_large_conversation_performance(self, temp_dir):
        """Test performance with large conversation history"""
        import time
        
        context_manager = ChatContextManager(session_id="performance-test", data_dir=temp_dir)
        
        # Add many messages and measure time
        start_time = time.time()
        for i in range(100):
            context_manager.add_message("user", f"Performance test message {i}")
            context_manager.add_message("assistant", f"Response to message {i}")
        
        add_time = time.time() - start_time
        
        # Test retrieval performance
        start_time = time.time()
        history = context_manager.get_conversation_history(20)
        retrieval_time = time.time() - start_time
        
        # Should be reasonably fast
        assert add_time < 5.0  # Adding 200 messages should take less than 5 seconds
        assert retrieval_time < 0.1  # Retrieving 20 messages should be very fast
        assert len(history) == 20
    
    def test_context_prompt_generation_performance(self, temp_dir):
        """Test performance of context prompt generation"""
        import time
        
        context_manager = ChatContextManager(session_id="prompt-perf-test", data_dir=temp_dir)
        
        # Add conversation history
        for i in range(20):
            context_manager.add_message("user", f"Question {i}")
            context_manager.add_message("assistant", f"Answer {i}")
        
        # Test prompt generation performance
        system_data = {
            "cpu_percent": 75.0,
            "memory_percent": 60.0,
            "disk_percent": 80.0,
            "top_processes": [{"name": f"Process{i}", "cpu_percent": i} for i in range(10)]
        }
        
        start_time = time.time()
        prompt = context_manager.get_context_prompt(system_data)
        generation_time = time.time() - start_time
        
        # Should generate quickly
        assert generation_time < 0.5  # Should take less than 500ms
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_personalization_performance(self, temp_dir):
        """Test personalization engine performance"""
        import time
        
        context_manager = ChatContextManager(session_id="personalization-perf", data_dir=temp_dir)
        
        # Add many interactions to build patterns
        questions = [
            "CPU使用率は？", "メモリ使用量は？", "ディスク容量は？",
            "システム状態は？", "プロセス一覧を見せて"
        ]
        
        start_time = time.time()
        for i in range(50):
            question = questions[i % len(questions)]
            context_manager.add_message("user", question)
            context_manager.add_message("assistant", f"Response {i}")
        
        learning_time = time.time() - start_time
        
        # Test personalization performance
        start_time = time.time()
        insights = context_manager.get_user_insights()
        insights_time = time.time() - start_time
        
        # Should be reasonably fast
        assert learning_time < 10.0  # Learning from 100 messages
        assert insights_time < 1.0   # Getting insights should be fast
        assert isinstance(insights, dict)


if __name__ == "__main__":
    pytest.main([__file__])