// DeepDrone - Minimal ChatGPT-style Interface

class DeepDrone {
    constructor() {
        this.ws = null;
        this.isAIConfigured = false;
        this.isDroneConnected = false;
        this.telemetryInterval = null;
        this.mapPath = [];
        this.mapBase = null;

        this.init();
    }

    init() {
        this.cacheElements();
        this.attachEventListeners();
        this.loadSavedConfig();
        this.checkHealth();
    }

    cacheElements() {
        // Sidebar
        this.sidebar = document.getElementById('sidebar');
        this.toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
        this.openSidebarBtn = document.getElementById('openSidebarBtn');
        this.newChatBtn = document.getElementById('newChatBtn');

        // Modals
        this.settingsModal = document.getElementById('settingsModal');
        this.settingsBtn = document.getElementById('settingsBtn');
        this.closeSettingsBtn = document.getElementById('closeSettingsBtn');
        this.missionModal = document.getElementById('missionModal');
        this.missionBtn = document.getElementById('missionBtn');
        this.closeMissionBtn = document.getElementById('closeMissionBtn');
        this.sessionsModal = document.getElementById('sessionsModal');
        this.sessionsBtn = document.getElementById('sessionsBtn');
        this.closeSessionsBtn = document.getElementById('closeSessionsBtn');

        // Settings form
        this.provider = document.getElementById('provider');
        this.apiKeyGroup = document.getElementById('apiKeyGroup');
        this.apiKey = document.getElementById('apiKey');
        this.modelGroup = document.getElementById('modelGroup');
        this.model = document.getElementById('model');
        this.saveBtn = document.getElementById('saveBtn');
        this.aiStatus = document.getElementById('aiStatus');

        // Drone form
        this.connectionString = document.getElementById('connectionString');
        this.connectBtn = document.getElementById('connectBtn');
        this.disconnectBtn = document.getElementById('disconnectBtn');
        this.droneStatus = document.getElementById('droneStatus');

        // Chat
        this.messages = document.getElementById('messages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');

        // Top bar
        this.currentModel = document.getElementById('currentModel');
        this.droneStatusBadge = document.getElementById('droneStatusBadge');

        // Telemetry
        this.telemetryPanel = document.getElementById('telemetryPanel');
        this.telemetryToggleBtn = document.getElementById('telemetryToggleBtn');
        this.closeTelemetryBtn = document.getElementById('closeTelemetryBtn');
        this.telemMode = document.getElementById('telemMode');
        this.telemArmed = document.getElementById('telemArmed');
        this.telemAlt = document.getElementById('telemAlt');
        this.telemBattery = document.getElementById('telemBattery');
        this.mapCanvas = document.getElementById('mapCanvas');
        this.mapLat = document.getElementById('mapLat');
        this.mapLon = document.getElementById('mapLon');
        this.mapAlt = document.getElementById('mapAlt');

        // Mission builder
        this.addWaypointBtn = document.getElementById('addWaypointBtn');
        this.waypointList = document.getElementById('waypointList');
        this.uploadMissionBtn = document.getElementById('uploadMissionBtn');
        this.executeMissionBtn = document.getElementById('executeMissionBtn');
        this.missionStatus = document.getElementById('missionStatus');

        // Sessions
        this.sessionsList = document.getElementById('sessionsList');
        this.refreshSessionsBtn = document.getElementById('refreshSessionsBtn');
    }

    attachEventListeners() {
        // Sidebar toggle
        this.toggleSidebarBtn.addEventListener('click', () => this.toggleSidebar());
        this.openSidebarBtn.addEventListener('click', () => this.toggleSidebar());
        this.newChatBtn.addEventListener('click', () => this.newChat());

        // Modal controls
        this.settingsBtn.addEventListener('click', () => this.openModal(this.settingsModal));
        this.closeSettingsBtn.addEventListener('click', () => this.closeModal(this.settingsModal));
        this.missionBtn.addEventListener('click', () => this.openMissionModal());
        this.closeMissionBtn.addEventListener('click', () => this.closeModal(this.missionModal));
        this.sessionsBtn.addEventListener('click', () => this.openSessionsModal());
        this.closeSessionsBtn.addEventListener('click', () => this.closeModal(this.sessionsModal));

        // Click outside modal to close
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) this.closeModal(this.settingsModal);
        });
        this.missionModal.addEventListener('click', (e) => {
            if (e.target === this.missionModal) this.closeModal(this.missionModal);
        });
        this.sessionsModal.addEventListener('click', (e) => {
            if (e.target === this.sessionsModal) this.closeModal(this.sessionsModal);
        });

        // Settings
        this.provider.addEventListener('change', () => this.onProviderChange());
        this.model.addEventListener('change', () => this.updateSaveButton());
        this.apiKey.addEventListener('input', () => this.updateSaveButton());
        this.saveBtn.addEventListener('click', () => this.saveSettings());

        // Drone
        this.connectBtn.addEventListener('click', () => this.connectDrone());
        this.disconnectBtn.addEventListener('click', () => this.disconnectDrone());

        // Chat
        this.messageInput.addEventListener('input', () => this.handleInputChange());
        this.messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.sendBtn.addEventListener('click', () => this.sendMessage());

        // Suggestion cards
        document.querySelectorAll('.suggestion-card').forEach(card => {
            card.addEventListener('click', () => {
                const prompt = card.dataset.prompt;
                this.messageInput.value = prompt;
                this.handleInputChange();
                this.sendMessage();
            });
        });

        // Telemetry
        this.telemetryToggleBtn.addEventListener('click', () => this.toggleTelemetry());
        this.closeTelemetryBtn.addEventListener('click', () => this.toggleTelemetry());

        // Mission builder
        this.addWaypointBtn.addEventListener('click', () => this.addWaypointRow());
        this.uploadMissionBtn.addEventListener('click', () => this.uploadMission());
        this.executeMissionBtn.addEventListener('click', () => this.executeMission());

        // Sessions
        this.refreshSessionsBtn.addEventListener('click', () => this.loadSessions());
    }

    // Sidebar
    toggleSidebar() {
        this.sidebar.classList.toggle('collapsed');
        if (this.sidebar.classList.contains('collapsed')) {
            this.openSidebarBtn.style.display = 'flex';
        } else {
            this.openSidebarBtn.style.display = 'none';
        }
    }

    newChat() {
        this.messages.innerHTML = `
            <div class="welcome-screen">
                <h1>DeepDrone</h1>
                <p>Control your drone with natural language</p>
                <div class="suggestion-grid">
                    <button class="suggestion-card" data-prompt="Take off to 20 meters">
                        <div class="suggestion-title">Take Off</div>
                        <div class="suggestion-text">Take off to 20 meters</div>
                    </button>
                    <button class="suggestion-card" data-prompt="What's my current altitude and battery status?">
                        <div class="suggestion-title">Check Status</div>
                        <div class="suggestion-text">Get altitude and battery</div>
                    </button>
                    <button class="suggestion-card" data-prompt="Fly in a square pattern with 30m sides">
                        <div class="suggestion-title">Square Pattern</div>
                        <div class="suggestion-text">Fly in a square pattern</div>
                    </button>
                    <button class="suggestion-card" data-prompt="Return home and land safely">
                        <div class="suggestion-title">Return Home</div>
                        <div class="suggestion-text">Return and land safely</div>
                    </button>
                </div>
            </div>
        `;
        // Reattach suggestion card listeners
        this.attachEventListeners();
    }

    // Modal controls
    openModal(modal) {
        modal.classList.add('open');
    }

    closeModal(modal) {
        modal.classList.remove('open');
    }

    openMissionModal() {
        if (!this.waypointList.children.length) {
            this.addWaypointRow();
        }
        this.openModal(this.missionModal);
    }

    openSessionsModal() {
        this.openModal(this.sessionsModal);
        this.loadSessions();
    }

    addWaypointRow(defaults = {}) {
        const row = document.createElement('div');
        row.className = 'waypoint-row';

        row.innerHTML = `
            <div class="waypoint-fields">
                <input type="number" step="0.000001" class="input waypoint-input" placeholder="Lat" value="${defaults.lat ?? ''}">
                <input type="number" step="0.000001" class="input waypoint-input" placeholder="Lon" value="${defaults.lon ?? ''}">
                <input type="number" step="0.1" class="input waypoint-input" placeholder="Alt (m)" value="${defaults.alt ?? ''}">
                <input type="number" step="0.1" class="input waypoint-input" placeholder="Delay (s)" value="${defaults.delay ?? ''}">
            </div>
            <button class="icon-btn-small waypoint-remove" title="Remove">×</button>
        `;

        row.querySelector('.waypoint-remove').addEventListener('click', () => row.remove());
        this.waypointList.appendChild(row);
    }

    async uploadMission() {
        const waypoints = this.collectWaypoints();
        if (!waypoints.length) {
            this.showStatus(this.missionStatus, 'Add at least one waypoint', 'error');
            return;
        }

        try {
            const response = await fetch('/api/mission/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ waypoints })
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Mission upload failed');
            }

            this.showStatus(this.missionStatus, `✓ Uploaded ${data.waypoints} waypoints`, 'success');
        } catch (error) {
            this.showStatus(this.missionStatus, `✗ ${error.message}`, 'error');
        }
    }

    async executeMission() {
        try {
            const response = await fetch('/api/mission/execute', { method: 'POST' });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Mission execution failed');
            }

            this.showStatus(this.missionStatus, `✓ ${data.message}`, 'success');
        } catch (error) {
            this.showStatus(this.missionStatus, `✗ ${error.message}`, 'error');
        }
    }

    collectWaypoints() {
        const waypoints = [];
        this.waypointList.querySelectorAll('.waypoint-row').forEach(row => {
            const inputs = row.querySelectorAll('.waypoint-input');
            const lat = parseFloat(inputs[0].value);
            const lon = parseFloat(inputs[1].value);
            const alt = parseFloat(inputs[2].value);
            const delay = parseFloat(inputs[3].value) || 0;

            if (!Number.isNaN(lat) && !Number.isNaN(lon) && !Number.isNaN(alt)) {
                waypoints.push({ lat, lon, alt, delay });
            }
        });
        return waypoints;
    }

    async loadSessions() {
        this.sessionsList.innerHTML = '<div class="session-empty">Loading sessions...</div>';
        try {
            const response = await fetch('/api/sessions');
            const data = await response.json();
            const sessions = data.sessions || [];

            if (!sessions.length) {
                this.sessionsList.innerHTML = '<div class="session-empty">No sessions logged yet.</div>';
                return;
            }

            this.sessionsList.innerHTML = '';
            sessions.forEach(session => {
                const item = document.createElement('div');
                item.className = 'session-item';
                item.innerHTML = `
                    <div class="session-info">
                        <div class="session-id">${session.id}</div>
                        <div class="session-meta">${session.updated_at}</div>
                    </div>
                    <button class="btn-secondary session-replay">Replay</button>
                `;
                item.querySelector('.session-replay').addEventListener('click', () => this.replaySession(session.id));
                this.sessionsList.appendChild(item);
            });
        } catch (error) {
            this.sessionsList.innerHTML = '<div class="session-empty">Failed to load sessions.</div>';
        }
    }

    async replaySession(sessionId) {
        try {
            const response = await fetch(`/api/sessions/${sessionId}`);
            const data = await response.json();
            const events = data.events || [];

            if (!events.length) {
                this.addMessage('No events found for this session.', 'error');
                return;
            }

            this.messages.innerHTML = '';
            this.addMessage(`Replaying session ${sessionId}...`, 'assistant');
            let delay = 500;

            events.forEach(event => {
                if (event.type === 'user_message' || event.type === 'ai_message') {
                    setTimeout(() => {
                        const type = event.type === 'user_message' ? 'user' : 'assistant';
                        this.addMessage(event.payload.message, type);
                    }, delay);
                    delay += 500;
                }
            });
        } catch (error) {
            this.addMessage('Failed to replay session.', 'error');
        }
    }

    // AI Configuration
    getProviderModels(provider) {
        const models = {
            openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
            anthropic: ['claude-3-5-sonnet-20241022', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
            google: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'],
            ollama: []
        };
        return models[provider] || [];
    }

    async onProviderChange() {
        const provider = this.provider.value;

        if (!provider) {
            this.apiKeyGroup.style.display = 'none';
            this.modelGroup.style.display = 'none';
            this.saveAIBtn.disabled = true;
            return;
        }

        this.apiKeyGroup.style.display = provider === 'ollama' ? 'none' : 'block';
        this.modelGroup.style.display = 'block';
        this.model.innerHTML = '<option value="">Loading...</option>';

        if (provider === 'ollama') {
            await this.loadOllamaModels();
        } else {
            const models = this.getProviderModels(provider);
            this.model.innerHTML = '<option value="">Select model...</option>';
            models.forEach(m => {
                const option = document.createElement('option');
                option.value = m;
                option.textContent = m;
                this.model.appendChild(option);
            });
        }

        this.updateSaveButton();
    }

    async loadOllamaModels() {
        try {
            const response = await fetch('/api/ollama/models');
            const data = await response.json();

            this.model.innerHTML = '<option value="">Select model...</option>';

            if (data.models && data.models.length > 0) {
                data.models.forEach(m => {
                    const option = document.createElement('option');
                    option.value = m;
                    option.textContent = m;
                    this.model.appendChild(option);
                });
            } else {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = data.error || 'No models found';
                this.model.appendChild(option);
            }
        } catch (error) {
            console.error('Error loading Ollama models:', error);
            this.showStatus(this.aiStatus, 'Error loading Ollama models', 'error');
        }
    }

    updateSaveButton() {
        const provider = this.provider.value;
        const model = this.model.value;
        const apiKey = this.apiKey.value;

        if (provider === 'ollama') {
            this.saveBtn.disabled = !provider || !model;
        } else {
            this.saveBtn.disabled = !provider || !model || !apiKey;
        }
    }

    async saveSettings() {
        // Save AI config
        const provider = this.provider.value;
        const model = this.model.value;
        const apiKey = provider === 'ollama' ? null : this.apiKey.value;

        if (provider && model) {
            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ provider, model, api_key: apiKey })
                });

                const data = await response.json();

                if (response.ok) {
                    this.isAIConfigured = true;
                    this.updateStatus(true, this.isDroneConnected);
                    this.showStatus(this.aiStatus, '✓ ' + data.message, 'success');
                    this.currentModel.textContent = `${provider} - ${model.split('/').pop()}`;
                    this.saveConfig({ provider, model });

                    // Enable send button
                    this.sendBtn.disabled = false;
                    if (this.messageInput) {
                        this.messageInput.disabled = false;
                    }

                    // Connect WebSocket
                    console.log('🔌 Connecting WebSocket after AI config...');
                    this.connectWebSocket();

                    setTimeout(() => {
                        this.closeModal(this.settingsModal);
                    }, 1500);
                } else {
                    throw new Error(data.detail || 'Configuration failed');
                }
            } catch (error) {
                this.showStatus(this.aiStatus, '✗ ' + error.message, 'error');
            }
        }
    }

    // Drone Connection
    async connectDrone() {
        const connStr = this.connectionString.value;

        if (!connStr) {
            this.showStatus(this.droneStatus, 'Please enter a connection string', 'error');
            return;
        }

        try {
            this.connectBtn.disabled = true;
            this.connectBtn.textContent = 'Connecting...';
            this.showStatus(this.droneStatus, 'Connecting to drone...', 'success');

            const response = await fetch('/api/drone/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ connection_string: connStr })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Connection failed');
            }

            const data = await response.json();

            this.isDroneConnected = true;
            this.updateStatus(this.isAIConfigured, true);
            this.showStatus(this.droneStatus, '✓ ' + data.message, 'success');
            this.connectBtn.style.display = 'none';
            this.disconnectBtn.style.display = 'block';
            this.startTelemetry();

        } catch (error) {
            console.error('Drone connection error:', error);
            this.showStatus(this.droneStatus, '✗ ' + error.message, 'error');
            this.connectBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                    <path d="M2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
                Connect Drone
            `;
        } finally {
            this.connectBtn.disabled = false;
        }
    }

    async disconnectDrone() {
        try {
            await fetch('/api/drone/disconnect', { method: 'POST' });

            this.isDroneConnected = false;
            this.updateStatus(this.isAIConfigured, false);
            this.showStatus(this.droneStatus, 'Disconnected', 'success');
            this.connectBtn.style.display = 'block';
            this.disconnectBtn.style.display = 'none';
            this.stopTelemetry();
        } catch (error) {
            console.error('Error disconnecting:', error);
        }
    }

    // Telemetry
    toggleTelemetry() {
        this.telemetryPanel.classList.toggle('open');
    }

    startTelemetry() {
        this.stopTelemetry();
    }

    stopTelemetry() {
        if (this.telemetryInterval) {
            clearInterval(this.telemetryInterval);
            this.telemetryInterval = null;
        }
    }

    updateTelemetryFromPayload(data) {
        if (!data) {
            return;
        }

        if (data.connected !== this.isDroneConnected) {
            this.isDroneConnected = data.connected;
            this.updateStatus(this.isAIConfigured, this.isDroneConnected);
        }

        if (!data.connected) {
            this.telemMode.textContent = '-';
            this.telemArmed.textContent = '-';
            this.telemAlt.textContent = '-';
            this.telemBattery.textContent = '-';
            this.mapLat.textContent = '-';
            this.mapLon.textContent = '-';
            this.mapAlt.textContent = '-';
            this.mapPath = [];
            this.mapBase = null;
            if (this.mapCanvas) {
                const ctx = this.mapCanvas.getContext('2d');
                ctx.clearRect(0, 0, this.mapCanvas.width, this.mapCanvas.height);
            }
            return;
        }

        this.telemMode.textContent = data.mode || '-';
        this.telemArmed.textContent = data.armed ? 'Yes' : 'No';
        this.telemAlt.textContent = data.altitude ? `${data.altitude.toFixed(1)}m` : '-';
        this.telemBattery.textContent = data.battery ? `${data.battery}%` : '-';

        if (data.gps) {
            const lat = data.gps.lat;
            const lon = data.gps.lon;
            if (typeof lat === 'number' && typeof lon === 'number') {
                this.updateMap(lat, lon, data.altitude || 0);
            }
        }
    }

    updateMap(lat, lon, alt) {
        if (!this.mapCanvas) return;

        const canvas = this.mapCanvas;
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        if (!this.mapBase) {
            this.mapBase = { lat, lon };
        }

        this.mapLat.textContent = lat.toFixed(6);
        this.mapLon.textContent = lon.toFixed(6);
        this.mapAlt.textContent = alt.toFixed(1) + 'm';

        this.mapPath.push({ lat, lon });
        if (this.mapPath.length > 100) {
            this.mapPath.shift();
        }

        const lats = this.mapPath.map(point => point.lat);
        const lons = this.mapPath.map(point => point.lon);
        const minLat = Math.min(...lats);
        const maxLat = Math.max(...lats);
        const minLon = Math.min(...lons);
        const maxLon = Math.max(...lons);

        const padding = 16;
        const latRange = maxLat - minLat || 0.0001;
        const lonRange = maxLon - minLon || 0.0001;

        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = '#1f1f1f';
        ctx.fillRect(0, 0, width, height);

        ctx.strokeStyle = '#3a3a3a';
        ctx.lineWidth = 1;
        ctx.strokeRect(padding, padding, width - padding * 2, height - padding * 2);

        ctx.beginPath();
        this.mapPath.forEach((point, index) => {
            const x = padding + ((point.lon - minLon) / lonRange) * (width - padding * 2);
            const y = padding + ((maxLat - point.lat) / latRange) * (height - padding * 2);
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.strokeStyle = '#10a37f';
        ctx.lineWidth = 2;
        ctx.stroke();

        const last = this.mapPath[this.mapPath.length - 1];
        const lastX = padding + ((last.lon - minLon) / lonRange) * (width - padding * 2);
        const lastY = padding + ((maxLat - last.lat) / latRange) * (height - padding * 2);
        ctx.fillStyle = '#fbbf24';
        ctx.beginPath();
        ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
        ctx.fill();
    }

    // Chat
    handleInputChange() {
        const value = this.messageInput.value.trim();
        // Only disable if no value, let sendMessage handle AI config check
        this.sendBtn.disabled = !value;

        // Auto-resize textarea
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
    }

    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    sendMessage() {
        const message = this.messageInput.value.trim();

        if (!message) return;

        // Check if AI is configured
        if (!this.isAIConfigured) {
            this.addMessage('Please configure an AI provider first. Click Settings in the sidebar to get started.', 'error');
            this.messageInput.value = '';
            return;
        }

        // Remove welcome screen
        const welcome = this.messages.querySelector('.welcome-screen');
        if (welcome) welcome.remove();

        // Add user message
        this.addMessage(message, 'user');

        // Add typing indicator
        this.addTypingIndicator();

        // Send to server
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('📤 Sending message:', message);
            this.ws.send(JSON.stringify({ message }));
        } else {
            console.error('❌ WebSocket not connected. State:', this.ws ? this.ws.readyState : 'null');
            this.removeTypingIndicator();
            this.addMessage('Error: Not connected to server. Please refresh the page.', 'error');
        }

        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.handleInputChange();
    }

    addMessage(content, type, metadata = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;

        messageDiv.appendChild(contentDiv);

        // Add thinking section if metadata includes thinking
        if (metadata && metadata.thinking && metadata.thinking_time) {
            const thinkingDiv = document.createElement('div');
            thinkingDiv.className = 'thinking-section';
            
            const thinkingHeader = document.createElement('div');
            thinkingHeader.className = 'thinking-header';
            thinkingHeader.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
                <span>Thought for ${metadata.thinking_time}s</span>
                <svg class="chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"/>
                </svg>
            `;
            
            const thinkingContent = document.createElement('div');
            thinkingContent.className = 'thinking-content';
            thinkingContent.textContent = metadata.thinking;
            
            thinkingDiv.appendChild(thinkingHeader);
            thinkingDiv.appendChild(thinkingContent);
            
            // Toggle thinking on click
            thinkingHeader.addEventListener('click', () => {
                thinkingDiv.classList.toggle('expanded');
            });
            
            messageDiv.appendChild(thinkingDiv);
        }

        this.messages.appendChild(messageDiv);

        // Scroll to bottom
        this.scrollToBottom();
    }

    addTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'message assistant typing-indicator';
        indicator.id = 'typingIndicator';
        indicator.innerHTML = `
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        this.messages.appendChild(indicator);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    scrollToBottom() {
        this.messages.parentElement.scrollTop = this.messages.parentElement.scrollHeight;
    }

    // WebSocket
    connectWebSocket() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('✅ WebSocket connected');
        };

        this.ws.onmessage = (event) => {
            console.log('📨 Received message:', event.data);
            const data = JSON.parse(event.data);

            if (data.type === 'ai_message') {
                // Remove typing indicator
                this.removeTypingIndicator();
                console.log('🤖 AI response:', data.content);
                this.addMessage(data.content, 'assistant', data.metadata);
            } else if (data.type === 'error') {
                // Remove typing indicator
                this.removeTypingIndicator();
                console.log('❌ Error:', data.content);
                this.addMessage(data.content, 'error');
            } else if (data.type === 'user_message') {
                // User message already shown, just for acknowledgment
                console.log('✓ User message acknowledged');
            } else if (data.type === 'telemetry') {
                this.updateTelemetryFromPayload(data.content);
            }
        };

        this.ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            this.removeTypingIndicator();
        };

        this.ws.onclose = () => {
            console.log('🔌 WebSocket closed');
            this.removeTypingIndicator();
            setTimeout(() => {
                if (this.isAIConfigured) {
                    console.log('🔄 Attempting to reconnect...');
                    this.connectWebSocket();
                }
            }, 3000);
        };
    }

    // Status
    updateStatus(aiConfigured, droneConnected) {
        // Update drone status badge
        if (droneConnected) {
            this.droneStatusBadge.classList.add('connected');
            this.droneStatusBadge.querySelector('span').textContent = 'Drone: Connected';
        } else {
            this.droneStatusBadge.classList.remove('connected');
            this.droneStatusBadge.querySelector('span').textContent = 'Drone: Not Connected';
        }
    }

    showStatus(element, message, type) {
        element.textContent = message;
        element.className = `status-msg ${type}`;

        setTimeout(() => {
            element.className = 'status-msg';
        }, 5000);
    }

    // Storage
    saveConfig(config) {
        localStorage.setItem('deepdrone_config', JSON.stringify(config));
    }

    loadSavedConfig() {
        const saved = localStorage.getItem('deepdrone_config');
        if (saved) {
            try {
                const config = JSON.parse(saved);
                this.provider.value = config.provider;
                this.onProviderChange().then(() => {
                    this.model.value = config.model;
                    this.updateSaveButton();
                });
            } catch (error) {
                console.error('Error loading config:', error);
            }
        }
    }

    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();

            if (data.llm_configured) {
                this.isAIConfigured = true;
                this.sendBtn.disabled = false;
            }

            if (data.drone_connected) {
                this.isDroneConnected = true;
                this.startTelemetry();
            }

            this.updateStatus(data.llm_configured, data.drone_connected);
            this.connectWebSocket();
        } catch (error) {
            console.error('Health check failed:', error);
        }
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    new DeepDrone();
});
