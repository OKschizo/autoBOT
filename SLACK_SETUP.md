# 💼 Slack Bot Setup Guide

## 🎉 Slack Bot is Ready!

Your Slack bot is fully implemented!

---

## 🔧 Slack App Setup

### **Step 1: Create Slack App**

1. Go to: https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. App Name: "Auto Finance Bot"
5. Pick your workspace
6. Click "Create App"

---

### **Step 2: Configure Bot User**

**In left sidebar:**

1. Click **OAuth & Permissions**
2. Scroll to **Scopes** → **Bot Token Scopes**
3. Add these scopes:
   - ✅ `chat:write` (Send messages)
   - ✅ `chat:write.public` (Send to any channel)
   - ✅ `channels:history` (Read messages)
   - ✅ `groups:history` (Read private channels)
   - ✅ `im:history` (Read DMs)
   - ✅ `mpim:history` (Read group DMs)
   - ✅ `app_mentions:read` (Detect @mentions)
   - ✅ `commands` (Slash commands)

---

### **Step 3: Install to Workspace**

1. Scroll up to **OAuth Tokens**
2. Click "Install to Workspace"
3. Click "Allow"
4. **Copy the "Bot User OAuth Token"** (starts with `xoxb-`)

---

### **Step 4: Enable Socket Mode (Easier!)**

**Recommended for development:**

1. Left sidebar → **Socket Mode**
2. Toggle **Enable Socket Mode** ON
3. Under "App-Level Tokens":
4. Click "Generate Token and Scopes"
5. Name: "Bot Token"
6. Add scope: `connections:write`
7. Click "Generate"
8. **Copy the token** (starts with `xapp-`)

---

### **Step 5: Enable Event Subscriptions**

1. Left sidebar → **Event Subscriptions**
2. Toggle **Enable Events** ON
3. Under **Subscribe to bot events**, add:
   - ✅ `app_mention`
   - ✅ `message.channels`
   - ✅ `message.groups`
   - ✅ `message.im`
   - ✅ `message.mpim`
4. Click "Save Changes"

---

### **Step 6: Add Slash Commands** (Optional)

1. Left sidebar → **Slash Commands**
2. Click "Create New Command"
3. Command: `/ask`
4. Description: "Ask Auto Finance Bot a question"
5. Usage Hint: `[your question]`
6. Click "Save"

Repeat for `/clear`, `/stats`

---

## 🔑 Add Tokens to Your System

### **In .env file:**

```env
SLACK_BOT_TOKEN_MAIN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
```

**Or use GUI:**
1. ⚙️ Configuration tab
2. Slack section
3. Name: `MAIN`
4. Token: `xoxb-...` (bot token)
5. Click "Add Bot"

---

## 🚀 Start Slack Bot

**In GUI:**

1. Restart to see Slack bot
2. 🤖 Bots tab
3. Slack Bots section
4. Click **Start**
5. Bot connects! ✅

---

## 💬 Using on Slack

### **Method 1: @Mention**
```
@AutoFinanceBot what are autopools?
```

### **Method 2: DM**
```
Message bot directly
No mention needed!
```

### **Method 3: Thread Reply**
```
Reply in thread where bot responded
Automatic context!
```

### **Method 4: Slash Commands**
```
/ask What are autopools?
/stats
/clear
```

---

## ✅ Features

**Same as Telegram & Discord:**
- ✅ Conversation memory (per user, per channel)
- ✅ Reply detection
- ✅ Same RAG system (464 chunks)
- ✅ Claude or OpenAI models
- ✅ Auto-summarization
- ✅ 30-minute timeout

**Slack-specific:**
- ✅ Thread support
- ✅ Socket Mode (no webhooks needed!)
- ✅ Slash commands
- ✅ Rich formatting

---

## 🎯 All Three Platforms Running!

```
🤖 Bots Tab

Telegram Bots
  Main    ● Running

Discord Bots
  Main    ● Running

Slack Bots
  Main    ● Running

All use same knowledge base!
Different audiences, same answers!
```

---

## 📊 Quick Reference

| Platform | Mention | DM | Reply | Slash Cmds |
|----------|---------|----|----|-----------|
| **Telegram** | @BotName | ✅ | ✅ | ❌ |
| **Discord** | @BotName | ✅ | ✅ | ✅ |
| **Slack** | @BotName | ✅ | ✅ | ✅ |

---

## 🔐 Required Tokens

**For Slack you need TWO tokens:**
- `SLACK_BOT_TOKEN` (xoxb-...) - For bot actions
- `SLACK_APP_TOKEN` (xapp-...) - For Socket Mode

**Both go in .env!**

---

## ✨ Complete!

**Your bot now works on:**
- ✅ Telegram
- ✅ Discord  
- ✅ Slack

**All from one GUI, same data, managed together!** 🎊

Add your Slack tokens and start it up! 🚀


