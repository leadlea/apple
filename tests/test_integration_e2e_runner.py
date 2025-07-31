#!/usr/bin/env python3
"""
統合テストとE2Eテストの実行スクリプト
Task 8.2の実装を検証するためのテストランナー
"""
import pytest
import asyncio
import sys
import os
from pathlib import Path
import logging
import time
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IntegrationTestRunner:
    """統合テストとE2Eテストのランナー"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def run_all_tests(self):
        """全ての統合テストとE2Eテストを実行"""
        self.start_time = datetime.now()
        logger.info("=== 統合テストとE2Eテスト開始 ===")
        
        # テストスイートの定義
        test_suites = [
            {
                'name': 'PWA Browser Functionality Tests',
                'file': 'tests/test_pwa_browser_functionality.py',
                'description': 'PWA機能のブラウザテスト',
                'timeout': 60
            },
            {
                'name': 'WebSocket Integration Tests',
                'file': 'tests/test_websocket_integration.py',
                'description': 'WebSocket通信の統合テスト',
                'timeout': 120
            },
            {
                'name': 'E2E User Scenarios Tests',
                'file': 'tests/test_e2e_user_scenarios.py',
                'description': 'ユーザーシナリオ全体のE2Eテスト',
                'timeout': 180
            }
        ]
        
        # 各テストスイートを実行
        for suite in test_suites:
            logger.info(f"\n--- {suite['name']} ---")
            logger.info(f"説明: {suite['description']}")
            
            result = self.run_test_suite(suite)
            self.test_results[suite['name']] = result
            
            if result['success']:
                logger.info(f"✅ {suite['name']} - 成功")
            else:
                logger.error(f"❌ {suite['name']} - 失敗")
        
        self.end_time = datetime.now()
        self.print_summary()
        
        return self.get_overall_success()
    
    def run_test_suite(self, suite):
        """個別のテストスイートを実行"""
        test_file = suite['file']
        
        if not Path(test_file).exists():
            return {
                'success': False,
                'error': f"テストファイルが見つかりません: {test_file}",
                'duration': 0,
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0
            }
        
        start_time = time.time()
        
        try:
            # pytestを実行
            result = pytest.main([
                test_file,
                '-v',
                '--tb=short',
                '--timeout=60',  # 個別テストのタイムアウト
                '--disable-warnings',
                '--no-header'
            ])
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 結果の解析
            success = result == 0
            
            return {
                'success': success,
                'exit_code': result,
                'duration': duration,
                'error': None if success else f"pytest exit code: {result}"
            }
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                'success': False,
                'error': str(e),
                'duration': duration
            }
    
    def print_summary(self):
        """テスト結果のサマリーを出力"""
        logger.info("\n" + "="*60)
        logger.info("テスト実行結果サマリー")
        logger.info("="*60)
        
        total_duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"総実行時間: {total_duration:.2f}秒")
        
        success_count = 0
        total_count = len(self.test_results)
        
        for suite_name, result in self.test_results.items():
            status = "✅ 成功" if result['success'] else "❌ 失敗"
            duration = result.get('duration', 0)
            
            logger.info(f"\n{suite_name}:")
            logger.info(f"  状態: {status}")
            logger.info(f"  実行時間: {duration:.2f}秒")
            
            if not result['success'] and result.get('error'):
                logger.info(f"  エラー: {result['error']}")
            
            if result['success']:
                success_count += 1
        
        logger.info(f"\n総合結果: {success_count}/{total_count} テストスイートが成功")
        
        if success_count == total_count:
            logger.info("🎉 全てのテストが成功しました！")
        else:
            logger.error("⚠️  一部のテストが失敗しました")
    
    def get_overall_success(self):
        """全体的な成功状態を取得"""
        return all(result['success'] for result in self.test_results.values())


def run_specific_test_category(category):
    """特定のカテゴリのテストのみを実行"""
    test_files = {
        'pwa': 'tests/test_pwa_browser_functionality.py',
        'websocket': 'tests/test_websocket_integration.py',
        'e2e': 'tests/test_e2e_user_scenarios.py'
    }
    
    if category not in test_files:
        logger.error(f"不明なテストカテゴリ: {category}")
        logger.info(f"利用可能なカテゴリ: {', '.join(test_files.keys())}")
        return False
    
    test_file = test_files[category]
    logger.info(f"実行中: {category} テスト ({test_file})")
    
    result = pytest.main([
        test_file,
        '-v',
        '--tb=short',
        '--disable-warnings'
    ])
    
    return result == 0


def check_test_environment():
    """テスト環境の確認"""
    logger.info("テスト環境を確認中...")
    
    # 必要なディレクトリの確認
    required_dirs = ['backend', 'frontend', 'tests']
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            logger.error(f"必要なディレクトリが見つかりません: {dir_name}")
            return False
    
    # 必要なファイルの確認
    required_files = [
        'backend/websocket_server.py',
        'backend/system_monitor.py',
        'backend/elyza_model.py',
        'frontend/manifest.json',
        'frontend/sw.js',
        'frontend/index.html'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.warning("一部のファイルが見つかりません:")
        for file_path in missing_files:
            logger.warning(f"  - {file_path}")
        logger.warning("一部のテストがスキップされる可能性があります")
    
    # Pythonパッケージの確認
    required_packages = ['pytest', 'asyncio', 'websockets', 'fastapi']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error("必要なPythonパッケージが不足しています:")
        for package in missing_packages:
            logger.error(f"  - {package}")
        logger.error("pip install -r requirements.txt を実行してください")
        return False
    
    logger.info("✅ テスト環境の確認完了")
    return True


def main():
    """メイン関数"""
    if len(sys.argv) > 1:
        category = sys.argv[1]
        if category == 'check':
            success = check_test_environment()
            sys.exit(0 if success else 1)
        else:
            success = run_specific_test_category(category)
            sys.exit(0 if success else 1)
    
    # 環境確認
    if not check_test_environment():
        sys.exit(1)
    
    # 全テスト実行
    runner = IntegrationTestRunner()
    success = runner.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()