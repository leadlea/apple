#!/usr/bin/env python3
"""
Test script to verify PWA functionality implementation
Tests manifest.json, service worker, and icon files
"""

import json
import os
import sys
from pathlib import Path

def test_manifest_json():
    """Test that manifest.json exists and has required fields"""
    print("Testing manifest.json...")
    
    manifest_path = Path('frontend/manifest.json')
    if not manifest_path.exists():
        print("❌ manifest.json not found")
        return False
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        required_fields = ['name', 'short_name', 'start_url', 'display', 'icons']
        missing_fields = [field for field in required_fields if field not in manifest]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        # Check icons
        if not manifest['icons'] or len(manifest['icons']) == 0:
            print("❌ No icons defined in manifest")
            return False
        
        # Check shortcuts
        if 'shortcuts' in manifest and len(manifest['shortcuts']) > 0:
            print("✅ PWA shortcuts configured")
        
        print("✅ manifest.json is valid")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in manifest.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading manifest.json: {e}")
        return False

def test_service_worker():
    """Test that service worker exists and has basic functionality"""
    print("\nTesting service worker...")
    
    sw_path = Path('frontend/sw.js')
    if not sw_path.exists():
        print("❌ sw.js not found")
        return False
    
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            sw_content = f.read()
        
        # Check for essential service worker features
        required_features = [
            'addEventListener(\'install\'',
            'addEventListener(\'fetch\'',
            'addEventListener(\'activate\'',
            'caches.open',
            'cache.addAll'
        ]
        
        missing_features = []
        for feature in required_features:
            if feature not in sw_content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing service worker features: {missing_features}")
            return False
        
        # Check for offline functionality
        if 'offline' in sw_content.lower():
            print("✅ Offline functionality implemented")
        
        # Check for caching strategies
        if 'networkFirstStrategy' in sw_content or 'cacheFirstStrategy' in sw_content:
            print("✅ Advanced caching strategies implemented")
        
        print("✅ Service worker is properly implemented")
        return True
        
    except Exception as e:
        print(f"❌ Error reading service worker: {e}")
        return False

def test_icons():
    """Test that all required icons exist"""
    print("\nTesting PWA icons...")
    
    icons_dir = Path('frontend/icons')
    if not icons_dir.exists():
        print("❌ Icons directory not found")
        return False
    
    # Required icon sizes
    required_icons = [
        'icon-72x72.png',
        'icon-96x96.png',
        'icon-128x128.png',
        'icon-144x144.png',
        'icon-152x152.png',
        'icon-192x192.png',
        'icon-384x384.png',
        'icon-512x512.png',
        'icon-maskable-192x192.png',
        'icon-maskable-512x512.png',
        'shortcut-status.png',
        'shortcut-chat.png'
    ]
    
    missing_icons = []
    for icon in required_icons:
        icon_path = icons_dir / icon
        if not icon_path.exists():
            missing_icons.append(icon)
    
    if missing_icons:
        print(f"❌ Missing icons: {missing_icons}")
        return False
    
    print(f"✅ All {len(required_icons)} icons are present")
    return True

def test_pwa_javascript():
    """Test that PWA JavaScript functionality is implemented"""
    print("\nTesting PWA JavaScript...")
    
    app_js_path = Path('frontend/app.js')
    if not app_js_path.exists():
        print("❌ app.js not found")
        return False
    
    try:
        with open(app_js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Check for PWA features
        pwa_features = [
            'PWAManager',
            'beforeinstallprompt',
            'appinstalled',
            'showInstallPrompt',
            'registerServiceWorker'
        ]
        
        missing_features = []
        for feature in pwa_features:
            if feature not in js_content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing PWA JavaScript features: {missing_features}")
            return False
        
        print("✅ PWA JavaScript functionality is implemented")
        return True
        
    except Exception as e:
        print(f"❌ Error reading app.js: {e}")
        return False

def test_pwa_styles():
    """Test that PWA styles are implemented"""
    print("\nTesting PWA styles...")
    
    styles_path = Path('frontend/styles.css')
    if not styles_path.exists():
        print("❌ styles.css not found")
        return False
    
    try:
        with open(styles_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # Check for PWA-specific styles
        pwa_styles = [
            '.install-button',
            '.offline-indicator',
            '.pwa-notification',
            '.update-notification',
            '@media (display-mode: standalone)'
        ]
        
        missing_styles = []
        for style in pwa_styles:
            if style not in css_content:
                missing_styles.append(style)
        
        if missing_styles:
            print(f"❌ Missing PWA styles: {missing_styles}")
            return False
        
        print("✅ PWA styles are implemented")
        return True
        
    except Exception as e:
        print(f"❌ Error reading styles.css: {e}")
        return False

def test_html_pwa_integration():
    """Test that HTML has proper PWA integration"""
    print("\nTesting HTML PWA integration...")
    
    html_path = Path('frontend/index.html')
    if not html_path.exists():
        print("❌ index.html not found")
        return False
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Check for PWA meta tags and links
        pwa_elements = [
            'rel="manifest"',
            'name="theme-color"',
            'name="apple-mobile-web-app-capable"',
            'rel="apple-touch-icon"',
            'serviceWorker.register'
        ]
        
        missing_elements = []
        for element in pwa_elements:
            if element not in html_content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing HTML PWA elements: {missing_elements}")
            return False
        
        print("✅ HTML PWA integration is complete")
        return True
        
    except Exception as e:
        print(f"❌ Error reading index.html: {e}")
        return False

def main():
    """Run all PWA tests"""
    print("🔍 Testing PWA Implementation for Mac Status PWA")
    print("=" * 50)
    
    tests = [
        test_manifest_json,
        test_service_worker,
        test_icons,
        test_pwa_javascript,
        test_pwa_styles,
        test_html_pwa_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All PWA functionality tests passed!")
        print("\n✨ PWA Features Implemented:")
        print("   • Web App Manifest with shortcuts")
        print("   • Enhanced Service Worker with offline support")
        print("   • Install prompt and notifications")
        print("   • Complete icon set (including maskable icons)")
        print("   • Offline functionality and caching")
        print("   • Apple-style design integration")
        print("   • Responsive PWA components")
        return True
    else:
        print(f"❌ {total - passed} tests failed. Please fix the issues above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)