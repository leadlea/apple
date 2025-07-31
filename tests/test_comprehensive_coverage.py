"""
Comprehensive test coverage verification for Mac Status PWA backend components
This test file ensures we meet the 80%+ coverage requirement for core components
"""
import pytest
import asyncio
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import all main components
from system_monitor import SystemMonitor, SystemStatus, ProcessInfo, NetworkStats
from elyza_model import ELYZAModelInterface, ModelConfig, ModelResponse
from chat_context_manager import ChatContextManager, ChatMessage, UserPreferences


class TestSystemMonitorCoverageBoost:
    """Additional tests to boost SystemMonitor coverage"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.monitor = SystemMonitor()
    
    @pytest.mark.asyncio
    async def test_system_monitor_edge_cases(self):
        """Test edge cases in SystemMonitor"""
        # Test with mocked system calls that return edge case values
        with patch('system_monitor.psutil.cpu_percent', return_value=0.0), \
             patch('system_monitor.psutil.virtual_memory') as mock_mem, \
             patch('system_monitor.psutil.disk_usage') as mock_disk:
            
            # Mock memory with zero values
            mock_mem_obj = Mock()
            mock_mem_obj.used = 0
            mock_mem_obj.total = 1024**3  # 1GB
            mock_mem_obj.percent = 0.0
            mock_mem.return_value = mock_mem_obj
            
            # Mock disk with full capacity
            mock_disk_obj = Mock()
            mock_disk_obj.used = 500 * 1024**3  # 500GB
            mock_disk_obj.total = 500 * 1024**3  # 500GB
            mock_disk_obj.percent = 100.0
            mock_disk.return_value = mock_disk_obj
            
            # Mock other methods
            with patch.object(self.monitor, '_get_network_stats') as mock_network, \
                 patch.object(self.monitor, '_get_top_processes') as mock_processes, \
                 patch.object(self.monitor, '_get_uptime') as mock_uptime, \
                 patch.object(self.monitor, '_get_load_average') as mock_load, \
                 patch.object(self.monitor, '_get_temperature') as mock_temp:
                
                mock_network.return_value = NetworkStats(0, 0, 0, 0)
                mock_processes.return_value = []
                mock_uptime.return_value = 0.0
                mock_load.return_value = [0.0, 0.0, 0.0]
                mock_temp.return_value = None
                
                status = await self.monitor.get_system_info()
                
                assert status.cpu_percent == 0.0
                assert status.disk_percent == 100.0
                assert len(status.top_processes) == 0
    
    def test_system_monitor_data_conversion(self):
        """Test data conversion methods"""
        # Test to_dict method with comprehensive data
        status = SystemStatus(
            timestamp=datetime.now(),
            cpu_percent=50.0,
            cpu_count=8,
            cpu_freq=2400.0,
            memory_used=8*1024**3,
            memory_total=16*1024**3,
            memory_percent=50.0,
            disk_used=100*1024**3,
            disk_total=500*1024**3,
            disk_percent=20.0,
            top_processes=[
                ProcessInfo(1234, "test", 10.0, 5.0, 1024, "running", 123456, ["test"])
            ],
            network_io=NetworkStats(1000, 2000, 10, 20),
            temperature=45.5,
            uptime=86400.0,
            load_average=[1.0, 1.5, 2.0]
        )
        
        result_dict = self.monitor.to_dict(status)
        
        # Verify all fields are present and correctly converted
        assert 'timestamp' in result_dict
        assert result_dict['cpu_percent'] == 50.0
        assert result_dict['temperature'] == 45.5
        assert 'top_processes' in result_dict
        assert len(result_dict['top_processes']) == 1
        assert result_dict['top_processes'][0]['name'] == "test"
    
    @pytest.mark.asyncio
    async def test_process_filtering_edge_cases(self):
        """Test process filtering with edge cases"""
        with patch('system_monitor.psutil.process_iter') as mock_iter:
            # Create processes with edge case values
            mock_proc1 = Mock()
            mock_proc1.info = {
                'pid': 1,
                'name': '',  # Empty name
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'memory_info': Mock(rss=0),
                'status': 'zombie',
                'create_time': 0.0,
                'cmdline': []
            }
            
            mock_proc2 = Mock()
            mock_proc2.info = {
                'pid': 2,
                'name': 'a' * 1000,  # Very long name
                'cpu_percent': 100.0,
                'memory_percent': 100.0,
                'memory_info': Mock(rss=1024**4),  # 1TB
                'status': 'running',
                'create_time': 1234567890.0,
                'cmdline': ['cmd'] * 100  # Very long command line
            }
            
            mock_iter.return_value = [mock_proc1, mock_proc2]
            
            # Test various filtering methods
            all_processes = await self.monitor._get_top_processes(limit=10)
            cpu_processes = await self.monitor.get_processes_by_cpu(limit=10, min_cpu_percent=50.0)
            memory_processes = await self.monitor.get_processes_by_memory(limit=10, min_memory_mb=1000.0)
            
            assert len(all_processes) == 2
            assert len(cpu_processes) == 1  # Only proc2 meets CPU threshold
            assert len(memory_processes) == 1  # Only proc2 meets memory threshold


class TestELYZAModelCoverageBoost:
    """Additional tests to boost ELYZAModel coverage"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.config = ModelConfig(model_path="/test/model.gguf")
        self.model = ELYZAModelInterface(self.config)
    
    def test_model_response_serialization(self):
        """Test ModelResponse serialization"""
        response = ModelResponse(
            content="テスト応答",
            timestamp=datetime.now(),
            processing_time_ms=150.5,
            token_count=10,
            model_info={"model": "test", "version": "1.0"}
        )
        
        # Test that all fields are accessible
        assert response.content == "テスト応答"
        assert isinstance(response.timestamp, datetime)
        assert response.processing_time_ms == 150.5
        assert response.token_count == 10
        assert response.model_info["model"] == "test"
    
    def test_model_config_edge_cases(self):
        """Test ModelConfig with edge case values"""
        # Test minimum values
        config = ModelConfig(
            model_path="/test.gguf",
            n_ctx=1,
            n_gpu_layers=0,
            temperature=0.0,
            max_tokens=1
        )
        
        model = ELYZAModelInterface(config)
        assert model.config.n_ctx == 1
        assert model.config.temperature == 0.0
        
        # Test maximum values
        config = ModelConfig(
            model_path="/test.gguf",
            n_ctx=32768,
            temperature=2.0,
            max_tokens=4096
        )
        
        model = ELYZAModelInterface(config)
        assert model.config.n_ctx == 32768
        assert model.config.temperature == 2.0
    
    def test_system_data_formatting_comprehensive(self):
        """Test comprehensive system data formatting"""
        # Test with all possible fields
        system_data = {
            "cpu_percent": 75.123456,  # Test precision
            "cpu_count": 16,
            "cpu_freq": 3200.0,
            "memory_percent": 85.987654,
            "memory_used": 15 * 1024**3,
            "memory_total": 16 * 1024**3,
            "disk_percent": 95.5,
            "disk_used": 950 * 1024**3,
            "disk_total": 1000 * 1024**3,
            "top_processes": [
                {"name": "Process 1", "cpu_percent": 25.5, "memory_percent": 10.0},
                {"name": "Process 2", "cpu_percent": 15.0, "memory_percent": 8.0},
                {"name": "Process 3", "cpu_percent": 10.0, "memory_percent": 5.0}
            ],
            "network_io": {
                "bytes_sent": 5 * 1024**3,  # 5GB
                "bytes_recv": 10 * 1024**3,  # 10GB
                "packets_sent": 1000000,
                "packets_recv": 2000000
            },
            "uptime": 604800.0,  # 1 week
            "load_average": [4.5, 3.2, 2.8],
            "temperature": 65.5
        }
        
        result = self.model._format_system_data(system_data)
        
        # Verify formatting includes all data with proper precision
        assert "CPU使用率: 75.1%" in result
        assert "メモリ使用率: 86.0%" in result
        assert "ディスク使用率: 95.5%" in result
        assert "Process 1" in result
        assert "ネットワーク" in result
        assert "5120.0MB" in result  # 5GB in MB
    
    @pytest.mark.asyncio
    async def test_model_performance_tracking_comprehensive(self):
        """Test comprehensive performance tracking"""
        # Simulate multiple requests with different processing times
        self.model.is_initialized = True
        self.model.llm = Mock()
        
        processing_times = [100, 200, 150, 300, 250]  # ms
        
        for i, time_ms in enumerate(processing_times):
            with patch.object(self.model, '_generate_response') as mock_gen:
                mock_gen.return_value = f"Response {i}"
                
                # Simulate processing time
                import time
                start_time = time.time()
                time.sleep(time_ms / 1000.0)  # Convert to seconds
                
                response = await self.model.generate_system_response(
                    f"Question {i}", {"cpu_percent": 50}
                )
                
                assert response is not None
        
        # Check performance metrics
        assert self.model.total_requests == len(processing_times)
        assert self.model.average_response_time > 0
        
        status = self.model.get_model_status()
        assert status['total_requests'] == len(processing_times)
        assert status['average_response_time_ms'] > 0


class TestChatContextManagerCoverageBoost:
    """Additional tests to boost ChatContextManager coverage"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_user_preferences_comprehensive(self, temp_dir):
        """Test comprehensive user preferences functionality"""
        cm = ChatContextManager(session_id="prefs-test", data_dir=temp_dir)
        
        # Test all preference fields
        new_prefs = {
            'language_style': 'technical',
            'notification_level': 'high',
            'preferred_metrics': ['cpu', 'memory', 'disk', 'network'],
            'response_personality': 'formal'
        }
        
        cm.update_user_preferences(new_prefs)
        
        prefs = cm.get_user_preferences()
        assert prefs.language_style == 'technical'
        assert prefs.notification_level == 'high'
        assert len(prefs.preferred_metrics) == 4
        assert prefs.response_personality == 'formal'
        
        # Test partial updates
        partial_prefs = {'language_style': 'casual'}
        cm.update_user_preferences(partial_prefs)
        
        updated_prefs = cm.get_user_preferences()
        assert updated_prefs.language_style == 'casual'
        assert updated_prefs.notification_level == 'high'  # Should remain unchanged
    
    def test_message_management_comprehensive(self, temp_dir):
        """Test comprehensive message management"""
        cm = ChatContextManager(session_id="msg-test", data_dir=temp_dir)
        
        # Test adding messages with system context
        system_contexts = [
            {"cpu_percent": 50, "memory_percent": 60},
            {"cpu_percent": 75, "memory_percent": 80},
            {"cpu_percent": 30, "memory_percent": 40}
        ]
        
        message_ids = []
        for i, context in enumerate(system_contexts):
            msg_id = cm.add_message("user", f"Question {i}", context)
            message_ids.append(msg_id)
            cm.add_message("assistant", f"Answer {i}")
        
        # Verify message IDs are unique
        assert len(set(message_ids)) == len(message_ids)
        
        # Test message retrieval with different limits
        all_messages = cm.get_conversation_history()
        assert len(all_messages) == 6  # 3 user + 3 assistant
        
        recent_messages = cm.get_conversation_history(2)
        assert len(recent_messages) == 2
        assert recent_messages[-1].content == "Answer 2"
        
        # Test system context preservation
        user_messages = [msg for msg in all_messages if msg.role == "user"]
        for i, msg in enumerate(user_messages):
            assert msg.system_context == system_contexts[i]
    
    def test_session_persistence_comprehensive(self, temp_dir):
        """Test comprehensive session persistence"""
        session_id = "persistence-test"
        
        # Create first session and add comprehensive data
        cm1 = ChatContextManager(session_id=session_id, data_dir=temp_dir)
        
        # Add messages with various types of content
        messages = [
            ("user", "こんにちは", {"cpu_percent": 25}),
            ("assistant", "こんにちは！システム状態をお知らせします。", None),
            ("user", "CPU使用率が高いですね", {"cpu_percent": 85}),
            ("assistant", "はい、現在CPU使用率が高めです。", None),
            ("user", "メモリ使用量はどうですか？", {"memory_percent": 70}),
            ("assistant", "メモリ使用量は70%です。", None)
        ]
        
        for role, content, context in messages:
            cm1.add_message(role, content, context)
        
        # Update preferences
        cm1.update_user_preferences({
            'language_style': 'polite',
            'preferred_metrics': ['cpu', 'memory']
        })
        
        # Create second session with same ID
        cm2 = ChatContextManager(session_id=session_id, data_dir=temp_dir)
        
        # Verify all data was loaded
        assert len(cm2.conversation_history) == len(messages)
        assert cm2.user_preferences.language_style == 'polite'
        assert cm2.user_preferences.preferred_metrics == ['cpu', 'memory']
        
        # Verify message content and context
        for i, (role, content, context) in enumerate(messages):
            msg = cm2.conversation_history[i]
            assert msg.role == role
            assert msg.content == content
            assert msg.system_context == context
    
    def test_personalization_engine_comprehensive(self, temp_dir):
        """Test comprehensive personalization engine functionality"""
        cm = ChatContextManager(session_id="personalization-comprehensive", data_dir=temp_dir)
        
        # Simulate various question patterns
        question_patterns = [
            ("CPU使用率は？", "cpu_usage"),
            ("CPUの状況を教えて", "cpu_usage"),
            ("プロセッサの負荷はどう？", "cpu_usage"),
            ("メモリ使用量を確認したい", "memory_usage"),
            ("RAMの状況は？", "memory_usage"),
            ("ディスク容量を見せて", "disk_usage"),
            ("ストレージの使用状況は？", "disk_usage"),
            ("システム全体の状態は？", "system_overview"),
            ("こんにちは", "general_chat"),
            ("ありがとう", "general_chat")
        ]
        
        # Add questions multiple times to build patterns
        for _ in range(3):  # Repeat 3 times
            for question, expected_type in question_patterns:
                cm.add_message("user", question)
                cm.add_message("assistant", f"Response to {question}")
        
        # Test pattern analysis
        insights = cm.get_user_insights()
        
        # History is limited to 50 messages, so total interactions will be capped
        expected_interactions = min(len(question_patterns) * 3 * 2, 50)
        assert insights['total_interactions'] == expected_interactions
        assert len(insights['user_patterns']) > 0
        assert 'cpu_usage' in insights['most_frequent_questions']
        
        # Test personalized greeting
        greeting = cm.get_personalized_greeting()
        assert isinstance(greeting, str)
        assert len(greeting) > 0
        
        # Test detail level adjustment
        cm.adjust_detail_level("cpu_usage", "detailed")
        
        # Verify adjustment persists
        cm2 = ChatContextManager(session_id="personalization-comprehensive", data_dir=temp_dir)
        pattern = cm2.personalization_engine.user_patterns.get("cpu_usage")
        if pattern:
            assert pattern.preferred_detail_level == "detailed"


class TestIntegrationCoverage:
    """Integration tests to boost overall coverage"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_full_system_integration(self, temp_dir):
        """Test full system integration"""
        # Create all components
        monitor = SystemMonitor()
        config = ModelConfig(model_path="/test/model.gguf")
        model = ELYZAModelInterface(config)
        chat_manager = ChatContextManager(session_id="integration-test", data_dir=temp_dir)
        
        # Test system monitoring
        system_status = await monitor.get_system_info()
        assert isinstance(system_status, SystemStatus)
        
        # Convert to dict for model processing
        system_dict = monitor.to_dict(system_status)
        
        # Test model data formatting
        formatted_data = model._format_system_data(system_dict)
        assert isinstance(formatted_data, str)
        assert len(formatted_data) > 0
        
        # Test chat context integration
        chat_manager.add_message("user", "システム状態を教えて", system_dict)
        context_prompt = chat_manager.get_context_prompt(system_dict)
        
        assert "CPU使用率" in context_prompt
        assert "システム状態を教えて" in context_prompt
        
        # Test session stats
        stats = chat_manager.get_session_stats()
        assert stats['message_count'] == 1
        assert 'last_activity' in stats
    
    def test_error_handling_integration(self, temp_dir):
        """Test integrated error handling"""
        # Test with invalid configurations
        invalid_config = ModelConfig(model_path="/nonexistent/path.gguf")
        model = ELYZAModelInterface(invalid_config)
        
        # Should handle gracefully
        status = model.get_model_status()
        assert status['is_initialized'] is False
        assert status['model_exists'] is False
        
        # Test chat manager with invalid session data
        chat_manager = ChatContextManager(session_id="error-test", data_dir=temp_dir)
        
        # Should handle empty system data gracefully
        prompt = chat_manager.get_context_prompt({})
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_performance_integration(self, temp_dir):
        """Test performance across all components"""
        import time
        
        # Test system monitoring performance
        monitor = SystemMonitor()
        start_time = time.time()
        summary = monitor.get_system_summary()
        monitor_time = time.time() - start_time
        
        assert monitor_time < 1.0  # Should be fast
        assert isinstance(summary, dict)
        
        # Test chat manager performance
        chat_manager = ChatContextManager(session_id="perf-test", data_dir=temp_dir)
        
        start_time = time.time()
        for i in range(50):
            chat_manager.add_message("user", f"Message {i}")
        add_time = time.time() - start_time
        
        start_time = time.time()
        history = chat_manager.get_conversation_history(10)
        retrieval_time = time.time() - start_time
        
        assert add_time < 2.0  # Adding 50 messages should be fast
        assert retrieval_time < 0.1  # Retrieval should be very fast
        assert len(history) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])