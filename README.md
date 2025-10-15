# Auto Finance Telegram Bot 🤖

Complete AI-powered Telegram bot for Auto Finance with live data scraping and conversation memory.

---

## 🎯 Features

✅ **Live Data** - Daily scraping of APYs, TVLs, pool allocations  
✅ **Complete Knowledge** - Docs + Website + Blog posts  
✅ **Conversation Memory** - Remembers context like Cursor AI  
✅ **Casual & Concise** - Natural, friendly responses  
✅ **Group Chat Ready** - Only responds when mentioned  
✅ **Claude Sonnet 4** - Latest, most capable model  
✅ **Desktop GUI** - Easy management interface  

---

## 🚀 Quick Start

### **1. Install Dependencies**

```bash
pip install -r requirements.txt
playwright install chromium
```

### **2. Configure API Keys**

Your `.env` file is already configured with:
- ✅ Claude API key
- ✅ Telegram bot token

### **3. Run First Scrape** (~20 minutes)

```bash
python scrape_all_data.py
```

This scrapes:
- Documentation (docs.auto.finance)
- Website + live data (app.auto.finance)
- Blog posts (blog.tokemak.xyz)

### **4. Start the Bot**

**Desktop GUI:**
```bash
python bot_gui.py
```
Click "Start Bot"

**Command Line:**
```bash
python telegram_bot.py --no-scrape
```

### **5. Use on Telegram!**

- Open Telegram
- Find your bot
- Send `/start`
- Ask questions!

---

## 💬 Usage Examples

### **In Direct Messages:**

```
You: What are Autopools?
Bot: Autopools are automated liquidity vaults that handle
     rebalancing, compounding, and yield optimization for you.
     Set-and-forget DeFi.

You: What's the current APY on plasmaUSD?
Bot: plasmaUSD is at 11.94% APY with $6.33M TVL. Deployed
     across Balancer, Euler, Aave, and Fluid.

You: Which pool is best?
Bot: Depends on your goals. plasmaUSD has highest APY (11.94%)
     but is on Plasma chain. autoUSD is on mainnet with 8.5% APY.
```

### **In Group Chats:**

```
@YourBotName what's the APY on autoUSD?
```

Bot only responds when mentioned!

---

## 🎛️ Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show help |
| `/stats` | Show statistics (questions answered, active conversations) |
| `/clear` | Clear your conversation history |

---

## 📅 Daily Updates

### **Get Fresh Data:**

```bash
python telegram_bot.py
```

When prompted:
```
Scrape fresh data? (y/n): y
```

Bot will scrape latest APYs, TVLs, blog posts, then start.

### **Or Skip Scraping:**

```bash
python telegram_bot.py --no-scrape
```

Uses yesterday's data (still works fine).

---

## 🗂️ Project Structure

```
TOKE_SCRAPER/
├── Core Bot Files
│   ├── telegram_bot.py           # Main Telegram bot
│   ├── bot_gui.py                # Desktop GUI manager
│   ├── rag_agent_complete.py     # RAG agent (all data)
│   └── conversation_manager.py   # Conversation tracking
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
│   ├── .env.example              # Template for others
│   ├── requirements.txt          # Dependencies
│   └── .gitignore                # Git ignore rules
│
├── Launchers
│   ├── START_BOT.bat             # Windows launcher
│   └── START_BOT.sh              # Linux/Mac launcher
│
├── Documentation
│   ├── START_HERE.md             # Main guide
│   ├── DAILY_SCRAPER_GUIDE.md    # Scraper reference
│   └── FINAL_SYSTEM_SUMMARY.md   # System overview
│
└── Data (auto-generated)
    ├── scraped_data/
    │   ├── gitbook_data.json     # Docs
    │   ├── website/              # Website + live data
    │   └── blog/                 # Blog posts
    └── chroma_db/
        └── auto_finance_complete/ # Vector database
```

---

## 🧠 What the Bot Knows

After daily scrape:

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

| Item | Cost |
|------|------|
| **Scraping** | FREE (runs locally) |
| **Vector database** | FREE (local embeddings) |
| **Per question** | ~$0.015 (Claude Sonnet 4) |

**Daily cost:** Only pay for questions asked (~$1.50 per 100 questions)

---

## 🔧 Advanced Configuration

### **Change Scrape Schedule**

Edit `telegram_bot.py` startup prompt, or run manually:
```bash
python scrape_all_data.py
```

### **Adjust Conversation Memory**

Edit `telegram_bot.py`:
```python
ConversationManager(
    max_messages=10,      # Summarize after 10 messages
    timeout_minutes=30    # Clear after 30 mins
)
```

### **Change Bot Model**

Edit `.env`:
```env
BOT_MODEL=claude-3-5-haiku-20241022  # Faster, cheaper
# or
BOT_MODEL=claude-sonnet-4-20250514   # Best quality (current)
```

### **Skip Certain Pages**

Edit `scrape_website.py`:
```python
self.skip_patterns = ['/portfolio', '/settings']
```

---

## 🐛 Troubleshooting

**Bot not starting?**
```bash
pip install -r requirements.txt
playwright install chromium
```

**No data found?**
```bash
python scrape_all_data.py
```

**Bot not responding?**
- In groups: Mention with `@BotName`
- In DMs: Send `/start` first
- Check GUI logs for errors

**Scraper failing?**
```bash
# Check Playwright
playwright install chromium

# Run individual scrapers
python scrape_website.py  # Test website only
python scrape_blog.py     # Test blog only
```

---

## 👥 Sharing with Team

**Share these files:**
- All `.py` files
- `scraped_data/` folder
- `.env.example` (NOT `.env`!)
- All documentation files
- `requirements.txt`

**Each user needs:**
- Their own Telegram bot (from @BotFather)
- Their own Claude API key
- Run: `pip install -r requirements.txt`
- Copy `.env.example` to `.env` and fill in keys

---

## 📊 System Capabilities

**Questions it can answer:**

✅ Technical: "How does the Autopool Router work?"  
✅ Live Data: "What's the current APY on plasmaUSD?"  
✅ Comparisons: "plasmaUSD vs autoUSD?"  
✅ News: "What's new with Auto Finance?"  
✅ General DeFi: "What is impermanent loss?"  
✅ Follow-ups: "What about the risks?" (remembers context)  

---

## 🎯 Current System Status

**Data Sources:** 3 (Docs, Website, Blog)  
**Total Pages Indexed:** ~100-120 pages  
**Vector Database:** ChromaDB with local embeddings  
**AI Model:** Claude Sonnet 4  
**Conversation:** Full memory with auto-summarization  
**Updates:** Daily scrape option  
**Interface:** Telegram + Desktop GUI  

---

## 📖 Documentation

- **START_HERE.md** - Quick start guide
- **DAILY_SCRAPER_GUIDE.md** - Scraper documentation
- **FINAL_SYSTEM_SUMMARY.md** - Complete overview
- **This README** - Quick reference

---

## 🚀 Next Steps

1. **First scrape:** `python scrape_all_data.py`
2. **Start bot:** `python bot_gui.py`
3. **Test on Telegram:** Ask questions with live data
4. **Daily:** Re-scrape for fresh APYs/TVLs

---

## 📞 Quick Commands

```bash
# First time setup
python scrape_all_data.py      # Build complete dataset

# Daily use
python telegram_bot.py          # Start with scrape option
python bot_gui.py               # GUI launcher

# Manual operations
python scrape_website.py        # Just website
python scrape_blog.py           # Just blog
python build_complete_index.py  # Just rebuild index
```

---

## ✨ Built With

- **Claude Sonnet 4** - AI responses
- **ChromaDB** - Vector database
- **Playwright** - JavaScript scraping
- **python-telegram-bot** - Telegram integration
- **Sentence Transformers** - Local embeddings

---

## 📄 License

MIT License - Use for your own projects!

---

**Ready to launch!** 🎉

See `START_HERE.md` for detailed step-by-step instructions.

