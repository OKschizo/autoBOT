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

// Thread and Prompt State
let threads = [];
let currentThreadId = null;
let currentSystemPrompt = null;
let promptTemplates = {};
let editingThreadId = null;

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
            // Check if client ID is configured
            if (!GOOGLE_CLIENT_ID || GOOGLE_CLIENT_ID.trim() === '') {
                console.error('GOOGLE_CLIENT_ID is not configured');
                const container = document.getElementById('google-signin-container');
                if (container) {
                    container.innerHTML = '<p style="color: red;">⚠️ Google OAuth not configured. Please set GOOGLE_CLIENT_ID environment variable.</p>';
                }
                return;
            }
            
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
    loadThreads();
    loadPromptTemplates();
    
    // Start auto-refresh
    refreshInterval = setInterval(() => {
        if (currentTab === 'bots') loadBots();
        if (currentTab === 'data') loadDataStatus();
        if (currentTab === 'chat') loadThreads();
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
    threads = [];
    currentThreadId = null;
    currentSystemPrompt = null;
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
    if (tabName === 'chat' && currentUser) {
        loadThreads();
        if (currentThreadId) {
            loadThreadMessages(currentThreadId);
        }
    }
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
    
    // Create thread if none exists
    if (!currentThreadId) {
        await createNewThread();
    }
    
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
                user_email: currentUser.email,
                thread_id: currentThreadId,  // Include thread ID
                system_prompt: currentSystemPrompt || null  // Include custom prompt (Option A)
            })
        });
        
        if (!response.ok) throw new Error('Failed to get response');
        
        const data = await response.json();
        
        // Update thread_id if returned
        if (data.thread_id) {
            currentThreadId = data.thread_id;
            await loadThreads(); // Reload to show new thread
            renderThreads(); // Update active state
        }
        
        // Remove loading, add response
        removeLoadingMessage(loadingId);
        addChatMessage('bot', data.answer);
        
        // Reload threads to update last message preview
        await loadThreads();
        
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
    
    // Format content with markdown if it's a bot message
    if (role === 'bot' && typeof marked !== 'undefined') {
        // Configure marked for better formatting
        marked.setOptions({
            breaks: true,  // Convert line breaks to <br>
            gfm: true,     // GitHub Flavored Markdown
            headerIds: false,
            mangle: false
        });
        
        // Convert markdown to HTML
        const markdownHtml = marked.parse(content);
        
        // Sanitize HTML to prevent XSS attacks
        if (typeof DOMPurify !== 'undefined') {
            contentDiv.innerHTML = DOMPurify.sanitize(markdownHtml, {
                ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'code', 'pre', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'a', 'hr'],
                ALLOWED_ATTR: ['href', 'title', 'target', 'rel']
            });
        } else {
            // Fallback if DOMPurify not loaded
            contentDiv.innerHTML = markdownHtml;
        }
    } else {
        // User messages or fallback: plain text
        contentDiv.textContent = content;
    }
    
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

// Auto-refresh interval for data status (faster when scraping)
let dataStatusInterval = null;

async function loadDataStatus() {
    if (!currentUser) return;
    
    try {
        const response = await fetch(`${API_URL}/api/scraper/status`);
        if (!response.ok) throw new Error('Failed to load scraper status');
        
        const status = await response.json();
        
        // Auto-refresh more frequently when scraping
        if (dataStatusInterval) {
            clearInterval(dataStatusInterval);
        }
        
        if (status.is_scraping) {
            // Refresh every 2 seconds when scraping
            dataStatusInterval = setInterval(loadDataStatus, 2000);
        } else {
            // Refresh every 10 seconds when idle
            dataStatusInterval = setInterval(loadDataStatus, 10000);
        }
        
        // Update status badge with more detail
        const statusBadge = document.getElementById('scraper-status');
        if (statusBadge) {
            if (status.is_scraping && status.current_progress && status.current_progress.stage) {
                // Show current stage during scraping
                const stageNames = {
                    'gitbook': '📚 Scraping Docs',
                    'website': '🌐 Scraping Website',
                    'blog': '📝 Scraping Blog',
                    'indexing': '🔍 Building Index'
                };
                const stageName = stageNames[status.current_progress.stage] || 'Scraping...';
                statusBadge.textContent = stageName;
                statusBadge.className = `status-badge running`;
            } else if (status.is_scraping) {
                statusBadge.textContent = 'Scraping...';
                statusBadge.className = `status-badge running`;
            } else if (status.is_running) {
                statusBadge.textContent = 'Running';
                statusBadge.className = `status-badge running`;
            } else {
                statusBadge.textContent = 'Stopped';
                statusBadge.className = `status-badge stopped`;
            }
        }
        
        // Update last scrape time (in user's local timezone)
        const lastScrapeEl = document.getElementById('last-scrape-time');
        if (lastScrapeEl && status.last_scrape_time) {
            const date = new Date(status.last_scrape_time);
            lastScrapeEl.textContent = date.toLocaleString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                timeZoneName: 'short'
            });
        } else if (lastScrapeEl && !status.last_scrape_time) {
            lastScrapeEl.textContent = 'Never';
        }
        
        // Update next scrape time
        const nextScrapeEl = document.getElementById('next-scrape-time');
        if (nextScrapeEl && status.next_scrape_in_seconds !== null && status.next_scrape_in_seconds > 0) {
            const minutes = Math.floor(status.next_scrape_in_seconds / 60);
            const seconds = status.next_scrape_in_seconds % 60;
            if (minutes > 0) {
                nextScrapeEl.textContent = `${minutes}m ${seconds}s`;
            } else {
                nextScrapeEl.textContent = `${seconds}s`;
            }
        } else if (nextScrapeEl) {
            nextScrapeEl.textContent = status.is_scraping ? 'In progress...' : 'Calculating...';
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
        
               // Update all scrape button states
               const buttonIds = ['manual-scrape-btn', 'gitbook-scrape-btn', 'website-scrape-btn', 'blog-scrape-btn'];
               buttonIds.forEach(btnId => {
                   const btn = document.getElementById(btnId);
                   if (btn) {
                       btn.disabled = status.is_scraping || !status.is_running;
                       if (status.is_scraping) {
                           btn.title = 'A scrape is currently running. Please wait for it to complete.';
                       } else if (!status.is_running) {
                           btn.title = 'The scraper service is not running. Please contact support.';
                       }
                   }
               });
        
        // Update progress display if scraping
        updateProgressDisplay(status.current_progress);
        
    } catch (error) {
        console.error('Error loading data status:', error);
    }
}

function updateProgressDisplay(progress) {
    const progressContainer = document.getElementById('scrape-progress-container');
    if (!progressContainer) return;
    
    if (!progress || !progress.stage) {
        progressContainer.style.display = 'none';
        return;
    }
    
    progressContainer.style.display = 'block';
    
    // Update current step with detailed message
    const currentStepEl = document.getElementById('scrape-current-step');
    if (currentStepEl) {
        const stepText = progress.current_step || 'Processing...';
        currentStepEl.textContent = stepText;
        currentStepEl.style.color = 'var(--text-primary)';
    }
    
    // Update stage-specific progress
    const stageNames = {
        'gitbook': '📚 GitBook Documentation',
        'website': '🌐 Website',
        'blog': '📝 Blog',
        'indexing': '🔍 Building Index'
    };
    
    const stageEl = document.getElementById('scrape-stage');
    if (stageEl) {
        stageEl.textContent = stageNames[progress.stage] || progress.stage;
    }
    
    // Show ALL progress bars when scraping (not just current stage)
    const gitbookProgress = document.getElementById('gitbook-progress');
    const websiteProgress = document.getElementById('website-progress');
    const blogProgress = document.getElementById('blog-progress');
    const indexProgress = document.getElementById('index-progress');
    
    // GitBook progress - show if scraping or if has data
    if (gitbookProgress) {
        if (progress.gitbook_pages_total > 0 || progress.stage === 'gitbook') {
            const total = progress.gitbook_pages_total || 1;
            const current = progress.gitbook_pages_scraped || 0;
            const percent = Math.min(100, (current / total) * 100);
            gitbookProgress.style.display = 'block';
            gitbookProgress.querySelector('.progress-bar-fill').style.width = `${percent}%`;
            const status = progress.stage === 'gitbook' ? '⏳ ' : (current >= total ? '✅ ' : '');
            gitbookProgress.querySelector('.progress-text').textContent = 
                `${status}${current}/${total} pages${percent.toFixed(0) !== '100' ? ` (${percent.toFixed(0)}%)` : ''}`;
        } else if (progress.stage !== 'gitbook') {
            gitbookProgress.style.display = 'none';
        }
    }
    
    // Website progress - show if scraping or if has data
    if (websiteProgress) {
        if (progress.website_pages_total > 0 || progress.stage === 'website') {
            const total = progress.website_pages_total || 1;
            const current = progress.website_pages_scraped || 0;
            const percent = Math.min(100, (current / total) * 100);
            websiteProgress.style.display = 'block';
            websiteProgress.querySelector('.progress-bar-fill').style.width = `${percent}%`;
            const status = progress.stage === 'website' ? '⏳ ' : (current >= total ? '✅ ' : '');
            websiteProgress.querySelector('.progress-text').textContent = 
                `${status}${current}/${total} pages${percent.toFixed(0) !== '100' ? ` (${percent.toFixed(0)}%)` : ''}`;
        } else if (progress.stage !== 'website') {
            websiteProgress.style.display = 'none';
        }
    }
    
    // Blog progress - show if scraping or if has data
    if (blogProgress) {
        if (progress.blog_posts_total > 0 || progress.stage === 'blog') {
            const total = progress.blog_posts_total || 1;
            const current = progress.blog_posts_scraped || 0;
            const percent = Math.min(100, (current / total) * 100);
            blogProgress.style.display = 'block';
            blogProgress.querySelector('.progress-bar-fill').style.width = `${percent}%`;
            const status = progress.stage === 'blog' ? '⏳ ' : (current >= total ? '✅ ' : '');
            blogProgress.querySelector('.progress-text').textContent = 
                `${status}${current}/${total} posts${percent.toFixed(0) !== '100' ? ` (${percent.toFixed(0)}%)` : ''}`;
        } else if (progress.stage !== 'blog') {
            blogProgress.style.display = 'none';
        }
    }
    
    // Index progress - show if indexing or if has data
    if (indexProgress) {
        if (progress.index_chunks_total > 0 || progress.stage === 'indexing') {
            const total = progress.index_chunks_total || 1;
            const current = progress.index_chunks_scraped || 0;
            const percent = Math.min(100, (current / total) * 100);
            indexProgress.style.display = 'block';
            indexProgress.querySelector('.progress-bar-fill').style.width = `${percent}%`;
            const status = progress.stage === 'indexing' ? '⏳ ' : (current >= total ? '✅ ' : '');
            indexProgress.querySelector('.progress-text').textContent = 
                `${status}${current}/${total} chunks${percent.toFixed(0) !== '100' ? ` (${percent.toFixed(0)}%)` : ''}`;
        } else if (progress.stage !== 'indexing') {
            indexProgress.style.display = 'none';
        }
    }
}

async function triggerManualScrape(scrapeType = 'full') {
    const buttonMap = {
        'full': 'manual-scrape-btn',
        'gitbook': 'gitbook-scrape-btn',
        'website': 'website-scrape-btn',
        'blog': 'blog-scrape-btn'
    };
    
    const button = document.getElementById(buttonMap[scrapeType]);
    if (!button) {
        console.error('Scrape button not found');
        return;
    }
    
    // Check if already scraping
    if (button.disabled && button.textContent.includes('Progress')) {
        showNotification('A scrape is already in progress. Please wait.', 'warning');
        return;
    }
    
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '⏳ Starting...';
    
    // Disable all scrape buttons
    Object.values(buttonMap).forEach(btnId => {
        const btn = document.getElementById(btnId);
        if (btn) btn.disabled = true;
    });
    
    try {
        const response = await fetch(`${API_URL}/api/scraper/trigger?scrape_type=${scrapeType}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            let errorMsg = 'Unknown error';
            try {
                const errorData = await response.json();
                errorMsg = errorData.detail || errorData.error || errorData.message || 'Unknown error';
            } catch (e) {
                errorMsg = `HTTP ${response.status}: ${response.statusText}`;
            }
            
            console.error('Failed to trigger scrape:', errorMsg);
            
            if (errorMsg.includes('already in progress') || errorMsg.includes('already running')) {
                showNotification('A scrape is already running. Please wait for it to complete.', 'warning');
            } else if (errorMsg.includes('not running') || errorMsg.includes('not available')) {
                showNotification('Scraper service is not running. Please contact support.', 'error');
            } else {
                showNotification(`Failed to trigger scrape: ${errorMsg}`, 'error');
            }
            return;
        }
        
        const result = await response.json();
        const typeNames = {
            'full': 'Full scrape',
            'gitbook': 'GitBook scrape',
            'website': 'Website scrape',
            'blog': 'Blog scrape'
        };
        showNotification(result.message || `${typeNames[scrapeType]} started!`, 'success');
        
        // Reload status immediately and then continue polling
        setTimeout(loadDataStatus, 1000);
        
    } catch (error) {
        console.error('Error triggering scrape:', error);
        showNotification(`Network error: ${error.message}`, 'error');
    } finally {
        // Re-enable buttons after a delay
        setTimeout(() => {
            Object.values(buttonMap).forEach(btnId => {
                const btn = document.getElementById(btnId);
                if (btn) {
                    btn.disabled = false;
                    // Restore original text for the clicked button
                    if (btnId === buttonMap[scrapeType]) {
                        btn.innerHTML = originalText;
                    }
                }
            });
        }, 1000);
    }
}

// ============================================================================
// CONVERSATION THREAD MANAGEMENT
// ============================================================================

async function loadThreads() {
    if (!currentUser) return;
    
    try {
        const response = await fetch(`${API_URL}/api/threads/${currentUser.user_id}`);
        if (!response.ok) {
            threads = [];
            renderThreads();
            return;
        }
        
        const data = await response.json();
        threads = data.threads || [];
        renderThreads();
        
    } catch (error) {
        console.error('Error loading threads:', error);
        threads = [];
        renderThreads();
    }
}

function renderThreads() {
    const container = document.getElementById('threads-list');
    if (!container) return;
    
    if (threads.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">No conversations yet</p>';
        return;
    }
    
    container.innerHTML = threads.map(thread => {
        const isActive = thread.thread_id === currentThreadId;
        const preview = thread.last_message_preview || 'No messages yet';
        
        return `
            <div class="thread-item ${isActive ? 'active' : ''}" onclick="selectThread('${thread.thread_id}')" data-thread-id="${thread.thread_id}">
                <div style="flex: 1; min-width: 0;">
                    <div class="thread-item-title">${escapeHtml(thread.title)}</div>
                    <div class="thread-item-preview">${escapeHtml(preview)}</div>
                </div>
                <div class="thread-item-actions" onclick="event.stopPropagation()">
                    <button class="thread-action-btn" onclick="editThreadTitle('${thread.thread_id}')" title="Edit title">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M11 2L14 5M12 1L13 2L12 3L11 2M5 11L2 14L5 11Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        </svg>
                    </button>
                    <button class="thread-action-btn" onclick="deleteThread('${thread.thread_id}')" title="Delete">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

async function createNewThread() {
    if (!currentUser) return;
    
    try {
        const response = await fetch(`${API_URL}/api/threads/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.user_id
            })
        });
        
        if (!response.ok) throw new Error('Failed to create thread');
        
        const data = await response.json();
        currentThreadId = data.thread_id;
        
        // Clear chat
        const container = document.getElementById('chat-messages');
        if (container) {
            container.innerHTML = getWelcomeMessage();
        }
        
        // Reload threads and select new one
        await loadThreads();
        renderThreads(); // Update active state
        
        showNotification('New conversation started', 'success');
        
    } catch (error) {
        console.error('Error creating thread:', error);
        showNotification('Failed to create conversation', 'error');
    }
}

async function selectThread(threadId) {
    currentThreadId = threadId;
    await loadThreadMessages(threadId);
    renderThreads(); // Update active state
}

async function loadThreadMessages(threadId) {
    if (!threadId) return;
    
    try {
        const response = await fetch(`${API_URL}/api/threads/${threadId}/messages`);
        if (!response.ok) {
            console.error('Failed to load thread messages');
            return;
        }
        
        const data = await response.json();
        const messages = data.messages || [];
        
        const container = document.getElementById('chat-messages');
        if (!container) return;
        
        // Clear welcome message
        container.innerHTML = '';
        
        // Add messages
        messages.forEach(msg => {
            addChatMessage('user', msg.question, false);
            addChatMessage('bot', msg.answer, false);
        });
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
        
    } catch (error) {
        console.error('Error loading thread messages:', error);
    }
}

async function deleteThread(threadId) {
    if (!currentUser || !confirm('Are you sure you want to delete this conversation?')) return;
    
    try {
        const response = await fetch(`${API_URL}/api/threads/${threadId}?user_id=${encodeURIComponent(currentUser.user_id)}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete thread');
        
        // Clear chat if this was the active thread
        if (threadId === currentThreadId) {
            currentThreadId = null;
            const container = document.getElementById('chat-messages');
            if (container) {
                container.innerHTML = getWelcomeMessage();
            }
        }
        
        await loadThreads();
        showNotification('Conversation deleted', 'success');
        
    } catch (error) {
        console.error('Error deleting thread:', error);
        showNotification('Failed to delete conversation', 'error');
    }
}

function editThreadTitle(threadId) {
    const thread = threads.find(t => t.thread_id === threadId);
    if (!thread) return;
    
    editingThreadId = threadId;
    document.getElementById('thread-title-input').value = thread.title;
    document.getElementById('thread-title-modal').classList.add('active');
}

function closeThreadTitleModal() {
    document.getElementById('thread-title-modal').classList.remove('active');
    editingThreadId = null;
}

async function saveThreadTitle() {
    if (!editingThreadId || !currentUser) return;
    
    const title = document.getElementById('thread-title-input').value.trim();
    if (!title) {
        showNotification('Title cannot be empty', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/threads/${editingThreadId}/title`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.user_id,
                title: title
            })
        });
        
        if (!response.ok) throw new Error('Failed to update title');
        
        closeThreadTitleModal();
        await loadThreads();
        showNotification('Title updated', 'success');
        
    } catch (error) {
        console.error('Error updating thread title:', error);
        showNotification('Failed to update title', 'error');
    }
}

// ============================================================================
// PROMPT EDITOR
// ============================================================================

async function loadPromptTemplates() {
    try {
        const response = await fetch(`${API_URL}/api/prompts/templates`);
        if (!response.ok) return;
        
        const data = await response.json();
        promptTemplates = data.prompts || {};
        
    } catch (error) {
        console.error('Error loading prompt templates:', error);
    }
}

function togglePromptEditor() {
    const panel = document.getElementById('prompt-editor-panel');
    const content = document.getElementById('prompt-editor-content');
    
    if (content.style.display === 'none') {
        content.style.display = 'flex';
        panel.classList.add('expanded');
    } else {
        content.style.display = 'none';
        panel.classList.remove('expanded');
    }
}

function loadPromptTemplate() {
    const select = document.getElementById('prompt-template-select');
    const textarea = document.getElementById('prompt-textarea');
    const status = document.getElementById('prompt-status');
    
    const templateName = select.value;
    
    if (!templateName) {
        // Custom mode
        status.textContent = 'Custom';
        return;
    }
    
    if (promptTemplates[templateName]) {
        textarea.value = promptTemplates[templateName];
        status.textContent = templateName.charAt(0).toUpperCase() + templateName.slice(1).replace('_', ' ');
    } else {
        status.textContent = 'Default';
    }
}

function savePrompt() {
    const textarea = document.getElementById('prompt-textarea');
    const prompt = textarea.value.trim();
    
    if (prompt) {
        currentSystemPrompt = prompt;
        const status = document.getElementById('prompt-status');
        const select = document.getElementById('prompt-template-select');
        
        // Check if it matches a template
        let matchedTemplate = null;
        for (const [name, template] of Object.entries(promptTemplates)) {
            if (template.trim() === prompt) {
                matchedTemplate = name;
                break;
            }
        }
        
        if (matchedTemplate) {
            status.textContent = matchedTemplate.charAt(0).toUpperCase() + matchedTemplate.slice(1).replace('_', ' ');
            select.value = matchedTemplate;
        } else {
            status.textContent = 'Custom';
            select.value = '';
        }
        
        showNotification('Prompt saved! Will be used for next message.', 'success');
        togglePromptEditor(); // Collapse
    } else {
        resetPrompt();
    }
}

function resetPrompt() {
    currentSystemPrompt = null;
    document.getElementById('prompt-textarea').value = '';
    document.getElementById('prompt-template-select').value = '';
    document.getElementById('prompt-status').textContent = 'Default';
    showNotification('Prompt reset to default', 'success');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// CONVERSATION HISTORY (Legacy - kept for compatibility)
// ============================================================================

async function loadConversationHistory() {
    // This is now handled by loadThreadMessages
    if (currentThreadId) {
        await loadThreadMessages(currentThreadId);
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
