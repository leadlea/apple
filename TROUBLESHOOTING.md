# Mac Status PWA トラブルシューティングガイド 🔧

Mac Status PWAアプリケーションの一般的な問題の診断と解決方法を説明します。

## 🤖 チャット機能の問題

### 問題: チャット応答が同じ内容になる

**症状**:
- 異なる質問をしても同じような応答が返される
- 応答が質問内容と関連していない

**解決方法**:
1. **サーバーの再起動**:
   ```bash
   # 既存のサーバープロセスを停止
   pkill -f "python.*working_server"
   
   # サーバーを再起動
   python3 working_server.py
   ```

2. **WebSocket接続の確認**:
   ```bash
   # WebSocket接続テスト
   python3 simple_chat_test.py
   ```

3. **フォールバック機能の確認**:
   ```bash
   # チャット応答テスト
   python3 test_elyza_integration.py
   ```

### 問題: チャット応答が生成されない

**症状**:
```
WebSocket connection failed
Empty response from server
```

**解決方法**:
1. **サーバー状態の確認**:
   ```bash
   # サーバーが起動しているか確認
   lsof -i :8002
   
   # ヘルスチェック
   curl http://localhost:8002/health
   ```

2. **ログの確認**:
   ```bash
   # サーバーログを確認
   python3 working_server.py
   # エラーメッセージを確認
   ```

3. **WebSocket接続テスト**:
   ```bash
   # WebSocket接続の詳細テスト
   python3 test_chat_responses.py
   ```

## 🚨 クイック診断

### 包括的ヘルスチェック

問題を特定するために、この包括的なヘルスチェックを実行してください：

```bash
# デプロイメント検証の実行
python3 validate_deployment.py

# システム状態確認
python3 -c "
import sys, psutil, os
print(f'Python: {sys.version}')
print(f'Memory: {psutil.virtual_memory().available/1024**3:.1f}GB available')
print(f'Disk: {psutil.disk_usage(\".\").free/1024**3:.1f}GB free')
print(f'CPU: {psutil.cpu_count()} cores')
print(f'Platform: {sys.platform}')
"

# モデル読み込みテスト
python3 -c "
try:
    from backend.elyza_model import ELYZAModelInterface
    print('✓ Model interface import successful')
except Exception as e:
    print(f'✗ Model interface error: {e}')
"

# 各機能のテスト実行
python3 test_battery_functionality.py
python3 test_wifi_functionality.py
python3 test_running_apps_functionality.py
python3 test_disk_details_functionality.py
python3 test_dev_tools_functionality.py
python3 test_thermal_functionality.py
```

## 🔧 インストール問題

### 問題: Pythonバージョン非互換

**症状**:
```
ERROR: This package requires Python >=3.12
```

**解決方法**:
1. **Pythonバージョン確認**:
   ```bash
   python3 --version
   ```

2. **Python 3.12のインストール**:
   ```bash
   # macOS with Homebrew
   brew install python@3.12
   
   # PATHの更新
   export PATH="/opt/homebrew/bin:$PATH"
   
   # または公式サイトからダウンロード
   # https://www.python.org/downloads/
   ```

3. **正しいPythonで仮想環境作成**:
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   ```

### 問題: 仮想環境の問題

**症状**:
```
ModuleNotFoundError: No module named 'fastapi'
```

**解決方法**:
1. **仮想環境がアクティブか確認**:
   ```bash
   source venv/bin/activate
   # プロンプトに (venv) が表示されることを確認
   ```

2. **仮想環境の再作成**:
   ```bash
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **仮想環境の確認**:
   ```bash
   which python
   # venv/bin/python のパスが表示されることを確認
   
   # インストール済みパッケージ確認
   pip list | grep -E "fastapi|uvicorn|psutil|llama-cpp-python"
   ```

### 問題: 依存関係インストール失敗

**症状**:
```
ERROR: Failed building wheel for llama-cpp-python
```

**解決方法**:
1. **ビルド依存関係のインストール**:
   ```bash
   # macOS
   xcode-select --install
   brew install cmake
   
   # M1/M2 Macの場合、Metal対応を有効化
   export CMAKE_ARGS="-DLLAMA_METAL=on"
   ```

2. **問題のあるパッケージの強制再インストール**:
   ```bash
   pip uninstall llama-cpp-python
   CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
   
   # または、特定バージョンを指定
   pip install llama-cpp-python==0.2.11 --force-reinstall
   ```

3. **プリコンパイル済みホイールの使用**:
   ```bash
   pip install llama-cpp-python --prefer-binary
   
   # 依存関係の個別インストール
   pip install fastapi uvicorn psutil websockets
   ```

4. **Apple Silicon Mac特有の問題**:
   ```bash
   # Rosetta経由でのインストール（最後の手段）
   arch -x86_64 pip install llama-cpp-python
   ```

## 🤖 AIモデル問題

### 問題: モデルファイルが見つからない

**症状**:
```
FileNotFoundError: Model file not found: models/elyza7b/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf
```

**解決方法**:
1. **モデルのダウンロード**:
   ```bash
   # Hugging Faceから直接ダウンロード
   wget -O models/elyza7b/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf \
     "https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf/resolve/main/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf"
   
   # または、ブラウザで以下にアクセス:
   # https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf
   ```

2. **正しいディレクトリに配置**:
   ```bash
   mkdir -p models/elyza7b
   # ダウンロードしたファイルを models/elyza7b/ に移動
   mv ~/Downloads/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf models/elyza7b/
   ```

3. **ファイル配置の確認**:
   ```bash
   ls -la models/elyza7b/
   # .gguf ファイルが表示されることを確認
   
   # ファイルサイズ確認（約4GB）
   du -h models/elyza7b/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf
   ```

### Issue: Model Loading Memory Error

**Symptoms**:
```
RuntimeError: Not enough memory to load model
```

**Solutions**:
1. **Check available memory**:
   ```bash
   python -c "import psutil; print(f'Available: {psutil.virtual_memory().available/1024**3:.1f}GB')"
   ```

2. **Reduce model context size**:
   ```python
   # In config/production.py
   MODEL_CONFIG = {
       "n_ctx": 1024,  # Reduce from 2048
       "n_gpu_layers": 10,  # Reduce GPU layers
   }
   ```

3. **Close other applications**:
   ```bash
   # Check memory usage
   top -o mem
   # Close memory-intensive applications
   ```

4. **Use smaller model variant** (if available):
   - Look for Q2_K or Q3_K variants which use less memory

### Issue: Model Loading Too Slow

**Symptoms**:
- Model takes >60 seconds to load
- High CPU usage during startup

**Solutions**:
1. **Optimize for M1 Macs**:
   ```python
   # In config/production.py
   MODEL_CONFIG = {
       "n_gpu_layers": -1,  # Use all Metal layers
       "n_threads": 4,      # Optimize thread count
   }
   ```

2. **Check Metal support**:
   ```bash
   python -c "
   try:
       from llama_cpp import Llama
       print('Metal support available')
   except:
       print('Metal support not available')
   "
   ```

3. **Monitor during loading**:
   ```bash
   # In another terminal
   top -pid $(pgrep -f "python.*main.py")
   ```

## 🌐 WebSocket and Network Issues

### Issue: WebSocket Connection Failed

**Symptoms**:
```
WebSocket connection failed: Connection refused
```

**Solutions**:
1. **Check if server is running**:
   ```bash
   lsof -i :8000
   # Should show python process
   ```

2. **Test server manually**:
   ```bash
   curl http://localhost:8000/health
   # Should return {"status": "healthy"}
   ```

3. **Check firewall settings**:
   ```bash
   # macOS
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
   
   # Allow Python through firewall if needed
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
   ```

4. **Try different address**:
   - Use `127.0.0.1:8000` instead of `localhost:8000`
   - Check if IPv6 is causing issues

### Issue: Port Already in Use

**Symptoms**:
```
OSError: [Errno 48] Address already in use
```

**Solutions**:
1. **Find process using port**:
   ```bash
   lsof -ti:8000
   ```

2. **Kill the process**:
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

3. **Use different port**:
   ```python
   # In config/production.py
   SERVER_CONFIG = {
       "port": 8001,  # Change port
   }
   ```

### Issue: CORS Errors

**Symptoms**:
```
Access to WebSocket blocked by CORS policy
```

**Solutions**:
1. **Check CORS configuration**:
   ```python
   # In config/security.py
   CORS_ORIGINS = [
       "http://localhost:8000",
       "http://127.0.0.1:8000",
   ]
   ```

2. **Access via correct origin**:
   - Use the same address as configured in CORS

## 📱 PWA Issues

### Issue: PWA Not Installing

**Symptoms**:
- No install prompt appears
- "Add to Home Screen" not available

**Solutions**:
1. **Check PWA requirements**:
   ```bash
   # Verify manifest.json
   curl http://localhost:8000/manifest.json
   
   # Check service worker
   curl http://localhost:8000/sw.js
   ```

2. **Use HTTPS or localhost**:
   - PWAs require secure context
   - `localhost` is considered secure

3. **Check browser support**:
   - Use Chrome, Safari, or Edge
   - Enable PWA features in browser settings

4. **Clear browser cache**:
   ```bash
   # Chrome DevTools > Application > Storage > Clear storage
   ```

### Issue: Service Worker Not Registering

**Symptoms**:
```
Failed to register service worker: SecurityError
```

**Solutions**:
1. **Check service worker file**:
   ```bash
   curl http://localhost:8000/sw.js
   # Should return service worker code
   ```

2. **Verify HTTPS/localhost**:
   - Service workers require secure context

3. **Check browser console**:
   - Open DevTools > Console
   - Look for service worker errors

### Issue: Icons Not Loading

**Symptoms**:
- PWA shows default browser icon
- Missing icons in manifest

**Solutions**:
1. **Verify icon files**:
   ```bash
   ls -la frontend/icons/
   # Should show various icon sizes
   ```

2. **Generate missing icons**:
   ```bash
   python create_pwa_icons.py
   ```

3. **Check manifest.json**:
   ```bash
   python -c "
   import json
   with open('frontend/manifest.json') as f:
       manifest = json.load(f)
       for icon in manifest['icons']:
           print(f'{icon[\"src\"]}: {icon[\"sizes\"]}')
   "
   ```

## 🎨 UI and Design Issues

### Issue: Apple Design Not Loading

**Symptoms**:
- Interface looks generic
- Missing Apple-style elements

**Solutions**:
1. **Check CSS loading**:
   ```bash
   curl http://localhost:8000/styles.css
   # Should return CSS content
   ```

2. **Verify font loading**:
   - Check if SF Pro fonts are available
   - Fallback fonts should work

3. **Clear browser cache**:
   - Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R

### Issue: Responsive Design Problems

**Symptoms**:
- Layout broken on mobile
- Elements overlapping

**Solutions**:
1. **Check viewport meta tag**:
   ```html
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   ```

2. **Test responsive design**:
   - Use browser DevTools device emulation
   - Test on actual mobile devices

3. **Check CSS media queries**:
   ```css
   @media (max-width: 768px) {
       /* Mobile styles */
   }
   ```

## 🔒 Security Issues

### Issue: CSP Violations

**Symptoms**:
```
Content Security Policy: The page's settings blocked the loading of a resource
```

**Solutions**:
1. **Check CSP configuration**:
   ```python
   # In config/security.py
   CSP_POLICY = {
       "default-src": "'self'",
       "script-src": "'self' 'unsafe-inline'",
       "style-src": "'self' 'unsafe-inline'",
   }
   ```

2. **Adjust CSP for development**:
   ```python
   # More permissive for development
   CSP_POLICY = {
       "default-src": "'self' 'unsafe-inline' 'unsafe-eval'",
   }
   ```

### Issue: Rate Limiting Triggered

**Symptoms**:
```
HTTP 429: Too Many Requests
```

**Solutions**:
1. **Check rate limit settings**:
   ```python
   # In config/security.py
   RATE_LIMIT = {
       "requests_per_minute": 60,  # Increase if needed
   }
   ```

2. **Clear rate limit cache**:
   ```bash
   # Restart the application
   ./start.sh
   ```

## 📊 Performance Issues

### Issue: Slow Response Times

**Symptoms**:
- Responses take >10 seconds
- High CPU usage

**Solutions**:
1. **Check model configuration**:
   ```python
   # In config/production.py
   MODEL_CONFIG = {
       "n_ctx": 1024,      # Reduce context
       "max_tokens": 256,  # Reduce response length
       "n_threads": 4,     # Optimize threads
   }
   ```

2. **Monitor system resources**:
   ```bash
   # CPU and memory usage
   top -pid $(pgrep -f "python.*main.py")
   
   # Disk I/O
   iostat -x 1
   ```

3. **Enable response caching**:
   ```python
   # In config/production.py
   CACHE_CONFIG = {
       "enabled": True,
       "ttl": 300,  # 5 minutes
   }
   ```

### Issue: High Memory Usage

**Symptoms**:
- Memory usage >8GB
- System becomes unresponsive

**Solutions**:
1. **Reduce model memory usage**:
   ```python
   MODEL_CONFIG = {
       "n_ctx": 512,       # Smaller context
       "n_gpu_layers": 10, # Fewer GPU layers
   }
   ```

2. **Monitor memory usage**:
   ```bash
   python -c "
   import psutil, os
   process = psutil.Process(os.getpid())
   print(f'Memory: {process.memory_info().rss/1024**3:.1f}GB')
   "
   ```

3. **Implement memory cleanup**:
   ```python
   # Add to application
   import gc
   gc.collect()  # Force garbage collection
   ```

## 🔍 Debugging Tools

### Enable Debug Mode

```python
# In config/production.py
DEBUG = True
LOG_LEVEL = "debug"
```

### Comprehensive Logging

```bash
# View all logs
tail -f logs/app.log logs/error.log

# Filter specific errors
grep -i "error" logs/app.log

# Monitor WebSocket connections
grep -i "websocket" logs/app.log
```

### Browser DevTools

1. **Open DevTools**: F12 or Cmd+Option+I
2. **Check Console**: Look for JavaScript errors
3. **Network Tab**: Monitor WebSocket connections
4. **Application Tab**: Check PWA status, service worker

### System Monitoring

```bash
# Real-time system monitoring
htop

# Network connections
netstat -an | grep 8000

# Process information
ps aux | grep python

# Disk usage
df -h
du -sh *
```

## 📞 Getting Help

### Before Asking for Help

1. **Run diagnostics**:
   ```bash
   python validate_deployment.py > diagnostics.txt
   ```

2. **Collect logs**:
   ```bash
   tar -czf debug-info.tar.gz logs/ config/ diagnostics.txt
   ```

3. **System information**:
   ```bash
   python -c "
   import sys, platform, psutil
   print(f'OS: {platform.system()} {platform.release()}')
   print(f'Python: {sys.version}')
   print(f'Memory: {psutil.virtual_memory().total/1024**3:.1f}GB')
   print(f'CPU: {platform.processor()}')
   " > system-info.txt
   ```

### Support Channels

- **GitHub Issues**: [Create an issue](https://github.com/yourusername/mac-status-pwa/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mac-status-pwa/discussions)
- **Documentation**: [README.md](README.md) and [INSTALL.md](INSTALL.md)

### Issue Template

When reporting issues, include:

1. **System Information**: OS, Python version, hardware
2. **Error Messages**: Full error logs and stack traces
3. **Steps to Reproduce**: Detailed steps that trigger the issue
4. **Expected Behavior**: What should happen
5. **Actual Behavior**: What actually happens
6. **Configuration**: Relevant config file contents
7. **Logs**: Application logs around the time of the issue

---

**Remember**: Most issues can be resolved by carefully following the installation guide and checking the logs. Don't hesitate to ask for help if you're stuck! 🚀