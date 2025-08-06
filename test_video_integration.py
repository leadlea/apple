#!/usr/bin/env python3
"""
Test Video Integration
動画統合機能のテスト
"""

import asyncio
import aiohttp
import os
from pathlib import Path

async def test_video_integration():
    """動画統合機能のテスト"""
    
    print("🎬 Testing Video Integration")
    print("=" * 50)
    
    # 1. 動画ファイルの存在確認
    video_path = Path("frontend/assets/videos/apple.mp4")
    print(f"📁 Video file check: {video_path}")
    
    if video_path.exists():
        file_size = video_path.stat().st_size
        print(f"✅ Video file found: {file_size:,} bytes ({file_size/1024/1024:.1f}MB)")
    else:
        print("❌ Video file not found")
        return False
    
    # 2. 静的ファイルアクセステスト
    test_urls = [
        "http://localhost:8002/static/assets/videos/apple.mp4",
        "http://localhost:8002/static/assets/video-styles.css",
        "http://localhost:8002/static/assets/video-component.js",
        "http://localhost:8002/fixed"
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in test_urls:
            try:
                async with session.head(url) as response:
                    if response.status == 200:
                        content_length = response.headers.get('content-length', 'unknown')
                        print(f"✅ {url} - Status: {response.status}, Size: {content_length}")
                    else:
                        print(f"❌ {url} - Status: {response.status}")
            except Exception as e:
                print(f"❌ {url} - Error: {e}")
    
    # 3. HTMLページの動画要素確認
    try:
        with open("fixed_index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
            
        checks = [
            ("video-styles.css", "video-styles.css" in html_content),
            ("video-component.js", "video-component.js" in html_content),
            ("profileVideo", "profileVideo" in html_content),
            ("apple.mp4", "apple.mp4" in html_content),
            ("VideoComponent", "VideoComponent" in html_content)
        ]
        
        print(f"\n📄 HTML Integration Check:")
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}: {'Found' if result else 'Not found'}")
            
    except Exception as e:
        print(f"❌ HTML check failed: {e}")
    
    # 4. CSS/JSファイルの内容確認
    css_path = Path("frontend/assets/video-styles.css")
    js_path = Path("frontend/assets/video-component.js")
    
    print(f"\n🎨 Asset Files Check:")
    
    if css_path.exists():
        css_size = css_path.stat().st_size
        print(f"✅ video-styles.css: {css_size:,} bytes")
        
        # マスク関連のCSSクラスをチェック
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
            
        mask_classes = [
            "video-mask-oval",
            "video-mask-circle", 
            "video-mask-portrait",
            "video-mask-face",
            "video-mask-custom"
        ]
        
        for mask_class in mask_classes:
            if mask_class in css_content:
                print(f"  ✅ {mask_class} class found")
            else:
                print(f"  ❌ {mask_class} class missing")
    else:
        print("❌ video-styles.css not found")
    
    if js_path.exists():
        js_size = js_path.stat().st_size
        print(f"✅ video-component.js: {js_size:,} bytes")
        
        # 重要な関数をチェック
        with open(js_path, "r", encoding="utf-8") as f:
            js_content = f.read()
            
        js_functions = [
            "class VideoComponent",
            "changeMask",
            "createVideoElement",
            "setupEventListeners"
        ]
        
        for func in js_functions:
            if func in js_content:
                print(f"  ✅ {func} found")
            else:
                print(f"  ❌ {func} missing")
    else:
        print("❌ video-component.js not found")
    
    print(f"\n🚀 Test completed!")
    print(f"📱 Access the app at: http://localhost:8002/fixed")
    print(f"🎭 The video should appear in the header with mask options")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_video_integration())