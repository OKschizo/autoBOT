# Bot Persistence & Cloud Storage Summary

## ✅ What's Implemented

### 1. **User Bot Persistence** 
User-created Telegram/Discord bots now **persist across container restarts**:

- ✅ Bot configs saved to SQLite (`bot_configs.db`)
- ✅ Configs backed up to GCS on shutdown
- ✅ Configs restored from GCS on startup
- ✅ Bots that were "running" auto-restart on container startup

### 2. **Conversation Persistence**
User conversations in the Q&A chat persist:

- ✅ Conversations saved to SQLite (`conversations.db`)
- ✅ Backed up to GCS on shutdown
- ✅ Restored from GCS on startup
- ✅ Users see their full conversation history

### 3. **Vector Database (ChromaDB)**
Knowledge base is **ephemeral** (rebuilt on startup):

- ✅ Scrapes fresh data on startup (~2 minutes)
- ✅ Always has latest website/blog content
- ✅ No stale data issues
- ✅ No external vector DB subscription needed

---

## How It Works

### On Container Startup:
```
1. Restore conversations.db from GCS
2. Restore bot_configs.db from GCS
3. Load saved bot configurations
4. Auto-start bots that were running before shutdown
5. Scrape fresh data (GitBook + Website + Blog)
6. Build ChromaDB locally
7. Start serving requests
```

### During Operation:
```
- User conversations → saved to local SQLite
- Bot configs → saved to local SQLite
- Bot status changes → saved immediately
- Data scraper → runs every 10 minutes (website only)
```

### On Container Shutdown:
```
1. Stop all running bots
2. Save bot statuses to bot_configs.db
3. Backup conversations.db to GCS
4. Backup bot_configs.db to GCS
5. Discard ephemeral ChromaDB
```

---

## What Persists vs. What Doesn't

| Data Type | Persists? | Storage | Notes |
|-----------|-----------|---------|-------|
| User conversations | ✅ Yes | GCS | Full history preserved |
| Bot configurations | ✅ Yes | GCS | Tokens, names, models |
| Bot running status | ✅ Yes | GCS | Auto-restart on startup |
| Bot activity logs | ❌ No | Memory | Lost on restart |
| Vector DB (ChromaDB) | ❌ No | Local | Rebuilt on startup |
| Scraped data files | ❌ No | Local | Re-scraped on startup |

---

## Storage Architecture

```
Cloud Run Container
├── /app/conversations.db (ephemeral)
│   ├── Restored from GCS on startup
│   └── Backed up to GCS on shutdown
│
├── /app/bot_configs.db (ephemeral)
│   ├── Restored from GCS on startup
│   └── Backed up to GCS on shutdown
│
├── /app/chroma_db/ (ephemeral)
│   └── Rebuilt on startup from fresh scrape
│
└── /app/scraped_data/ (ephemeral)
    └── Re-scraped on startup

Google Cloud Storage Bucket
├── conversations.db (persistent)
└── bot_configs.db (persistent)
```

---

## Auto-Restart Behavior

### Scenario 1: User adds a bot and starts it
```
1. User registers bot via web UI
2. Bot config saved to bot_configs.db
3. User clicks "Start"
4. Bot status updated to "running"
5. Status saved to bot_configs.db

[Container restarts]

6. bot_configs.db restored from GCS
7. Bot manager sees bot was "running"
8. Bot automatically restarted in background
9. User's bot continues running 24/7
```

### Scenario 2: User stops a bot
```
1. User clicks "Stop"
2. Bot status updated to "stopped"
3. Status saved to bot_configs.db

[Container restarts]

4. bot_configs.db restored from GCS
5. Bot manager sees bot was "stopped"
6. Bot remains stopped (no auto-restart)
```

---

## Cost Breakdown

### GCS Storage:
- `conversations.db`: ~10 MB
- `bot_configs.db`: ~1 KB
- **Total: $0.02/month**

### GCS Operations:
- Backup on shutdown: 2 files × 10 MB = 20 MB
- Restore on startup: 2 files × 10 MB = 20 MB
- Daily restarts: 40 MB/day = 1.2 GB/month
- **Total: $0.08/month**

### **Grand Total: ~$0.10/month** 🎉

---

## Testing Persistence

### Test 1: Bot Persistence
```bash
# 1. Start server
cd cloud/backend
python api.py

# 2. Open browser: http://localhost:8000
# 3. Add a Telegram bot and start it
# 4. Verify bot is "running"

# 5. Stop server (Ctrl+C)
# 6. Restart server
python api.py

# 7. Refresh browser
# ✅ Bot should still be there and auto-restart
```

### Test 2: Conversation Persistence
```bash
# 1. Sign in with Google
# 2. Ask a few questions in Q&A chat
# 3. Stop server (Ctrl+C)
# 4. Restart server
# 5. Sign in again
# ✅ Your conversation history should be there
```

### Test 3: GCS Backup (Cloud Only)
```bash
# 1. Deploy to Cloud Run
# 2. Add bots and have conversations
# 3. Check GCS bucket:
gsutil ls gs://your-bucket-name/

# ✅ Should see:
# gs://your-bucket-name/conversations.db
# gs://your-bucket-name/bot_configs.db
```

---

## Troubleshooting

### Bots not auto-restarting
- Check logs for "Restored X bot(s) from storage"
- Verify `bot_configs.db` exists
- Check bot status in database: `sqlite3 bot_configs.db "SELECT * FROM bot_configs;"`

### Conversations not persisting
- Check logs for "Backing up data to GCS"
- Verify GCS bucket is configured
- Test manually: `gsutil cp conversations.db gs://your-bucket-name/`

### GCS not working
- Verify `GCS_BUCKET_NAME` environment variable is set
- Check `GOOGLE_APPLICATION_CREDENTIALS` points to valid service account key
- Ensure service account has Storage Admin role

---

## Next Steps

1. ✅ Bot persistence implemented
2. ⏳ Add auto-restart on data updates (TODO #5)
3. ⏳ Add running indicators that persist (TODO #6)
4. ⏳ Deploy to Cloud Run (TODO #8)

**Bot persistence is now fully functional!** 🎉

Users can:
- Add bots that run 24/7
- Stop/restart bots anytime
- Bots survive container restarts
- Conversation history preserved
- No data loss on deployment updates


