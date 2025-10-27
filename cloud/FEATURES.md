# Auto Finance Cloud Bot Manager - Features

## 🎨 Design
- **Auto Finance Aesthetic**: Dark theme (#000000) with neon green accents (#BFFF00)
- **Modern UI**: Card-based layout with smooth animations and hover effects
- **Responsive**: Works on desktop, tablet, and mobile devices
- **Professional**: Matches the look and feel of app.auto.finance

## 🚀 Features

### 1. Bot Management Dashboard
- **Add Bots**: Register new Telegram or Discord bots
- **Configure**: Set bot name, platform, token, and AI model
- **Control**: Start, stop, and restart bots with one click
- **Monitor**: View bot status, uptime, and last activity
- **Logs**: Access detailed activity logs for each bot

### 2. Q&A Chat Interface
- **AI-Powered**: Ask questions about Auto Finance, Autopools, and DeFi
- **Context-Aware**: Uses RAG (Retrieval-Augmented Generation) with scraped data
- **Multi-Model**: Supports GPT-4o and Claude Sonnet 4
- **Conversation History**: Maintains context across multiple questions
- **Beautiful UI**: Clean chat interface with user/bot avatars

### 3. Analytics Dashboard
- **Bot Statistics**: Total bots, running bots
- **Usage Metrics**: Conversation counts, unique users
- **Real-time Updates**: Auto-refresh every 5 seconds
- **Visual Cards**: Easy-to-read stat cards with icons

### 4. Authentication
- **Google Sign-In**: Secure OAuth 2.0 authentication
- **User Profiles**: Display user name and avatar
- **Session Management**: Persistent login with localStorage
- **Sign Out**: Clean logout functionality

## 🛠️ Technical Stack

### Frontend
- **HTML5/CSS3**: Modern, semantic markup
- **Vanilla JavaScript**: No framework dependencies
- **Google Sign-In**: OAuth 2.0 integration
- **Responsive Design**: Mobile-first approach

### Backend
- **FastAPI**: High-performance Python web framework
- **Uvicorn**: ASGI server for production
- **SQLite**: Persistent bot configuration storage
- **ChromaDB**: Vector database for RAG
- **Sentence Transformers**: Local embeddings (all-MiniLM-L6-v2)

### AI Models
- **OpenAI GPT-4o**: Advanced language model
- **Claude Sonnet 4**: Anthropic's latest model
- **RAG System**: Retrieval-Augmented Generation for accurate answers

### Bot Platforms
- **Telegram**: python-telegram-bot library
- **Discord**: discord.py library
- **Multi-threading**: Concurrent bot execution

## 📁 File Structure

```
cloud/
├── backend/
│   ├── api.py              # FastAPI application
│   ├── bot_manager.py      # Bot lifecycle management
│   ├── bot_config.py       # Persistent bot storage
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main HTML structure
│   ├── styles.css          # Auto Finance-themed styles
│   └── app.js              # Frontend logic
├── Dockerfile              # Container configuration
├── deploy.ps1              # Deployment script
└── .env                    # Environment variables
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# OpenAI API Key
OPENAI_API_KEY=your_openai_key

# Anthropic API Key (optional)
ANTHROPIC_API_KEY=your_anthropic_key

# Google OAuth Client ID
GOOGLE_CLIENT_ID=your_google_client_id
```

### Bot Configuration
- **Platform**: Telegram or Discord
- **Token**: Bot token from BotFather or Discord Developer Portal
- **Model**: gpt-4o, gpt-4o-mini, or claude-sonnet-4
- **System Prompt**: Personality/behavior configuration

## 🚀 Deployment

### Local Testing
```powershell
cd cloud/backend
python api.py
# Visit http://localhost:8000
```

### Cloud Deployment (Google Cloud Run)
```powershell
cd cloud
.\deploy.ps1
```

## 🔒 Security Features
- **Google OAuth**: Secure authentication
- **Token Storage**: Bot tokens stored securely in database
- **CORS**: Configured for production domains
- **Environment Variables**: Sensitive data in .env files

## 📊 Bot Management Features

### Lifecycle Management
- **Register**: Add new bot configurations
- **Start**: Launch bot in background thread
- **Stop**: Gracefully shutdown bot
- **Restart**: Stop and start in one action
- **Delete**: Remove bot configuration

### Monitoring
- **Status Tracking**: running, stopped, starting, error
- **Activity Logs**: Last 100 log entries per bot
- **Uptime Tracking**: Monitor how long bots have been running
- **Error Handling**: Capture and display error messages

### Persistence
- **SQLite Database**: Bot configurations survive restarts
- **Auto-restore**: Bots can be configured to auto-start on deployment
- **Statistics**: Track messages processed, errors, uptime

## 🎯 Use Cases

1. **Team Access**: Multiple team members can manage bots from anywhere
2. **24/7 Operation**: Bots run continuously in the cloud
3. **Centralized Management**: Single dashboard for all bots
4. **Easy Deployment**: No local setup required
5. **Scalable**: Add unlimited bots as needed

## 🔄 Auto-Refresh
- Bot status updates every 5 seconds
- Analytics refresh automatically
- No manual refresh needed

## 🎨 UI Components

### Navigation Bar
- Logo with neon green icon
- Tab switcher (Bots, Q&A Chat, Analytics)
- User profile with avatar
- Sign in/out button

### Bot Cards
- Platform icon (📱 Telegram, 💬 Discord)
- Bot name and status badge
- Model and last activity
- Action buttons (Start/Stop/Restart/Details)
- Hover effects with neon glow

### Chat Interface
- Welcome message with example questions
- User/bot message bubbles
- Loading animation
- Auto-scroll to latest message

### Modal
- Detailed bot information
- Activity logs viewer
- Delete bot option
- Close button

## 🌟 Future Enhancements (TODO)
- [ ] WebSocket support for real-time log streaming
- [ ] Bot performance metrics and graphs
- [ ] Scheduled bot restarts
- [ ] Multi-user permissions
- [ ] Bot templates for quick setup
- [ ] Export conversation data
- [ ] Advanced analytics dashboard

## 📝 Notes
- Requires Google Cloud project for OAuth
- Bot tokens must be obtained from respective platforms
- OpenAI API key required for GPT models
- Scraped data must be present for Q&A functionality


