/**
 * Mac Status PWA - Main Application JavaScript
 */

class MacStatusApp {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.messageHistory = [];
        
        this.initializeElements();
        this.setupEventListeners();
        this.connectWebSocket();
    }
    
    initializeElements() {
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.statusIndicator = this.connectionStatus.querySelector('.status-indicator');
        this.statusText = this.connectionStatus.querySelector('.status-text');
    }
    
    setupEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key press
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Input focus/blur for mobile
        this.messageInput.addEventListener('focus', () => {
            document.body.classList.add('input-focused');
        });
        
        this.messageInput.addEventListener('blur', () => {
            document.body.classList.remove('input-focused');
        });
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleIncomingMessage(data);
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                // Attempt to reconnect after 3 seconds
                setTimeout(() => this.connectWebSocket(), 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    updateConnectionStatus(connected) {
        this.isConnected = connected;
        
        if (connected) {
            this.statusIndicator.classList.add('connected');
            this.statusIndicator.classList.remove('disconnected');
            this.statusText.textContent = '接続済み';
            this.sendButton.disabled = false;
        } else {
            this.statusIndicator.classList.add('disconnected');
            this.statusIndicator.classList.remove('connected');
            this.statusText.textContent = '接続中...';
            this.sendButton.disabled = true;
        }
    }
    
    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.isConnected) return;
        
        // Display user message
        this.displayMessage(message, 'user');
        
        // Send to server
        const messageData = {
            type: 'chat',
            content: message,
            timestamp: new Date().toISOString()
        };
        
        this.websocket.send(JSON.stringify(messageData));
        
        // Clear input
        this.messageInput.value = '';
        this.messageInput.focus();
        
        // Add to history
        this.messageHistory.push({
            role: 'user',
            content: message,
            timestamp: new Date()
        });
    }
    
    handleIncomingMessage(data) {
        if (data.type === 'response') {
            this.displayMessage(data.content, 'assistant');
            
            // Add to history
            this.messageHistory.push({
                role: 'assistant',
                content: data.content,
                timestamp: new Date()
            });
        }
    }
    
    displayMessage(content, role) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${role}`;
        messageElement.textContent = content;
        
        // Remove welcome message if it exists
        const welcomeMessage = this.messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.messagesContainer.appendChild(messageElement);
        
        // Scroll to bottom
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    // Utility method for future use
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
});

// Handle PWA install prompt
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