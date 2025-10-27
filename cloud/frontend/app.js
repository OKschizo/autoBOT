// ============================================================================
// AUTO FINANCE BOT MANAGER - Frontend JavaScript
// ============================================================================

// Configuration
const API_URL = window.location.origin;
let GOOGLE_CLIENT_ID = null;

// State
let currentUser = null;
let currentTab = 'bots';
let bots = [];
let isWaitingForResponse = false;
let refreshInterval = null;

// ============================================================================
// INITIALIZATION
// ============================================================================

window.onload = async function() {
    try {
        // Fetch config from backend
        const configResponse = await fetch(`${API_URL}/api/config`);
        const config = await configResponse.json();
        GOOGLE_CLIENT_ID = config.google_client_id;
        
        // Setup event listeners first
        setupEventListeners();
        
        // Wait for Google Sign-In library to load
        const initGoogleSignIn = () => {
            if (typeof google !== 'undefined' && google.accounts) {
                // Initialize Google Sign-In
                google.accounts.id.initialize({
                    client_id: GOOGLE_CLIENT_ID,
                    callback: handleCredentialResponse
                });
                
                // Render sign-in button
                const container = document.getElementById('google-signin-container');
                if (container) {
                    google.accounts.id.renderButton(
                        container,
                        { 
                            theme: 'outline',
                            size: 'large',
                            text: 'signin_with',
                            shape: 'rectangular',
                            width: 200
                        }
                    );
                }
                
                // Check if user is already signed in
                const savedUser = localStorage.getItem('autoFinanceUser');
                if (savedUser) {
                    currentUser = JSON.parse(savedUser);
                    showAuthenticatedUI();
                }
            } else {
                // Retry after a short delay
                setTimeout(initGoogleSignIn, 100);
            }
        };
        
        initGoogleSignIn();
        
    } catch (error) {
        console.error('Failed to initialize app:', error);
        showNotification('Failed to load app. Please refresh.', 'error');
    }
};

// ============================================================================
// AUTHENTICATION
// ============================================================================

async function handleCredentialResponse(response) {
    try {
        const result = await fetch(`${API_URL}/api/auth/google`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_token: response.credential })
        });
        
        if (!result.ok) throw new Error('Authentication failed');
        
        currentUser = await result.json();
        localStorage.setItem('autoFinanceUser', JSON.stringify(currentUser));
        
        showAuthenticatedUI();
        showNotification('Signed in successfully!', 'success');
        
    } catch (error) {
        console.error('Sign-in error:', error);
        showNotification('Failed to sign in. Please try again.', 'error');
    }
}

function showAuthenticatedUI() {
    // Hide sign-in button, show user info
    const signInContainer = document.getElementById('google-signin-container');
    if (signInContainer) signInContainer.style.display = 'none';
    
    const userInfo = document.getElementById('user-info');
    if (userInfo) {
        userInfo.style.display = 'flex';
        const userName = document.getElementById('user-name');
        const userAvatar = document.getElementById('user-avatar');
        if (userName) userName.textContent = currentUser.name;
        if (userAvatar) userAvatar.src = currentUser.picture || 'https://via.placeholder.com/32';
    }
    
    // Enable chat input
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    if (chatInput) chatInput.disabled = false;
    if (sendButton) sendButton.disabled = false;
    
    // Load initial data
    loadBots();
    loadDataStatus();
    
    // Start auto-refresh
    refreshInterval = setInterval(() => {
        if (currentTab === 'bots') loadBots();
        if (currentTab === 'data') loadDataStatus();
    }, 5000);
}

function signOut() {
    currentUser = null;
    localStorage.removeItem('autoFinanceUser');
    if (typeof google !== 'undefined' && google.accounts) {
        google.accounts.id.disableAutoSelect();
    }
    
    // Clear refresh interval
    if (refreshInterval) clearInterval(refreshInterval);
    
    // Reset UI
    const signInContainer = document.getElementById('google-signin-container');
    const userInfo = document.getElementById('user-info');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const botsList = document.getElementById('bots-list');
    const chatMessages = document.getElementById('chat-messages');
    
    if (signInContainer) signInContainer.style.display = 'block';
    if (userInfo) userInfo.style.display = 'none';
    if (chatInput) chatInput.disabled = true;
    if (sendButton) sendButton.disabled = true;
    
    // Clear data
    bots = [];
    if (botsList) botsList.innerHTML = '';
    if (chatMessages) chatMessages.innerHTML = getWelcomeMessage();
    
    showNotification('Signed out successfully', 'success');
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
    
    // Add bot form
    document.getElementById('add-bot-form').addEventListener('submit', handleAddBot);
    
    // Chat input
    const chatInput = document.getElementById('chat-input');
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    document.getElementById('send-button').addEventListener('click', sendMessage);
    
    // Modal close
    document.querySelector('.modal-close').addEventListener('click', closeModal);
    document.getElementById('modal-close-btn').addEventListener('click', closeModal);
    document.getElementById('modal-delete-btn').addEventListener('click', handleDeleteBot);
    
    // Click outside modal to close
    document.getElementById('bot-modal').addEventListener('click', (e) => {
        if (e.target.id === 'bot-modal') closeModal();
    });
}

function switchTab(tabName) {
    currentTab = tabName;
    
    // Update nav tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
    
    // Load data for tab
    if (tabName === 'bots' && currentUser) loadBots();
    if (tabName === 'data' && currentUser) loadDataStatus();
    if (tabName === 'chat' && currentUser) loadConversationHistory();
}

// ============================================================================
// BOT MANAGEMENT
// ============================================================================

async function loadBots() {
    if (!currentUser) return;
    
    try {
        const response = await fetch(`${API_URL}/api/bots`);
        if (!response.ok) throw new Error('Failed to load bots');
        
        const data = await response.json();
        bots = data.bots || data || [];
        renderBots();
        
    } catch (error) {
        console.error('Error loading bots:', error);
        bots = [];
        renderBots();
    }
}

function renderBots() {
    const container = document.getElementById('bots-list');
    
    if (bots.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 40px;">No bots configured yet. Add your first bot above!</p>';
        return;
    }
    
    container.innerHTML = bots.map(bot => {
        // Handle both bot.id and bot.bot_id for compatibility
        const botId = bot.bot_id || bot.id;
        return `
        <div class="bot-card" onclick="showBotDetails('${botId}')">
            <div class="bot-card-header">
                <div class="bot-card-title">
                    <div class="bot-icon">
                        ${bot.platform === 'telegram' ? '📱' : '💬'}
                    </div>
                    <div>
                        <h3>${bot.name}</h3>
                        <p>${bot.platform === 'telegram' ? 'Telegram' : 'Discord'}</p>
                    </div>
                </div>
                <div class="status-badge ${bot.status}">${bot.status}</div>
            </div>
            <div class="bot-card-info">
                <div class="bot-info-item">
                    <span class="label">Model:</span>
                    <span class="value">${bot.model}</span>
                </div>
                <div class="bot-info-item">
                    <span class="label">Last Activity:</span>
                    <span class="value">${formatTimestamp(bot.last_activity)}</span>
                </div>
            </div>
            <div class="bot-card-actions" onclick="event.stopPropagation()">
                ${bot.status === 'running' ? 
                    `<button class="bot-action-btn stop" onclick="stopBot('${botId}')">Stop</button>
                     <button class="bot-action-btn" onclick="restartBot('${botId}')">Restart</button>` :
                    `<button class="bot-action-btn start" onclick="startBot('${botId}')">Start</button>`
                }
                <button class="bot-action-btn" onclick="showBotDetails('${botId}')">Details</button>
            </div>
        </div>
    `}).join('');
}

async function handleAddBot(e) {
    e.preventDefault();
    
    const botData = {
        bot_id: `bot_${Date.now()}`,
        platform: document.getElementById('bot-platform').value,
        token: document.getElementById('bot-token').value,
        name: document.getElementById('bot-name').value,
        model: document.getElementById('bot-model').value,
        system_prompt: 'default'
    };
    
    if (!botData.platform || !botData.token || !botData.name) {
        showNotification('Please fill in all fields', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/bots/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(botData)
        });
        
        if (!response.ok) throw new Error('Failed to add bot');
        
        const result = await response.json();
        showNotification(result.message || 'Bot added successfully!', 'success');
        
        // Reset form
        e.target.reset();
        
        // Reload bots
        loadBots();
        
    } catch (error) {
        console.error('Error adding bot:', error);
        showNotification('Failed to add bot', 'error');
    }
}

async function startBot(botId) {
    try {
        const response = await fetch(`${API_URL}/api/bots/${botId}/start`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to start bot');
        
        showNotification('Bot starting...', 'success');
        setTimeout(loadBots, 1000);
        
    } catch (error) {
        console.error('Error starting bot:', error);
        showNotification('Failed to start bot', 'error');
    }
}

async function stopBot(botId) {
    try {
        const response = await fetch(`${API_URL}/api/bots/${botId}/stop`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to stop bot');
        
        showNotification('Bot stopped', 'success');
        setTimeout(loadBots, 1000);
        
    } catch (error) {
        console.error('Error stopping bot:', error);
        showNotification('Failed to stop bot', 'error');
    }
}

async function restartBot(botId) {
    try {
        const response = await fetch(`${API_URL}/api/bots/${botId}/restart`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to restart bot');
        
        showNotification('Bot restarting...', 'success');
        setTimeout(loadBots, 1000);
        
    } catch (error) {
        console.error('Error restarting bot:', error);
        showNotification('Failed to restart bot', 'error');
    }
}

async function showBotDetails(botId) {
    const bot = bots.find(b => b.id === botId);
    if (!bot) return;
    
    // Update modal content
    document.getElementById('modal-bot-name').textContent = bot.name;
    document.getElementById('modal-status').textContent = bot.status;
    document.getElementById('modal-status').className = `status-badge ${bot.status}`;
    document.getElementById('modal-platform').textContent = bot.platform;
    document.getElementById('modal-model').textContent = bot.model;
    document.getElementById('modal-uptime').textContent = formatTimestamp(bot.last_activity);
    
    // Load logs
    try {
        const response = await fetch(`${API_URL}/api/bots/${botId}/logs`);
        if (response.ok) {
            const logs = await response.json();
            const logsContainer = document.getElementById('modal-logs');
            
            if (logs && logs.length > 0) {
                logsContainer.innerHTML = logs.map(log => 
                    `<div class="log-entry">${log}</div>`
                ).join('');
            } else {
                logsContainer.innerHTML = '<p class="no-logs">No logs available</p>';
            }
        }
    } catch (error) {
        console.error('Error loading logs:', error);
    }
    
    // Store bot ID for delete action
    document.getElementById('modal-delete-btn').dataset.botId = botId;
    
    // Show modal
    document.getElementById('bot-modal').classList.add('active');
}

async function handleDeleteBot() {
    const botId = document.getElementById('modal-delete-btn').dataset.botId;
    if (!botId) return;
    
    if (!confirm('Are you sure you want to delete this bot? This cannot be undone.')) return;
    
    try {
        const response = await fetch(`${API_URL}/api/bots/${botId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete bot');
        
        showNotification('Bot deleted successfully', 'success');
        closeModal();
        loadBots();
        
    } catch (error) {
        console.error('Error deleting bot:', error);
        showNotification('Failed to delete bot', 'error');
    }
}

function closeModal() {
    document.getElementById('bot-modal').classList.remove('active');
}

// ============================================================================
// CHAT INTERFACE
// ============================================================================

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const question = input.value.trim();
    
    if (!question || isWaitingForResponse || !currentUser) return;
    
    // Add user message
    addChatMessage('user', question);
    
    // Clear input
    input.value = '';
    isWaitingForResponse = true;
    document.getElementById('send-button').disabled = true;
    
    // Show loading
    const loadingId = addLoadingMessage();
    
    try {
        const response = await fetch(`${API_URL}/api/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                user_id: currentUser.user_id,
                user_name: currentUser.name,
                user_email: currentUser.email
            })
        });
        
        if (!response.ok) throw new Error('Failed to get response');
        
        const data = await response.json();
        
        // Remove loading, add response
        removeLoadingMessage(loadingId);
        addChatMessage('bot', data.answer);
        
    } catch (error) {
        console.error('Error:', error);
        removeLoadingMessage(loadingId);
        addChatMessage('bot', '❌ Sorry, I encountered an error. Please try again.');
    } finally {
        isWaitingForResponse = false;
        document.getElementById('send-button').disabled = false;
        input.focus();
    }
}

function addChatMessage(role, content, scroll = true) {
    const container = document.getElementById('chat-messages');
    
    // Remove welcome message if it exists
    const welcome = container.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    container.appendChild(messageDiv);
    if (scroll) {
        container.scrollTop = container.scrollHeight;
    }
}

function addLoadingMessage() {
    const container = document.getElementById('chat-messages');
    const id = 'loading-' + Date.now();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    messageDiv.id = id;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = '<div class="message-loading"><span></span><span></span><span></span></div>';
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
    
    return id;
}

function removeLoadingMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function getWelcomeMessage() {
    return `
        <div class="welcome-message">
            <div class="welcome-icon">💬</div>
            <h2>Welcome to Auto Finance Bot</h2>
            <p>Ask me anything about Auto Finance, Autopools, or DeFi strategies!</p>
        </div>
    `;
}

// ============================================================================
// DATA STATUS
// ============================================================================

async function loadDataStatus() {
    if (!currentUser) return;
    
    try {
        const response = await fetch(`${API_URL}/api/scraper/status`);
        if (!response.ok) throw new Error('Failed to load scraper status');
        
        const status = await response.json();
        
        // Update status badge
        const statusBadge = document.getElementById('scraper-status');
        if (statusBadge) {
            statusBadge.textContent = status.is_running ? 'Running' : 'Stopped';
            statusBadge.className = `status-badge ${status.is_running ? 'running' : 'stopped'}`;
        }
        
        // Update last scrape time
        const lastScrapeEl = document.getElementById('last-scrape-time');
        if (lastScrapeEl && status.last_scrape_time) {
            const date = new Date(status.last_scrape_time);
            lastScrapeEl.textContent = date.toLocaleString();
        }
        
        // Update next scrape time
        const nextScrapeEl = document.getElementById('next-scrape-time');
        if (nextScrapeEl && status.next_scrape_in_seconds !== null) {
            const minutes = Math.floor(status.next_scrape_in_seconds / 60);
            const seconds = status.next_scrape_in_seconds % 60;
            nextScrapeEl.textContent = `${minutes}m ${seconds}s`;
        }
        
        // Update scrape count
        const scrapeCountEl = document.getElementById('scrape-count');
        if (scrapeCountEl) {
            scrapeCountEl.textContent = status.scrape_count;
        }
        
        // Update chunk counts
        const gitbookChunksEl = document.getElementById('gitbook-chunks');
        const websiteChunksEl = document.getElementById('website-chunks');
        const blogChunksEl = document.getElementById('blog-chunks');
        const totalChunksEl = document.getElementById('total-chunks');
        if (gitbookChunksEl) gitbookChunksEl.textContent = status.chunk_counts.gitbook || 0;
        if (websiteChunksEl) websiteChunksEl.textContent = status.chunk_counts.website || 0;
        if (blogChunksEl) blogChunksEl.textContent = status.chunk_counts.blog || 0;
        if (totalChunksEl) totalChunksEl.textContent = status.chunk_counts.total || 0;
        
        // Update scrape history
        if (status.recent_history && status.recent_history.length > 0) {
            const historyContainer = document.getElementById('scrape-history');
            if (historyContainer) {
                historyContainer.innerHTML = status.recent_history.map(entry => {
                    const date = new Date(entry.timestamp);
                    const statusClass = entry.status;
                    const scrapeType = entry.scrape_type === 'full' ? '📦 Full' : '🌐 Website';
                    const statusText = entry.status === 'success' 
                        ? `✅ ${scrapeType} (${entry.chunks?.total || 0} chunks)` 
                        : `❌ ${entry.error || 'Failed'}`;
                    
                    return `
                        <div class="scrape-history-item">
                            <span class="scrape-history-time">${date.toLocaleString()}</span>
                            <span class="scrape-history-status ${statusClass}">${statusText}</span>
                        </div>
                    `;
                }).join('');
            }
        }
        
    } catch (error) {
        console.error('Error loading data status:', error);
    }
}

async function triggerManualScrape() {
    const button = document.getElementById('manual-scrape-btn');
    if (!button) return;
    
    button.disabled = true;
    button.textContent = 'Scraping...';
    
    try {
        const response = await fetch(`${API_URL}/api/scraper/trigger`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to trigger scrape');
        
        showNotification('Manual scrape started!', 'success');
        
        // Reload status after a delay
        setTimeout(loadDataStatus, 2000);
        
    } catch (error) {
        console.error('Error triggering scrape:', error);
        showNotification('Failed to trigger scrape', 'error');
    } finally {
        button.disabled = false;
        button.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style="margin-right: 8px;">
                <path d="M13 2L3 12M13 2V7M13 2H8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Refresh Now
        `;
    }
}

// ============================================================================
// CONVERSATION HISTORY
// ============================================================================

async function loadConversationHistory() {
    if (!currentUser) return;
    
    try {
        const response = await fetch(`${API_URL}/api/conversation/${currentUser.user_id}`);
        if (!response.ok) return; // No history yet
        
        const messages = await response.json();
        const container = document.getElementById('chat-messages');
        
        if (!container) return;
        
        // Clear welcome message
        container.innerHTML = '';
        
        // Add messages
        messages.forEach(msg => {
            addChatMessage(msg.role, msg.content, false);
        });
        
    } catch (error) {
        console.error('Error loading conversation history:', error);
    }
}

// ============================================================================
// UTILITIES
// ============================================================================

function formatTimestamp(timestamp) {
    if (!timestamp) return 'Never';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
}

function showNotification(message, type = 'info') {
    // Simple notification system (could be enhanced with a toast library)
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${type === 'error' ? '#ff4444' : type === 'success' ? '#BFFF00' : '#333'};
        color: ${type === 'success' ? '#000' : '#fff'};
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4);
        z-index: 10000;
        animation: slideIn 0.3s ease;
        font-weight: 500;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);
