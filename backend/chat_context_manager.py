"""
Chat Context Manager for Mac Status PWA
Manages conversation history, session management, and personalization
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ChatMessage:
    """Individual chat message structure"""
    id: str
    timestamp: datetime
    role: str  # 'user' or 'assistant'
    content: str
    system_context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'role': self.role,
            'content': self.content,
            'system_context': self.system_context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            role=data['role'],
            content=data['content'],
            system_context=data.get('system_context')
        )


@dataclass
class UserPreferences:
    """User preferences for personalization"""
    language_style: str = "friendly"
    notification_level: str = "normal"
    preferred_metrics: List[str] = None
    response_personality: str = "helpful"
    
    def __post_init__(self):
        if self.preferred_metrics is None:
            self.preferred_metrics = ["cpu", "memory", "disk"]


class ChatContextManager:
    """Manages conversation history and user context"""
    
    def __init__(self, session_id: str = "default", data_dir: str = "data"):
        self.session_id = session_id
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.conversation_history: List[ChatMessage] = []
        self.user_preferences = UserPreferences()
        self.personalization_engine = PersonalizationEngine()
        self.session_file = self.data_dir / f"session_{session_id}.json"
        
        # Load existing session if available
        self._load_session()    

    def add_message(self, role: str, content: str, system_context: Optional[Dict[str, Any]] = None) -> str:
        """Add a message to conversation history"""
        import uuid
        
        # Learn from user messages
        if role == "user":
            self.personalization_engine.learn_user_pattern(content)
        
        message = ChatMessage(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            role=role,
            content=content,
            system_context=system_context
        )
        
        self.conversation_history.append(message)
        
        # Keep only last 50 messages to manage memory
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
        
        # Auto-save session
        self._save_session()
        
        return message.id
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[ChatMessage]:
        """Get conversation history with optional limit"""
        if limit is None:
            return self.conversation_history.copy()
        return self.conversation_history[-limit:] if limit > 0 else []
    
    def get_context_prompt(self, system_data: Dict[str, Any]) -> str:
        """Generate context-aware prompt including conversation history"""
        # Get recent conversation for context (last 10 messages)
        recent_messages = self.get_conversation_history(10)
        
        # Build conversation context
        conversation_context = ""
        if recent_messages:
            conversation_context = "\n過去の会話:\n"
            for msg in recent_messages[-5:]:  # Last 5 messages for context
                role_jp = "ユーザー" if msg.role == "user" else "アシスタント"
                conversation_context += f"{role_jp}: {msg.content}\n"
        
        # Build system context
        system_context = f"""
現在のシステム状態:
- CPU使用率: {system_data.get('cpu_percent', 'N/A')}%
- メモリ使用率: {system_data.get('memory_percent', 'N/A')}%
- ディスク使用率: {system_data.get('disk_percent', 'N/A')}%
"""
        
        # Combine contexts
        full_context = f"""あなたはMacのシステム状態を監視し、ユーザーと自然な日本語で会話するアシスタントです。
{system_context}
{conversation_context}

ユーザーの好み:
- 応答スタイル: {self.user_preferences.response_personality}
- 言語スタイル: {self.user_preferences.language_style}

上記の情報を参考に、ユーザーの質問に適切に答えてください。"""
        
        return full_context    

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        self._save_session()
    
    def update_user_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences"""
        if 'language_style' in preferences:
            self.user_preferences.language_style = preferences['language_style']
        if 'notification_level' in preferences:
            self.user_preferences.notification_level = preferences['notification_level']
        if 'preferred_metrics' in preferences:
            self.user_preferences.preferred_metrics = preferences['preferred_metrics']
        if 'response_personality' in preferences:
            self.user_preferences.response_personality = preferences['response_personality']
        
        self._save_session()
    
    def get_user_preferences(self) -> UserPreferences:
        """Get current user preferences"""
        return self.user_preferences
    
    def personalize_response(self, response: str, user_question: str) -> str:
        """Apply personalization to response"""
        question_type = self.personalization_engine.analyze_user_question(user_question)
        return self.personalization_engine.personalize_response(
            response, 
            self.user_preferences.response_personality,
            question_type
        )
    
    def get_user_insights(self) -> Dict[str, Any]:
        """Get insights about user behavior patterns"""
        frequent_questions = self.personalization_engine.get_most_frequent_questions()
        
        return {
            'most_frequent_questions': frequent_questions,
            'total_interactions': len(self.conversation_history),
            'user_patterns': {
                pattern_type: {
                    'frequency': pattern.frequency,
                    'last_asked': pattern.last_asked.isoformat(),
                    'preferred_detail_level': pattern.preferred_detail_level
                }
                for pattern_type, pattern in self.personalization_engine.user_patterns.items()
            },
            'preferences': asdict(self.user_preferences)
        }
    
    def adjust_detail_level(self, question_type: str, detail_level: str):
        """Adjust preferred detail level for a question type"""
        if question_type in self.personalization_engine.user_patterns:
            self.personalization_engine.user_patterns[question_type].preferred_detail_level = detail_level
            self._save_session()
    
    def get_personalized_greeting(self) -> str:
        """Get personalized greeting based on user patterns"""
        personality = self.user_preferences.response_personality
        style = self.personalization_engine.response_styles.get(personality, 
                                                               self.personalization_engine.response_styles['helpful'])
        
        # Add context based on frequent questions
        frequent_questions = self.personalization_engine.get_most_frequent_questions(3)
        
        greeting = style['greeting']
        
        if frequent_questions:
            if 'system_overview' in frequent_questions:
                greeting += " システム全体の状況を確認しましょうか？"
            elif 'cpu_usage' in frequent_questions:
                greeting += " CPU使用率をチェックしますか？"
            elif 'memory_usage' in frequent_questions:
                greeting += " メモリの状況を見てみましょうか？"
        
        return greeting
    
    def _save_session(self):
        """Save session data to file"""
        try:
            session_data = {
                'session_id': self.session_id,
                'conversation_history': [msg.to_dict() for msg in self.conversation_history],
                'user_preferences': asdict(self.user_preferences),
                'personalization_data': self.personalization_engine.to_dict(),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Error saving session: {e}")
    
    def _load_session(self):
        """Load session data from file"""
        try:
            if self.session_file.exists():
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Load conversation history
                if 'conversation_history' in session_data:
                    self.conversation_history = [
                        ChatMessage.from_dict(msg_data) 
                        for msg_data in session_data['conversation_history']
                    ]
                
                # Load user preferences
                if 'user_preferences' in session_data:
                    prefs_data = session_data['user_preferences']
                    self.user_preferences = UserPreferences(
                        language_style=prefs_data.get('language_style', 'friendly'),
                        notification_level=prefs_data.get('notification_level', 'normal'),
                        preferred_metrics=prefs_data.get('preferred_metrics', ["cpu", "memory", "disk"]),
                        response_personality=prefs_data.get('response_personality', 'helpful')
                    )
                
                # Load personalization data
                if 'personalization_data' in session_data:
                    self.personalization_engine.from_dict(session_data['personalization_data'])
                    
        except Exception as e:
            print(f"Error loading session: {e}")
            # Initialize with defaults if loading fails
            self.conversation_history = []
            self.user_preferences = UserPreferences()
            self.personalization_engine = PersonalizationEngine()
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return {
            'session_id': self.session_id,
            'message_count': len(self.conversation_history),
            'last_activity': self.conversation_history[-1].timestamp.isoformat() if self.conversation_history else None,
            'user_preferences': asdict(self.user_preferences)
        }


@dataclass
class UserPattern:
    """User interaction pattern for learning"""
    question_type: str
    frequency: int
    last_asked: datetime
    preferred_detail_level: str = "normal"  # brief, normal, detailed
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'question_type': self.question_type,
            'frequency': self.frequency,
            'last_asked': self.last_asked.isoformat(),
            'preferred_detail_level': self.preferred_detail_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPattern':
        return cls(
            question_type=data['question_type'],
            frequency=data['frequency'],
            last_asked=datetime.fromisoformat(data['last_asked']),
            preferred_detail_level=data.get('preferred_detail_level', 'normal')
        )


class PersonalizationEngine:
    """Handles user behavior learning and response personalization"""
    
    def __init__(self):
        self.user_patterns: Dict[str, UserPattern] = {}
        self.response_styles = {
            'helpful': {
                'greeting': 'こんにちは！何かお手伝いできることはありますか？',
                'system_info_prefix': 'システム状態をお知らせします：',
                'tone': 'friendly'
            },
            'technical': {
                'greeting': 'システム監視データを確認します。',
                'system_info_prefix': 'システムメトリクス：',
                'tone': 'professional'
            },
            'casual': {
                'greeting': 'やあ！調子はどう？',
                'system_info_prefix': 'システムの様子はこんな感じだよ：',
                'tone': 'informal'
            }
        }
    
    def analyze_user_question(self, question: str) -> str:
        """Analyze user question to determine type"""
        question_lower = question.lower()
        
        # Define question patterns
        patterns = {
            'cpu_usage': ['cpu', 'プロセッサ', '処理能力', 'cpu使用率'],
            'memory_usage': ['メモリ', 'ram', 'memory', 'メモリ使用率'],
            'disk_usage': ['ディスク', 'disk', 'storage', 'ストレージ', 'ディスク使用率'],
            'process_info': ['プロセス', 'process', 'アプリ', 'application', '実行中'],
            'system_overview': ['システム', 'system', '全体', '状態', 'ステータス', '概要'],
            'performance': ['パフォーマンス', 'performance', '速度', '重い', '遅い'],
            'general_chat': ['こんにちは', 'hello', 'ありがとう', 'thank', 'どう', 'how']
        }
        
        for question_type, keywords in patterns.items():
            if any(keyword in question_lower for keyword in keywords):
                return question_type
        
        return 'general_chat'
    
    def learn_user_pattern(self, question: str):
        """Learn from user question patterns"""
        question_type = self.analyze_user_question(question)
        
        if question_type in self.user_patterns:
            # Update existing pattern
            pattern = self.user_patterns[question_type]
            pattern.frequency += 1
            pattern.last_asked = datetime.now()
        else:
            # Create new pattern
            self.user_patterns[question_type] = UserPattern(
                question_type=question_type,
                frequency=1,
                last_asked=datetime.now()
            )
    
    def get_preferred_detail_level(self, question_type: str) -> str:
        """Get user's preferred detail level for question type"""
        if question_type in self.user_patterns:
            return self.user_patterns[question_type].preferred_detail_level
        return "normal"
    
    def get_most_frequent_questions(self, limit: int = 5) -> List[str]:
        """Get most frequently asked question types"""
        sorted_patterns = sorted(
            self.user_patterns.items(),
            key=lambda x: x[1].frequency,
            reverse=True
        )
        return [pattern[0] for pattern in sorted_patterns[:limit]]
    
    def personalize_response(self, response: str, personality: str, question_type: str) -> str:
        """Personalize response based on user preferences"""
        if personality not in self.response_styles:
            personality = 'helpful'
        
        style = self.response_styles[personality]
        detail_level = self.get_preferred_detail_level(question_type)
        
        # Adjust response based on detail level
        if detail_level == "brief":
            # Make response more concise
            lines = response.split('\n')
            # Keep only essential information
            essential_lines = [line for line in lines if any(
                keyword in line.lower() for keyword in 
                ['cpu', 'メモリ', 'ディスク', '%', 'gb', 'mb']
            )]
            if essential_lines:
                response = '\n'.join(essential_lines[:3])  # Max 3 lines
        elif detail_level == "detailed":
            # Add more context and explanation
            if question_type == "cpu_usage":
                response += "\n\nCPU使用率が高い場合は、重いアプリケーションを終了することを検討してください。"
            elif question_type == "memory_usage":
                response += "\n\nメモリ使用率が80%を超える場合は、不要なアプリケーションを終了することをお勧めします。"
        
        # Apply tone adjustments
        if style['tone'] == 'informal':
            response = response.replace('です', 'だよ').replace('ます', 'るよ')
        elif style['tone'] == 'professional':
            response = response.replace('！', '。').replace('？', 'でしょうか。')
        
        return response
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'user_patterns': {k: v.to_dict() for k, v in self.user_patterns.items()}
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Load from dictionary"""
        if 'user_patterns' in data:
            self.user_patterns = {
                k: UserPattern.from_dict(v) 
                for k, v in data['user_patterns'].items()
            }