"""
ELYZA Model Interface for Mac Status PWA
Provides integration with ELYZA-japanese-Llama-2-7b model using llama-cpp-python
"""
import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import json

# Import error handling
from error_handler import (
    handle_model_error, 
    execute_with_fallback, 
    ErrorCategory, 
    global_fallback_manager,
    error_handler_decorator
)

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None
    logging.warning("llama-cpp-python not installed. Model functionality will be disabled.")


@dataclass
class ModelConfig:
    """Configuration for ELYZA model"""
    model_path: str
    n_ctx: int = 2048
    n_gpu_layers: int = -1  # Use all GPU layers on M1
    n_threads: int = 0  # Auto-detect
    verbose: bool = False
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    max_tokens: int = 512


@dataclass
class ModelResponse:
    """Response from ELYZA model"""
    content: str
    timestamp: datetime
    processing_time_ms: float
    token_count: int
    model_info: Dict[str, Any]


class ELYZAModelError(Exception):
    """Custom exception for ELYZA model errors"""
    pass


class ELYZAModelInterface:
    """
    Interface for ELYZA-japanese-Llama-2-7b model
    Optimized for M1 chip performance with proper error handling
    """
    
    def __init__(self, config: ModelConfig):
        """
        Initialize ELYZA model interface
        
        Args:
            config: Model configuration
        """
        self.config = config
        self.llm: Optional[Llama] = None
        self.is_initialized = False
        self.initialization_error: Optional[str] = None
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.total_requests = 0
        self.total_processing_time = 0.0
        self.average_response_time = 0.0
        
    async def initialize_model(self) -> bool:
        """
        Initialize the ELYZA model with M1 optimizations
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if self.is_initialized:
            return True
            
        if Llama is None:
            self.initialization_error = "llama-cpp-python not installed"
            error_info = handle_model_error(
                Exception(self.initialization_error),
                {'component': 'model_initialization', 'step': 'dependency_check'}
            )
            self.logger.error(f"[{error_info.error_id}] {self.initialization_error}")
            return False
            
        try:
            # Check if model file exists
            if not os.path.exists(self.config.model_path):
                self.initialization_error = f"Model file not found: {self.config.model_path}"
                error_info = handle_model_error(
                    FileNotFoundError(self.initialization_error),
                    {'component': 'model_initialization', 'model_path': self.config.model_path}
                )
                self.logger.error(f"[{error_info.error_id}] {self.initialization_error}")
                return False
            
            self.logger.info(f"Initializing ELYZA model from {self.config.model_path}")
            
            # Get M1-specific batch size if available
            batch_size = 512  # Default
            try:
                from m1_optimization import M1Optimizer
                optimizer = M1Optimizer()
                batch_size = optimizer.system_info.recommended_batch_size
            except ImportError:
                pass
            
            # Initialize model with M1 optimizations
            self.llm = Llama(
                model_path=self.config.model_path,
                n_ctx=self.config.n_ctx,
                n_gpu_layers=self.config.n_gpu_layers,  # Use Metal on M1
                n_threads=self.config.n_threads,
                verbose=self.config.verbose,
                # M1 specific optimizations
                use_mmap=True,
                use_mlock=False,  # Don't lock memory on macOS
                n_batch=batch_size,  # Optimal batch size for M1
                # Additional M1 optimizations
                rope_scaling_type=1,  # Linear scaling for better performance
                rope_freq_base=10000.0,  # Standard frequency base
            )
            
            self.is_initialized = True
            self.logger.info("ELYZA model initialized successfully")
            
            # Test the model with a simple prompt
            test_response = await self._generate_response("こんにちは", max_tokens=10)
            if test_response:
                self.logger.info("Model test successful")
                return True
            else:
                self.initialization_error = "Model test failed"
                error_info = handle_model_error(
                    Exception(self.initialization_error),
                    {'component': 'model_initialization', 'step': 'model_test'}
                )
                self.logger.error(f"[{error_info.error_id}] {self.initialization_error}")
                return False
                
        except Exception as e:
            self.initialization_error = f"Model initialization failed: {str(e)}"
            error_info = handle_model_error(
                e, 
                {'component': 'model_initialization', 'model_path': self.config.model_path}
            )
            self.logger.error(f"[{error_info.error_id}] {self.initialization_error}", exc_info=True)
            self.is_initialized = False
            return False
    
    async def generate_system_response(self, user_message: str, system_data: Dict[str, Any], 
                                     conversation_history: List[Dict[str, str]] = None) -> Optional[ModelResponse]:
        """
        Generate response based on user message and system data with optimization
        
        Args:
            user_message: User's input message
            system_data: Current system status data
            conversation_history: Previous conversation messages
            
        Returns:
            ModelResponse object or None if generation failed
        """
        if not self.is_initialized:
            error_info = handle_model_error(
                Exception("Model not initialized"),
                {'component': 'response_generation', 'user_message': user_message[:50]}
            )
            self.logger.error(f"[{error_info.error_id}] Model not initialized")
            return None
        
        # フォールバック機能付きで応答生成を実行
        async def primary_generation():
            # Try to use ResponseOptimizer if available
            try:
                from response_optimizer import ResponseOptimizer, OptimizationStrategy
                
                # Create optimizer with 5-second timeout
                optimizer = ResponseOptimizer()
                
                # Generate optimized response
                response, metrics = await optimizer.generate_optimized_response(
                    model_interface=self,
                    user_message=user_message,
                    system_data=system_data,
                    conversation_history=conversation_history,
                    strategy=OptimizationStrategy.BALANCED
                )
                
                # Log performance metrics
                if metrics.total_time_ms > 5000:
                    self.logger.warning(f"Response time exceeded 5s: {metrics.total_time_ms:.1f}ms")
                else:
                    self.logger.info(f"Optimized response generated in {metrics.total_time_ms:.1f}ms")
                
                return response
                
            except ImportError:
                # Fallback to direct generation if optimizer not available
                return await self._generate_direct_response(user_message, system_data, conversation_history)
        
        async def fallback_generation():
            # フォールバック応答を生成
            fallback_content = global_fallback_manager.get_fallback_chat_response(user_message)
            return ModelResponse(
                content=fallback_content,
                timestamp=datetime.now(),
                processing_time_ms=0.0,
                token_count=len(fallback_content.split()),
                model_info={'fallback': True, 'reason': 'primary_generation_failed'}
            )
        
        try:
            return await execute_with_fallback(
                primary_func=primary_generation,
                fallback_func=fallback_generation,
                error_category=ErrorCategory.MODEL_ERROR,
                context={'user_message': user_message[:50], 'component': 'response_generation'}
            )
        except Exception as e:
            error_info = handle_model_error(
                e, 
                {'component': 'response_generation', 'user_message': user_message[:50]}
            )
            self.logger.error(f"[{error_info.error_id}] Response generation failed: {str(e)}", exc_info=True)
            return None
    
    async def _generate_direct_response(self, user_message: str, system_data: Dict[str, Any], 
                                      conversation_history: List[Dict[str, str]] = None) -> Optional[ModelResponse]:
        """
        Direct response generation (fallback method)
        """
        # Create system-aware prompt
        prompt = self._create_system_prompt(user_message, system_data, conversation_history)
        
        # Generate response
        start_time = asyncio.get_event_loop().time()
        response_text = await self._generate_response(prompt, max_tokens=self.config.max_tokens)
        end_time = asyncio.get_event_loop().time()
        
        if response_text is None:
            return None
        
        processing_time_ms = (end_time - start_time) * 1000
        
        # Update performance tracking
        self.total_requests += 1
        self.total_processing_time += processing_time_ms
        self.average_response_time = self.total_processing_time / self.total_requests
        
        # Create response object
        response = ModelResponse(
            content=response_text.strip(),
            timestamp=datetime.now(),
            processing_time_ms=processing_time_ms,
            token_count=len(response_text.split()),  # Approximate token count
            model_info={
                'model_path': self.config.model_path,
                'temperature': self.config.temperature,
                'max_tokens': self.config.max_tokens
            }
        )
        
        self.logger.info(f"Generated response in {processing_time_ms:.1f}ms")
        return response
    
    async def _generate_response(self, prompt: str, max_tokens: int = None) -> Optional[str]:
        """
        Generate response from model
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or None if failed
        """
        if not self.llm:
            return None
            
        try:
            # Run model inference in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def _run_inference():
                return self.llm(
                    prompt,
                    max_tokens=max_tokens or self.config.max_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    top_k=self.config.top_k,
                    repeat_penalty=self.config.repeat_penalty,
                    stop=["</s>", "\n\n", "Human:", "ユーザー:"],
                    echo=False
                )
            
            # Run inference with timeout
            result = await asyncio.wait_for(
                loop.run_in_executor(None, _run_inference),
                timeout=10.0  # 10 second timeout
            )
            
            if result and 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['text']
            else:
                self.logger.warning("No valid response from model")
                return None
                
        except asyncio.TimeoutError:
            self.logger.error("Model inference timeout")
            return None
        except Exception as e:
            self.logger.error(f"Model inference error: {str(e)}")
            return None
    
    def _create_system_prompt(self, user_message: str, system_data: Dict[str, Any], 
                            conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Create system-aware prompt for the model using JapanesePromptGenerator
        
        Args:
            user_message: User's input message
            system_data: Current system status
            conversation_history: Previous messages
            
        Returns:
            Formatted prompt string
        """
        try:
            # Import here to avoid circular imports
            from prompt_generator import JapanesePromptGenerator, ConversationContext
            
            # Create prompt generator
            generator = JapanesePromptGenerator()
            
            # Create conversation context
            context = ConversationContext(
                conversation_history=conversation_history or [],
                preferred_style=generator._determine_prompt_style(user_message, ConversationContext())
            )
            
            # Generate prompt using the advanced system
            return generator.generate_system_prompt(
                user_query=user_message,
                system_data=system_data,
                context=context
            )
            
        except ImportError:
            # Fallback to simple prompt if prompt_generator is not available
            return self._create_simple_system_prompt(user_message, system_data, conversation_history)
    
    def _create_simple_system_prompt(self, user_message: str, system_data: Dict[str, Any], 
                                   conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Fallback simple prompt creation (original implementation)
        """
        # System information summary
        system_summary = self._format_system_data(system_data)
        
        # Conversation context
        context = ""
        if conversation_history:
            context = "\n".join([
                f"{'ユーザー' if msg['role'] == 'user' else 'アシスタント'}: {msg['content']}"
                for msg in conversation_history[-5:]  # Last 5 messages
            ])
        
        # Create prompt
        prompt = f"""あなたはMacのシステム状態を監視し、ユーザーと自然な日本語で会話するアシスタントです。
以下の現在のシステム情報を参考にして、ユーザーの質問に答えてください。

現在のシステム状態:
{system_summary}

{f"会話履歴:\n{context}\n" if context else ""}

ユーザー: {user_message}
アシスタント: """
        
        return prompt
    
    def _format_system_data(self, system_data: Dict[str, Any]) -> str:
        """
        Format system data for prompt inclusion
        
        Args:
            system_data: System status data
            
        Returns:
            Formatted system information string
        """
        try:
            formatted = []
            
            # CPU information
            if 'cpu_percent' in system_data:
                formatted.append(f"CPU使用率: {system_data['cpu_percent']:.1f}%")
            
            # Memory information
            if 'memory_percent' in system_data:
                formatted.append(f"メモリ使用率: {system_data['memory_percent']:.1f}%")
                
            if 'memory_used' in system_data and 'memory_total' in system_data:
                used_gb = system_data['memory_used'] / (1024**3)
                total_gb = system_data['memory_total'] / (1024**3)
                formatted.append(f"メモリ使用量: {used_gb:.1f}GB / {total_gb:.1f}GB")
            
            # Disk information
            if 'disk_percent' in system_data:
                formatted.append(f"ディスク使用率: {system_data['disk_percent']:.1f}%")
            
            # Top processes
            if 'top_processes' in system_data and system_data['top_processes']:
                top_proc = system_data['top_processes'][0]
                formatted.append(f"最もCPUを使用しているプロセス: {top_proc.get('name', 'Unknown')} ({top_proc.get('cpu_percent', 0):.1f}%)")
            
            # Network information
            if 'network_io' in system_data:
                net = system_data['network_io']
                if isinstance(net, dict):
                    sent_mb = net.get('bytes_sent', 0) / (1024**2)
                    recv_mb = net.get('bytes_recv', 0) / (1024**2)
                    formatted.append(f"ネットワーク: 送信 {sent_mb:.1f}MB, 受信 {recv_mb:.1f}MB")
            
            return "\n".join(formatted) if formatted else "システム情報を取得できませんでした"
            
        except Exception as e:
            self.logger.error(f"Error formatting system data: {str(e)}")
            return "システム情報の処理中にエラーが発生しました"
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get current model status and performance metrics
        
        Returns:
            Dictionary with model status information
        """
        return {
            'is_initialized': self.is_initialized,
            'initialization_error': self.initialization_error,
            'model_path': self.config.model_path,
            'model_exists': os.path.exists(self.config.model_path) if self.config.model_path else False,
            'total_requests': self.total_requests,
            'average_response_time_ms': round(self.average_response_time, 2),
            'config': {
                'n_ctx': self.config.n_ctx,
                'n_gpu_layers': self.config.n_gpu_layers,
                'temperature': self.config.temperature,
                'max_tokens': self.config.max_tokens
            }
        }
    
    async def cleanup(self):
        """Clean up model resources"""
        if self.llm:
            # llama-cpp-python doesn't have explicit cleanup, but we can clear the reference
            self.llm = None
        self.is_initialized = False
        self.logger.info("Model resources cleaned up")


# Utility functions
def get_default_model_path() -> str:
    """Get default path for ELYZA model"""
    return os.path.join("models", "elyza7b", "ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf")


def create_default_config(model_path: str = None) -> ModelConfig:
    """
    Create default model configuration optimized for M1 Mac
    
    Args:
        model_path: Path to model file, uses default if None
        
    Returns:
        ModelConfig with M1 optimizations
    """
    if model_path is None:
        model_path = get_default_model_path()
    
    # Try to use M1 optimizations if available
    try:
        from m1_optimization import get_m1_optimized_config
        config, _ = get_m1_optimized_config(model_path)
        return config
    except ImportError:
        # Fallback to basic configuration
        return ModelConfig(
            model_path=model_path,
            n_ctx=2048,  # Context size
            n_gpu_layers=-1,  # Use all GPU layers (Metal on M1)
            n_threads=0,  # Auto-detect optimal thread count
            verbose=False,
            temperature=0.7,  # Balanced creativity
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1,
            max_tokens=512  # Reasonable response length
        )


async def test_model_interface():
    """Test function for ELYZAModelInterface"""
    print("Testing ELYZA Model Interface...")
    
    # Create configuration
    config = create_default_config()
    print(f"Model path: {config.model_path}")
    print(f"Model exists: {os.path.exists(config.model_path)}")
    
    # Create interface
    model = ELYZAModelInterface(config)
    
    # Test initialization
    print("Initializing model...")
    success = await model.initialize_model()
    
    if success:
        print("✅ Model initialized successfully")
        
        # Test system response generation
        test_system_data = {
            'cpu_percent': 25.5,
            'memory_percent': 60.2,
            'memory_used': 8 * 1024**3,
            'memory_total': 16 * 1024**3,
            'disk_percent': 45.0,
            'top_processes': [{'name': 'Google Chrome', 'cpu_percent': 15.2}]
        }
        
        print("Generating test response...")
        response = await model.generate_system_response(
            "現在のシステム状態を教えて",
            test_system_data
        )
        
        if response:
            print(f"✅ Response generated in {response.processing_time_ms:.1f}ms")
            print(f"Response: {response.content[:100]}...")
        else:
            print("❌ Failed to generate response")
        
        # Show model status
        status = model.get_model_status()
        print(f"Model status: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # Cleanup
        await model.cleanup()
        
    else:
        print(f"❌ Model initialization failed: {model.initialization_error}")
        
        # Show status even if failed
        status = model.get_model_status()
        print(f"Model status: {json.dumps(status, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run test
    asyncio.run(test_model_interface())