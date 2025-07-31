"""
Unit tests for JapanesePromptGenerator class
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

# Import the classes we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from prompt_generator import (
    JapanesePromptGenerator,
    ConversationContext,
    PromptTemplate,
    PromptStyle,
    SystemMetricType,
    create_status_check_prompt,
    create_performance_analysis_prompt,
    create_troubleshooting_prompt
)


class TestConversationContext:
    """Test cases for ConversationContext dataclass"""
    
    def test_conversation_context_creation(self):
        """Test ConversationContext creation with defaults"""
        context = ConversationContext()
        
        assert context.user_name is None
        assert context.preferred_style == PromptStyle.FRIENDLY
        assert context.recent_topics == []
        assert context.user_expertise_level == "beginner"
        assert context.conversation_history == []
    
    def test_conversation_context_custom_values(self):
        """Test ConversationContext with custom values"""
        context = ConversationContext(
            user_name="テストユーザー",
            preferred_style=PromptStyle.TECHNICAL,
            recent_topics=["CPU", "メモリ"],
            user_expertise_level="advanced",
            conversation_history=[{"role": "user", "content": "こんにちは"}]
        )
        
        assert context.user_name == "テストユーザー"
        assert context.preferred_style == PromptStyle.TECHNICAL
        assert context.recent_topics == ["CPU", "メモリ"]
        assert context.user_expertise_level == "advanced"
        assert len(context.conversation_history) == 1


class TestPromptTemplate:
    """Test cases for PromptTemplate dataclass"""
    
    def test_prompt_template_creation(self):
        """Test PromptTemplate creation"""
        template = PromptTemplate(
            system_role="テストロール",
            context_format="コンテキスト: {system_info}",
            user_query_format="質問: {query}",
            response_guidelines=["ガイドライン1", "ガイドライン2"],
            style_modifiers={"greeting": "こんにちは"}
        )
        
        assert template.system_role == "テストロール"
        assert template.context_format == "コンテキスト: {system_info}"
        assert template.user_query_format == "質問: {query}"
        assert len(template.response_guidelines) == 2
        assert template.style_modifiers["greeting"] == "こんにちは"


class TestJapanesePromptGenerator:
    """Test cases for JapanesePromptGenerator class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.generator = JapanesePromptGenerator()
        self.sample_system_data = {
            'timestamp': datetime.now(),
            'cpu_percent': 45.2,
            'cpu_count': 8,
            'memory_percent': 68.5,
            'memory_used': 11 * 1024**3,
            'memory_total': 16 * 1024**3,
            'disk_percent': 72.1,
            'disk_used': 360 * 1024**3,
            'disk_total': 500 * 1024**3,
            'top_processes': [
                {'name': 'Google Chrome', 'cpu_percent': 25.3, 'memory_percent': 15.2},
                {'name': 'Xcode', 'cpu_percent': 12.1, 'memory_percent': 8.7}
            ],
            'network_io': {
                'bytes_sent': 150 * 1024**2,
                'bytes_recv': 300 * 1024**2
            }
        }
    
    def test_init(self):
        """Test JapanesePromptGenerator initialization"""
        assert len(self.generator.templates) == 4  # 4 prompt styles
        assert PromptStyle.CASUAL in self.generator.templates
        assert PromptStyle.TECHNICAL in self.generator.templates
        assert PromptStyle.FRIENDLY in self.generator.templates
        assert PromptStyle.PROFESSIONAL in self.generator.templates
        
        assert len(self.generator.system_formatters) == 6  # 6 formatter types
        assert 'cpu' in self.generator.system_formatters
        assert 'memory' in self.generator.system_formatters
    
    def test_determine_prompt_style(self):
        """Test prompt style determination"""
        context = ConversationContext()
        
        # Test technical style detection
        technical_query = "詳細なスペック情報を教えてください"
        style = self.generator._determine_prompt_style(technical_query, context)
        assert style == PromptStyle.TECHNICAL
        
        # Test professional style detection
        professional_query = "業務用のレポートを作成してください"
        style = self.generator._determine_prompt_style(professional_query, context)
        assert style == PromptStyle.PROFESSIONAL
        
        # Test casual style detection
        casual_query = "どうなってるの？😊"
        style = self.generator._determine_prompt_style(casual_query, context)
        assert style == PromptStyle.CASUAL
        
        # Test default style
        neutral_query = "システムの状態を教えて"
        style = self.generator._determine_prompt_style(neutral_query, context)
        assert style == PromptStyle.FRIENDLY  # Default
    
    def test_format_cpu_info(self):
        """Test CPU information formatting"""
        # Test technical style
        cpu_info = self.generator._format_cpu_info(self.sample_system_data, PromptStyle.TECHNICAL)
        assert "CPU使用率: 45.2%" in cpu_info
        assert "コア数: 8" in cpu_info
        
        # Test casual style
        cpu_info = self.generator._format_cpu_info(self.sample_system_data, PromptStyle.CASUAL)
        assert "45.2%" in cpu_info
        assert "余裕があります" in cpu_info  # CPU < 50%
        
        # Test with high CPU
        high_cpu_data = {**self.sample_system_data, 'cpu_percent': 85.0}
        cpu_info = self.generator._format_cpu_info(high_cpu_data, PromptStyle.CASUAL)
        assert "忙しそう" in cpu_info
    
    def test_format_memory_info(self):
        """Test memory information formatting"""
        # Test technical style
        memory_info = self.generator._format_memory_info(self.sample_system_data, PromptStyle.TECHNICAL)
        assert "メモリ使用量:" in memory_info
        assert "11.0GB / 16.0GB" in memory_info
        assert "68.5%" in memory_info
        
        # Test casual style
        memory_info = self.generator._format_memory_info(self.sample_system_data, PromptStyle.CASUAL)
        assert "68.5%" in memory_info
        
        # Test with high memory usage
        high_memory_data = {**self.sample_system_data, 'memory_percent': 90.0}
        memory_info = self.generator._format_memory_info(high_memory_data, PromptStyle.CASUAL)
        assert "いっぱい" in memory_info
    
    def test_format_disk_info(self):
        """Test disk information formatting"""
        # Test technical style
        disk_info = self.generator._format_disk_info(self.sample_system_data, PromptStyle.TECHNICAL)
        assert "ディスク使用量:" in disk_info
        assert "360.0GB / 500.0GB" in disk_info
        assert "72.1%" in disk_info
        
        # Test casual style with high usage
        high_disk_data = {**self.sample_system_data, 'disk_percent': 95.0}
        disk_info = self.generator._format_disk_info(high_disk_data, PromptStyle.CASUAL)
        assert "お掃除" in disk_info
    
    def test_format_process_info(self):
        """Test process information formatting"""
        # Test technical style
        process_info = self.generator._format_process_info(self.sample_system_data, PromptStyle.TECHNICAL)
        assert "上位プロセス:" in process_info
        assert "Google Chrome" in process_info
        assert "25.3%" in process_info
        
        # Test casual style
        process_info = self.generator._format_process_info(self.sample_system_data, PromptStyle.CASUAL)
        assert "Google Chrome" in process_info
        
        # Test with empty processes
        empty_data = {**self.sample_system_data, 'top_processes': []}
        process_info = self.generator._format_process_info(empty_data, PromptStyle.CASUAL)
        assert process_info == ""
    
    def test_format_network_info(self):
        """Test network information formatting"""
        # Test technical style
        network_info = self.generator._format_network_info(self.sample_system_data, PromptStyle.TECHNICAL)
        assert "ネットワーク I/O:" in network_info
        assert "150.0MB" in network_info
        assert "300.0MB" in network_info
        
        # Test casual style
        network_info = self.generator._format_network_info(self.sample_system_data, PromptStyle.CASUAL)
        assert "450MB" in network_info  # 150 + 300
        
        # Test with missing network data
        no_network_data = {k: v for k, v in self.sample_system_data.items() if k != 'network_io'}
        network_info = self.generator._format_network_info(no_network_data, PromptStyle.CASUAL)
        assert network_info == ""
    
    def test_build_conversation_context(self):
        """Test conversation context building"""
        context = ConversationContext(
            conversation_history=[
                {"role": "user", "content": "こんにちは"},
                {"role": "assistant", "content": "こんにちは！何かお手伝いできることはありますか？"},
                {"role": "user", "content": "システムの状態を教えて"}
            ]
        )
        
        context_str = self.generator._build_conversation_context(context)
        assert "ユーザー: こんにちは" in context_str
        assert "アシスタント: こんにちは！" in context_str
        
        # Test with empty history
        empty_context = ConversationContext()
        context_str = self.generator._build_conversation_context(empty_context)
        assert context_str == ""
    
    def test_generate_system_prompt(self):
        """Test complete system prompt generation"""
        context = ConversationContext(preferred_style=PromptStyle.FRIENDLY)
        
        prompt = self.generator.generate_system_prompt(
            user_query="システムの調子はどうですか？",
            system_data=self.sample_system_data,
            context=context
        )
        
        # Check that prompt contains expected elements
        assert "Macの状態を監視" in prompt  # System role
        assert "CPU使用率:" in prompt or "CPU:" in prompt  # System info
        assert "システムの調子はどうですか？" in prompt  # User query
        assert "アシスタント:" in prompt  # Response starter
        assert len(prompt) > 100  # Reasonable length
    
    def test_create_focused_prompt(self):
        """Test focused prompt creation"""
        prompt = self.generator.create_focused_prompt(
            user_query="CPUの状況を教えて",
            system_data=self.sample_system_data,
            metric_type=SystemMetricType.CPU
        )
        
        assert "CPU" in prompt
        assert len(prompt) > 50
    
    def test_create_comparison_prompt(self):
        """Test comparison prompt creation"""
        previous_data = {**self.sample_system_data, 'cpu_percent': 30.0}
        
        prompt = self.generator.create_comparison_prompt(
            user_query="前回と比べてどう変わりましたか？",
            current_data=self.sample_system_data,
            previous_data=previous_data,
            context=ConversationContext()
        )
        
        assert "現在の状態:" in prompt
        assert "以前の状態:" in prompt
        assert "比較分析" in prompt
        assert "45.2" in prompt  # Current CPU
        assert "30.0" in prompt  # Previous CPU
    
    def test_extract_query_intent(self):
        """Test query intent extraction"""
        # Test CPU focus
        cpu_query = "CPUの使用率はどうですか？"
        intent = self.generator.extract_query_intent(cpu_query)
        assert intent['metric_focus'] == SystemMetricType.CPU
        
        # Test memory focus
        memory_query = "メモリが足りないかもしれません"
        intent = self.generator.extract_query_intent(memory_query)
        assert intent['metric_focus'] == SystemMetricType.MEMORY
        
        # Test urgency detection
        urgent_query = "システムが動かなくて緊急です！"
        intent = self.generator.extract_query_intent(urgent_query)
        assert intent['urgency_level'] == 'high'
        
        # Test detailed response request
        detailed_query = "詳しく教えてください"
        intent = self.generator.extract_query_intent(detailed_query)
        assert intent['response_type'] == 'detailed'
        
        # Test brief response request
        brief_query = "簡単に要約してください"
        intent = self.generator.extract_query_intent(brief_query)
        assert intent['response_type'] == 'brief'


class TestUtilityFunctions:
    """Test utility functions"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.sample_system_data = {
            'cpu_percent': 50.0,
            'memory_percent': 70.0,
            'disk_percent': 80.0
        }
    
    def test_create_status_check_prompt(self):
        """Test status check prompt creation"""
        prompt = create_status_check_prompt(self.sample_system_data, PromptStyle.FRIENDLY)
        
        assert "現在のシステムの状態を教えてください" in prompt
        assert "50.0%" in prompt
        assert len(prompt) > 100
    
    def test_create_performance_analysis_prompt(self):
        """Test performance analysis prompt creation"""
        issues = ["CPU使用率が高い", "メモリ不足"]
        prompt = create_performance_analysis_prompt(self.sample_system_data, issues)
        
        assert "パフォーマンスを分析" in prompt
        assert "CPU使用率が高い" in prompt
        assert "メモリ不足" in prompt
    
    def test_create_troubleshooting_prompt(self):
        """Test troubleshooting prompt creation"""
        issue = "アプリケーションが頻繁にクラッシュする"
        prompt = create_troubleshooting_prompt(self.sample_system_data, issue)
        
        assert "対処法を教えてください" in prompt
        assert "アプリケーションが頻繁にクラッシュする" in prompt


class TestPromptStyles:
    """Test different prompt styles"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.generator = JapanesePromptGenerator()
        self.sample_data = {
            'cpu_percent': 75.0,
            'memory_percent': 85.0,
            'disk_percent': 60.0
        }
    
    def test_casual_style_characteristics(self):
        """Test casual style characteristics"""
        context = ConversationContext(preferred_style=PromptStyle.CASUAL)
        prompt = self.generator.generate_system_prompt(
            "調子はどう？",
            self.sample_data,
            context
        )
        
        # Casual style should be friendly and use emojis/casual language
        assert "親しみやすい" in prompt or "気軽に" in prompt
    
    def test_technical_style_characteristics(self):
        """Test technical style characteristics"""
        context = ConversationContext(preferred_style=PromptStyle.TECHNICAL)
        prompt = self.generator.generate_system_prompt(
            "詳細な分析をお願いします",
            self.sample_data,
            context
        )
        
        # Technical style should include detailed metrics
        assert "技術的" in prompt
        assert "正確" in prompt
    
    def test_professional_style_characteristics(self):
        """Test professional style characteristics"""
        context = ConversationContext(preferred_style=PromptStyle.PROFESSIONAL)
        prompt = self.generator.generate_system_prompt(
            "レポートを作成してください",
            self.sample_data,
            context
        )
        
        # Professional style should be formal
        assert "プロフェッショナル" in prompt or "ビジネス" in prompt
    
    def test_friendly_style_characteristics(self):
        """Test friendly style characteristics"""
        context = ConversationContext(preferred_style=PromptStyle.FRIENDLY)
        prompt = self.generator.generate_system_prompt(
            "教えてください",
            self.sample_data,
            context
        )
        
        # Friendly style should be warm and helpful
        assert "温かく" in prompt or "親切" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])