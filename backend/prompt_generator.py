"""
Japanese Prompt Generation System for Mac Status PWA
Converts system information and conversation context into Japanese prompts for ELYZA model
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import re


class PromptStyle(Enum):
    """Different prompt styles for various interaction types"""
    CASUAL = "casual"           # カジュアルな会話
    TECHNICAL = "technical"     # 技術的な詳細
    FRIENDLY = "friendly"       # フレンドリーな対話
    PROFESSIONAL = "professional"  # プロフェッショナル


class SystemMetricType(Enum):
    """Types of system metrics for focused responses"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    PROCESSES = "processes"
    NETWORK = "network"
    GENERAL = "general"


@dataclass
class ConversationContext:
    """Context information for conversation continuity"""
    user_name: Optional[str] = None
    preferred_style: PromptStyle = PromptStyle.FRIENDLY
    recent_topics: List[str] = None
    user_expertise_level: str = "beginner"  # beginner, intermediate, advanced
    conversation_history: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.recent_topics is None:
            self.recent_topics = []
        if self.conversation_history is None:
            self.conversation_history = []


@dataclass
class PromptTemplate:
    """Template for generating prompts"""
    system_role: str
    context_format: str
    user_query_format: str
    response_guidelines: List[str]
    style_modifiers: Dict[str, str]


class JapanesePromptGenerator:
    """
    Generates Japanese prompts for ELYZA model based on system data and conversation context
    """
    
    def __init__(self):
        """Initialize the prompt generator with templates and formatting rules"""
        self.templates = self._initialize_templates()
        self.system_formatters = self._initialize_system_formatters()
        self.conversation_patterns = self._initialize_conversation_patterns()
        
    def _initialize_templates(self) -> Dict[PromptStyle, PromptTemplate]:
        """Initialize prompt templates for different styles"""
        return {
            PromptStyle.CASUAL: PromptTemplate(
                system_role="あなたはMacの状態を監視する親しみやすいアシスタントです。ユーザーと気軽に会話しながら、システム情報を分かりやすく説明します。",
                context_format="現在のMacの状態:\n{system_info}\n",
                user_query_format="ユーザー: {query}\n",
                response_guidelines=[
                    "親しみやすい口調で話す",
                    "専門用語は分かりやすく説明する", 
                    "必要に応じて絵文字を使用する",
                    "簡潔で理解しやすい回答をする"
                ],
                style_modifiers={
                    "greeting": "こんにちは！",
                    "concern": "ちょっと気になることがありますね",
                    "good_news": "良い感じですね！",
                    "suggestion": "こんなことを試してみてはいかがでしょうか"
                }
            ),
            
            PromptStyle.TECHNICAL: PromptTemplate(
                system_role="あなたはMacシステムの技術的な詳細に精通した専門アシスタントです。正確で詳細な技術情報を提供します。",
                context_format="システム詳細情報:\n{system_info}\n",
                user_query_format="クエリ: {query}\n",
                response_guidelines=[
                    "技術的に正確な情報を提供する",
                    "具体的な数値やメトリクスを含める",
                    "専門用語を適切に使用する",
                    "詳細な分析と推奨事項を提供する"
                ],
                style_modifiers={
                    "analysis": "システム分析結果:",
                    "metrics": "パフォーマンスメトリクス:",
                    "recommendation": "技術的推奨事項:",
                    "warning": "注意が必要な項目:"
                }
            ),
            
            PromptStyle.FRIENDLY: PromptTemplate(
                system_role="あなたはMacユーザーの頼れる友人のようなアシスタントです。温かく親切に、システム状態について説明します。",
                context_format="あなたのMacの今の様子:\n{system_info}\n",
                user_query_format="質問: {query}\n",
                response_guidelines=[
                    "温かく親切な口調で対応する",
                    "ユーザーの心配事に共感する",
                    "分かりやすい例えを使用する",
                    "安心感を与える回答をする"
                ],
                style_modifiers={
                    "reassurance": "ご安心ください",
                    "explanation": "簡単に説明すると",
                    "help": "お手伝いできることがあります",
                    "status": "現在の状況は"
                }
            ),
            
            PromptStyle.PROFESSIONAL: PromptTemplate(
                system_role="あなたはMacシステム管理の専門家として、ビジネス環境でのシステム監視をサポートします。",
                context_format="システム監視レポート:\n{system_info}\n",
                user_query_format="お問い合わせ: {query}\n",
                response_guidelines=[
                    "プロフェッショナルで丁寧な言葉遣い",
                    "ビジネス影響を考慮した回答",
                    "具体的な対処法を提示",
                    "リスク評価を含める"
                ],
                style_modifiers={
                    "report": "システム状況報告:",
                    "impact": "業務への影響:",
                    "action": "推奨対応:",
                    "priority": "優先度:"
                }
            )
        }
    
    def _initialize_system_formatters(self) -> Dict[str, callable]:
        """Initialize system information formatters"""
        return {
            'cpu': self._format_cpu_info,
            'memory': self._format_memory_info,
            'disk': self._format_disk_info,
            'processes': self._format_process_info,
            'network': self._format_network_info,
            'general': self._format_general_info
        }
    
    def _initialize_conversation_patterns(self) -> Dict[str, List[str]]:
        """Initialize conversation patterns for context awareness"""
        return {
            'greetings': [
                'こんにちは', 'おはよう', 'こんばんは', 'はじめまして',
                'hello', 'hi', 'hey'
            ],
            'status_requests': [
                '状態', 'ステータス', '様子', '調子', '具合',
                'status', 'condition', 'how'
            ],
            'performance_concerns': [
                '遅い', '重い', '動かない', '問題', 'エラー',
                'slow', 'heavy', 'problem', 'error', 'issue'
            ],
            'resource_queries': [
                'CPU', 'メモリ', 'ディスク', 'プロセス', 'ネットワーク',
                'memory', 'disk', 'process', 'network'
            ]
        }
    
    def generate_system_prompt(self, 
                             user_query: str,
                             system_data: Dict[str, Any],
                             context: Optional[ConversationContext] = None,
                             focus_metric: Optional[SystemMetricType] = None) -> str:
        """
        Generate a complete Japanese prompt for the ELYZA model
        
        Args:
            user_query: User's input query
            system_data: Current system status data
            context: Conversation context for personalization
            focus_metric: Specific metric to focus on
            
        Returns:
            Complete formatted prompt string
        """
        if context is None:
            context = ConversationContext()
        
        # Determine appropriate style based on query and context
        style = self._determine_prompt_style(user_query, context)
        template = self.templates[style]
        
        # Format system information
        system_info = self._format_system_information(system_data, style, focus_metric)
        
        # Build conversation context
        conversation_context = self._build_conversation_context(context)
        
        # Generate the complete prompt
        prompt_parts = [
            template.system_role,
            "",
            template.context_format.format(system_info=system_info),
        ]
        
        # Add conversation history if available
        if conversation_context:
            prompt_parts.extend([
                "会話履歴:",
                conversation_context,
                ""
            ])
        
        # Add response guidelines
        guidelines = "回答時の注意点:\n" + "\n".join(f"- {guideline}" for guideline in template.response_guidelines)
        prompt_parts.extend([guidelines, ""])
        
        # Add user query
        prompt_parts.append(template.user_query_format.format(query=user_query))
        
        # Add response starter
        prompt_parts.append("アシスタント: ")
        
        return "\n".join(prompt_parts)
    
    def _determine_prompt_style(self, user_query: str, context: ConversationContext) -> PromptStyle:
        """Determine the most appropriate prompt style based on query and context"""
        query_lower = user_query.lower()
        
        # Check for technical keywords
        technical_keywords = ['詳細', 'スペック', '技術', 'パフォーマンス', 'メトリクス', 'ログ']
        if any(keyword in query_lower for keyword in technical_keywords):
            return PromptStyle.TECHNICAL
        
        # Check for professional context
        professional_keywords = ['レポート', '報告', 'ビジネス', '業務', '会社']
        if any(keyword in query_lower for keyword in professional_keywords):
            return PromptStyle.PROFESSIONAL
        
        # Check for casual indicators
        casual_keywords = ['どう', 'なんか', 'ちょっと', '😊', '👍']
        if any(keyword in query_lower for keyword in casual_keywords):
            return PromptStyle.CASUAL
        
        # Default to user's preferred style or friendly
        return context.preferred_style
    
    def _format_system_information(self, 
                                 system_data: Dict[str, Any], 
                                 style: PromptStyle,
                                 focus_metric: Optional[SystemMetricType] = None) -> str:
        """Format system information according to style and focus"""
        formatted_parts = []
        
        if focus_metric:
            # Focus on specific metric
            if focus_metric.value in self.system_formatters:
                formatter = self.system_formatters[focus_metric.value]
                formatted_parts.append(formatter(system_data, style))
        else:
            # Include all relevant system information
            for metric_type, formatter in self.system_formatters.items():
                if metric_type != 'general':  # General is used for overview
                    formatted_info = formatter(system_data, style)
                    if formatted_info:
                        formatted_parts.append(formatted_info)
        
        return "\n".join(formatted_parts)
    
    def _format_cpu_info(self, system_data: Dict[str, Any], style: PromptStyle) -> str:
        """Format CPU information"""
        if 'cpu_percent' not in system_data:
            return ""
        
        cpu_percent = system_data['cpu_percent']
        cpu_count = system_data.get('cpu_count', 'N/A')
        
        # Handle invalid data types
        try:
            cpu_percent = float(cpu_percent)
        except (ValueError, TypeError):
            return "CPU使用率: データ取得エラー"
        
        if style == PromptStyle.TECHNICAL:
            return f"CPU使用率: {cpu_percent:.1f}% (コア数: {cpu_count})"
        elif style == PromptStyle.CASUAL:
            if cpu_percent > 80:
                return f"CPU: {cpu_percent:.1f}% - ちょっと忙しそうですね 😅"
            elif cpu_percent > 50:
                return f"CPU: {cpu_percent:.1f}% - まあまあ働いてます"
            else:
                return f"CPU: {cpu_percent:.1f}% - 余裕がありますね 👍"
        else:
            return f"CPU使用率: {cpu_percent:.1f}%"
    
    def _format_memory_info(self, system_data: Dict[str, Any], style: PromptStyle) -> str:
        """Format memory information"""
        if 'memory_percent' not in system_data:
            return ""
        
        memory_percent = system_data['memory_percent']
        memory_used = system_data.get('memory_used', 0)
        memory_total = system_data.get('memory_total', 0)
        
        # Handle invalid data types
        try:
            memory_percent = float(memory_percent) if memory_percent is not None else 0.0
            memory_used = float(memory_used) if memory_used is not None else 0.0
            memory_total = float(memory_total) if memory_total is not None else 0.0
        except (ValueError, TypeError):
            return "メモリ使用率: データ取得エラー"
        
        if memory_total > 0:
            used_gb = memory_used / (1024**3)
            total_gb = memory_total / (1024**3)
            
            if style == PromptStyle.TECHNICAL:
                return f"メモリ使用量: {used_gb:.1f}GB / {total_gb:.1f}GB ({memory_percent:.1f}%)"
            elif style == PromptStyle.CASUAL:
                if memory_percent > 85:
                    return f"メモリ: {memory_percent:.1f}% - そろそろいっぱいかも 💭"
                elif memory_percent > 70:
                    return f"メモリ: {memory_percent:.1f}% - 結構使ってますね"
                else:
                    return f"メモリ: {memory_percent:.1f}% - まだ余裕があります"
            else:
                return f"メモリ使用率: {memory_percent:.1f}% ({used_gb:.1f}GB / {total_gb:.1f}GB)"
        else:
            return f"メモリ使用率: {memory_percent:.1f}%"
    
    def _format_disk_info(self, system_data: Dict[str, Any], style: PromptStyle) -> str:
        """Format disk information"""
        if 'disk_percent' not in system_data:
            return ""
        
        disk_percent = system_data['disk_percent']
        disk_used = system_data.get('disk_used', 0)
        disk_total = system_data.get('disk_total', 0)
        
        if disk_total > 0:
            used_gb = disk_used / (1024**3)
            total_gb = disk_total / (1024**3)
            
            if style == PromptStyle.TECHNICAL:
                return f"ディスク使用量: {used_gb:.1f}GB / {total_gb:.1f}GB ({disk_percent:.1f}%)"
            elif style == PromptStyle.CASUAL:
                if disk_percent > 90:
                    return f"ディスク: {disk_percent:.1f}% - そろそろお掃除が必要かも 🧹"
                elif disk_percent > 75:
                    return f"ディスク: {disk_percent:.1f}% - だいぶ使ってますね"
                else:
                    return f"ディスク: {disk_percent:.1f}% - まだ大丈夫です"
            else:
                return f"ディスク使用率: {disk_percent:.1f}%"
        else:
            return f"ディスク使用率: {disk_percent:.1f}%"
    
    def _format_process_info(self, system_data: Dict[str, Any], style: PromptStyle) -> str:
        """Format process information"""
        if 'top_processes' not in system_data or not system_data['top_processes']:
            return ""
        
        # Handle invalid data types
        try:
            if not isinstance(system_data['top_processes'], list):
                return ""
            top_processes = system_data['top_processes'][:3]  # Top 3 processes
        except (TypeError, AttributeError):
            return ""
        
        if style == PromptStyle.TECHNICAL:
            process_lines = []
            for i, proc in enumerate(top_processes, 1):
                name = proc.get('name', 'Unknown')
                cpu = proc.get('cpu_percent', 0)
                memory = proc.get('memory_percent', 0)
                process_lines.append(f"{i}. {name} (CPU: {cpu:.1f}%, Memory: {memory:.1f}%)")
            return "上位プロセス:\n" + "\n".join(process_lines)
        
        elif style == PromptStyle.CASUAL:
            top_proc = top_processes[0]
            name = top_proc.get('name', 'Unknown')
            cpu = top_proc.get('cpu_percent', 0)
            
            if cpu > 50:
                return f"一番忙しいアプリ: {name} ({cpu:.1f}%) - 頑張ってますね！"
            else:
                return f"一番活発なアプリ: {name} ({cpu:.1f}%)"
        
        else:
            top_proc = top_processes[0]
            name = top_proc.get('name', 'Unknown')
            cpu = top_proc.get('cpu_percent', 0)
            return f"最もCPUを使用しているプロセス: {name} ({cpu:.1f}%)"
    
    def _format_network_info(self, system_data: Dict[str, Any], style: PromptStyle) -> str:
        """Format network information"""
        if 'network_io' not in system_data:
            return ""
        
        network = system_data['network_io']
        if isinstance(network, dict):
            sent_mb = network.get('bytes_sent', 0) / (1024**2)
            recv_mb = network.get('bytes_recv', 0) / (1024**2)
            
            if style == PromptStyle.TECHNICAL:
                return f"ネットワーク I/O: 送信 {sent_mb:.1f}MB, 受信 {recv_mb:.1f}MB"
            elif style == PromptStyle.CASUAL:
                total_mb = sent_mb + recv_mb
                if total_mb > 1000:
                    return f"ネットワーク: {total_mb:.0f}MB - よく通信してますね 📡"
                else:
                    return f"ネットワーク: {total_mb:.0f}MB"
            else:
                return f"ネットワーク通信量: 送信 {sent_mb:.1f}MB, 受信 {recv_mb:.1f}MB"
        
        return ""
    
    def _format_general_info(self, system_data: Dict[str, Any], style: PromptStyle) -> str:
        """Format general system overview"""
        timestamp = system_data.get('timestamp')
        if timestamp:
            if isinstance(timestamp, str):
                time_str = timestamp
            else:
                time_str = timestamp.strftime('%H:%M:%S')
            
            if style == PromptStyle.CASUAL:
                return f"📊 {time_str} 現在の状況"
            else:
                return f"取得時刻: {time_str}"
        
        return ""
    
    def _build_conversation_context(self, context: ConversationContext) -> str:
        """Build conversation context string"""
        if not context.conversation_history:
            return ""
        
        # Get recent conversation (last 3 exchanges)
        recent_history = context.conversation_history[-6:]  # 3 exchanges = 6 messages
        
        context_lines = []
        for msg in recent_history:
            role = "ユーザー" if msg.get('role') == 'user' else "アシスタント"
            content = msg.get('content', '')[:100]  # Limit length
            if len(msg.get('content', '')) > 100:
                content += "..."
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
    
    def create_focused_prompt(self, 
                            user_query: str,
                            system_data: Dict[str, Any],
                            metric_type: SystemMetricType,
                            context: Optional[ConversationContext] = None) -> str:
        """
        Create a prompt focused on a specific system metric
        
        Args:
            user_query: User's query
            system_data: System information
            metric_type: Type of metric to focus on
            context: Conversation context
            
        Returns:
            Focused prompt string
        """
        return self.generate_system_prompt(
            user_query=user_query,
            system_data=system_data,
            context=context,
            focus_metric=metric_type
        )
    
    def create_comparison_prompt(self,
                               user_query: str,
                               current_data: Dict[str, Any],
                               previous_data: Dict[str, Any],
                               context: Optional[ConversationContext] = None) -> str:
        """
        Create a prompt that compares current and previous system states
        
        Args:
            user_query: User's query
            current_data: Current system data
            previous_data: Previous system data
            context: Conversation context
            
        Returns:
            Comparison prompt string
        """
        if context is None:
            context = ConversationContext()
        
        style = self._determine_prompt_style(user_query, context)
        template = self.templates[style]
        
        # Format current and previous data
        current_info = self._format_system_information(current_data, style)
        previous_info = self._format_system_information(previous_data, style)
        
        # Create comparison context
        comparison_context = f"現在の状態:\n{current_info}\n\n以前の状態:\n{previous_info}\n"
        
        # Build conversation context
        conversation_context = self._build_conversation_context(context)
        
        # Generate comparison prompt
        prompt_parts = [
            template.system_role + " 現在の状態と以前の状態を比較して、変化や傾向について説明してください。",
            "",
            comparison_context,
        ]
        
        if conversation_context:
            prompt_parts.extend([
                "会話履歴:",
                conversation_context,
                ""
            ])
        
        prompt_parts.extend([
            "比較分析の注意点:",
            "- 重要な変化を特定する",
            "- 改善点や悪化点を明確にする", 
            "- 必要に応じて対処法を提案する",
            "",
            template.user_query_format.format(query=user_query),
            "アシスタント: "
        ])
        
        return "\n".join(prompt_parts)
    
    def extract_query_intent(self, user_query: str) -> Dict[str, Any]:
        """
        Extract intent and entities from user query
        
        Args:
            user_query: User's input query
            
        Returns:
            Dictionary with intent and extracted information
        """
        query_lower = user_query.lower()
        
        intent_info = {
            'primary_intent': 'general_inquiry',
            'metric_focus': None,
            'urgency_level': 'normal',
            'response_type': 'informative',
            'entities': []
        }
        
        # Detect metric focus
        for pattern_type, keywords in self.conversation_patterns.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    if pattern_type == 'resource_queries':
                        if 'cpu' in keyword.lower():
                            intent_info['metric_focus'] = SystemMetricType.CPU
                        elif 'メモリ' in keyword or 'memory' in keyword.lower():
                            intent_info['metric_focus'] = SystemMetricType.MEMORY
                        elif 'ディスク' in keyword or 'disk' in keyword.lower():
                            intent_info['metric_focus'] = SystemMetricType.DISK
                        elif 'プロセス' in keyword or 'process' in keyword.lower():
                            intent_info['metric_focus'] = SystemMetricType.PROCESSES
                        elif 'ネットワーク' in keyword or 'network' in keyword.lower():
                            intent_info['metric_focus'] = SystemMetricType.NETWORK
                    
                    intent_info['entities'].append({
                        'type': pattern_type,
                        'value': keyword,
                        'category': pattern_type
                    })
        
        # Detect urgency
        urgent_keywords = ['緊急', '急いで', '問題', 'エラー', '動かない', '遅い', '重い', '！', 'クラッシュ', '停止']
        if any(keyword in query_lower for keyword in urgent_keywords):
            intent_info['urgency_level'] = 'high'
        
        # Detect response type preference
        if any(word in query_lower for word in ['詳しく', '詳細', '具体的']):
            intent_info['response_type'] = 'detailed'
        elif any(word in query_lower for word in ['簡単', '要約', '短く']):
            intent_info['response_type'] = 'brief'
        
        return intent_info


# Utility functions for common prompt generation scenarios
def create_status_check_prompt(system_data: Dict[str, Any], 
                             style: PromptStyle = PromptStyle.FRIENDLY) -> str:
    """Create a prompt for general status check"""
    generator = JapanesePromptGenerator()
    context = ConversationContext(preferred_style=style)
    
    return generator.generate_system_prompt(
        user_query="現在のシステムの状態を教えてください",
        system_data=system_data,
        context=context
    )


def create_performance_analysis_prompt(system_data: Dict[str, Any],
                                     performance_issues: List[str] = None) -> str:
    """Create a prompt for performance analysis"""
    generator = JapanesePromptGenerator()
    context = ConversationContext(preferred_style=PromptStyle.TECHNICAL)
    
    query = "システムのパフォーマンスを分析してください"
    if performance_issues:
        query += f"。特に以下の点について: {', '.join(performance_issues)}"
    
    return generator.generate_system_prompt(
        user_query=query,
        system_data=system_data,
        context=context
    )


def create_troubleshooting_prompt(system_data: Dict[str, Any],
                                issue_description: str) -> str:
    """Create a prompt for troubleshooting assistance"""
    generator = JapanesePromptGenerator()
    context = ConversationContext(preferred_style=PromptStyle.PROFESSIONAL)
    
    query = f"次の問題について対処法を教えてください: {issue_description}"
    
    return generator.generate_system_prompt(
        user_query=query,
        system_data=system_data,
        context=context
    )


# Test function
async def test_prompt_generator():
    """Test function for JapanesePromptGenerator"""
    print("🧪 Testing Japanese Prompt Generator")
    print("=" * 50)
    
    # Sample system data
    sample_system_data = {
        'timestamp': datetime.now(),
        'cpu_percent': 45.2,
        'cpu_count': 8,
        'memory_percent': 68.5,
        'memory_used': 11 * 1024**3,  # 11GB
        'memory_total': 16 * 1024**3,  # 16GB
        'disk_percent': 72.1,
        'disk_used': 360 * 1024**3,   # 360GB
        'disk_total': 500 * 1024**3,  # 500GB
        'top_processes': [
            {'name': 'Google Chrome', 'cpu_percent': 25.3, 'memory_percent': 15.2},
            {'name': 'Xcode', 'cpu_percent': 12.1, 'memory_percent': 8.7},
            {'name': 'Finder', 'cpu_percent': 3.2, 'memory_percent': 2.1}
        ],
        'network_io': {
            'bytes_sent': 150 * 1024**2,  # 150MB
            'bytes_recv': 300 * 1024**2   # 300MB
        }
    }
    
    generator = JapanesePromptGenerator()
    
    # Test different styles
    test_cases = [
        ("システムの調子はどうですか？", PromptStyle.CASUAL),
        ("詳細なパフォーマンス分析をお願いします", PromptStyle.TECHNICAL),
        ("現在の状況を教えてください", PromptStyle.FRIENDLY),
        ("システム監視レポートを作成してください", PromptStyle.PROFESSIONAL)
    ]
    
    for i, (query, style) in enumerate(test_cases, 1):
        print(f"\n{i}. Test Case: {style.value.upper()}")
        print("-" * 30)
        
        context = ConversationContext(
            preferred_style=style,
            user_expertise_level="intermediate",
            conversation_history=[
                {"role": "user", "content": "こんにちは"},
                {"role": "assistant", "content": "こんにちは！何かお手伝いできることはありますか？"}
            ]
        )
        
        prompt = generator.generate_system_prompt(
            user_query=query,
            system_data=sample_system_data,
            context=context
        )
        
        print(f"Query: {query}")
        print(f"Generated Prompt Length: {len(prompt)} characters")
        print(f"Preview: {prompt[:200]}...")
        
        # Test intent extraction
        intent = generator.extract_query_intent(query)
        print(f"Detected Intent: {intent['primary_intent']}")
        if intent['metric_focus']:
            print(f"Metric Focus: {intent['metric_focus'].value}")
    
    # Test focused prompts
    print(f"\n5. Test Focused Prompt (CPU)")
    print("-" * 30)
    
    focused_prompt = generator.create_focused_prompt(
        user_query="CPUの使用状況について教えて",
        system_data=sample_system_data,
        metric_type=SystemMetricType.CPU
    )
    
    print(f"Focused Prompt Length: {len(focused_prompt)} characters")
    print(f"Preview: {focused_prompt[:200]}...")
    
    print("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_prompt_generator())