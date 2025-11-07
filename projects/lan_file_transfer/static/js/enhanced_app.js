/**
 * Enhanced LAN File Transfer - Multi-File, Multi-User JavaScript
 * Handles multiple file uploads to multiple servers with real-time progress tracking
 */

class EnhancedFileTransferApp {
    constructor() {
        this.selectedFiles = [];
        this.targetServers = [];
        this.transferStatus = {
            active: 0,
            completed: 0,
            queue: 0,
            totalBytes: 0
        };
        
        // Chat system variables (100% offline polling-based)
        this.chatSessionId = null;
        this.currentUsername = null;
        this.isConnected = false;
        this.connectedUsers = [];
        this.lastMessageId = 0;
        this.pollInterval = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.startStatusUpdates();
        this.loadNetworkInfo();
        this.updateServerStatus();
        this.initTheme();
        this.initChat();
    }

    setupEventListeners() {
        // Server management
        document.getElementById('start-server-btn').addEventListener('click', () => this.startServer());
        document.getElementById('stop-server-btn').addEventListener('click', () => this.stopServer());
        document.getElementById('cleanup-files-btn').addEventListener('click', () => this.cleanupFiles());

        // Discovery
        document.getElementById('discover-btn').addEventListener('click', () => this.discoverServers());

        // File selection
        document.getElementById('file-input').addEventListener('change', (e) => this.handleFileSelection(e));

        // Target servers
        document.getElementById('add-server-btn').addEventListener('click', () => this.addTargetServer());
        document.getElementById('server-ip-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addTargetServer();
        });

        // Transfer actions
        document.getElementById('start-transfer-btn').addEventListener('click', () => this.startTransfer());
        document.getElementById('clear-selection-btn').addEventListener('click', () => this.clearSelection());

        // Status updates
        document.getElementById('refresh-status-btn').addEventListener('click', () => this.updateTransferStatus());
        document.getElementById('clear-completed-btn').addEventListener('click', () => this.clearCompletedTransfers());

        // Files management
        document.getElementById('refresh-files-btn').addEventListener('click', () => this.loadReceivedFiles());
        document.getElementById('clear-log-btn').addEventListener('click', () => this.clearActivityLog());
        
        // Theme toggle
        document.getElementById('theme-toggle-btn').addEventListener('click', () => this.toggleTheme());
        
        // Chat system
        document.getElementById('send-message-btn').addEventListener('click', () => this.sendMessage());
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        document.getElementById('chat-input').addEventListener('input', (e) => this.updateCharCount());
        document.getElementById('change-username-btn').addEventListener('click', () => this.changeUsername());
        document.getElementById('clear-chat-btn').addEventListener('click', () => this.clearChat());
    }

    // Server Management
    async startServer() {
        try {
            const response = await fetch('/api/server/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    port: 8888,
                    password: 'lan_transfer_2024',
                    receive_dir: 'web_received'
                })
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                this.showNotification('Server started successfully!', 'success');
                this.updateServerStatus();
            } else {
                this.showNotification(`Failed to start server: ${result.message}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Error starting server: ${error.message}`, 'error');
        }
    }

    async stopServer() {
        try {
            const response = await fetch('/api/server/stop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                this.showNotification('Server stopped successfully!', 'success');
                this.updateServerStatus();
            } else {
                this.showNotification(`Failed to stop server: ${result.message}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Error stopping server: ${error.message}`, 'error');
        }
    }

    async cleanupFiles() {
        if (!confirm('Are you sure you want to delete all uploaded and received files? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch('/api/files/cleanup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                this.showNotification('Files cleaned up successfully!', 'success');
                this.updateFileList(); // Refresh file list if it exists
            } else {
                this.showNotification(`Failed to cleanup files: ${result.message}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Error cleaning up files: ${error.message}`, 'error');
        }
    }

    async updateServerStatus() {
        try {
            const response = await fetch('/api/server/status');
            const result = await response.json();

            const statusElement = document.getElementById('server-status');
            const indicatorElement = document.getElementById('status-indicator');
            const startBtn = document.getElementById('start-server-btn');
            const stopBtn = document.getElementById('stop-server-btn');
            const infoElement = document.getElementById('server-info');

            if (result.status === 'running') {
                statusElement.textContent = 'Server Running';
                indicatorElement.classList.add('running');
                startBtn.disabled = true;
                stopBtn.disabled = false;
                
                // Show server info
                document.getElementById('server-ip').textContent = result.info.server_ip;
                document.getElementById('server-port').textContent = result.info.port;
                document.getElementById('connected-clients').textContent = result.connected_clients.length;
                infoElement.style.display = 'block';
            } else {
                statusElement.textContent = 'Server Stopped';
                indicatorElement.classList.remove('running');
                startBtn.disabled = false;
                stopBtn.disabled = true;
                infoElement.style.display = 'none';
            }
        } catch (error) {
            console.error('Error updating server status:', error);
        }
    }

    // Server Discovery
    async discoverServers() {
        const discoverBtn = document.getElementById('discover-btn');
        const statusElement = document.getElementById('discovery-status');
        const serversList = document.getElementById('servers-list');
        const serversUl = document.getElementById('servers-ul');

        discoverBtn.disabled = true;
        discoverBtn.innerHTML = '<span class="spinner"></span> Discovering...';
        statusElement.textContent = 'Discovering servers on the network...';

        try {
            const response = await fetch('/api/discover');
            const result = await response.json();

            if (result.status === 'success') {
                serversUl.innerHTML = '';
                
                if (result.servers.length > 0) {
                    result.servers.forEach(server => {
                        const li = document.createElement('li');
                        li.textContent = server.display;
                        li.addEventListener('click', () => this.selectDiscoveredServer(server));
                        serversUl.appendChild(li);
                    });
                    
                    statusElement.textContent = `Found ${result.servers.length} server(s)`;
                    serversList.style.display = 'block';
                } else {
                    statusElement.textContent = 'No servers found on the network';
                    serversList.style.display = 'none';
                }
            } else {
                statusElement.textContent = `Discovery failed: ${result.message}`;
                serversList.style.display = 'none';
            }
        } catch (error) {
            statusElement.textContent = `Discovery error: ${error.message}`;
            serversList.style.display = 'none';
        } finally {
            discoverBtn.disabled = false;
            discoverBtn.textContent = 'Discover Servers';
        }
    }

    selectDiscoveredServer(server) {
        document.getElementById('server-ip-input').value = server.ip;
        document.getElementById('server-port-input').value = server.port;
        this.showNotification(`Selected server: ${server.display}`, 'success');
    }

    // File Selection
    handleFileSelection(event) {
        const files = Array.from(event.target.files);
        this.selectedFiles = files;
        this.updateSelectedFilesDisplay();
        this.updateBatchTransferButton();
    }

    updateSelectedFilesDisplay() {
        const container = document.getElementById('selected-files');
        container.innerHTML = '';

        if (this.selectedFiles.length === 0) {
            container.innerHTML = '<p class="empty-state">No files selected</p>';
            return;
        }

        this.selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${this.formatFileSize(file.size)}</div>
                </div>
                <button class="remove-file" onclick="app.removeFile(${index})">Remove</button>
            `;
            container.appendChild(fileItem);
        });
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.updateSelectedFilesDisplay();
        this.updateBatchTransferButton();
    }

    // Target Servers
    addTargetServer() {
        const ipInput = document.getElementById('server-ip-input');
        const portInput = document.getElementById('server-port-input');
        
        const ip = ipInput.value.trim();
        const port = parseInt(portInput.value) || 8888;

        if (!ip) {
            this.showNotification('Please enter a server IP address', 'warning');
            return;
        }

        // Check if server already exists
        const exists = this.targetServers.some(server => 
            server.ip === ip && server.port === port
        );

        if (exists) {
            this.showNotification('Server already added', 'warning');
            return;
        }

        const server = { ip, port };
        this.targetServers.push(server);
        
        // Clear inputs
        ipInput.value = '';
        portInput.value = '8888';
        
        this.updateTargetServersDisplay();
        this.updateBatchTransferButton();
        this.showNotification(`Added server: ${ip}:${port}`, 'success');
    }

    updateTargetServersDisplay() {
        const container = document.getElementById('target-servers-list');
        container.innerHTML = '';

        if (this.targetServers.length === 0) {
            container.innerHTML = '<p class="empty-state">No target servers added</p>';
            return;
        }

        this.targetServers.forEach((server, index) => {
            const serverItem = document.createElement('div');
            serverItem.className = 'server-item';
            serverItem.innerHTML = `
                <div class="server-info-text">${server.ip}:${server.port}</div>
                <button class="remove-server" onclick="app.removeTargetServer(${index})">Remove</button>
            `;
            container.appendChild(serverItem);
        });
    }

    removeTargetServer(index) {
        const server = this.targetServers[index];
        this.targetServers.splice(index, 1);
        this.updateTargetServersDisplay();
        this.updateBatchTransferButton();
        this.showNotification(`Removed server: ${server.ip}:${server.port}`, 'success');
    }

    updateBatchTransferButton() {
        const btn = document.getElementById('start-transfer-btn');
        const canTransfer = this.selectedFiles.length > 0 && this.targetServers.length > 0;
        btn.disabled = !canTransfer;
    }

    // Batch Transfer
    async startTransfer() {
        if (this.selectedFiles.length === 0 || this.targetServers.length === 0) {
            this.showNotification('Please select files and target servers', 'warning');
            return;
        }

        const transferName = document.getElementById('batch-name').value || `Transfer_${Date.now()}`;
        const password = document.getElementById('password').value || 'lan_transfer_2024';

        const formData = new FormData();
        
        // Add files
        this.selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        // Add target servers
        formData.append('target_servers', JSON.stringify(this.targetServers));
        formData.append('password', password);
        formData.append('batch_name', transferName);

        try {
            const response = await fetch('/api/upload/batch', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.status === 'success') {
                const fileCount = this.selectedFiles.length;
                const serverCount = this.targetServers.length;
                const fileText = fileCount === 1 ? 'file' : 'files';
                const serverText = serverCount === 1 ? 'server' : 'servers';
                
                this.showNotification(
                    `Transfer started: ${fileCount} ${fileText} to ${serverCount} ${serverText}`, 
                    'success'
                );
                this.clearSelection();
                this.updateTransferStatus();
            } else {
                this.showNotification(`Transfer failed: ${result.message}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Error starting transfer: ${error.message}`, 'error');
        }
    }


    // Transfer Status
    async updateTransferStatus() {
        try {
            const response = await fetch('/api/transfers/status');
            const result = await response.json();

            if (result.status === 'success') {
                const data = result.data;
                
                // Update statistics
                document.getElementById('active-transfers').textContent = data.active_transfers;
                document.getElementById('completed-transfers').textContent = data.completed_transfers;
                document.getElementById('queue-size').textContent = data.queue_size;
                document.getElementById('total-bytes').textContent = this.formatFileSize(data.statistics.total_bytes_transferred);

                // Update active transfers
                this.updateTransfersDisplay('active-transfers-container', data.transfers.active, 'Active Transfers');
                
                // Update completed transfers
                this.updateTransfersDisplay('completed-transfers-container', data.transfers.completed, 'Recent Completed Transfers');
            }
        } catch (error) {
            console.error('Error updating transfer status:', error);
        }
    }

    updateTransfersDisplay(containerId, transfers, title) {
        const container = document.getElementById(containerId);
        const parent = container.parentElement;
        const titleElement = parent.querySelector('h3');
        
        if (titleElement) {
            titleElement.textContent = title;
        }

        if (transfers.length === 0) {
            container.innerHTML = '<p class="empty-state">No transfers</p>';
            return;
        }

        container.innerHTML = '';
        transfers.forEach(transfer => {
            const transferItem = document.createElement('div');
            transferItem.className = `transfer-item ${transfer.status}`;
            
            const progressHtml = transfer.status === 'in_progress' ? `
                <div class="transfer-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${transfer.progress}%"></div>
                    </div>
                    <div class="progress-text">${transfer.progress.toFixed(1)}% - ${transfer.sent_bytes_formatted} / ${transfer.file_size_formatted}</div>
                </div>
            ` : '';

            const cancelButton = transfer.status === 'in_progress' ? 
                `<button class="btn btn-warning btn-sm" onclick="app.cancelTransfer('${transfer.id}')">Cancel</button>` : '';

            transferItem.innerHTML = `
                <div class="transfer-header">
                    <div class="transfer-filename">${transfer.filename}</div>
                    <div class="transfer-status ${transfer.status}">${transfer.status}</div>
                </div>
                <div class="transfer-details">
                    <div><strong>Size:</strong> ${transfer.file_size_formatted}</div>
                    <div><strong>Target:</strong> ${transfer.target_server}</div>
                    <div><strong>Started:</strong> ${transfer.start_time ? new Date(transfer.start_time * 1000).toLocaleTimeString() : 'N/A'}</div>
                    <div><strong>Duration:</strong> ${transfer.duration ? transfer.duration.toFixed(1) + 's' : 'N/A'}</div>
                </div>
                ${progressHtml}
                ${transfer.error_message ? `<div class="error-message">Error: ${transfer.error_message}</div>` : ''}
                ${cancelButton}
            `;
            
            container.appendChild(transferItem);
        });
    }

    async cancelTransfer(taskId) {
        try {
            const response = await fetch(`/api/transfers/${taskId}/cancel`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.showNotification('Transfer cancelled', 'success');
                this.updateTransferStatus();
            } else {
                this.showNotification(`Failed to cancel transfer: ${result.message}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Error cancelling transfer: ${error.message}`, 'error');
        }
    }

    // Files Management
    async loadReceivedFiles() {
        try {
            const response = await fetch('/api/files');
            const result = await response.json();

            if (result.status === 'success') {
                this.updateFilesDisplay(result.files);
            }
        } catch (error) {
            console.error('Error loading files:', error);
        }
    }

    updateFilesDisplay(files) {
        const container = document.getElementById('files-list');

        if (files.length === 0) {
            container.innerHTML = '<p class="empty-state">No files received yet.</p>';
            return;
        }

        container.innerHTML = '';
        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <div class="file-details">
                    <div class="file-name">${file.name}</div>
                    <div class="file-meta">${file.size_formatted} - ${file.modified}</div>
                </div>
                <button class="download-btn" onclick="app.downloadFile('${file.name}')">Download</button>
            `;
            container.appendChild(fileItem);
        });
    }

    downloadFile(filename) {
        window.open(`/api/files/${filename}`, '_blank');
    }

    // Utility Functions
    clearSelection() {
        this.selectedFiles = [];
        this.targetServers = [];
        document.getElementById('file-input').value = '';
        document.getElementById('batch-name').value = '';
        this.updateSelectedFilesDisplay();
        this.updateTargetServersDisplay();
        this.updateBatchTransferButton();
    }

    clearCompletedTransfers() {
        // This would need to be implemented on the server side
        this.showNotification('Clear completed transfers feature coming soon', 'info');
    }

    clearActivityLog() {
        document.getElementById('activity-log').innerHTML = '<p>Activity log cleared.</p>';
    }

    async loadNetworkInfo() {
        try {
            const response = await fetch('/api/network/info');
            const result = await response.json();

            if (result.status === 'success') {
                document.getElementById('network-info').innerHTML = `
                    <p><strong>Local IP:</strong> ${result.local_ip}</p>
                    <p><strong>Access URL:</strong> <a href="http://${result.local_ip}:8080" target="_blank">http://${result.local_ip}:8080</a></p>
                    <p><strong>Message:</strong> ${result.message}</p>
                `;
            }
        } catch (error) {
            console.error('Error loading network info:', error);
        }
    }

    startStatusUpdates() {
        // Update server status every 5 seconds
        setInterval(() => {
            this.updateServerStatus();
        }, 5000);

        // Update transfer status every 2 seconds
        setInterval(() => {
            this.updateTransferStatus();
        }, 2000);

        // Load files every 10 seconds
        setInterval(() => {
            this.loadReceivedFiles();
        }, 10000);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showNotification(message, type = 'info') {
        const notifications = document.getElementById('notifications');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        notifications.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    // Theme Management
    initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        const themeBtn = document.getElementById('theme-toggle-btn');
        const icon = themeBtn.querySelector('i');
        const text = themeBtn.querySelector('span');
        
        if (theme === 'dark') {
            icon.className = 'fas fa-sun';
            text.textContent = 'Light Mode';
        } else {
            icon.className = 'fas fa-moon';
            text.textContent = 'Dark Mode';
        }
    }

    // Chat System (100% Offline - Polling-based)
    initChat() {
        try {
            // Auto-join chat with default username
            this.joinChat();
        } catch (error) {
            console.error('Error initializing chat:', error);
            this.updateChatStatus('Chat Error', 'error');
        }
    }
    
    async joinChat() {
        try {
            const response = await fetch('/api/chat/join', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: this.currentUsername || `User_${Math.floor(Math.random() * 1000)}`
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.chatSessionId = result.session_id;
                this.currentUsername = result.username;
                this.isConnected = true;
                this.connectedUsers = result.users;
                
                this.updateChatStatus('Connected', 'success');
                this.updateOnlineCount();
                this.loadChatHistory(result.messages);
                this.startPolling();
                
                this.showNotification('Connected to chat!', 'success');
            } else {
                this.updateChatStatus('Connection Failed', 'error');
                this.showNotification('Failed to join chat', 'error');
            }
        } catch (error) {
            console.error('Error joining chat:', error);
            this.updateChatStatus('Connection Error', 'error');
            this.showNotification('Chat connection error', 'error');
        }
    }
    
    startPolling() {
        // Poll for new messages every 2 seconds
        this.pollInterval = setInterval(() => {
            this.pollForMessages();
        }, 2000);
    }
    
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }
    
    async pollForMessages() {
        if (!this.isConnected) return;
        
        try {
            const response = await fetch(`/api/chat/messages?since=${this.lastMessageId}`);
            const result = await response.json();
            
            if (result.status === 'success') {
                // Update user list
                this.connectedUsers = result.users;
                this.updateOnlineCount();
                
                // Process new messages
                result.messages.forEach(message => {
                    if (message.type === 'user') {
                        this.addChatMessage(message);
                    } else if (message.type === 'system') {
                        this.addSystemMessage(message.message, 'system');
                    }
                    
                    // Update last message ID
                    const msgId = parseInt(message.id.split('_')[1]);
                    if (msgId > this.lastMessageId) {
                        this.lastMessageId = msgId;
                    }
                });
            }
        } catch (error) {
            console.error('Error polling messages:', error);
        }
    }
    
    updateChatStatus(status, type) {
        const statusElement = document.getElementById('chat-status');
        statusElement.textContent = status;
        statusElement.className = `chat-status ${type}`;
    }
    
    updateOnlineCount() {
        const countElement = document.getElementById('online-count');
        const count = this.connectedUsers.length;
        countElement.textContent = `${count} user${count !== 1 ? 's' : ''} online`;
    }
    
    addChatMessage(message) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageElement = document.createElement('div');
        messageElement.className = 'chat-message';
        messageElement.innerHTML = `
            <div class="message-header">
                <span class="message-username">${message.username}</span>
                <span class="message-time">${message.timestamp}</span>
            </div>
            <div class="message-content">${this.escapeHtml(message.message)}</div>
        `;
        
        messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    addSystemMessage(message, type) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageElement = document.createElement('div');
        messageElement.className = `system-message ${type}`;
        messageElement.innerHTML = `
            <div class="system-message-content">
                <i class="fas fa-info-circle"></i>
                <span>${this.escapeHtml(message)}</span>
            </div>
        `;
        
        messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    loadChatHistory(messages) {
        const messagesContainer = document.getElementById('chat-messages');
        
        // Clear welcome message
        const welcomeElement = messagesContainer.querySelector('.chat-welcome');
        if (welcomeElement) {
            welcomeElement.remove();
        }
        
        // Add historical messages
        messages.forEach(message => {
            this.addChatMessage(message);
        });
    }
    
    async sendMessage() {
        if (!this.isConnected || !this.chatSessionId) {
            this.showNotification('Not connected to chat', 'error');
            return;
        }
        
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) {
            return;
        }
        
        try {
            const response = await fetch('/api/chat/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.chatSessionId,
                    message: message
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                // Clear input
                input.value = '';
                this.updateCharCount();
            } else {
                this.showNotification('Failed to send message', 'error');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.showNotification('Error sending message', 'error');
        }
    }
    
    updateCharCount() {
        const input = document.getElementById('chat-input');
        const countElement = document.getElementById('char-count');
        const count = input.value.length;
        countElement.textContent = `${count}/500`;
        
        if (count > 450) {
            countElement.className = 'char-count warning';
        } else {
            countElement.className = 'char-count';
        }
    }
    
    async changeUsername() {
        const newUsername = prompt('Enter new username:', this.currentUsername || 'User');
        
        if (newUsername && newUsername.trim() && newUsername.trim() !== this.currentUsername) {
            try {
                const response = await fetch('/api/chat/change-username', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: this.chatSessionId,
                        username: newUsername.trim()
                    })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    this.currentUsername = result.new_username;
                    this.showNotification(`Username changed to ${this.currentUsername}`, 'success');
                } else {
                    this.showNotification('Failed to change username', 'error');
                }
            } catch (error) {
                console.error('Error changing username:', error);
                this.showNotification('Error changing username', 'error');
            }
        }
    }
    
    clearChat() {
        if (!confirm('Are you sure you want to clear the chat? This will only clear your view.')) {
            return;
        }
        
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = `
            <div class="chat-welcome">
                <p><i class="fas fa-info-circle"></i> Chat cleared</p>
                <p>You can continue chatting with other users.</p>
            </div>
        `;
    }
    
    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Cleanup when page is unloaded
    cleanup() {
        this.stopPolling();
        if (this.chatSessionId) {
            // Leave chat room
            fetch('/api/chat/leave', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.chatSessionId })
            }).catch(() => {}); // Ignore errors during cleanup
        }
    }
}

// Initialize the app when the page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new EnhancedFileTransferApp();
});

// Cleanup when page is unloaded
window.addEventListener('beforeunload', () => {
    if (app) {
        app.cleanup();
    }
});
