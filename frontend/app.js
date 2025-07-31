/**
 * Mac Status PWA - Main Application JavaScript
 */

class SystemStatusDisplay {
    constructor() {
        this.isCollapsed = false;
        this.lastStatus = null;
        this.animationTimeouts = new Map();
        
        this.initializeElements();
        this.setupEventListeners();
    }
    
    initializeElements() {
        this.container = document.getElementById('systemStatusContainer');
        this.toggleBtn = document.getElementById('toggleBtn');
        
        // CPU elements
        this.cpuCard = document.getElementById('cpuCard');
        this.cpuValue = document.getElementById('cpuValue');
        this.cpuBar = document.getElementById('cpuBar');
        
        // Memory elements
        this.memoryCard = document.getElementById('memoryCard');
        this.memoryValue = document.getElementById('memoryValue');
        this.memoryBar = document.getElementById('memoryBar');
        this.memoryDetail = document.getElementById('memoryDetail');
        
        // Disk elements
        this.diskCard = document.getElementById('diskCard');
        this.diskValue = document.getElementById('diskValue');
        this.diskBar = document.getElementById('diskBar');
        this.diskDetail = document.getElementById('diskDetail');
        
        // Debug: Check if elements are found
        console.log('SystemStatusDisplay elements:', {
            cpuValue: this.cpuValue,
            memoryValue: this.memoryValue,
            diskValue: this.diskValue,
            cpuBar: this.cpuBar,
            memoryBar: this.memoryBar,
            diskBar: this.diskBar
        });
    }
    
    setupEventListeners() {
        this.toggleBtn.addEventListener('click', () => this.toggleDisplay());
    }
    
    toggleDisplay() {
        this.isCollapsed = !this.isCollapsed;
        
        if (this.isCollapsed) {
            this.container.classList.add('collapsed');
        } else {
            this.container.classList.remove('collapsed');
        }
    }
    
    updateStatus(statusData) {
        console.log('SystemStatusDisplay.updateStatus called with:', statusData);
        if (!statusData) {
            console.log('No status data provided');
            return;
        }
        
        // Update CPU
        console.log('Updating CPU:', statusData.cpu_percent);
        this.updateCPU(statusData.cpu_percent);
        
        // Update Memory
        console.log('Updating Memory:', statusData.memory_percent);
        this.updateMemory(statusData.memory_percent, statusData.memory_used, statusData.memory_total);
        
        // Update Disk
        console.log('Updating Disk:', statusData.disk_percent);
        this.updateDisk(statusData.disk_percent, statusData.disk_used, statusData.disk_total);
        
        // Store last status for change detection
        this.lastStatus = statusData;
    }
    
    updateCPU(cpuPercent) {
        console.log('updateCPU called with:', cpuPercent);
        if (cpuPercent === undefined || cpuPercent === null) {
            console.log('Invalid CPU percent value');
            return;
        }
        
        const value = Math.round(cpuPercent);
        const oldValue = this.cpuValue.textContent.replace('%', '');
        
        console.log('Setting CPU value to:', `${value}%`);
        
        // Update value with animation
        this.animateValueChange(this.cpuValue, `${value}%`, oldValue !== value.toString());
        
        // Update progress bar
        this.cpuBar.style.width = `${value}%`;
        
        // Update card status based on usage
        this.updateCardStatus(this.cpuCard, value, [70, 85]);
        
        // Update bar color based on usage
        this.updateBarColor(this.cpuBar, value, [70, 85]);
    }
    
    updateMemory(memoryPercent, memoryUsed, memoryTotal) {
        const value = Math.round(memoryPercent);
        const oldValue = this.memoryValue.textContent.replace('%', '');
        
        // Update value with animation
        this.animateValueChange(this.memoryValue, `${value}%`, oldValue !== value.toString());
        
        // Update progress bar
        this.memoryBar.style.width = `${value}%`;
        
        // Update detail text
        const usedGB = (memoryUsed / (1024 ** 3)).toFixed(1);
        const totalGB = (memoryTotal / (1024 ** 3)).toFixed(1);
        this.memoryDetail.textContent = `${usedGB}GB / ${totalGB}GB`;
        
        // Update card status based on usage
        this.updateCardStatus(this.memoryCard, value, [75, 90]);
        
        // Update bar color based on usage
        this.updateBarColor(this.memoryBar, value, [75, 90]);
    }
    
    updateDisk(diskPercent, diskUsed, diskTotal) {
        const value = Math.round(diskPercent);
        const oldValue = this.diskValue.textContent.replace('%', '');
        
        // Update value with animation
        this.animateValueChange(this.diskValue, `${value}%`, oldValue !== value.toString());
        
        // Update progress bar
        this.diskBar.style.width = `${value}%`;
        
        // Update detail text
        const usedGB = (diskUsed / (1024 ** 3)).toFixed(1);
        const totalGB = (diskTotal / (1024 ** 3)).toFixed(1);
        this.diskDetail.textContent = `${usedGB}GB / ${totalGB}GB`;
        
        // Update card status based on usage
        this.updateCardStatus(this.diskCard, value, [80, 95]);
        
        // Update bar color based on usage
        this.updateBarColor(this.diskBar, value, [80, 95]);
    }
    
    animateValueChange(element, newValue, hasChanged) {
        if (hasChanged) {
            // Add changing class for animation
            element.classList.add('changing');
            
            // Clear existing timeout
            const timeoutKey = element.id;
            if (this.animationTimeouts.has(timeoutKey)) {
                clearTimeout(this.animationTimeouts.get(timeoutKey));
            }
            
            // Remove changing class after animation
            const timeout = setTimeout(() => {
                element.classList.remove('changing');
                this.animationTimeouts.delete(timeoutKey);
            }, 300);
            
            this.animationTimeouts.set(timeoutKey, timeout);
        }
        
        element.textContent = newValue;
    }
    
    updateCardStatus(card, value, thresholds) {
        const [warningThreshold, criticalThreshold] = thresholds;
        
        // Remove existing status classes
        card.classList.remove('warning', 'alert');
        
        if (value >= criticalThreshold) {
            card.classList.add('alert');
        } else if (value >= warningThreshold) {
            card.classList.add('warning');
        }
    }
    
    updateBarColor(bar, value, thresholds) {
        const [warningThreshold, criticalThreshold] = thresholds;
        
        // Remove existing color classes
        bar.classList.remove('high-usage', 'critical-usage');
        
        if (value >= criticalThreshold) {
            bar.classList.add('critical-usage');
        } else if (value >= warningThreshold) {
            bar.classList.add('high-usage');
        }
    }
    
    showError(message) {
        // Show error state in status cards
        [this.cpuValue, this.memoryValue, this.diskValue].forEach(element => {
            element.textContent = 'エラー';
        });
        
        [this.cpuBar, this.memoryBar, this.diskBar].forEach(bar => {
            bar.style.width = '0%';
        });
        
        this.memoryDetail.textContent = message || 'データを取得できません';
        this.diskDetail.textContent = message || 'データを取得できません';
    }
}

class MacStatusApp {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.messageHistory = [];
        this.isTyping = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.statusDisplay = new SystemStatusDisplay();
        this.statusUpdateInterval = null;
        
        // Enhanced connection management
        this.connectionState = 'disconnected'; // disconnected, connecting, connected, reconnecting, failed, offline
        this.reconnectDelay = 1000; // Initial reconnect delay in ms
        this.maxReconnectDelay = 30000; // Maximum reconnect delay
        this.reconnectBackoffMultiplier = 2;
        this.reconnectTimer = null;
        this.lastConnectionTime = null;
        this.connectionMetrics = {
            totalAttempts: 0,
            successfulConnections: 0,
            totalUptime: 0,
            totalDowntime: 0
        };
        
        // Offline support
        this.offlineMode = false;
        this.offlineDataCache = new Map();
        this.offlineMessageQueue = [];
        this.lastSystemStatus = null;
        
        // Network status monitoring
        this.isOnline = navigator.onLine;
        this.networkStatusCallbacks = [];
        
        this.initializeElements();
        this.setupEventListeners();
        this.connectWebSocket();
    }
    
    initializeElements() {
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.clearButton = document.getElementById('clearButton');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.statusIndicator = this.connectionStatus.querySelector('.status-indicator');
        this.statusText = this.connectionStatus.querySelector('.status-text');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.scrollToBottom = document.getElementById('scrollToBottom');
        this.characterCount = document.getElementById('characterCount');
        this.queuedMessagesIndicator = document.getElementById('queuedMessagesIndicator');
        this.queuedMessagesCount = document.getElementById('queuedMessagesCount');
    }
    
    setupEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Clear button click
        this.clearButton.addEventListener('click', () => this.clearChatHistory());
        
        // Enter key press
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Input character count
        this.messageInput.addEventListener('input', () => {
            this.updateCharacterCount();
        });
        
        // Example question buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('example-btn')) {
                const question = e.target.getAttribute('data-question');
                this.messageInput.value = question;
                this.sendMessage();
            }
        });
        
        // Scroll to bottom button
        this.scrollToBottom.querySelector('.scroll-btn').addEventListener('click', () => {
            this.scrollToBottomOfMessages();
        });
        
        // Monitor scroll position
        this.messagesContainer.addEventListener('scroll', () => {
            this.handleScroll();
        });
        
        // Input focus/blur for mobile
        this.messageInput.addEventListener('focus', () => {
            document.body.classList.add('input-focused');
        });
        
        this.messageInput.addEventListener('blur', () => {
            document.body.classList.remove('input-focused');
        });
        
        // Network status monitoring
        window.addEventListener('online', () => {
            console.log('Network came online');
            this.handleNetworkStatusChange(true);
        });
        
        window.addEventListener('offline', () => {
            console.log('Network went offline');
            this.handleNetworkStatusChange(false);
        });
        
        // Connection status click for manual reconnection
        this.connectionStatus.addEventListener('click', () => {
            if (!this.isConnected && this.connectionState !== 'connecting') {
                this.forceReconnect();
            }
        });
        
        // Add retry button functionality
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('retry-connection-btn')) {
                this.forceReconnect();
            }
        });
    }
    
    connectWebSocket() {
        // Clear any existing reconnect timer
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        // Check network status first
        if (!navigator.onLine) {
            this.handleNetworkStatusChange(false);
            return;
        }
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.setConnectionState('connecting');
        this.connectionMetrics.totalAttempts++;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            // Set connection timeout
            const connectionTimeout = setTimeout(() => {
                if (this.websocket && this.websocket.readyState === WebSocket.CONNECTING) {
                    console.log('WebSocket connection timeout');
                    this.websocket.close();
                }
            }, 10000); // 10 second timeout
            
            this.websocket.onopen = () => {
                clearTimeout(connectionTimeout);
                console.log('WebSocket connected');
                this.lastConnectionTime = Date.now();
                this.connectionMetrics.successfulConnections++;
                this.setConnectionState('connected');
                this.reconnectAttempts = 0;
                this.reconnectDelay = 1000; // Reset delay
                
                // Process any queued offline messages
                this.processOfflineMessageQueue();
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleIncomingMessage(data);
            };
            
            this.websocket.onclose = (event) => {
                clearTimeout(connectionTimeout);
                console.log('WebSocket disconnected', event.code, event.reason);
                
                // Update connection metrics
                if (this.lastConnectionTime) {
                    this.connectionMetrics.totalUptime += Date.now() - this.lastConnectionTime;
                }
                
                this.setConnectionState('disconnected');
                this.hideTypingIndicator();
                
                // Determine if we should attempt reconnection
                if (this.shouldAttemptReconnection(event)) {
                    this.scheduleReconnection();
                } else {
                    this.setConnectionState('failed');
                }
            };
            
            this.websocket.onerror = (error) => {
                clearTimeout(connectionTimeout);
                console.error('WebSocket error:', error);
                this.setConnectionState('disconnected');
                
                // Show appropriate error message based on connection attempts
                if (this.reconnectAttempts === 0) {
                    this.displayError('サーバーとの接続でエラーが発生しました', 'high', [
                        'ネットワーク接続を確認してください',
                        '接続状態をクリックして再試行してください'
                    ]);
                }
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.setConnectionState('failed');
            this.displayError('WebSocket接続の作成に失敗しました', 'critical', [
                'ブラウザを再起動してください',
                'システム管理者にお問い合わせください'
            ]);
        }
    }
    
    // エラーメッセージを表示（拡張版）
    displayError(message, severity = 'medium', suggestedActions = []) {
        const errorDiv = document.createElement('div');
        errorDiv.className = `error-message error-${severity}`;
        
        // エラーメッセージ本体
        const messageDiv = document.createElement('div');
        messageDiv.className = 'error-text';
        messageDiv.textContent = message;
        errorDiv.appendChild(messageDiv);
        
        // 推奨アクションがある場合は表示
        if (suggestedActions.length > 0) {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'error-actions';
            actionsDiv.innerHTML = '<strong>推奨アクション:</strong>';
            
            const actionsList = document.createElement('ul');
            suggestedActions.forEach(action => {
                const actionItem = document.createElement('li');
                actionItem.textContent = action;
                actionsList.appendChild(actionItem);
            });
            
            actionsDiv.appendChild(actionsList);
            errorDiv.appendChild(actionsDiv);
        }
        
        // 閉じるボタン
        const closeButton = document.createElement('button');
        closeButton.className = 'error-close';
        closeButton.innerHTML = '×';
        closeButton.onclick = () => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        };
        errorDiv.appendChild(closeButton);
        
        this.messagesContainer.appendChild(errorDiv);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        
        // 重要度に応じて自動削除時間を調整
        const autoRemoveTime = {
            'low': 3000,
            'medium': 5000,
            'high': 8000,
            'critical': 0  // 手動でのみ削除
        }[severity] || 5000;
        
        if (autoRemoveTime > 0) {
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.parentNode.removeChild(errorDiv);
                }
            }, autoRemoveTime);
        }
    }
    
    // システムエラーの処理
    handleSystemError(errorData) {
        const { category, severity, user_message, suggested_actions } = errorData;
        
        // エラーメッセージを表示
        this.displayError(user_message, severity, suggested_actions || []);
        
        // カテゴリ別の追加処理
        switch (category) {
            case 'websocket_error':
                this.updateConnectionStatus(false);
                break;
            case 'model_error':
                // AIモデルエラーの場合、チャット入力を一時的に無効化
                if (severity === 'critical') {
                    this.messageInput.disabled = true;
                    this.messageInput.placeholder = 'AIモデルが利用できません';
                    
                    // 30秒後に再有効化を試行
                    setTimeout(() => {
                        this.messageInput.disabled = false;
                        this.messageInput.placeholder = 'メッセージを入力...';
                    }, 30000);
                }
                break;
            case 'system_monitor_error':
                // システム監視エラーの場合、ステータス表示を更新
                this.statusDisplay.showError('システム情報を取得できません');
                break;
        }
    }

    setConnectionState(newState) {
        const oldState = this.connectionState;
        this.connectionState = newState;
        
        console.log(`Connection state changed: ${oldState} -> ${newState}`);
        
        // Update UI based on connection state
        this.updateConnectionStatusUI();
        
        // Handle state-specific logic
        switch (newState) {
            case 'connected':
                this.isConnected = true;
                this.exitOfflineMode();
                this.requestSystemStatus();
                this.startStatusUpdates();
                break;
                
            case 'disconnected':
            case 'failed':
                this.isConnected = false;
                this.stopStatusUpdates();
                this.statusDisplay.showError('接続が切断されました');
                break;
                
            case 'offline':
                this.isConnected = false;
                this.enterOfflineMode();
                this.stopStatusUpdates();
                break;
                
            case 'connecting':
            case 'reconnecting':
                this.isConnected = false;
                break;
        }
        
        // Execute callbacks
        this.networkStatusCallbacks.forEach(callback => {
            try {
                callback(newState, oldState);
            } catch (error) {
                console.error('Error in network status callback:', error);
            }
        });
    }
    
    updateConnectionStatusUI() {
        // Remove all state classes
        this.connectionStatus.classList.remove(
            'status-connected', 'status-connecting', 'status-disconnected', 
            'status-reconnecting', 'status-failed', 'status-offline'
        );
        this.statusIndicator.classList.remove('connected', 'disconnected', 'connecting', 'offline');
        
        // Add current state class
        this.connectionStatus.classList.add(`status-${this.connectionState}`);
        this.statusIndicator.classList.add(this.connectionState === 'connected' ? 'connected' : 'disconnected');
        
        // Update status text and controls
        switch (this.connectionState) {
            case 'connected':
                this.statusText.textContent = '接続済み';
                this.sendButton.disabled = false;
                this.messageInput.disabled = false;
                this.messageInput.placeholder = 'メッセージを入力...';
                this.connectionStatus.title = 'サーバーに接続されています';
                break;
                
            case 'connecting':
                this.statusText.textContent = '接続中...';
                this.sendButton.disabled = true;
                this.messageInput.disabled = true;
                this.messageInput.placeholder = '接続中...';
                this.connectionStatus.title = 'サーバーに接続しています';
                break;
                
            case 'reconnecting':
                this.statusText.textContent = `再接続中... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`;
                this.sendButton.disabled = true;
                this.messageInput.disabled = true;
                this.messageInput.placeholder = '再接続中...';
                this.connectionStatus.title = 'クリックして手動で再接続';
                break;
                
            case 'disconnected':
                this.statusText.textContent = '切断';
                this.sendButton.disabled = true;
                this.messageInput.disabled = true;
                this.messageInput.placeholder = '接続が切断されました';
                this.connectionStatus.title = 'クリックして再接続';
                break;
                
            case 'failed':
                this.statusText.textContent = '接続失敗';
                this.sendButton.disabled = true;
                this.messageInput.disabled = true;
                this.messageInput.placeholder = '接続に失敗しました';
                this.connectionStatus.title = 'クリックして再試行';
                this.showConnectionFailedMessage();
                break;
                
            case 'offline':
                this.statusText.textContent = 'オフライン';
                this.sendButton.disabled = false; // Allow offline messages
                this.messageInput.disabled = false;
                this.messageInput.placeholder = 'オフラインモード - 基本機能のみ利用可能';
                this.connectionStatus.title = 'オフラインモード';
                break;
        }
        
        // Update connection indicator animation
        if (this.connectionState === 'connecting' || this.connectionState === 'reconnecting') {
            this.statusIndicator.classList.add('connecting');
        } else {
            this.statusIndicator.classList.remove('connecting');
        }
    }
    
    requestSystemStatus() {
        if (!this.isConnected) return;
        
        const statusRequest = {
            type: 'system_status_request',
            data: {
                request_id: Date.now().toString()
            },
            timestamp: new Date().toISOString()
        };
        
        try {
            this.websocket.send(JSON.stringify(statusRequest));
        } catch (error) {
            console.error('Failed to request system status:', error);
        }
    }
    
    startStatusUpdates() {
        // Clear any existing interval
        this.stopStatusUpdates();
        
        // Request status every 5 seconds
        this.statusUpdateInterval = setInterval(() => {
            this.requestSystemStatus();
        }, 5000);
    }
    
    stopStatusUpdates() {
        if (this.statusUpdateInterval) {
            clearInterval(this.statusUpdateInterval);
            this.statusUpdateInterval = null;
        }
    }
    
    shouldAttemptReconnection(closeEvent) {
        // Don't reconnect if manually closed or if we've exceeded max attempts
        if (closeEvent.code === 1000 || this.reconnectAttempts >= this.maxReconnectAttempts) {
            return false;
        }
        
        // Don't reconnect if network is offline
        if (!navigator.onLine) {
            this.handleNetworkStatusChange(false);
            return false;
        }
        
        return true;
    }
    
    scheduleReconnection() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }
        
        this.reconnectAttempts++;
        this.setConnectionState('reconnecting');
        
        // Calculate delay with exponential backoff
        const delay = Math.min(
            this.reconnectDelay * Math.pow(this.reconnectBackoffMultiplier, this.reconnectAttempts - 1),
            this.maxReconnectDelay
        );
        
        console.log(`Scheduling reconnection in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        this.reconnectTimer = setTimeout(() => {
            this.connectWebSocket();
        }, delay);
    }
    
    forceReconnect() {
        console.log('Force reconnecting...');
        
        // Cancel any pending reconnection
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        // Close existing connection if any
        if (this.websocket) {
            this.websocket.close();
        }
        
        // Reset reconnection state
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        
        // Attempt connection
        this.connectWebSocket();
    }
    
    handleNetworkStatusChange(isOnline) {
        this.isOnline = isOnline;
        
        if (isOnline) {
            console.log('Network is online, attempting to reconnect...');
            if (this.connectionState === 'offline') {
                this.forceReconnect();
            }
        } else {
            console.log('Network is offline, entering offline mode...');
            this.setConnectionState('offline');
            
            // Close WebSocket connection
            if (this.websocket) {
                this.websocket.close();
            }
            
            // Cancel any pending reconnection
            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
                this.reconnectTimer = null;
            }
        }
    }
    
    enterOfflineMode() {
        this.offlineMode = true;
        console.log('Entered offline mode');
        
        // Show offline notification
        this.displayMessage('オフラインモードに移行しました。基本機能のみ利用可能です。', 'system');
        
        // Cache current system status if available
        if (this.lastSystemStatus) {
            this.cacheOfflineData('system_status', this.lastSystemStatus);
        }
    }
    
    exitOfflineMode() {
        if (this.offlineMode) {
            this.offlineMode = false;
            console.log('Exited offline mode');
            
            // Show online notification
            this.displayMessage('オンラインに復帰しました。', 'system');
        }
    }
    
    cacheOfflineData(key, data) {
        this.offlineDataCache.set(key, {
            data: data,
            timestamp: Date.now(),
            ttl: 300000 // 5 minutes TTL
        });
    }
    
    getOfflineData(key) {
        const cached = this.offlineDataCache.get(key);
        if (!cached) return null;
        
        // Check TTL
        if (Date.now() - cached.timestamp > cached.ttl) {
            this.offlineDataCache.delete(key);
            return null;
        }
        
        return cached.data;
    }
    
    queueOfflineMessage(message) {
        this.offlineMessageQueue.push({
            message: message,
            timestamp: Date.now(),
            type: 'chat_message'
        });
        
        // Limit queue size
        if (this.offlineMessageQueue.length > 50) {
            this.offlineMessageQueue = this.offlineMessageQueue.slice(-50);
        }
        
        console.log(`Message queued for offline processing. Queue size: ${this.offlineMessageQueue.length}`);
        this.updateQueuedMessagesIndicator();
    }
    
    updateQueuedMessagesIndicator() {
        const queueSize = this.offlineMessageQueue.length;
        
        if (queueSize > 0) {
            this.queuedMessagesCount.textContent = queueSize;
            this.queuedMessagesIndicator.classList.add('visible');
        } else {
            this.queuedMessagesIndicator.classList.remove('visible');
        }
    }
    
    processOfflineMessageQueue() {
        if (this.offlineMessageQueue.length === 0) return;
        
        console.log(`Processing ${this.offlineMessageQueue.length} queued messages`);
        
        // Process queued messages
        const messages = [...this.offlineMessageQueue];
        this.offlineMessageQueue = [];
        this.updateQueuedMessagesIndicator();
        
        messages.forEach((queuedMessage, index) => {
            setTimeout(() => {
                this.sendQueuedMessage(queuedMessage);
            }, index * 100); // Stagger messages to avoid overwhelming server
        });
    }
    
    sendQueuedMessage(queuedMessage) {
        if (!this.isConnected) {
            // Re-queue if connection lost again
            this.offlineMessageQueue.push(queuedMessage);
            return;
        }
        
        const messageData = {
            type: 'chat_message',
            data: {
                message: queuedMessage.message,
                queued_at: queuedMessage.timestamp,
                processed_at: Date.now()
            },
            timestamp: new Date().toISOString()
        };
        
        try {
            this.websocket.send(JSON.stringify(messageData));
        } catch (error) {
            console.error('Failed to send queued message:', error);
            // Re-queue the message
            this.offlineMessageQueue.push(queuedMessage);
        }
    }
    
    showConnectionFailedMessage() {
        const retryButton = `<button class="retry-connection-btn" style="
            background: var(--apple-blue);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            margin-top: 8px;
            cursor: pointer;
            font-size: 14px;
        ">再接続を試す</button>`;
        
        this.displayError(
            '接続に失敗しました。ネットワーク接続を確認してください。',
            'high',
            [
                'ネットワーク接続を確認してください',
                'ファイアウォール設定を確認してください',
                'しばらく待ってから再試行してください'
            ]
        );
        
        // Add retry button to the last error message
        const lastError = this.messagesContainer.querySelector('.error-message:last-of-type');
        if (lastError) {
            lastError.innerHTML += retryButton;
        }
    }
    
    getOfflineSystemStatus() {
        const cachedStatus = this.getOfflineData('system_status');
        if (cachedStatus) {
            return {
                ...cachedStatus,
                offline_mode: true,
                message: 'オフラインモード - キャッシュされたデータを表示中'
            };
        }
        
        return {
            offline_mode: true,
            cpu_percent: 0,
            memory_percent: 0,
            disk_percent: 0,
            timestamp: new Date().toISOString(),
            message: 'オフラインモード - システム情報は利用できません'
        };
    }
    
    generateOfflineResponse(userMessage) {
        const lowerMessage = userMessage.toLowerCase();
        
        // System-related queries
        if (lowerMessage.includes('システム') || lowerMessage.includes('cpu') || 
            lowerMessage.includes('メモリ') || lowerMessage.includes('ディスク')) {
            const cachedStatus = this.getOfflineData('system_status');
            if (cachedStatus) {
                return `オフラインモードです。最後に取得したシステム情報をお伝えします：\n\nCPU使用率: ${cachedStatus.cpu_percent?.toFixed(1) || 0}%\nメモリ使用率: ${cachedStatus.memory_percent?.toFixed(1) || 0}%\nディスク使用率: ${cachedStatus.disk_percent?.toFixed(1) || 0}%\n\n※ この情報はキャッシュされたものです。`;
            } else {
                return 'オフラインモードのため、現在のシステム情報を取得できません。オンラインに復帰してから再度お試しください。';
            }
        }
        
        // General queries
        return 'オフラインモードのため、AIアシスタント機能は利用できません。基本的なシステム情報の表示のみ可能です。オンラインに復帰すると、すべての機能が利用できるようになります。';
    }
    
    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Handle offline mode
        if (this.offlineMode || !this.isConnected) {
            this.handleOfflineMessage(message);
            return;
        }
        
        if (this.isTyping) return;
        
        // Display user message
        this.displayMessage(message, 'user');
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Send to server
        const messageData = {
            type: 'chat_message',
            data: {
                message: message
            },
            timestamp: new Date().toISOString()
        };
        
        try {
            this.websocket.send(JSON.stringify(messageData));
        } catch (error) {
            console.error('Failed to send message:', error);
            this.hideTypingIndicator();
            this.displayMessage('メッセージの送信に失敗しました。接続を確認してください。', 'system');
        }
        
        // Clear input
        this.messageInput.value = '';
        this.updateCharacterCount();
        this.messageInput.focus();
        
        // Add to history
        this.messageHistory.push({
            role: 'user',
            content: message,
            timestamp: new Date()
        });
    }
    
    handleOfflineMessage(message) {
        // Display user message
        this.displayMessage(message, 'user');
        
        // Queue message for when connection is restored
        this.queueOfflineMessage(message);
        
        // Generate offline response
        const offlineResponse = this.generateOfflineResponse(message);
        
        // Show typing indicator briefly for better UX
        this.showTypingIndicator();
        setTimeout(() => {
            this.hideTypingIndicator();
            this.displayMessage(offlineResponse, 'assistant', true);
            
            // Add to history
            this.messageHistory.push({
                role: 'user',
                content: message,
                timestamp: new Date()
            });
            this.messageHistory.push({
                role: 'assistant',
                content: offlineResponse,
                timestamp: new Date(),
                offline: true
            });
        }, 1000);
        
        // Clear input
        this.messageInput.value = '';
        this.updateCharacterCount();
        this.messageInput.focus();
    }
    
    handleIncomingMessage(data) {
        this.hideTypingIndicator();
        
        console.log('Received message:', data);
        
        if (data.type === 'chat_response') {
            this.displayMessage(data.data.content || data.data.message, 'assistant');
            
            // Add to history
            this.messageHistory.push({
                role: 'assistant',
                content: data.data.content || data.data.message,
                timestamp: new Date()
            });
        } else if (data.type === 'error') {
            this.displayMessage(data.data.message || 'エラーが発生しました。', 'system');
        } else if (data.type === 'system_status_update') {
            // Handle system status updates
            console.log('System status update:', data);
            console.log('StatusDisplay object:', this.statusDisplay);
            if (data.data) {
                console.log('Calling statusDisplay.updateStatus with:', data.data);
                this.lastSystemStatus = data.data;
                this.cacheOfflineData('system_status', data.data);
                this.statusDisplay.updateStatus(data.data);
            } else {
                console.log('No data found in system_status_update');
            }
        } else if (data.type === 'system_status_response') {
            // Handle system status response
            console.log('System status response:', data);
            console.log('StatusDisplay object:', this.statusDisplay);
            if (data.data && data.data.system_status) {
                console.log('Calling statusDisplay.updateStatus with:', data.data.system_status);
                this.lastSystemStatus = data.data.system_status;
                this.cacheOfflineData('system_status', data.data.system_status);
                this.statusDisplay.updateStatus(data.data.system_status);
            } else {
                console.log('No system_status data found in response');
            }
        } else if (data.type === 'pong') {
            // Handle pong response
            console.log('Received pong:', data);
        } else if (data.type === 'connection_status') {
            // Handle connection status updates
            console.log('Connection status:', data);
        }
    }
    
    displayMessage(content, role, isOffline = false) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${role}`;
        
        if (isOffline) {
            messageElement.setAttribute('data-offline', 'true');
        }
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = this.formatTimestamp(new Date());
        
        messageElement.appendChild(messageContent);
        messageElement.appendChild(timestamp);
        
        // Remove welcome message if it exists
        const welcomeMessage = this.messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        // Handle message grouping
        this.handleMessageGrouping(messageElement, role);
        
        this.messagesContainer.appendChild(messageElement);
        
        // Scroll to bottom
        this.scrollToBottomOfMessages();
    }
    
    handleMessageGrouping(messageElement, role) {
        const messages = this.messagesContainer.querySelectorAll('.message');
        const lastMessage = messages[messages.length - 1];
        
        if (lastMessage && lastMessage.classList.contains(role)) {
            // Same sender as previous message
            const timeDiff = Date.now() - parseInt(lastMessage.dataset.timestamp || '0');
            
            if (timeDiff < 60000) { // Within 1 minute
                // Remove last-in-group from previous message
                lastMessage.classList.remove('last-in-group', 'first-in-group');
                lastMessage.classList.add('middle-in-group');
                
                // Add grouping classes to new message
                messageElement.classList.add('last-in-group');
            } else {
                // Time gap too large, start new group
                lastMessage.classList.add('last-in-group');
                messageElement.classList.add('first-in-group', 'last-in-group');
            }
        } else {
            // Different sender or first message
            if (lastMessage) {
                lastMessage.classList.add('last-in-group');
            }
            messageElement.classList.add('first-in-group', 'last-in-group');
        }
        
        // Store timestamp for grouping logic
        messageElement.dataset.timestamp = Date.now().toString();
    }
    
    showTypingIndicator() {
        this.isTyping = true;
        this.typingIndicator.style.display = 'flex';
    }
    
    hideTypingIndicator() {
        this.isTyping = false;
        this.typingIndicator.style.display = 'none';
    }
    
    scrollToBottomOfMessages() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        this.scrollToBottom.style.display = 'none';
    }
    
    handleScroll() {
        const { scrollTop, scrollHeight, clientHeight } = this.messagesContainer;
        const isAtBottom = scrollTop + clientHeight >= scrollHeight - 50;
        
        if (isAtBottom) {
            this.scrollToBottom.style.display = 'none';
        } else {
            this.scrollToBottom.style.display = 'block';
        }
    }
    
    updateCharacterCount() {
        const count = this.messageInput.value.length;
        this.characterCount.textContent = `${count}/500`;
        
        if (count > 450) {
            this.characterCount.style.color = 'var(--apple-red)';
        } else if (count > 400) {
            this.characterCount.style.color = 'var(--apple-gray)';
        } else {
            this.characterCount.style.color = 'var(--apple-gray)';
        }
    }
    
    clearChatHistory() {
        if (confirm('チャット履歴をクリアしますか？')) {
            this.messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-icon">👋</div>
                    <h2>Mac Status アシスタント</h2>
                    <p>こんにちは！Macのステータスについて何でも聞いてください。</p>
                    <div class="example-questions">
                        <button class="example-btn" data-question="CPUの使用率はどうですか？">CPUの使用率はどうですか？</button>
                        <button class="example-btn" data-question="メモリの状況を教えて">メモリの状況を教えて</button>
                        <button class="example-btn" data-question="システムの全体的な状況は？">システムの全体的な状況は？</button>
                    </div>
                </div>
            `;
            this.messageHistory = [];
            this.scrollToBottomOfMessages();
        }
    }
    
    // Utility method for timestamp formatting
    formatTimestamp(date) {
        return new Intl.DateTimeFormat('ja-JP', {
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.macStatusApp = new MacStatusApp();
    window.pwaManager = new PWAManager();
});

/**
 * PWA Manager Class
 * Handles PWA installation, offline functionality, and service worker management
 */
class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.isOnline = navigator.onLine;
        this.installButton = null;
        this.offlineIndicator = null;
        
        this.initializePWA();
        this.setupEventListeners();
    }
    
    initializePWA() {
        // Check if app is already installed
        this.checkInstallationStatus();
        
        // Create install button
        this.createInstallButton();
        
        // Create offline indicator
        this.createOfflineIndicator();
        
        // Register service worker
        this.registerServiceWorker();
    }
    
    setupEventListeners() {
        // PWA install prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('PWA install prompt available');
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallButton();
        });
        
        // App installed
        window.addEventListener('appinstalled', () => {
            console.log('PWA was installed');
            this.deferredPrompt = null;
            this.isInstalled = true;
            this.hideInstallButton();
            this.showInstallSuccessMessage();
        });
        
        // Online/offline status
        window.addEventListener('online', () => {
            console.log('App is online');
            this.isOnline = true;
            this.updateOfflineIndicator();
            this.handleOnlineStatusChange(true);
        });
        
        window.addEventListener('offline', () => {
            console.log('App is offline');
            this.isOnline = false;
            this.updateOfflineIndicator();
            this.handleOnlineStatusChange(false);
        });
        
        // Service worker messages
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                this.handleServiceWorkerMessage(event.data);
            });
        }
    }
    
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/static/sw.js');
                console.log('Service Worker registered successfully:', registration);
                
                // Handle service worker updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateAvailableNotification();
                        }
                    });
                });
                
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }
    
    checkInstallationStatus() {
        // Check if running in standalone mode (installed)
        this.isInstalled = window.matchMedia('(display-mode: standalone)').matches ||
                          window.navigator.standalone === true;
        
        console.log('PWA installation status:', this.isInstalled ? 'Installed' : 'Not installed');
    }
    
    createInstallButton() {
        this.installButton = document.createElement('button');
        this.installButton.className = 'install-button';
        this.installButton.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M21 15V19C21 19.5523 20.4477 20 20 20H4C3.44772 20 3 19.5523 3 19V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 10L12 15L17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 15V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>アプリをインストール</span>
        `;
        this.installButton.title = 'Mac Status PWAをデスクトップにインストール';
        this.installButton.style.display = 'none';
        
        this.installButton.addEventListener('click', () => {
            this.showInstallPrompt();
        });
        
        // Add to header
        const header = document.querySelector('.app-header');
        if (header) {
            header.appendChild(this.installButton);
        }
    }
    
    createOfflineIndicator() {
        this.offlineIndicator = document.createElement('div');
        this.offlineIndicator.className = 'offline-indicator';
        this.offlineIndicator.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M1 9L12 2L23 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M5 12L12 7L19 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M9 16L12 13L15 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="20" r="1" fill="currentColor"/>
            </svg>
            <span>オフライン</span>
        `;
        this.offlineIndicator.style.display = 'none';
        
        // Add to connection status area
        const connectionStatus = document.getElementById('connectionStatus');
        if (connectionStatus) {
            connectionStatus.appendChild(this.offlineIndicator);
        }
        
        this.updateOfflineIndicator();
    }
    
    showInstallButton() {
        if (!this.isInstalled && this.installButton) {
            this.installButton.style.display = 'flex';
            
            // Show install notification
            this.showNotification('このアプリをデスクトップにインストールできます', 'info', 5000);
        }
    }
    
    hideInstallButton() {
        if (this.installButton) {
            this.installButton.style.display = 'none';
        }
    }
    
    async showInstallPrompt() {
        if (!this.deferredPrompt) {
            this.showNotification('インストールプロンプトが利用できません', 'warning');
            return;
        }
        
        try {
            // Show the install prompt
            this.deferredPrompt.prompt();
            
            // Wait for the user to respond
            const { outcome } = await this.deferredPrompt.userChoice;
            
            console.log(`User response to install prompt: ${outcome}`);
            
            if (outcome === 'accepted') {
                this.showNotification('アプリのインストールを開始しています...', 'success');
            } else {
                this.showNotification('インストールがキャンセルされました', 'info');
            }
            
            // Clear the deferred prompt
            this.deferredPrompt = null;
            this.hideInstallButton();
            
        } catch (error) {
            console.error('Error showing install prompt:', error);
            this.showNotification('インストールプロンプトの表示に失敗しました', 'error');
        }
    }
    
    showInstallSuccessMessage() {
        this.showNotification('Mac Status PWAが正常にインストールされました！', 'success', 3000);
    }
    
    updateOfflineIndicator() {
        if (this.offlineIndicator) {
            this.offlineIndicator.style.display = this.isOnline ? 'none' : 'flex';
        }
    }
    
    handleOnlineStatusChange(isOnline) {
        if (isOnline) {
            this.showNotification('インターネット接続が復旧しました', 'success', 2000);
            
            // Trigger sync if available
            if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
                navigator.serviceWorker.ready.then((registration) => {
                    return registration.sync.register('background-sync-messages');
                }).catch((error) => {
                    console.error('Background sync registration failed:', error);
                });
            }
        } else {
            this.showNotification('オフラインモードに切り替わりました', 'warning', 3000);
        }
    }
    
    handleServiceWorkerMessage(data) {
        console.log('Received message from service worker:', data);
        
        if (data.type === 'SYNC_COMPLETE') {
            this.showNotification('オフラインデータが同期されました', 'success', 2000);
        }
    }
    
    showUpdateAvailableNotification() {
        const updateNotification = document.createElement('div');
        updateNotification.className = 'update-notification';
        updateNotification.innerHTML = `
            <div class="update-content">
                <span>新しいバージョンが利用可能です</span>
                <button class="update-button" onclick="this.parentElement.parentElement.remove(); location.reload();">
                    更新
                </button>
                <button class="dismiss-button" onclick="this.parentElement.parentElement.remove();">
                    後で
                </button>
            </div>
        `;
        
        document.body.appendChild(updateNotification);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (updateNotification.parentElement) {
                updateNotification.remove();
            }
        }, 10000);
    }
    
    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `pwa-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove();">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.classList.add('fade-out');
                    setTimeout(() => notification.remove(), 300);
                }
            }, duration);
        }
    }
    
    // Public methods for integration with main app
    getInstallationStatus() {
        return {
            isInstalled: this.isInstalled,
            canInstall: !!this.deferredPrompt,
            isOnline: this.isOnline
        };
    }
    
    triggerInstall() {
        this.showInstallPrompt();
    }
}

// Handle PWA install prompt - Legacy support
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent Chrome 67 and earlier from automatically showing the prompt
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    
    // Show install button or notification
    console.log('PWA install prompt available');
});

window.addEventListener('appinstalled', () => {
    console.log('PWA was installed');
    deferredPrompt = null;
});