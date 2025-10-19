// Configuration
const API_URL = window.location.origin;  // Automatically uses current domain (works locally and in production)
let GOOGLE_CLIENT_ID = null;  // Loaded from backend

// State
let currentUser = null;
let isWaitingForResponse = false;

// DOM Elements
const authGate = document.getElementById('authGate');
const chatInterface = document.getElementById('chatInterface');
const messagesContainer = document.getElementById('messagesContainer');
const questionInput = document.getElementById('questionInput');
const sendButton = document.getElementById('sendButton');
const clearButton = document.getElementById('clearButton');
const charCount = document.getElementById('charCount');
const modelBadge = document.getElementById('modelBadge');
const userInfo = document.getElementById('userInfo');
const userName = document.getElementById('userName');
const userAvatar = document.getElementById('userAvatar');
const signOutButton = document.getElementById('signOutButton');

// Initialize app
window.onload = async function() {
    try {
        // Fetch config from backend (includes Google Client ID)
        const configResponse = await fetch(`${API_URL}/api/config`);
        const config = await configResponse.json();
        GOOGLE_CLIENT_ID = config.google_client_id;
        
        // Update model badge
        const modelName = config.model.includes('gpt') ? 'GPT-4o' : 'Claude Sonnet 4';
        modelBadge.textContent = modelName;
        
        // Initialize Google Sign-In
        google.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: handleCredentialResponse
        });
        
        // Render sign-in button in auth gate
        google.accounts.id.renderButton(
            document.getElementById('googleSignInButton'),
            { 
                theme: 'filled_blue', 
                size: 'large',
                text: 'signin_with',
                shape: 'rectangular',
                width: 300
            }
        );
        
        // Check if user is already signed in (from localStorage)
        const savedUser = localStorage.getItem('autoFinanceUser');
        if (savedUser) {
            currentUser = JSON.parse(savedUser);
            showChatInterface();
        }
    } catch (error) {
        console.error('Failed to initialize app:', error);
        alert('Failed to load app configuration. Please refresh the page.');
    }
};

// Handle Google Sign-In
async function handleCredentialResponse(response) {
    try {
        // Verify token with backend
        const result = await fetch(`${API_URL}/api/auth/google`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_token: response.credential })
        });
        
        if (!result.ok) throw new Error('Authentication failed');
        
        currentUser = await result.json();
        localStorage.setItem('autoFinanceUser', JSON.stringify(currentUser));
        
        showChatInterface();
    } catch (error) {
        console.error('Sign-in error:', error);
        alert('Failed to sign in. Please try again.');
    }
}

// Show chat interface after sign-in
function showChatInterface() {
    authGate.style.display = 'none';
    chatInterface.style.display = 'flex';
    
    // Update user info in header
    userName.textContent = currentUser.name;
    userAvatar.src = currentUser.picture || 'https://via.placeholder.com/40';
    userInfo.style.display = 'flex';
    
    // Focus input
    questionInput.focus();
}

// Sign out
signOutButton.addEventListener('click', () => {
    currentUser = null;
    localStorage.removeItem('autoFinanceUser');
    google.accounts.id.disableAutoSelect();
    
    // Reset UI
    chatInterface.style.display = 'none';
    authGate.style.display = 'flex';
    userInfo.style.display = 'none';
    messagesContainer.innerHTML = getWelcomeMessage();
});

// Input handling
questionInput.addEventListener('input', () => {
    const length = questionInput.value.length;
    charCount.textContent = `${length}/500`;
    
    // Auto-resize textarea
    questionInput.style.height = 'auto';
    questionInput.style.height = questionInput.scrollHeight + 'px';
    
    // Enable/disable send button
    sendButton.disabled = length === 0 || isWaitingForResponse;
});

questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuestion();
    }
});

sendButton.addEventListener('click', sendQuestion);
clearButton.addEventListener('click', clearConversation);

// Send question
async function sendQuestion() {
    const question = questionInput.value.trim();
    if (!question || isWaitingForResponse || !currentUser) return;
    
    // Add user message
    addMessage('user', question);
    
    // Clear input
    questionInput.value = '';
    questionInput.style.height = 'auto';
    charCount.textContent = '0/500';
    sendButton.disabled = true;
    isWaitingForResponse = true;
    
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
        addMessage('assistant', data.answer);
        
    } catch (error) {
        console.error('Error:', error);
        removeLoadingMessage(loadingId);
        addMessage('assistant', '❌ Sorry, I encountered an error. Please try again.');
    } finally {
        isWaitingForResponse = false;
        sendButton.disabled = false;
        questionInput.focus();
    }
}

// Clear conversation
async function clearConversation() {
    if (!confirm('Clear your conversation history?')) return;
    
    try {
        await fetch(`${API_URL}/api/conversation/clear`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.user_id })
        });
        
        messagesContainer.innerHTML = getWelcomeMessage();
    } catch (error) {
        console.error('Error clearing conversation:', error);
        alert('Failed to clear conversation');
    }
}

// Add message to UI
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    const timestamp = document.createElement('div');
    timestamp.className = 'message-timestamp';
    timestamp.textContent = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    contentDiv.appendChild(timestamp);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    // Remove welcome message if it exists
    const welcome = messagesContainer.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Loading message
function addLoadingMessage() {
    const id = 'loading-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = id;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    
    return id;
}

function removeLoadingMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Scroll to bottom
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Example question buttons
function askExample(question) {
    questionInput.value = question;
    questionInput.dispatchEvent(new Event('input'));
    questionInput.focus();
}

// Welcome message
function getWelcomeMessage() {
    return `
        <div class="welcome-message">
            <h2>👋 Welcome!</h2>
            <p>I'm here to help you with anything about Auto Finance - Autopools, plasmaUSD, yield strategies, and more!</p>
            <div class="example-questions">
                <p><strong>Try asking:</strong></p>
                <button class="example-btn" onclick="askExample('What are Autopools?')">What are Autopools?</button>
                <button class="example-btn" onclick="askExample('What is the current TVL?')">What is the current TVL?</button>
                <button class="example-btn" onclick="askExample('How do I deposit into an Autopool?')">How do I deposit?</button>
                <button class="example-btn" onclick="askExample('Is Auto Finance audited?')">Is it audited?</button>
            </div>
        </div>
    `;
}

