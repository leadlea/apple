"""
Integration tests for JapanesePromptGenerator and ELYZAModelInterface
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Import the classes we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from prompt_generator import (
    JapanesePromptGenerator,
    ConversationContext,
    PromptStyle,
    SystemMetricType
)
from elyza_model import (
    ELYZAModelInterface,
    ModelConfig,
    ModelResponse
)


class TestPromptModelIntegration:
    """Integration tests for prompt generator and model interface"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.prompt_generator = JapanesePromptGenerator()
        self.model_config = ModelConfig(model_path="/test/model.gguf")
        self.model_interface = ELYZAModelInterface(self.model_config)
        
        self.sample_system_data = {
            'timestamp': datetime.now(),
            'cpu_percent': 65.3,
            'cpu_count': 8,
            'memory_percent': 78.2,
            'memory_used': 12 * 1024**3,
            'memory_total': 16 * 1024**3,
            'disk_percent': 45.7,
            'top_processes': [
                {'name': 'Google Chrome', 'cpu_percent': 35.2, 'memory_percent': 18.5},
                {'name': 'Xcode', 'cpu_percent': 15.8, 'memory_percent': 12.3}
            ],
            'network_io': {
                'bytes_sent': 200 * 1024**2,
                'bytes_recv': 500 * 1024**2
            }
        }
    
    def test_prompt_format_compatibility(self):
        """Test that generated prompts are compatible with model interface"""
        context = ConversationContext(preferred_style=PromptStyle.FRIENDLY)
        
        # Generate prompt
        prompt = self.prompt_generator.generate_system_prompt(
            user_query="システムの状態を教えてください",
            system_data=self.sample_system_data,
            context=context
        )
        
        # Check prompt structure
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Reasonable length
        assert "アシスタント:" in prompt  # Response starter
        assert "システム" in prompt  # Contains system info
        
        # Check that prompt doesn't contain problematic characters
        assert "\x00" not in prompt  # No null characters
        assert len(prompt.encode('utf-8')) < 4096  # Reasonable byte length
    
    def test_system_data_formatting_consistency(self):
        """Test that system data is consistently formatted across different styles"""
        styles = [PromptStyle.CASUAL, PromptStyle.TECHNICAL, PromptStyle.FRIENDLY, PromptStyle.PROFESSIONAL]
        
        for style in styles:
            context = ConversationContext(preferred_style=style)
            prompt = self.prompt_generator.generate_system_prompt(
                user_query="現在の状況は？",
                system_data=self.sample_system_data,
                context=context
            )
            
            # All styles should include basic system metrics
            assert "65.3" in prompt  # CPU percentage
            assert "78.2" in prompt  # Memory percentage
            assert "45.7" in prompt  # Disk percentage
            assert "Google Chrome" in prompt  # Top process
    
    @pytest.mark.asyncio
    async def test_prompt_generation_for_model_input(self):
        """Test generating prompts specifically for model input"""
        # Test different conversation scenarios
        test_scenarios = [
            {
                'query': 'CPUの使用率が心配です',
                'focus': SystemMetricType.CPU,
                'style': PromptStyle.FRIENDLY
            },
            {
                'query': '詳細なメモリ分析をお願いします',
                'focus': SystemMetricType.MEMORY,
                'style': PromptStyle.TECHNICAL
            },
            {
                'query': 'システム全体の状況を報告してください',
                'focus': None,
                'style': PromptStyle.PROFESSIONAL
            }
        ]
        
        for scenario in test_scenarios:
            context = ConversationContext(preferred_style=scenario['style'])
            
            if scenario['focus']:
                prompt = self.prompt_generator.create_focused_prompt(
                    user_query=scenario['query'],
                    system_data=self.sample_system_data,
                    metric_type=scenario['focus'],
                    context=context
                )
            else:
                prompt = self.prompt_generator.generate_system_prompt(
                    user_query=scenario['query'],
                    system_data=self.sample_system_data,
                    context=context
                )
            
            # Validate prompt structure for model consumption
            assert prompt.endswith("アシスタント: ")
            assert scenario['query'] in prompt
            assert len(prompt.split('\n')) >= 5  # Multi-line structure
    
    @pytest.mark.asyncio
    async def test_conversation_context_integration(self):
        """Test conversation context integration between prompt generator and model"""
        # Simulate a conversation history
        conversation_history = [
            {"role": "user", "content": "こんにちは"},
            {"role": "assistant", "content": "こんにちは！システム監視についてお手伝いします。"},
            {"role": "user", "content": "CPUの状況を教えて"},
            {"role": "assistant", "content": "現在のCPU使用率は65.3%です。少し高めですね。"}
        ]
        
        context = ConversationContext(
            preferred_style=PromptStyle.FRIENDLY,
            conversation_history=conversation_history,
            user_expertise_level="intermediate"
        )
        
        # Generate prompt with conversation context
        prompt = self.prompt_generator.generate_system_prompt(
            user_query="メモリの状況も教えてください",
            system_data=self.sample_system_data,
            context=context
        )
        
        # Check that conversation history is included
        assert "会話履歴:" in prompt
        assert "CPUの状況を教えて" in prompt
        assert "65.3%" in prompt  # Previous CPU mention should be in context
    
    def test_prompt_length_optimization(self):
        """Test that prompts are optimized for model context length"""
        # Test with extensive conversation history
        long_history = []
        for i in range(20):  # 20 exchanges = 40 messages
            long_history.extend([
                {"role": "user", "content": f"質問{i}: システムについて教えて"},
                {"role": "assistant", "content": f"回答{i}: システムは正常に動作しています。"}
            ])
        
        context = ConversationContext(
            conversation_history=long_history,
            preferred_style=PromptStyle.TECHNICAL
        )
        
        prompt = self.prompt_generator.generate_system_prompt(
            user_query="現在の詳細な状況を分析してください",
            system_data=self.sample_system_data,
            context=context
        )
        
        # Prompt should be reasonable length (not include all history)
        assert len(prompt) < 3000  # Reasonable upper limit
        
        # Should include recent history but not all
        assert "質問19" in prompt or "質問18" in prompt  # Recent items
        assert "質問0" not in prompt  # Old items should be excluded
    
    def test_special_characters_handling(self):
        """Test handling of special characters in system data and queries"""
        # System data with special characters
        special_system_data = {
            **self.sample_system_data,
            'top_processes': [
                {'name': 'App with "quotes"', 'cpu_percent': 10.0, 'memory_percent': 5.0},
                {'name': 'App with 日本語', 'cpu_percent': 8.0, 'memory_percent': 3.0},
                {'name': 'App with émojis 🚀', 'cpu_percent': 5.0, 'memory_percent': 2.0}
            ]
        }
        
        # Query with special characters
        special_query = 'システムの"パフォーマンス"について教えて 🤔'
        
        prompt = self.prompt_generator.generate_system_prompt(
            user_query=special_query,
            system_data=special_system_data,
            context=ConversationContext()
        )
        
        # Should handle special characters properly
        assert '"quotes"' in prompt
        assert '日本語' in prompt
        assert '🚀' in prompt
        assert '🤔' in prompt
        assert '"パフォーマンス"' in prompt
    
    def test_intent_extraction_accuracy(self):
        """Test accuracy of intent extraction for different query types"""
        test_queries = [
            ("CPUが重いです", SystemMetricType.CPU, "high"),
            ("メモリ使用量を確認したい", SystemMetricType.MEMORY, "normal"),
            ("ディスクの空き容量は？", SystemMetricType.DISK, "normal"),
            ("システムが動かない！緊急です", None, "high"),
            ("詳しいプロセス情報を教えて", SystemMetricType.PROCESSES, "normal")
        ]
        
        for query, expected_metric, expected_urgency in test_queries:
            intent = self.prompt_generator.extract_query_intent(query)
            
            if expected_metric:
                assert intent['metric_focus'] == expected_metric
            
            assert intent['urgency_level'] == expected_urgency
    
    @pytest.mark.asyncio
    async def test_mock_model_response_integration(self):
        """Test integration with mocked model response"""
        # Mock model interface
        with patch.object(self.model_interface, 'generate_system_response') as mock_generate:
            # Setup mock response
            mock_response = ModelResponse(
                content="現在のシステム状況をお伝えします。CPUは65.3%で少し高めですが、正常範囲内です。",
                timestamp=datetime.now(),
                processing_time_ms=150.0,
                token_count=25,
                model_info={'model': 'test'}
            )
            mock_generate.return_value = mock_response
            
            # Generate prompt
            context = ConversationContext(preferred_style=PromptStyle.FRIENDLY)
            prompt = self.prompt_generator.generate_system_prompt(
                user_query="システムの状況を教えて",
                system_data=self.sample_system_data,
                context=context
            )
            
            # Simulate model call (would normally use the prompt)
            response = await self.model_interface.generate_system_response(
                user_message="システムの状況を教えて",
                system_data=self.sample_system_data,
                conversation_history=[]
            )
            
            # Verify integration
            assert response is not None
            assert response.content == mock_response.content
            assert "65.3%" in response.content  # Should reference system data
    
    def test_prompt_template_consistency(self):
        """Test that all prompt templates maintain consistent structure"""
        styles = [PromptStyle.CASUAL, PromptStyle.TECHNICAL, PromptStyle.FRIENDLY, PromptStyle.PROFESSIONAL]
        
        for style in styles:
            template = self.prompt_generator.templates[style]
            
            # All templates should have required components
            assert template.system_role
            assert template.context_format
            assert template.user_query_format
            assert template.response_guidelines
            assert template.style_modifiers
            
            # Context format should have system_info placeholder
            assert "{system_info}" in template.context_format
            
            # User query format should have query placeholder
            assert "{query}" in template.user_query_format
            
            # Should have at least some response guidelines
            assert len(template.response_guidelines) > 0
    
    def test_error_handling_in_integration(self):
        """Test error handling when system data is incomplete or malformed"""
        # Test with missing data
        incomplete_data = {
            'cpu_percent': 50.0
            # Missing other expected fields
        }
        
        prompt = self.prompt_generator.generate_system_prompt(
            user_query="システム状況は？",
            system_data=incomplete_data,
            context=ConversationContext()
        )
        
        # Should handle missing data gracefully
        assert "50.0" in prompt
        assert len(prompt) > 100  # Should still generate reasonable prompt
        
        # Test with malformed data
        malformed_data = {
            'cpu_percent': "not_a_number",
            'memory_percent': None,
            'top_processes': "not_a_list"
        }
        
        # Should not raise exception
        try:
            prompt = self.prompt_generator.generate_system_prompt(
                user_query="状況確認",
                system_data=malformed_data,
                context=ConversationContext()
            )
            # Should generate some prompt even with bad data
            assert isinstance(prompt, str)
            assert len(prompt) > 50
        except Exception as e:
            pytest.fail(f"Should handle malformed data gracefully, but raised: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])