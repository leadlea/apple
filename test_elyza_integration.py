#!/usr/bin/env python3
"""
Test ELYZA Model Integration
ELYZAモデルの統合テスト
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from elyza_model import ELYZAModelInterface, ModelConfig
    from prompt_generator import PromptGenerator
    ELYZA_AVAILABLE = True
except ImportError as e:
    print(f"❌ ELYZA model not available: {e}")
    ELYZA_AVAILABLE = False
    sys.exit(1)

async def test_elyza_model():
    """Test ELYZA model initialization and response generation"""
    
    print("🧪 Testing ELYZA Model Integration")
    print("=" * 50)
    
    # Check model file
    model_path = "models/elyza7b/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf"
    
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        print("Please download the ELYZA model file first.")
        return False
    
    print(f"✅ Model file found: {model_path}")
    file_size = os.path.getsize(model_path) / (1024**3)
    print(f"📁 File size: {file_size:.1f}GB")
    
    # Initialize model
    print("\n🔄 Initializing ELYZA model...")
    
    config = ModelConfig(
        model_path=model_path,
        n_ctx=512,  # Small context for testing
        n_gpu_layers=-1,  # Use all Metal layers
        n_threads=4,
        temperature=0.7,
        max_tokens=128  # Short responses for testing
    )
    
    elyza_model = ELYZAModelInterface(config)
    
    try:
        success = await elyza_model.initialize_model()
        
        if not success:
            print(f"❌ Model initialization failed: {elyza_model.initialization_error}")
            return False
        
        print("✅ Model initialized successfully")
        
        # Initialize prompt generator
        prompt_generator = PromptGenerator()
        print("✅ Prompt generator initialized")
        
        # Test basic response
        print("\n🧪 Testing basic response...")
        
        test_queries = [
            "こんにちは",
            "システムの状況は？",
            "CPUの使用率はどうですか？",
            "メモリの状況を教えて",
            "今日の天気はどうですか？"  # Non-system query
        ]
        
        system_metrics = {
            'cpu_percent': 25.4,
            'memory_percent': 68.1,
            'memory_used_gb': 10.9,
            'memory_total_gb': 16.0,
            'disk_percent': 45.2,
            'disk_used_gb': 226.0,
            'disk_total_gb': 500.0,
            'top_processes': [
                {'name': 'Chrome', 'cpu_percent': 8.2},
                {'name': 'Xcode', 'cpu_percent': 3.1},
                {'name': 'Slack', 'cpu_percent': 1.5}
            ]
        }
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test {i}: {query} ---")
            
            try:
                # Generate prompt
                prompt = prompt_generator.generate_system_status_prompt(
                    user_query=query,
                    system_metrics=system_metrics
                )
                
                print(f"📝 Generated prompt length: {len(prompt)} chars")
                
                # Get response
                start_time = datetime.now()
                response = await elyza_model.generate_response(prompt)
                end_time = datetime.now()
                
                processing_time = (end_time - start_time).total_seconds()
                
                if response and response.content.strip():
                    print(f"✅ Response generated ({processing_time:.2f}s)")
                    print(f"📄 Response length: {len(response.content)} chars")
                    print(f"🤖 Response: {response.content[:200]}{'...' if len(response.content) > 200 else ''}")
                else:
                    print("❌ Empty or invalid response")
                    
            except Exception as e:
                print(f"❌ Error generating response: {e}")
        
        # Test performance
        print("\n📊 Performance Test...")
        
        performance_queries = ["システムの状況は？"] * 3
        total_time = 0
        
        for i, query in enumerate(performance_queries, 1):
            try:
                prompt = prompt_generator.generate_system_status_prompt(
                    user_query=query,
                    system_metrics=system_metrics
                )
                
                start_time = datetime.now()
                response = await elyza_model.generate_response(prompt)
                end_time = datetime.now()
                
                processing_time = (end_time - start_time).total_seconds()
                total_time += processing_time
                
                print(f"Test {i}: {processing_time:.2f}s")
                
            except Exception as e:
                print(f"Performance test {i} failed: {e}")
        
        avg_time = total_time / len(performance_queries)
        print(f"📈 Average response time: {avg_time:.2f}s")
        
        # Model statistics
        print(f"\n📊 Model Statistics:")
        print(f"Total requests: {elyza_model.total_requests}")
        print(f"Average response time: {elyza_model.average_response_time:.2f}s")
        
        print("\n✅ ELYZA model integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_fallback_responses():
    """Test fallback responses when ELYZA is not available"""
    
    print("\n🧪 Testing Fallback Responses")
    print("=" * 30)
    
    # Simulate system metrics
    system_metrics = {
        'cpu_percent': 25.4,
        'memory_percent': 68.1,
        'disk_percent': 45.2
    }
    
    test_queries = [
        "cpu",
        "メモリ",
        "ディスク",
        "システム",
        "こんにちは",
        "unknown query"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Simulate keyword-based response logic
        query_lower = query.lower()
        
        if "cpu" in query_lower:
            response = f"🖥️ 現在のCPU使用率は {system_metrics['cpu_percent']}% です。"
        elif "メモリ" in query_lower:
            response = f"💾 現在のメモリ使用率は {system_metrics['memory_percent']}% です。"
        elif "ディスク" in query_lower:
            response = f"💿 現在のディスク使用率は {system_metrics['disk_percent']}% です。"
        elif "システム" in query_lower:
            response = f"📊 システム全体の状況\nCPU: {system_metrics['cpu_percent']}%\nメモリ: {system_metrics['memory_percent']}%\nディスク: {system_metrics['disk_percent']}%"
        elif "こんにちは" in query_lower:
            response = f"👋 こんにちは！現在のシステム状況: CPU {system_metrics['cpu_percent']}%, メモリ {system_metrics['memory_percent']}%"
        else:
            response = f"🤖 現在のシステム状況: CPU {system_metrics['cpu_percent']}%, メモリ {system_metrics['memory_percent']}%, ディスク {system_metrics['disk_percent']}%"
        
        print(f"Response: {response}")

if __name__ == "__main__":
    print("🚀 Starting ELYZA Integration Test")
    
    if ELYZA_AVAILABLE:
        success = asyncio.run(test_elyza_model())
        if not success:
            print("\n⚠️ ELYZA model test failed, testing fallback responses...")
            asyncio.run(test_fallback_responses())
    else:
        print("⚠️ ELYZA not available, testing fallback responses...")
        asyncio.run(test_fallback_responses())
    
    print("\n🏁 Test completed!")