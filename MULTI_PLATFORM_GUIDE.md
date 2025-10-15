# Multi-Platform Bot System 🌐

## 🎯 What's New

Your bot system now supports **multiple platforms and multiple bots**!

---

## 🤖 Supported Platforms

| Platform | Status | How to Get Token |
|----------|--------|------------------|
| **Telegram** | ✅ Active | @BotFather on Telegram |
| **Discord** | 🔄 Planned | Discord Developer Portal |
| **Slack** | 🔄 Future | Slack API |

---

## ⚙️ Configuration

### **Setup in .env File:**

```env
# AI Model
ANTHROPIC_API_KEY=sk-ant-your-key

# Telegram Bots (you can have multiple!)
TELEGRAM_BOT_TOKEN_MAIN=123456:ABC-your-main-bot
TELEGRAM_BOT_TOKEN_SUPPORT=789012:DEF-your-support-bot
TELEGRAM_BOT_TOKEN_COMMUNITY=345678:GHI-your-community-bot

# Discord Bots (coming soon)
DISCORD_BOT_TOKEN_MAIN=your-discord-token
DISCORD_BOT_TOKEN_COMMUNITY=your-community-discord-token
```

---

## 🎮 How It Works

### **GUI Platform Selector:**

```
┌──────────────────────────────────────────┐
│  Auto Finance Bot Manager                │
├──────────────────────────────────────────┤
│  Platform: [Telegram - Main      ▼]     │
│                                          │
│  Options:                                │
│    • Telegram - Main                     │
│    • Telegram - Support                  │
│    • Telegram - Community                │
│    • Discord - Main (planned)            │
│                                          │
│  Bot Status: Stopped                     │
│  [Start Bot] [Stop Bot]                  │
└──────────────────────────────────────────┘
```

**Select platform → Click Start → Bot runs!**

---

## 💡 Use Cases

### **Multiple Telegram Bots:**

**Main Bot** - Public support
```env
TELEGRAM_BOT_TOKEN_MAIN=your-public-bot-token
```
- Answers user questions
- Public-facing
- Professional tone

**Support Bot** - Technical support
```env
TELEGRAM_BOT_TOKEN_SUPPORT=your-support-bot-token
```
- More detailed technical answers
- For power users
- Can be more technical

**Community Bot** - Casual community chat
```env
TELEGRAM_BOT_TOKEN_COMMUNITY=your-community-bot-token
```
- Super casual
- Community engagement
- Fun personality

---

### **Cross-Platform:**

**Telegram** - Public community
```env
TELEGRAM_BOT_TOKEN_MAIN=...
```

**Discord** - Developer community (future)
```env
DISCORD_BOT_TOKEN_MAIN=...
```

**Same knowledge base, different platforms!**

---

## 🔧 How to Add a New Bot

### **Step 1: Create the Bot**

**For Telegram:**
1. Open Telegram
2. Message @BotFather
3. Send `/newbot`
4. Follow instructions
5. Copy token

**For Discord (future):**
1. Visit discord.com/developers
2. Create application
3. Add bot
4. Copy token

---

### **Step 2: Add to .env**

```env
# Choose a descriptive name (MAIN, SUPPORT, COMMUNITY, etc.)
TELEGRAM_BOT_TOKEN_YOURNAME=your-bot-token-here
```

---

### **Step 3: Select in GUI**

1. Restart GUI: `python bot_gui.py`
2. Dropdown now shows: "Telegram - Yourname"
3. Select it
4. Click "Start Bot"

**Done!** 🎉

---

## 🎯 Current Setup

**Your .env currently has:**
```env
TELEGRAM_BOT_TOKEN=8343215230:AAEKq29...
```

**This will show in GUI as:**
```
Platform: [Telegram - Main ▼]
```

---

## 📝 Naming Convention

**Format:** `PLATFORM_BOT_TOKEN_NAME`

**Examples:**
- `TELEGRAM_BOT_TOKEN_MAIN`
- `TELEGRAM_BOT_TOKEN_SUPPORT`  
- `TELEGRAM_BOT_TOKEN_DEV`
- `DISCORD_BOT_TOKEN_MAIN`
- `DISCORD_BOT_TOKEN_COMMUNITY`

**Name can be anything** - shows in dropdown as "Platform - Name"

---

## 🔄 Switching Between Bots

1. **Stop current bot** (if running)
2. **Select different bot** from dropdown
3. **Start bot**

**Each bot:**
- Uses same data (docs + website + blog)
- Same RAG system
- Same conversation memory (per-user)
- Different platform/audience

---

## 🆕 What Changed in GUI

**Added:**
- ✅ Platform dropdown selector
- ✅ Auto-discovers bots from .env
- ✅ Shows bot display name
- ✅ Locks selector while bot is running
- ✅ Validates platform support

**Updated:**
- Bot status now shows selected platform
- Config check shows all configured bots
- Can switch between bots easily

---

## 🎯 Migration from Old .env

**Old format:**
```env
TELEGRAM_BOT_TOKEN=your-token
```

**New format:**
```env
TELEGRAM_BOT_TOKEN_MAIN=your-token
```

**Still works!** But won't show in dropdown. Recommend updating to new format.

---

## 🚀 Future: Discord Support

When Discord is ready, it will work exactly the same:

```env
DISCORD_BOT_TOKEN_MAIN=your-discord-token
```

Then select "Discord - Main" in GUI and click Start!

**Same codebase, multiple platforms!** 🌐

---

## 📊 Example Multi-Bot Setup

```env
# AI
ANTHROPIC_API_KEY=sk-ant-your-key

# Public Telegram Bot
TELEGRAM_BOT_TOKEN_MAIN=123:ABC...

# Support Telegram Bot  
TELEGRAM_BOT_TOKEN_SUPPORT=456:DEF...

# Discord for Developers
DISCORD_BOT_TOKEN_DEV=789...

# Internal Slack Bot
SLACK_BOT_TOKEN=012...
```

**GUI dropdown shows:**
```
- Telegram - Main
- Telegram - Support
- Discord - Dev (planned)
- Slack - Default (planned)
```

**Pick one, click Start!** ✅

---

## 🎯 Summary

**What you can now do:**

✅ **Multiple bots per platform** - Main, Support, Community, etc.  
✅ **Multiple platforms** - Telegram (now), Discord/Slack (future)  
✅ **Easy switching** - Dropdown selector in GUI  
✅ **Same knowledge base** - All bots share same data  
✅ **Flexible naming** - Call them whatever you want  
✅ **Simple setup** - Just add to .env  

---

## 🔄 Next Steps

**Your current bot is already configured!**

To add more bots:
1. Create new bot (e.g., another Telegram bot)
2. Add to .env: `TELEGRAM_BOT_TOKEN_SUPPORT=...`
3. Restart GUI
4. See it in dropdown!

**System is ready for multi-platform expansion!** 🚀

