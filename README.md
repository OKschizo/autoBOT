# Auto Finance Multi-Platform Bot 🤖

Complete AI-powered bot for Auto Finance across **Telegram**, **Discord**, and **Slack** with live data scraping, conversation memory, and a professional management GUI.

---

## 🎯 Features

✅ **Multi-Platform** - Telegram, Discord, and Slack support  
✅ **Dual AI Models** - Switch between Claude Sonnet 4 and GPT-4o  
✅ **Live Data** - Daily scraping of APYs, TVLs, pool allocations  
✅ **Complete Knowledge** - Docs + Website + Blog posts  
✅ **Conversation Memory** - Per-user, per-chat context tracking  
✅ **Persistent Storage** - SQLite database for conversation history  
✅ **Analytics Dashboard** - Track usage, questions, and user engagement  
✅ **Custom Personalities** - Editable system prompts with presets  
✅ **Professional GUI** - 6-tab desktop interface for complete control  
✅ **Reply Detection** - Responds to message replies (Telegram)  
✅ **Slash Commands** - Full command support (Discord)  

---

## 🚀 Quick Start

### **1. Install Dependencies**

```bash
pip install -r requirements.txt
playwright install chromium
```

### **2. Configure API Keys**

Create a `.env` file with:

```env
# AI Models (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...

# Platform Tokens (add the ones you need)
TELEGRAM_BOT_TOKEN=8343215230:AAE...
DISCORD_BOT_TOKEN=MTMyN...
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...

# Optional
BOT_MODEL=claude-sonnet-4-20250514  # or gpt-4o
```

### **3. Run First Scrape** (~20 minutes)

```bash
python scrape_all_data.py
```

This scrapes:
- Documentation (docs.auto.finance)
- Website + live data (app.auto.finance)
- Blog posts (blog.tokemak.xyz)

### **4. Launch the GUI**

**Windows:**
```bash
LAUNCH_GUI.bat
```

**Or manually:**
```bash
python bot_gui.py
```

### **5. Start Your Bots!**

In the GUI:
1. Select **Activity** tab
2. Choose AI model (Claude or OpenAI)
3. Click **Start** for each platform you configured
4. Monitor live activity logs

---

## 💬 Usage Examples

### **Telegram - Direct Messages:**

```
You: What are Autopools?
Bot: Autopools are automated liquidity vaults that handle
     rebalancing, compounding, and yield optimization for you.
     Set-and-forget DeFi.

You: What's the current APY on plasmaUSD?
Bot: plasmaUSD is at 11.94% APY with $6.33M TVL. Deployed
     across Balancer, Euler, Aave, and Fluid.
```

### **Telegram - Group Chats:**

```
@AutoFinanceBot what's the APY on autoUSD?
```

Or **reply to any message the bot sent** - it'll respond in context!

### **Discord - Slash Commands:**

```
/ask What are Autopools?
/stats
/clear
/help
```

### **Slack:**

```
@AutoFinanceBot what's happening with Autopilot?
```

---

## 🎛️ Bot Commands

### **Telegram:**
| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show help |
| `/stats` | Show statistics |
| `/clear` | Clear your conversation history |

### **Discord:**
| Command | Description |
|---------|-------------|
| `/ask [question]` | Ask a question |
| `/stats` | View bot statistics |
| `/clear` | Clear conversation |
| `/help` | Show help |

### **Slack:**
| Command | Description |
|---------|-------------|
| `@bot [question]` | Ask in channels |
| `/auto-help` | Show help |
| `/auto-stats` | View statistics |

---

## 🖥️ GUI Features

### **6 Tabs:**

#### **1. Activity**
- Live bot status for all platforms
- Real-time activity logs
- Model switcher (Claude ↔ GPT-4)
- Start/Stop controls per platform

#### **2. Conversations**
- Browse all user conversations
- Search by user or content
- View full conversation history
- Export to JSON or training format

#### **3. Analytics**
- Total questions answered
- Active users count
- Platform breakdown
- Top questions list
- Question frequency charts

#### **4. Prompt**
- Edit system prompt in real-time
- 4 personality presets:
  - Default (friendly & concise)
  - Technical (detailed analysis)
  - Beginner (simplified explanations)
  - Marketing (engaging & promotional)
- Save custom prompts

#### **5. Settings**
- API key management (Claude & OpenAI)
- Add/manage Telegram bots
- Add/manage Discord bots
- Add/manage Slack bots
- All settings scrollable & organized

#### **6. Updates**
- One-click data refresh
- Scraper status
- Last update timestamp
- Auto-rebuild index

---

## 🗂️ Project Structure

```
TOKE_SCRAPER/
├── Core Bot Files
│   ├── telegram_bot.py           # Telegram bot
│   ├── discord_bot.py            # Discord bot
│   ├── slack_bot.py              # Slack bot
│   ├── bot_gui.py                # Main GUI (6 tabs)
│   ├── bot_gui_light.py          # Lightweight version
│   ├── platform_manager.py       # Multi-platform orchestration
│   ├── conversation_manager.py   # In-memory conversation tracking
│   └── conversation_storage.py   # SQLite persistence
│
├── AI Agents
│   ├── rag_agent_complete.py     # Claude RAG agent
│   └── rag_agent_openai.py       # OpenAI RAG agent
│
├── Scrapers
│   ├── scrape_gitbook.py         # Docs scraper
│   ├── scrape_website.py         # Website scraper (Playwright)
│   ├── scrape_blog.py            # Blog scraper (Playwright)
│   ├── scrape_all_data.py        # Master scraper
│   └── build_complete_index.py   # Index builder
│
├── Configuration
│   ├── .env                      # Your API keys (secret!)
│   ├── .env.example              # Template
│   ├── requirements.txt          # Dependencies
│   ├── system_prompts.json       # Bot personalities
│   └── .gitignore                # Git ignore rules
│
├── Launchers
│   ├── LAUNCH_GUI.bat            # Windows GUI launcher
│   └── START_BOT.sh              # Linux/Mac launcher
│
├── Documentation
│   ├── DISCORD_SETUP.md          # Discord bot setup
│   ├── SLACK_SETUP.md            # Slack bot setup
│   └── This README               # You are here
│
└── Data (auto-generated)
    ├── scraped_data/
    │   ├── gitbook_data.json     # Docs
    │   ├── website/              # Website + live data
    │   └── blog/                 # Blog posts
    ├── chroma_db/
    │   └── auto_finance_complete/ # Vector database (464 chunks)
    └── bot_conversations.db      # SQLite conversation storage
```

---

## 🧠 What the Bot Knows

After scraping (464 indexed chunks):

**Technical Documentation:**
- Protocol mechanics
- Smart contract architecture
- Security audits
- Integration guides
- Developer documentation

**Live Data (Updated Daily):**
- Current APY for each pool
- Current TVL
- Daily returns
- Active allocations
- Destination breakdown
- Protocol usage

**Marketing Content:**
- Homepage copy
- Feature descriptions
- Value propositions
- FAQs

**Blog Posts:**
- All announcements
- Product launches
- Community updates
- Technical deep-dives

**General Knowledge:**
- DeFi concepts
- Protocol comparisons
- Best practices

---

## 💰 Costs

| Item | Claude Sonnet 4 | GPT-4o |
|------|----------------|--------|
| **Per question** | ~$0.015 | ~$0.008 |
| **100 questions** | ~$1.50 | ~$0.80 |
| **Scraping** | FREE (local) | FREE (local) |
| **Vector DB** | FREE (local) | FREE (local) |

**Daily cost:** Only pay for questions asked. Switch models in GUI based on budget vs. quality needs.

---

## 🔧 Advanced Configuration

### **Change AI Model (GUI)**

1. Open GUI
2. Go to **Activity** tab
3. Select model from dropdown
4. Click any **Start** button

### **Change AI Model (Code)**

Edit `.env`:
```env
BOT_MODEL=claude-sonnet-4-20250514  # Best quality
# or
BOT_MODEL=gpt-4o                     # Faster, cheaper
```

### **Adjust Conversation Memory**

Edit `conversation_manager.py`:
```python
ConversationManager(
    max_messages=10,      # Summarize after 10 messages
    timeout_minutes=30    # Clear after 30 mins inactivity
)
```

### **Customize Bot Personality**

1. Open GUI → **Prompt** tab
2. Choose preset or edit custom prompt
3. Click **Save Prompt**
4. Restart bots to apply

### **Add More Bots**

1. Open GUI → **Settings** tab
2. Scroll to platform (Telegram/Discord/Slack)
3. Enter name and token
4. Click **Add Bot**
5. Return to **Activity** tab to start

---

## 🐛 Troubleshooting

**Bot not starting?**
```bash
pip install -r requirements.txt
playwright install chromium
```

**GUI shows "offline" after tab switch?**
- Fixed in latest version! Bots stay running when switching tabs.

**No data found?**
```bash
python scrape_all_data.py
```

**API key errors?**
- Open GUI → **Settings** tab
- Enter keys and click **Save**
- Or edit `.env` manually (no quotes, no spaces)

**Discord bot "privileged intents" error?**
- Go to Discord Developer Portal
- Enable: MESSAGE CONTENT INTENT, SERVER MEMBERS INTENT, PRESENCE INTENT
- See `DISCORD_SETUP.md` for details

**Bot not responding in groups?**
- **Telegram:** Mention with `@BotName` or reply to bot's messages
- **Discord:** Use `/ask` command or mention `@BotName`
- **Slack:** Mention `@BotName` in channels

**ChromaDB empty (0 chunks)?**
```bash
python scrape_all_data.py
```
This rebuilds the complete index.

---

## 🔒 Security

**Protected from Git:**
- `.env` (API keys)
- `.env.backup` (key backups)
- `bot_conversations.db` (user conversations)
- `chroma_db/` (vector database)

**Never commit:**
- Your API keys
- User conversation data
- Bot tokens

---

## 👥 Sharing with Team

**Share these files:**
- All `.py` files
- `requirements.txt`
- Documentation files (`.md`)
- `system_prompts.json`
- `.env.example` (NOT `.env`!)

**Each user needs:**
- Their own bot tokens (Telegram/Discord/Slack)
- Their own AI API keys (Claude/OpenAI)
- Run: `pip install -r requirements.txt`
- Copy `.env.example` to `.env` and fill in keys

**Optional: Share scraped data**
- Share `scraped_data/` folder to skip initial 20min scrape
- Share `chroma_db/` to skip index building
- They can still re-scrape anytime for fresh data

---

## 📊 System Capabilities

**Questions it can answer:**

✅ Technical: "How does the Autopool Router work?"  
✅ Live Data: "What's the current APY on plasmaUSD?"  
✅ Comparisons: "plasmaUSD vs autoUSD?"  
✅ News: "What's new with Auto Finance?"  
✅ General DeFi: "What is impermanent loss?"  
✅ Follow-ups: "What about the risks?" (remembers context)  
✅ Multi-turn: Maintains conversation across messages  

**Conversation Features:**

✅ Per-user memory in DMs  
✅ Per-chat memory in groups/channels  
✅ Auto-summarization after 10 messages  
✅ Timeout after 30 mins inactivity  
✅ Persistent storage across restarts  
✅ Full conversation history in GUI  

---

## 🎯 Current System Status

**Platforms:** Telegram, Discord, Slack  
**AI Models:** Claude Sonnet 4, GPT-4o  
**Data Sources:** 3 (Docs, Website, Blog)  
**Total Chunks Indexed:** 464  
**Vector Database:** ChromaDB with local embeddings  
**Conversation Storage:** SQLite (persistent)  
**GUI Tabs:** 6 (Activity, Conversations, Analytics, Prompt, Settings, Updates)  
**Updates:** Manual via GUI or daily scrape  

---

## 📖 Setup Guides

- **DISCORD_SETUP.md** - Discord bot creation & OAuth setup
- **SLACK_SETUP.md** - Slack app creation & installation
- **This README** - Complete reference

---

## 🚀 Next Steps

### **First Time:**
1. Install dependencies
2. Configure `.env` with API keys
3. Run `python scrape_all_data.py`
4. Launch GUI: `LAUNCH_GUI.bat` or `python bot_gui.py`
5. Add bots in Settings tab
6. Start bots in Activity tab

### **Daily Use:**
1. Launch GUI
2. Check Updates tab for data freshness
3. Start bots as needed
4. Monitor activity logs
5. View analytics and conversations

### **Maintenance:**
- Re-scrape weekly for latest data
- Check Analytics for user engagement
- Update system prompts for better responses
- Export conversations for fine-tuning

---

## 📞 Quick Commands

```bash
# First time setup
python scrape_all_data.py      # Build complete dataset (20 mins)

# Launch GUI
python bot_gui.py              # Main GUI
LAUNCH_GUI.bat                 # Windows shortcut

# Manual bot launches (advanced)
python telegram_bot.py         # Telegram only
python discord_bot.py          # Discord only
python slack_bot.py            # Slack only

# Manual operations
python scrape_website.py       # Just website
python scrape_blog.py          # Just blog
python build_complete_index.py # Just rebuild index
```

---

## ✨ Built With

**AI Models:**
- Claude Sonnet 4 (Anthropic)
- GPT-4o (OpenAI)

**Databases:**
- ChromaDB (vector storage)
- SQLite (conversation persistence)

**Platforms:**
- python-telegram-bot
- discord.py
- slack-bolt

**Scraping:**
- Playwright (JavaScript rendering)
- Requests (static pages)

**Embeddings:**
- Sentence Transformers (all-MiniLM-L6-v2)

**GUI:**
- Tkinter/ttk

---

## 📄 License

MIT License - Use for your own projects!

---

## 🎉 Features Highlights

### **Multi-Platform Architecture**
One codebase, shared knowledge base, works across all platforms simultaneously.

### **Dual AI Models**
Switch between Claude (best quality) and GPT-4o (faster, cheaper) without code changes.

### **Conversation Intelligence**
- Remembers context per user AND per chat
- Auto-summarizes long conversations
- Persists across bot restarts
- Searchable history in GUI

### **Professional Management**
- No terminal required (GUI handles everything)
- Live monitoring and logs
- Analytics dashboard
- Complete control over bot personality

### **Reply Detection (Telegram)**
Bot responds when users reply to its messages, making group conversations natural.

### **Data Quality**
464 chunks covering docs, website data (including live pool stats), and all blog posts.

---

**Ready to launch!** 🎉

Double-click `LAUNCH_GUI.bat` to get started!
