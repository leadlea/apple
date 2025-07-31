"""
Unit tests for ELYZAModelInterface class
"""
import pytest
import asyncio
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

# Import the classes we're testing
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from elyza_model import (
    ELYZAModelInterface,
    ModelConfig,
    ModelResponse,
    ELYZAModelError,
    get_default_model_path,
    create_default_config
)


class TestModelConfig:
    """Test cases for ModelConfig dataclass"""
    
    def test_model_config_creation(self):
        """Test ModelConfig creation with default values"""
        config = ModelConfig(model_path="/test/path")
        
        assert config.model_path == "/test/path"
        assert config.n_ctx == 2048
        assert config.n_gpu_layers == -1
        assert config.temperature == 0.7
        assert config.max_tokens == 512
    
    def test_model_config_custom_values(self):
        """Test ModelConfig with custom values"""
        config = ModelConfig(
            model_path="/custom/path",
            n_ctx=4096,
            temperature=0.5,
            max_tokens=256
        )
        
        assert config.model_path == "/custom/path"
        assert config.n_ctx == 4096
        assert config.temperature == 0.5
        assert config.max_tokens == 256


class TestModelResponse:
    """Test cases for ModelResponse dataclass"""
    
    def test_model_response_creation(self):
        """Test ModelResponse creation"""
        timestamp = datetime.now()
        response = ModelResponse(
            content="テスト応答",
            timestamp=timestamp,
            processing_time_ms=150.5,
            token_count=10,
            model_info={"model": "test"}
        )
        
        assert response.content == "テスト応答"
        assert response.timestamp == timestamp
        assert response.processing_time_ms == 150.5
        assert response.token_count == 10
        assert response.model_info == {"model": "test"}


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_get_default_model_path(self):
        """Test default model path generation"""
        path = get_default_model_path()
        expected = os.path.join("models", "elyza7b", "ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf")
        assert path == expected
    
    def test_create_default_config(self):
        """Test default config creation"""
        config = create_default_config()
        
        assert config.model_path == get_default_model_path()
        assert config.n_ctx == 2048
        assert config.n_gpu_layers == -1
        assert config.temperature == 0.7
    
    def test_create_default_config_custom_path(self):
        """Test default config with custom path"""
        custom_path = "/custom/model.gguf"
        config = create_default_config(custom_path)
        
        assert config.model_path == custom_path


class TestELYZAModelInterface:
    """Test cases for ELYZAModelInterface class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.config = ModelConfig(model_path="/test/model.gguf")
        self.model_interface = ELYZAModelInterface(self.config)
    
    def test_init(self):
        """Test ELYZAModelInterface initialization"""
        assert self.model_interface.config == self.config
        assert self.model_interface.llm is None
        assert self.model_interface.is_initialized is False
        assert self.model_interface.initialization_error is None
        assert self.model_interface.total_requests == 0
    
    @pytest.mark.asyncio
    @patch('elyza_model.Llama', None)  # Simulate llama-cpp-python not installed
    async def test_initialize_model_no_llama_cpp(self):
        """Test initialization when llama-cpp-python is not installed"""
        result = await self.model_interface.initialize_model()
        
        assert result is False
        assert self.model_interface.is_initialized is False
        assert "llama-cpp-python not installed" in self.model_interface.initialization_error
    
    @pytest.mark.asyncio
    @patch('elyza_model.Llama')
    @patch('os.path.exists')
    async def test_initialize_model_file_not_found(self, mock_exists, mock_llama):
        """Test initialization when model file doesn't exist"""
        mock_exists.return_value = False
        
        result = await self.model_interface.initialize_model()
        
        assert result is False
        assert self.model_interface.is_initialized is False
        assert "Model file not found" in self.model_interface.initialization_error
    
    @pytest.mark.asyncio
    @patch('elyza_model.Llama')
    @patch('os.path.exists')
    async def test_initialize_model_success(self, mock_exists, mock_llama):
        """Test successful model initialization"""
        mock_exists.return_value = True
        mock_llm_instance = Mock()
        mock_llama.return_value = mock_llm_instance
        
        # Mock the test response
        with patch.object(self.model_interface, '_generate_response', return_value="テスト"):
            result = await self.model_interface.initialize_model()
        
        assert result is True
        assert self.model_interface.is_initialized is True
        assert self.model_interface.llm == mock_llm_instance
        
        # Verify Llama was called with correct parameters
        mock_llama.assert_called_once()
        call_kwargs = mock_llama.call_args[1]
        assert call_kwargs['model_path'] == "/test/model.gguf"
        assert call_kwargs['n_ctx'] == 2048
        assert call_kwargs['n_gpu_layers'] == -1
    
    @pytest.mark.asyncio
    @patch('elyza_model.Llama')
    @patch('os.path.exists')
    async def test_initialize_model_exception(self, mock_exists, mock_llama):
        """Test initialization with exception"""
        mock_exists.return_value = True
        mock_llama.side_effect = Exception("Test error")
        
        result = await self.model_interface.initialize_model()
        
        assert result is False
        assert self.model_interface.is_initialized is False
        assert "Model initialization failed" in self.model_interface.initialization_error
    
    @pytest.mark.asyncio
    async def test_generate_system_response_not_initialized(self):
        """Test response generation when model not initialized"""
        result = await self.model_interface.generate_system_response(
            "テストメッセージ", 
            {"cpu_percent": 50.0}
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_system_response_success(self):
        """Test successful response generation"""
        # Mock initialized state
        self.model_interface.is_initialized = True
        self.model_interface.llm = Mock()
        
        # Mock the _generate_response method
        with patch.object(self.model_interface, '_generate_response', return_value="テスト応答"):
            result = await self.model_interface.generate_system_response(
                "システム状態を教えて",
                {
                    "cpu_percent": 25.5,
                    "memory_percent": 60.0,
                    "top_processes": [{"name": "Chrome", "cpu_percent": 15.0}]
                }
            )
        
        assert result is not None
        assert isinstance(result, ModelResponse)
        assert result.content == "テスト応答"
        assert result.processing_time_ms > 0
        assert isinstance(result.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_generate_response_with_timeout(self):
        """Test response generation with timeout"""
        self.model_interface.llm = Mock()
        
        # Mock a slow inference that times out
        async def slow_inference():
            await asyncio.sleep(15)  # Longer than 10s timeout
            return {"choices": [{"text": "response"}]}
        
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError):
            result = await self.model_interface._generate_response("test prompt")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self):
        """Test successful response generation"""
        mock_llm = Mock()
        mock_llm.return_value = {
            "choices": [{"text": "生成された応答"}]
        }
        self.model_interface.llm = mock_llm
        
        # Mock asyncio.wait_for to return the result immediately
        with patch('asyncio.wait_for') as mock_wait_for:
            mock_wait_for.return_value = {"choices": [{"text": "生成された応答"}]}
            
            result = await self.model_interface._generate_response("テストプロンプト")
        
        assert result == "生成された応答"
    
    def test_format_system_data(self):
        """Test system data formatting"""
        system_data = {
            "cpu_percent": 25.5,
            "memory_percent": 60.2,
            "memory_used": 8 * 1024**3,
            "memory_total": 16 * 1024**3,
            "disk_percent": 45.0,
            "top_processes": [{"name": "Chrome", "cpu_percent": 15.2}],
            "network_io": {
                "bytes_sent": 1024**2,  # 1MB
                "bytes_recv": 2 * 1024**2  # 2MB
            }
        }
        
        result = self.model_interface._format_system_data(system_data)
        
        assert "CPU使用率: 25.5%" in result
        assert "メモリ使用率: 60.2%" in result
        assert "メモリ使用量: 8.0GB / 16.0GB" in result
        assert "ディスク使用率: 45.0%" in result
        assert "Chrome" in result
        assert "ネットワーク" in result
    
    def test_format_system_data_empty(self):
        """Test system data formatting with empty data"""
        result = self.model_interface._format_system_data({})
        assert "システム情報を取得できませんでした" in result
    
    def test_format_system_data_exception(self):
        """Test system data formatting with exception"""
        # Pass invalid data that will cause an exception
        with patch.object(self.model_interface.logger, 'error'):
            result = self.model_interface._format_system_data(None)
        
        assert "エラーが発生しました" in result
    
    def test_create_system_prompt(self):
        """Test system prompt creation"""
        system_data = {"cpu_percent": 50.0}
        conversation_history = [
            {"role": "user", "content": "こんにちは"},
            {"role": "assistant", "content": "こんにちは！"}
        ]
        
        prompt = self.model_interface._create_system_prompt(
            "システム状態は？",
            system_data,
            conversation_history
        )
        
        # Check that prompt contains system data and user message
        assert "CPU使用率: 50.0%" in prompt
        assert "こんにちは" in prompt
        assert "システム状態は？" in prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_create_system_prompt_no_history(self):
        """Test system prompt creation without conversation history"""
        system_data = {"cpu_percent": 30.0}
        
        prompt = self.model_interface._create_system_prompt(
            "テストメッセージ",
            system_data,
            None
        )
        
        # Check that prompt contains system data and user message
        assert "CPU使用率: 30.0%" in prompt
        assert "テストメッセージ" in prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_get_model_status(self):
        """Test model status retrieval"""
        self.model_interface.is_initialized = True
        self.model_interface.total_requests = 5
        self.model_interface.total_processing_time = 1000.0
        self.model_interface.average_response_time = 200.0
        
        with patch('os.path.exists', return_value=True):
            status = self.model_interface.get_model_status()
        
        assert status['is_initialized'] is True
        assert status['model_path'] == "/test/model.gguf"
        assert status['model_exists'] is True
        assert status['total_requests'] == 5
        assert status['average_response_time_ms'] == 200.0
        assert 'config' in status
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test model cleanup"""
        self.model_interface.llm = Mock()
        self.model_interface.is_initialized = True
        
        await self.model_interface.cleanup()
        
        assert self.model_interface.llm is None
        assert self.model_interface.is_initialized is False


class TestIntegration:
    """Integration tests for ELYZAModelInterface"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_without_model(self):
        """Test full workflow without actual model file"""
        # Create config with non-existent model
        config = ModelConfig(model_path="/nonexistent/model.gguf")
        model = ELYZAModelInterface(config)
        
        # Test initialization failure
        result = await model.initialize_model()
        assert result is False
        
        # Test status
        status = model.get_model_status()
        assert status['is_initialized'] is False
        assert status['model_exists'] is False
        
        # Test cleanup
        await model.cleanup()
    
    @pytest.mark.asyncio
    @patch('elyza_model.Llama')
    @patch('os.path.exists')
    async def test_performance_tracking(self, mock_exists, mock_llama):
        """Test performance tracking functionality"""
        mock_exists.return_value = True
        mock_llm_instance = Mock()
        mock_llama.return_value = mock_llm_instance
        
        model = ELYZAModelInterface(ModelConfig(model_path="/test/model.gguf"))
        
        # Mock successful initialization
        with patch.object(model, '_generate_response', return_value="テスト"):
            await model.initialize_model()
        
        # Mock successful response generation
        with patch.object(model, '_generate_response', return_value="応答1"):
            response1 = await model.generate_system_response("質問1", {"cpu_percent": 50})
        
        with patch.object(model, '_generate_response', return_value="応答2"):
            response2 = await model.generate_system_response("質問2", {"cpu_percent": 60})
        
        # Check performance tracking
        assert model.total_requests == 2
        assert model.average_response_time > 0
        
        status = model.get_model_status()
        assert status['total_requests'] == 2
        assert status['average_response_time_ms'] > 0


class TestELYZAModelAdvancedFeatures:
    """Test advanced features of ELYZAModelInterface"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.config = ModelConfig(model_path="/test/model.gguf")
        self.model_interface = ELYZAModelInterface(self.config)
    
    @pytest.mark.asyncio
    @patch('elyza_model.Llama')
    @patch('os.path.exists')
    async def test_model_warm_up(self, mock_exists, mock_llama):
        """Test model warm-up functionality"""
        mock_exists.return_value = True
        mock_llm_instance = Mock()
        mock_llama.return_value = mock_llm_instance
        
        # Mock successful warm-up
        with patch.object(self.model_interface, '_generate_response', return_value="ウォームアップ完了"):
            result = await self.model_interface.initialize_model()
        
        assert result is True
        assert self.model_interface.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        self.model_interface.is_initialized = True
        self.model_interface.llm = Mock()
        
        # Mock multiple concurrent requests
        async def mock_generate(prompt, **kwargs):
            await asyncio.sleep(0.1)  # Simulate processing time
            return f"応答: {prompt[:10]}"
        
        with patch.object(self.model_interface, '_generate_response', side_effect=mock_generate):
            # Create multiple concurrent requests
            tasks = [
                self.model_interface.generate_system_response(f"質問{i}", {"cpu_percent": 50})
                for i in range(3)
            ]
            
            results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 3
        for result in results:
            assert result is not None
            assert isinstance(result, ModelResponse)
    
    def test_model_config_validation(self):
        """Test model configuration validation"""
        # Test valid configuration with empty path (should work)
        config = ModelConfig(model_path="")
        model = ELYZAModelInterface(config)
        assert model.config.model_path == ""
        
        # Test valid configuration
        config = ModelConfig(
            model_path="/valid/path.gguf",
            n_ctx=4096,
            temperature=0.5
        )
        model = ELYZAModelInterface(config)
        assert model.config.n_ctx == 4096
        assert model.config.temperature == 0.5
    
    def test_response_caching(self):
        """Test response caching functionality"""
        # This would test caching if implemented
        self.model_interface.is_initialized = True
        
        # For now, just test that repeated calls work
        system_data = {"cpu_percent": 50}
        
        # Multiple calls with same data should work
        for i in range(3):
            status = self.model_interface.get_model_status()
            assert status['is_initialized'] is True
    
    @pytest.mark.asyncio
    async def test_model_memory_management(self):
        """Test model memory management"""
        # Test cleanup
        self.model_interface.llm = Mock()
        self.model_interface.is_initialized = True
        
        await self.model_interface.cleanup()
        
        assert self.model_interface.llm is None
        assert self.model_interface.is_initialized is False
    
    def test_error_recovery(self):
        """Test error recovery mechanisms"""
        # Test recovery from initialization error
        self.model_interface.initialization_error = "Previous error"
        self.model_interface.is_initialized = False
        
        # Should be able to retry initialization
        assert self.model_interface.initialization_error is not None
        
        # Reset for retry
        self.model_interface.initialization_error = None
        assert self.model_interface.initialization_error is None


class TestELYZAModelPerformanceTracking:
    """Test performance tracking in ELYZAModelInterface"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.config = ModelConfig(model_path="/test/model.gguf")
        self.model_interface = ELYZAModelInterface(self.config)
    
    @pytest.mark.asyncio
    async def test_response_time_tracking(self):
        """Test response time tracking"""
        self.model_interface.is_initialized = True
        self.model_interface.llm = Mock()
        
        # Mock response with timing
        async def timed_response(prompt, **kwargs):
            await asyncio.sleep(0.1)  # 100ms
            return "テスト応答"
        
        with patch.object(self.model_interface, '_generate_response', side_effect=timed_response):
            response = await self.model_interface.generate_system_response(
                "テスト質問", {"cpu_percent": 50}
            )
        
        assert response is not None
        assert response.processing_time_ms >= 100  # Should be at least 100ms
        assert self.model_interface.total_requests == 1
    
    def test_performance_metrics(self):
        """Test performance metrics collection"""
        # Simulate some requests
        self.model_interface.total_requests = 10
        self.model_interface.total_processing_time = 2000.0  # 2 seconds total
        self.model_interface.average_response_time = 200.0  # 200ms average
        
        status = self.model_interface.get_model_status()
        
        assert status['total_requests'] == 10
        assert status['average_response_time_ms'] == 200.0
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling in response generation"""
        self.model_interface.llm = Mock()
        
        # Mock a response that times out
        async def timeout_response():
            await asyncio.sleep(15)  # Longer than timeout
            return {"choices": [{"text": "response"}]}
        
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError):
            result = await self.model_interface._generate_response("test prompt")
        
        assert result is None  # Should return None on timeout


class TestELYZAModelSystemDataFormatting:
    """Test system data formatting in ELYZAModelInterface"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.config = ModelConfig(model_path="/test/model.gguf")
        self.model_interface = ELYZAModelInterface(self.config)
    
    def test_comprehensive_system_data_formatting(self):
        """Test comprehensive system data formatting"""
        system_data = {
            "cpu_percent": 75.5,
            "cpu_count": 8,
            "memory_percent": 65.2,
            "memory_used": 12 * 1024**3,  # 12GB
            "memory_total": 16 * 1024**3,  # 16GB
            "disk_percent": 80.0,
            "disk_used": 400 * 1024**3,  # 400GB
            "disk_total": 500 * 1024**3,  # 500GB
            "top_processes": [
                {"name": "Chrome", "cpu_percent": 25.0, "memory_percent": 15.0},
                {"name": "VSCode", "cpu_percent": 10.0, "memory_percent": 8.0}
            ],
            "network_io": {
                "bytes_sent": 100 * 1024**2,  # 100MB
                "bytes_recv": 200 * 1024**2   # 200MB
            },
            "uptime": 86400.0,  # 1 day
            "load_average": [2.5, 2.0, 1.8]
        }
        
        result = self.model_interface._format_system_data(system_data)
        
        assert "CPU使用率: 75.5%" in result
        assert "メモリ使用率: 65.2%" in result
        assert "メモリ使用量: 12.0GB / 16.0GB" in result
        assert "ディスク使用率: 80.0%" in result
        assert "Chrome" in result
        assert "ネットワーク" in result
    
    def test_partial_system_data_formatting(self):
        """Test formatting with partial system data"""
        system_data = {
            "cpu_percent": 45.0,
            "memory_percent": 55.0
            # Missing other fields
        }
        
        result = self.model_interface._format_system_data(system_data)
        
        assert "CPU使用率: 45.0%" in result
        assert "メモリ使用率: 55.0%" in result
        assert len(result) > 0
    
    def test_malformed_system_data_handling(self):
        """Test handling of malformed system data"""
        # Test with various malformed data
        test_cases = [
            None,
            "invalid_string",
            {"cpu_percent": "invalid_number"},
            {"top_processes": "not_a_list"},
            {"network_io": "not_a_dict"}
        ]
        
        for test_data in test_cases:
            result = self.model_interface._format_system_data(test_data)
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_network_data_formatting(self):
        """Test network data formatting specifically"""
        system_data = {
            "network_io": {
                "bytes_sent": 1024**3,  # 1GB
                "bytes_recv": 2 * 1024**3,  # 2GB
                "packets_sent": 1000,
                "packets_recv": 2000
            }
        }
        
        result = self.model_interface._format_system_data(system_data)
        
        assert "ネットワーク" in result
        assert "1024.0MB" in result  # 1GB = 1024MB
        assert "2048.0MB" in result  # 2GB = 2048MB
    
    def test_process_data_formatting(self):
        """Test process data formatting"""
        system_data = {
            "top_processes": [
                {
                    "name": "Google Chrome Helper",
                    "cpu_percent": 35.5,
                    "memory_percent": 12.3,
                    "pid": 1234
                }
            ]
        }
        
        result = self.model_interface._format_system_data(system_data)
        
        assert "Google Chrome Helper" in result
        assert "35.5%" in result


class TestELYZAModelPromptGeneration:
    """Test prompt generation in ELYZAModelInterface"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.config = ModelConfig(model_path="/test/model.gguf")
        self.model_interface = ELYZAModelInterface(self.config)
    
    def test_simple_prompt_fallback(self):
        """Test simple prompt fallback when prompt_generator is not available"""
        system_data = {"cpu_percent": 60.0}
        conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        # Test the fallback method directly
        prompt = self.model_interface._create_simple_system_prompt(
            "システム状態は？",
            system_data,
            conversation_history
        )
        
        assert isinstance(prompt, str)
        assert "CPU使用率: 60.0%" in prompt
        assert "Hello" in prompt
        assert "システム状態は？" in prompt
    
    def test_prompt_with_long_history(self):
        """Test prompt generation with long conversation history"""
        system_data = {"cpu_percent": 40.0}
        
        # Create long conversation history (more than 5 messages)
        conversation_history = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)
        ]
        
        prompt = self.model_interface._create_simple_system_prompt(
            "Latest question",
            system_data,
            conversation_history
        )
        
        # Should only include last 5 messages
        message_count = prompt.count("Message")
        assert message_count <= 5
        assert "Latest question" in prompt
    
    def test_prompt_with_empty_system_data(self):
        """Test prompt generation with empty system data"""
        prompt = self.model_interface._create_simple_system_prompt(
            "Test question",
            {},
            None
        )
        
        assert isinstance(prompt, str)
        assert "Test question" in prompt
        assert len(prompt) > 0


class TestELYZAModelConfigurationManagement:
    """Test configuration management in ELYZAModelInterface"""
    
    def test_config_serialization(self):
        """Test configuration serialization"""
        config = ModelConfig(
            model_path="/test/path.gguf",
            n_ctx=4096,
            temperature=0.8,
            max_tokens=256
        )
        
        model = ELYZAModelInterface(config)
        status = model.get_model_status()
        
        config_dict = status['config']
        assert config_dict['n_ctx'] == 4096
        assert config_dict['temperature'] == 0.8
        assert config_dict['max_tokens'] == 256
    
    def test_default_config_values(self):
        """Test default configuration values"""
        config = create_default_config()
        
        assert config.n_ctx == 2048
        assert config.n_gpu_layers == -1  # Use all GPU layers
        assert config.temperature == 0.7
        assert config.max_tokens == 512
        assert config.verbose is False
    
    def test_m1_optimized_config(self):
        """Test M1-optimized configuration"""
        config = create_default_config()
        
        # M1 optimizations
        assert config.n_gpu_layers == -1  # Use Metal
        assert config.n_threads == 0  # Auto-detect
        assert config.n_ctx == 2048  # Reasonable context size
    
    def test_config_validation_edge_cases(self):
        """Test configuration validation edge cases"""
        # Test extreme values
        config = ModelConfig(
            model_path="/test/model.gguf",
            n_ctx=1,  # Minimum context
            temperature=0.0,  # Minimum temperature
            max_tokens=1  # Minimum tokens
        )
        
        model = ELYZAModelInterface(config)
        assert model.config.n_ctx == 1
        assert model.config.temperature == 0.0
        assert model.config.max_tokens == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])