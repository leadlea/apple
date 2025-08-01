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
    BATTERY = "battery"
    WIFI = "wifi"
    APPS = "apps"
    DISK_DETAILS = "disk_details"
    DEV_TOOLS = "dev_tools"
    THERMAL = "thermal"
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


class PromptGenerator:
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
            'battery': self._format_battery_info,
            'wifi': self._format_wifi_info,
            'apps': self._format_running_apps_info,
            'disk_details': self._format_disk_details_info,
            'dev_tools': self._format_dev_tools_info,
            'thermal': self._format_thermal_info,
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
            ],
            'battery_queries': [
                'バッテリー', '電池', '充電', '残量', 'あと', '時間',
                'battery', 'power', 'charge', 'remaining'
            ],
            'wifi_queries': [
                'WiFi', 'wifi', 'ワイファイ', 'ネットワーク', '接続', '信号',
                '電波', 'SSID', 'チャンネル', '速度', 'network', 'wireless',
                'signal', 'connection', 'internet'
            ],
            'app_queries': [
                'アプリ', 'アプリケーション', '開いてる', '実行中', '動いてる',
                'プログラム', 'ソフト', 'app', 'application', 'running',
                'open', 'program', 'software', 'Chrome', 'Safari', 'Finder'
            ],
            'disk_detail_queries': [
                'ディスク詳細', 'パーティション', '外付け', 'ドライブ', 'ボリューム',
                'ストレージ詳細', 'HDD', 'SSD', 'USB', 'disk details', 'partition',
                'external', 'drive', 'volume', 'storage details', 'Volumes'
            ],
            'dev_tools_queries': [
                '開発ツール', '開発環境', 'Xcode', 'Git', 'Homebrew', 'Node',
                'Python', 'Docker', 'VS Code', 'brew', 'npm', 'pip',
                'development tools', 'dev tools', 'coding tools', 'programming'
            ],
            'thermal_queries': [
                '温度', '熱', 'ファン', '冷却', '発熱', 'サーマル', '回転数',
                'temperature', 'thermal', 'fan', 'cooling', 'heat', 'rpm',
                '暑い', '熱い', 'hot', 'warm', 'cool'
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
        
        # Auto-detect focus metric if not provided
        if focus_metric is None:
            focus_metric = self._detect_query_focus(user_query)
        
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
    
    def _detect_query_focus(self, user_query: str) -> Optional[SystemMetricType]:
        """Detect what system metric the user is asking about"""
        query_lower = user_query.lower()
        
        # Battery queries
        battery_keywords = self.conversation_patterns['battery_queries']
        if any(keyword.lower() in query_lower for keyword in battery_keywords):
            return SystemMetricType.BATTERY
        
        # WiFi queries
        wifi_keywords = self.conversation_patterns['wifi_queries']
        if any(keyword.lower() in query_lower for keyword in wifi_keywords):
            return SystemMetricType.WIFI
        
        # App queries
        app_keywords = self.conversation_patterns['app_queries']
        if any(keyword.lower() in query_lower for keyword in app_keywords):
            return SystemMetricType.APPS
        
        # Disk details queries
        disk_detail_keywords = self.conversation_patterns['disk_detail_queries']
        if any(keyword.lower() in query_lower for keyword in disk_detail_keywords):
            return SystemMetricType.DISK_DETAILS
        
        # Dev tools queries
        dev_tools_keywords = self.conversation_patterns['dev_tools_queries']
        if any(keyword.lower() in query_lower for keyword in dev_tools_keywords):
            return SystemMetricType.DEV_TOOLS
        
        # Thermal queries
        thermal_keywords = self.conversation_patterns['thermal_queries']
        if any(keyword.lower() in query_lower for keyword in thermal_keywords):
            return SystemMetricType.THERMAL
        
        # CPU queries
        cpu_keywords = ['cpu', 'プロセッサ', '処理', '計算']
        if any(keyword in query_lower for keyword in cpu_keywords):
            return SystemMetricType.CPU
        
        # Memory queries
        memory_keywords = ['メモリ', 'ram', '記憶', 'memory']
        if any(keyword in query_lower for keyword in memory_keywords):
            return SystemMetricType.MEMORY
        
        # Disk queries
        disk_keywords = ['ディスク', 'ストレージ', '容量', 'disk', 'storage']
        if any(keyword in query_lower for keyword in disk_keywords):
            return SystemMetricType.DISK
        
        # Process queries
        process_keywords = ['プロセス', 'アプリ', 'process', 'application']
        if any(keyword in query_lower for keyword in process_keywords):
            return SystemMetricType.PROCESSES
        
        # Network queries
        network_keywords = ['ネットワーク', '通信', 'network', 'internet']
        if any(keyword in query_lower for keyword in network_keywords):
            return SystemMetricType.NETWORK
        
        return None
    
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
    
    def _format_battery_info(self, system_data: Dict[str, Any], style: PromptStyle) -> str:
        """Format battery information"""
        battery_data = system_data.get('battery')
        if not battery_data:
            return ""
        
        percent = battery_data.get('percent')
        power_plugged = battery_data.get('power_plugged')
        secsleft = battery_data.get('secsleft')
        status = battery_data.get('status', 'unknown')
        
        if percent is None:
            return ""
        
        # Format based on style
        if style == PromptStyle.CASUAL:
            battery_emoji = "🔋" if not power_plugged else "🔌"
            status_text = ""
            
            if power_plugged:
                if percent >= 100:
                    status_text = "フル充電完了！"
                else:
                    status_text = f"充電中 ({percent:.0f}%)"
            else:
                status_text = f"バッテリー駆動 ({percent:.0f}%)"
                if secsleft and secsleft > 0:
                    hours = secsleft // 3600
                    minutes = (secsleft % 3600) // 60
                    if hours > 0:
                        status_text += f" - あと約{hours}時間{minutes}分"
                    else:
                        status_text += f" - あと約{minutes}分"
            
            return f"{battery_emoji} {status_text}"
            
        elif style == PromptStyle.TECHNICAL:
            status_details = []
            status_details.append(f"バッテリー残量: {percent:.1f}%")
            status_details.append(f"電源接続: {'はい' if power_plugged else 'いいえ'}")
            status_details.append(f"状態: {status}")
            
            if secsleft and secsleft > 0:
                hours = secsleft // 3600
                minutes = (secsleft % 3600) // 60
                status_details.append(f"推定残り時間: {hours}時間{minutes}分")
            
            return " | ".join(status_details)
            
        else:  # FRIENDLY or PROFESSIONAL
            if power_plugged:
                if percent >= 100:
                    return f"バッテリーは満充電です ({percent:.0f}%)"
                else:
                    return f"充電中です ({percent:.0f}%)"
            else:
                base_text = f"バッテリー残量は{percent:.0f}%です"
                if secsleft and secsleft > 0:
                    hours = secsleft // 3600
                    minutes = (secsleft % 3600) // 60
                    if hours > 0:
                        base_text += f"。あと約{hours}時間{minutes}分使用可能です"
                    else:
                        base_text += f"。あと約{minutes}分使用可能です"
                return base_text
    
    def _format_wifi_info(self, system_data: Dict[str, Any], style: PromptStyle) -> str:
        """Format WiFi information"""
        wifi_data = system_data.get('wifi')
        if not wifi_data:
            return ""
        
        is_connected = wifi_data.get('is_connected', False)
        ssid = wifi_data.get('ssid')
        signal_strength = wifi_data.get('signal_strength')
        signal_quality = wifi_data.get('signal_quality', 'unknown')
        channel = wifi_data.get('channel')
        frequency = wifi_data.get('frequency')
        security = wifi_data.get('security')
        link_speed = wifi_data.get('link_speed')
        
        if not is_connected or not ssid:
            if style == PromptStyle.CASUAL:
                return "📶❌ WiFiに接続されていません"
            else:
                return "WiFi: 未接続"
        
        # Format based on style
        if style == PromptStyle.CASUAL:
            wifi_emoji = "📶"
            quality_emoji = {
                'excellent': '🟢',
                'good': '🟡',
                'fair': '🟠',
                'poor': '🔴',
                'very_poor': '🔴',
                'unknown': '⚪'
            }.get(signal_quality, '⚪')
            
            base_text = f"{wifi_emoji} 「{ssid}」に接続中"
            
            if signal_strength is not None:
                base_text += f" {quality_emoji} {signal_strength}dBm"
            
            if channel:
                base_text += f" (ch.{channel})"
                
            return base_text
            
        elif style == PromptStyle.TECHNICAL:
            details = []
            details.append(f"SSID: {ssid}")
            
            if signal_strength is not None:
                details.append(f"信号強度: {signal_strength}dBm ({signal_quality})")
            
            if channel and frequency:
                details.append(f"チャンネル: {channel} ({frequency}GHz)")
            elif channel:
                details.append(f"チャンネル: {channel}")
            
            if security:
                details.append(f"セキュリティ: {security}")
            
            if link_speed:
                details.append(f"リンク速度: {link_speed}Mbps")
            
            return " | ".join(details)
            
        else:  # FRIENDLY or PROFESSIONAL
            base_text = f"WiFiネットワーク「{ssid}」に接続中です"
            
            # Add signal quality description
            quality_descriptions = {
                'excellent': '信号強度は非常に良好',
                'good': '信号強度は良好',
                'fair': '信号強度は普通',
                'poor': '信号強度は弱め',
                'very_poor': '信号強度は非常に弱い',
                'unknown': '信号強度は不明'
            }
            
            if signal_quality in quality_descriptions:
                base_text += f"。{quality_descriptions[signal_quality]}"
                if signal_strength is not None:
                    base_text += f"（{signal_strength}dBm）"
                base_text += "です"
            
            # Add additional info for professional style
            if style == PromptStyle.PROFESSIONAL:
                additional_info = []
                if channel:
                    additional_info.append(f"チャンネル{channel}")
                if frequency:
                    additional_info.append(f"{frequency}GHz帯")
                if link_speed:
                    additional_info.append(f"{link_speed}Mbps")
                
                if additional_info:
                    base_text += f"。{', '.join(additional_info)}で動作中です"
            
            return base_text
    
    def _format_running_apps_info(self, system_data: Dict[str, Any], style: PromptStyle) -> str:
        """Format running applications information"""
        apps_data = system_data.get('running_apps', [])
        if not apps_data:
            return ""
        
        # Limit to top apps to avoid overwhelming the model
        top_apps = apps_data[:8]  # Show top 8 apps
        
        if style == PromptStyle.CASUAL:
            if len(top_apps) == 0:
                return "🖥️ アプリが見つかりません"
            
            app_list = []
            for app in top_apps[:5]:  # Show top 5 for casual
                cpu = app.get('cpu_percent', 0)
                memory_mb = app.get('memory_mb', 0)
                name = app.get('name', 'Unknown')
                
                if cpu > 5:  # Only show apps using significant CPU
                    app_list.append(f"• {name} (CPU: {cpu:.1f}%)")
                elif memory_mb > 100:  # Or using significant memory
                    app_list.append(f"• {name} (メモリ: {memory_mb:.0f}MB)")
                else:
                    app_list.append(f"• {name}")
            
            if app_list:
                return f"🖥️ 実行中のアプリ:\n" + "\n".join(app_list[:3])
            else:
                return f"🖥️ {len(top_apps)}個のアプリが実行中"
                
        elif style == PromptStyle.TECHNICAL:
            details = []
            for app in top_apps:
                name = app.get('name', 'Unknown')
                cpu = app.get('cpu_percent', 0)
                memory_mb = app.get('memory_mb', 0)
                memory_percent = app.get('memory_percent', 0)
                pid = app.get('pid', 0)
                status = app.get('status', 'unknown')
                
                details.append(f"{name} (PID:{pid}): CPU {cpu:.1f}%, メモリ {memory_mb:.0f}MB ({memory_percent:.1f}%), {status}")
            
            return "実行中アプリケーション:\n" + "\n".join(details)
            
        else:  # FRIENDLY or PROFESSIONAL
            if len(top_apps) == 0:
                return "現在実行中のアプリケーションはありません"
            
            # Focus on resource-heavy apps
            heavy_apps = [app for app in top_apps if app.get('cpu_percent', 0) > 3 or app.get('memory_mb', 0) > 50]
            
            if heavy_apps:
                app_descriptions = []
                for app in heavy_apps[:4]:
                    name = app.get('name', 'Unknown')
                    cpu = app.get('cpu_percent', 0)
                    memory_mb = app.get('memory_mb', 0)
                    
                    if cpu > 10:
                        app_descriptions.append(f"{name}（CPU使用率 {cpu:.1f}%）")
                    elif memory_mb > 200:
                        app_descriptions.append(f"{name}（メモリ使用量 {memory_mb:.0f}MB）")
                    else:
                        app_descriptions.append(f"{name}")
                
                base_text = f"現在 {len(top_apps)}個のアプリケーションが実行中です"
                if app_descriptions:
                    base_text += f"。主要なアプリ: {', '.join(app_descriptions)}"
                
                return base_text
            else:
                return f"現在 {len(top_apps)}個のアプリケーションが実行中です（軽量な使用状況）"
    
    def _format_disk_details_info(self, system_data: Dict[str, Any], style: PromptStyle) -> str:
        """Format disk details information"""
        disk_data = system_data.get('disk_details', [])
        if not disk_data:
            return ""
        
        if style == PromptStyle.CASUAL:
            if len(disk_data) == 0:
                return "💾 ディスク情報が見つかりません"
            
            disk_list = []
            for disk in disk_data[:4]:  # Show top 4 disks
                label = disk.get('label') or disk.get('mountpoint', 'Unknown')
                total_gb = disk.get('total_gb', 0)
                used_gb = disk.get('used_gb', 0)
                percent = disk.get('percent', 0)
                is_removable = disk.get('is_removable', False)
                
                icon = "🔌" if is_removable else "💾"
                
                if total_gb > 1000:  # > 1TB
                    size_text = f"{total_gb/1000:.1f}TB"
                else:
                    size_text = f"{total_gb:.0f}GB"
                
                disk_list.append(f"{icon} {label}: {used_gb:.0f}GB/{size_text} ({percent:.0f}%)")
            
            return "💾 ディスク情報:\n" + "\n".join(disk_list)
            
        elif style == PromptStyle.TECHNICAL:
            details = []
            for disk in disk_data:
                device = disk.get('device', 'Unknown')
                mountpoint = disk.get('mountpoint', 'Unknown')
                fstype = disk.get('fstype', 'Unknown')
                total_gb = disk.get('total_gb', 0)
                used_gb = disk.get('used_gb', 0)
                free_gb = disk.get('free_gb', 0)
                percent = disk.get('percent', 0)
                is_system = disk.get('is_system', False)
                is_removable = disk.get('is_removable', False)
                
                disk_type = "システム" if is_system else ("外付け" if is_removable else "内蔵")
                
                details.append(f"{device} ({mountpoint}): {fstype}, {used_gb:.1f}GB/{total_gb:.1f}GB ({percent:.1f}%), 空き{free_gb:.1f}GB, {disk_type}")
            
            return "ディスク詳細情報:\n" + "\n".join(details)
            
        else:  # FRIENDLY or PROFESSIONAL
            if len(disk_data) == 0:
                return "ディスク情報を取得できませんでした"
            
            # Separate system and external disks
            system_disks = [d for d in disk_data if d.get('is_system', False)]
            external_disks = [d for d in disk_data if d.get('is_removable', False)]
            other_disks = [d for d in disk_data if not d.get('is_system', False) and not d.get('is_removable', False)]
            
            result_parts = []
            
            # System disks
            if system_disks:
                for disk in system_disks[:2]:  # Show top 2 system disks
                    label = disk.get('label') or 'システムディスク'
                    total_gb = disk.get('total_gb', 0)
                    used_gb = disk.get('used_gb', 0)
                    free_gb = disk.get('free_gb', 0)
                    percent = disk.get('percent', 0)
                    
                    if total_gb > 1000:
                        size_text = f"{total_gb/1000:.1f}TB"
                        used_text = f"{used_gb/1000:.1f}TB"
                        free_text = f"{free_gb/1000:.1f}TB"
                    else:
                        size_text = f"{total_gb:.0f}GB"
                        used_text = f"{used_gb:.0f}GB"
                        free_text = f"{free_gb:.0f}GB"
                    
                    result_parts.append(f"💾 {label}: {used_text}/{size_text}使用中 ({percent:.0f}%), 空き容量{free_text}")
            
            # External disks
            if external_disks:
                ext_names = []
                for disk in external_disks[:3]:  # Show top 3 external disks
                    label = disk.get('label') or '外付けディスク'
                    total_gb = disk.get('total_gb', 0)
                    percent = disk.get('percent', 0)
                    
                    if total_gb > 1000:
                        size_text = f"{total_gb/1000:.1f}TB"
                    else:
                        size_text = f"{total_gb:.0f}GB"
                    
                    ext_names.append(f"{label}({size_text}, {percent:.0f}%使用)")
                
                if ext_names:
                    result_parts.append(f"🔌 外付けディスク: {', '.join(ext_names)}")
            
            # Other disks
            if other_disks and not system_disks and not external_disks:
                for disk in other_disks[:2]:
                    label = disk.get('label') or disk.get('mountpoint', 'ディスク')
                    total_gb = disk.get('total_gb', 0)
                    percent = disk.get('percent', 0)
                    
                    if total_gb > 1000:
                        size_text = f"{total_gb/1000:.1f}TB"
                    else:
                        size_text = f"{total_gb:.0f}GB"
                    
                    result_parts.append(f"💿 {label}: {size_text} ({percent:.0f}%使用)")
            
            if result_parts:
                return "\n".join(result_parts)
            else:
                return f"{len(disk_data)}個のディスクが検出されました"
    
    def _format_dev_tools_info(self, system_data: Dict[str, Any], style: PromptStyle) -> str:
        """Format development tools information"""
        dev_tools_data = system_data.get('dev_tools', [])
        if not dev_tools_data:
            return ""
        
        installed_tools = [tool for tool in dev_tools_data if tool.get('is_installed', False)]
        not_installed_tools = [tool for tool in dev_tools_data if not tool.get('is_installed', False)]
        
        if style == PromptStyle.CASUAL:
            if not installed_tools:
                return "⚙️ 開発ツールが見つかりません"
            
            tool_list = []
            for tool in installed_tools[:5]:  # Show top 5 tools
                name = tool.get('name', 'Unknown')
                version = tool.get('version', '')
                is_running = tool.get('is_running', False)
                
                status_icon = "🟢" if is_running else "⚪"
                version_text = f" v{version}" if version else ""
                
                tool_list.append(f"{status_icon} {name}{version_text}")
            
            return "⚙️ 開発ツール:\n" + "\n".join(tool_list)
            
        elif style == PromptStyle.TECHNICAL:
            details = []
            for tool in dev_tools_data:
                name = tool.get('name', 'Unknown')
                version = tool.get('version', 'N/A')
                path = tool.get('path', 'N/A')
                is_installed = tool.get('is_installed', False)
                is_running = tool.get('is_running', False)
                additional_info = tool.get('additional_info', {})
                
                status = "インストール済み" if is_installed else "未インストール"
                if is_installed and is_running:
                    status += " (実行中)"
                
                detail_line = f"{name}: {version}, {status}, パス: {path}"
                
                # Add additional info
                if additional_info:
                    extra_info = []
                    for key, value in additional_info.items():
                        if key == 'user_name':
                            extra_info.append(f"Git User: {value}")
                        elif key == 'npm_version':
                            extra_info.append(f"npm: {value}")
                        elif key == 'pip_version':
                            extra_info.append(f"pip: {value}")
                    
                    if extra_info:
                        detail_line += f" ({', '.join(extra_info)})"
                
                details.append(detail_line)
            
            return "開発ツール詳細:\n" + "\n".join(details)
            
        else:  # FRIENDLY or PROFESSIONAL
            if not installed_tools:
                return "開発ツールがインストールされていません"
            
            # Group by status
            running_tools = [t for t in installed_tools if t.get('is_running', False)]
            installed_only = [t for t in installed_tools if not t.get('is_running', False)]
            
            result_parts = []
            
            # Installed and running tools
            if running_tools:
                running_names = []
                for tool in running_tools[:3]:
                    name = tool.get('name', 'Unknown')
                    version = tool.get('version', '')
                    version_text = f" v{version}" if version else ""
                    running_names.append(f"{name}{version_text}")
                
                result_parts.append(f"🟢 実行中: {', '.join(running_names)}")
            
            # Installed but not running tools
            if installed_only:
                installed_names = []
                for tool in installed_only[:4]:
                    name = tool.get('name', 'Unknown')
                    version = tool.get('version', '')
                    version_text = f" v{version}" if version else ""
                    installed_names.append(f"{name}{version_text}")
                
                result_parts.append(f"⚪ インストール済み: {', '.join(installed_names)}")
            
            # Not installed tools (only show a few important ones)
            important_missing = []
            for tool in not_installed_tools:
                name = tool.get('name', '')
                if name in ['Xcode', 'Git', 'Homebrew', 'Docker']:
                    important_missing.append(name)
            
            if important_missing and len(important_missing) <= 2:
                result_parts.append(f"❌ 未インストール: {', '.join(important_missing)}")
            
            if result_parts:
                return "\n".join(result_parts)
            else:
                return f"{len(installed_tools)}個の開発ツールがインストール済みです"
    
    def _format_thermal_info(self, system_data: Dict[str, Any], style: PromptStyle) -> str:
        """Format thermal and fan information"""
        thermal_data = system_data.get('thermal_info')
        if not thermal_data:
            return ""
        
        cpu_temp = thermal_data.get('cpu_temperature')
        gpu_temp = thermal_data.get('gpu_temperature')
        fan_speeds = thermal_data.get('fan_speeds', [])
        thermal_state = thermal_data.get('thermal_state', 'unknown')
        power_metrics = thermal_data.get('power_metrics', {})
        
        if style == PromptStyle.CASUAL:
            if not cpu_temp and not gpu_temp and not fan_speeds:
                return "🌡️ 温度情報を取得できません"
            
            temp_parts = []
            if cpu_temp:
                temp_emoji = "🔥" if cpu_temp > 80 else "🌡️" if cpu_temp > 60 else "❄️"
                temp_parts.append(f"{temp_emoji} CPU: {cpu_temp:.0f}°C")
            
            if gpu_temp:
                temp_emoji = "🔥" if gpu_temp > 80 else "🌡️" if gpu_temp > 60 else "❄️"
                temp_parts.append(f"{temp_emoji} GPU: {gpu_temp:.0f}°C")
            
            if fan_speeds:
                fan_info = []
                for fan in fan_speeds[:2]:  # Show top 2 fans
                    name = fan.get('name', 'Fan')
                    rpm = fan.get('rpm', 0)
                    fan_info.append(f"💨 {name}: {rpm}rpm")
                temp_parts.extend(fan_info)
            
            if temp_parts:
                return "\n".join(temp_parts)
            else:
                return f"🌡️ システム温度: {thermal_state}"
                
        elif style == PromptStyle.TECHNICAL:
            details = []
            
            if cpu_temp:
                details.append(f"CPU温度: {cpu_temp:.1f}°C")
            if gpu_temp:
                details.append(f"GPU温度: {gpu_temp:.1f}°C")
            
            details.append(f"サーマル状態: {thermal_state}")
            
            if fan_speeds:
                fan_details = []
                for fan in fan_speeds:
                    name = fan.get('name', 'Unknown Fan')
                    rpm = fan.get('rpm', 0)
                    fan_details.append(f"{name}: {rpm}rpm")
                details.append(f"ファン: {', '.join(fan_details)}")
            
            if power_metrics and power_metrics.get('power_source'):
                details.append(f"電源: {power_metrics['power_source']}")
            
            return "サーマル情報: " + " | ".join(details)
            
        else:  # FRIENDLY or PROFESSIONAL
            if not cpu_temp and not gpu_temp and not fan_speeds:
                return "温度・ファン情報は利用できません（macOSでは管理者権限が必要な場合があります）"
            
            result_parts = []
            
            # Temperature info
            temp_info = []
            if cpu_temp:
                if cpu_temp > 85:
                    temp_status = "高温"
                    temp_icon = "🔥"
                elif cpu_temp > 70:
                    temp_status = "やや高温"
                    temp_icon = "🌡️"
                elif cpu_temp > 50:
                    temp_status = "正常"
                    temp_icon = "✅"
                else:
                    temp_status = "低温"
                    temp_icon = "❄️"
                
                temp_info.append(f"{temp_icon} CPU温度: {cpu_temp:.0f}°C ({temp_status})")
            
            if gpu_temp:
                if gpu_temp > 85:
                    temp_status = "高温"
                    temp_icon = "🔥"
                elif gpu_temp > 70:
                    temp_status = "やや高温"
                    temp_icon = "🌡️"
                else:
                    temp_status = "正常"
                    temp_icon = "✅"
                
                temp_info.append(f"{temp_icon} GPU温度: {gpu_temp:.0f}°C ({temp_status})")
            
            if temp_info:
                result_parts.extend(temp_info)
            
            # Fan info
            if fan_speeds:
                fan_info = []
                for fan in fan_speeds:
                    name = fan.get('name', 'ファン')
                    rpm = fan.get('rpm', 0)
                    
                    if rpm > 3000:
                        fan_status = "高速"
                        fan_icon = "💨"
                    elif rpm > 1500:
                        fan_status = "中速"
                        fan_icon = "🌀"
                    elif rpm > 500:
                        fan_status = "低速"
                        fan_icon = "💨"
                    else:
                        fan_status = "停止"
                        fan_icon = "⏸️"
                    
                    fan_info.append(f"{fan_icon} {name}: {rpm}rpm ({fan_status})")
                
                if fan_info:
                    result_parts.extend(fan_info)
            
            # Thermal state summary
            if thermal_state != "unknown":
                state_descriptions = {
                    'normal': '🟢 システム温度は正常です',
                    'warm': '🟡 システムがやや温かくなっています',
                    'hot': '🔴 システムが高温になっています',
                    'critical': '🚨 システムが危険な高温状態です'
                }
                
                if thermal_state in state_descriptions:
                    result_parts.append(state_descriptions[thermal_state])
            
            if result_parts:
                return "\n".join(result_parts)
            else:
                return "温度・ファン情報の詳細は取得できませんでした"
    
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
    generator = PromptGenerator()
    context = ConversationContext(preferred_style=style)
    
    return generator.generate_system_prompt(
        user_query="現在のシステムの状態を教えてください",
        system_data=system_data,
        context=context
    )


def create_performance_analysis_prompt(system_data: Dict[str, Any],
                                     performance_issues: List[str] = None) -> str:
    """Create a prompt for performance analysis"""
    generator = PromptGenerator()
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
    generator = PromptGenerator()
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
    
    generator = PromptGenerator()
    
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