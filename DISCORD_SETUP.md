# 🎮 Discord Bot Setup - Complete Guide

## 🎉 Discord Bot is NOW READY!

Your Discord bot is fully implemented with all the same features as Telegram!

---

## ✅ Features

**Same as Telegram:**
- ✅ Conversation memory (per user, per channel)
- ✅ Reply detection (reply to bot without mentioning)
- ✅ Mention detection (@BotName)
- ✅ DM support (always responds)
- ✅ Same RAG system (464 chunks)
- ✅ Claude or OpenAI models
- ✅ Casual, concise tone

**Discord-specific:**
- ✅ Slash commands (`/ask`, `/clear`, `/stats`, `/help`)
- ✅ Thread support
- ✅ 2000 character auto-splitting
- ✅ Embed messages for stats
- ✅ Ephemeral messages (private responses)

---

## 🚀 Quick Setup

### **1. Add Your Discord Token to .env**

```env
DISCORD_BOT_TOKEN_MAIN=your-discord-bot-token-here
```

**Or use GUI:**
1. ⚙️ Configuration tab
2. Discord Bots section
3. Name: `MAIN`
4. Token: [paste]
5. Click "Add Bot"

---

### **2. Start Discord Bot from GUI**

1. Restart GUI (to see Discord bot)
2. Go to 🤖 Bots tab
3. Find "Discord Bots" section
4. Click **Start** on Discord - Main
5. Bot connects to Discord! ✅

---

## 💬 How to Use on Discord

### **Method 1: Mention Bot**
```
@AutoFinanceBot what are autopools?
```

### **Method 2: Reply to Bot**
```
User: @AutoFinanceBot what are autopools?
Bot: [Explains]

User: [Right-click bot message → Reply]
      "What's the TVL?"
Bot: [Responds without needing mention!]
```

### **Method 3: Slash Commands**
```
/ask question:What are autopools?
/stats
/clear
/help
```

### **Method 4: DM**
```
Just message the bot directly
No mention needed in DMs!
```

---

## 📊 Slash Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/ask` | Ask a question | `/ask question:What are autopools?` |
| `/clear` | Clear your conversation | `/clear` |
| `/stats` | Show bot statistics | `/stats` |
| `/help` | Show help info | `/help` |

---

## 🎯 Conversation Features

### **Per-Channel Memory:**

```
#general channel:
You: @Bot what are autopools?
Bot: [Explains]
You: What's the TVL? [replies to bot]
Bot: [Knows we're talking about autopools]

#trading channel:
You: @Bot which pool is best?
Bot: [Fresh context, doesn't assume autopools]
```

**Each channel = separate conversation!**

---

### **Auto-Summarization:**

```
10 messages in channel → Summarize
Continue conversation with summary
Infinite conversation like Cursor!
```

---

## 🖥️ Running Both Bots

**In GUI:**

```
Discord Bots
  Main       ● Running  [Stop]

Telegram Bots  
  Main       ● Running  [Stop]

Both running simultaneously!
Same knowledge, different platforms!
```

---

## 🔧 Discord Bot Permissions

**When inviting bot, grant:**
- ✅ Send Messages
- ✅ Send Messages in Threads
- ✅ Embed Links
- ✅ Read Message History
- ✅ Use Slash Commands

**Use this invite URL format:**
```
https://discord.com/oauth2/authorize?client_id=YOUR_APP_ID&permissions=378944&scope=bot+applications.commands
```

(Replace YOUR_APP_ID with your Application ID from Discord Developer Portal)

---

## 🎮 Discord-Specific Features

### **Embeds for Pretty Responses:**

When you use `/stats`, you get a nice embed:
```
┌─────────────────────────────┐
│  📊 Bot Statistics          │
├─────────────────────────────┤
│  Questions: 42              │
│  Documents: 464             │
│  Conversations: 5           │
│  Model: claude-sonnet-4     │
└─────────────────────────────┘
```

### **Ephemeral Messages:**

`/help` and `/clear` send private messages only you see!

---

## 🔄 Switching Models

**Works same as Telegram:**

1. Select model from dropdown (Claude or GPT)
2. Stop Discord bot
3. Start Discord bot
4. Uses new model!

**Both Telegram and Discord can use different models if you want!**

---

## 📝 Your .env Should Have

```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
TELEGRAM_BOT_TOKEN_MAIN=8343...
DISCORD_BOT_TOKEN_MAIN=your-discord-token
BOT_MODEL=gpt-4o
```

---

## 🧪 Test Discord Bot

After starting:

**In Discord:**
```
/help
→ Shows help message

@AutoFinanceBot how many autopools are there?
→ Bot responds with 14

[Reply to bot's message]
"Which has highest APY?"
→ Bot knows context!

/stats
→ Shows pretty statistics embed
```

---

## ✅ Ready to Use!

**Add your Discord token and start the bot from GUI!**

**Your Auto Finance bot now works on BOTH Telegram and Discord!** 🎉


