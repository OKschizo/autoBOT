# Complete Update System Guide 🔄

## 🎯 Overview

Your bot now has a **complete update system** with full optionality!

---

## 📊 Update Options

### **1. Quick Update** ⚡ (Recommended Daily)

**What it does:**
- Scrapes ONLY app.auto.finance
- Gets fresh APYs, TVLs, pool data
- Keeps existing docs and blog

**Time:** 5-10 minutes  
**Use when:** Daily, for live data updates

```bash
# Command line:
python scrape_selective.py quick

# Or click "Quick Update (Website)" in GUI
```

---

### **2. Full Update** 🔄 (Weekly)

**What it does:**
- Scrapes docs.auto.finance
- Scrapes app.auto.finance
- Scrapes blog.tokemak.xyz
- Rebuilds complete index

**Time:** 15-20 minutes  
**Use when:** Weekly, or when docs/blog change

```bash
# Command line:
python scrape_selective.py full

# Or click "Full Update (All)" in GUI
```

---

### **3. Blog Only** 📰

**What it does:**
- Scrapes ONLY blog.tokemak.xyz
- Keeps existing docs and website

**Time:** 3-5 minutes  
**Use when:** After publishing new blog post

```bash
# Command line:
python scrape_selective.py blog

# Or click "Blog Only" in GUI
```

---

### **4. Docs Only** 📚

**What it does:**
- Scrapes ONLY docs.auto.finance  
- Keeps existing website and blog

**Time:** 3-5 minutes  
**Use when:** After updating documentation

```bash
# Command line:
python scrape_selective.py docs

# Or click "Docs Only" in GUI
```

---

## 🖥️ GUI Features

### **Updated Interface:**

```
┌────────────────────────────────────────┐
│  Auto Finance Telegram Bot Manager    │
├────────────────────────────────────────┤
│  Status                                │
│  • Bot Status: Running ✅              │
│  • Questions: 42                       │
│  • Documents: 433                      │
│  • Model: claude-sonnet-4              │
│                                        │
│  [Start Bot] [Stop Bot] [Check Config]│
├────────────────────────────────────────┤
│  Data Updates                          │
│                                        │
│  Manual Updates:                       │
│  [Quick Update]  [Full Update]        │
│  [Blog Only]     [Docs Only]          │
│                                        │
│  Last Updated:                         │
│  • Website: 2025-10-15 11:00          │
│  • Blog: 2025-10-15 11:00             │
│  • Docs: 2025-10-15 11:00             │
│                                        │
│  Automated Schedule:                   │
│  Daily: [03:00] [quick ▼] [Enable]   │
│  Next run: Tomorrow 3:00 AM            │
├────────────────────────────────────────┤
│  Bot Logs                              │
│  [Logs shown here...]                  │
└────────────────────────────────────────┘
```

---

## ⚙️ Automated Scheduling

### **Enable in GUI:**

1. Set time (e.g., `03:00`)
2. Choose type: `quick` or `full`
3. Click "Enable Scheduler"

**Scheduler runs in background!**

### **Schedule Options:**

**Daily Quick Update:**
- Time: 03:00 AM (customizable)
- Type: Website only
- Updates: Every day at 3 AM
- Duration: 5-10 mins

**Daily Full Update:**
- Time: 03:00 AM (customizable)
- Type: Everything
- Updates: Every day at 3 AM
- Duration: 15-20 mins

---

## 📅 Recommended Schedule

### **Option A: Daily Quick** ⭐ (Recommended)

```
Monday-Sunday: Quick update at 3 AM
  → Fresh APYs/TVLs daily
  → Fast (5-10 mins)

Manually: Full update on Sundays
  → When you have time
  → Catches doc/blog changes
```

### **Option B: Daily Full**

```
Every day: Full update at 3 AM
  → Everything fresh daily
  → Slower (20 mins)
  → Overkill unless docs change daily
```

### **Option C: Manual Only**

```
No scheduler
Click buttons when needed
  → Quick: Daily before work
  → Blog: When you publish
  → Docs: When you update docs
```

---

## 💡 Smart Scraping Logic

### **What Gets Re-Scraped:**

| Update Type | Docs | Website | Blog | Time |
|-------------|------|---------|------|------|
| **Quick** | ❌ (keeps existing) | ✅ Fresh | ❌ (keeps existing) | 5-10m |
| **Full** | ✅ Fresh | ✅ Fresh | ✅ Fresh | 15-20m |
| **Blog Only** | ❌ (keeps existing) | ❌ (keeps existing) | ✅ Fresh | 3-5m |
| **Docs Only** | ✅ Fresh | ❌ (keeps existing) | ❌ (keeps existing) | 3-5m |

### **Why This Is Efficient:**

❌ **Without selective scraping:**
- Every update = 20 mins (scrape everything)
- Wastes time on unchanged data

✅ **With selective scraping:**
- Daily quick = 5-10 mins (just live data)
- Only scrape what changes
- 50-75% time savings!

---

## 🔄 How Merging Works

### **Quick Update Example:**

```python
# Step 1: Load existing data
existing_docs_chunks = load_from_index(source='docs')    # Keep these
existing_blog_chunks = load_from_index(source='blog')    # Keep these

# Step 2: Scrape fresh website data
new_website_chunks = scrape_website()                     # New fresh data

# Step 3: Merge
all_chunks = existing_docs_chunks + existing_blog_chunks + new_website_chunks

# Step 4: Rebuild index with merged data
rebuild_index(all_chunks)
```

**Result:** Docs and blog stay the same, website is fresh!

---

## 📊 Data Freshness

After different updates:

### **After Quick Update:**
- Docs: From last full update
- Website: ✅ **Fresh** (scraped just now)
- Blog: From last full/blog update

### **After Full Update:**
- Docs: ✅ **Fresh**
- Website: ✅ **Fresh**
- Blog: ✅ **Fresh**

### **After Blog Update:**
- Docs: From last full/docs update
- Website: From last full/quick update
- Blog: ✅ **Fresh**

---

## 🎮 Usage Examples

### **Scenario 1: Daily Morning Routine**

```
3:00 AM: Scheduler runs quick update automatically
  → Scrapes app.auto.finance
  → Fresh APYs, TVLs for the day
  → Takes 5-10 mins

9:00 AM: You start working
  → Bot has fresh data
  → No manual work needed!
```

---

### **Scenario 2: You Publish Blog Post**

```
1. Write and publish blog post
2. Open GUI
3. Click "Blog Only" button
4. Wait 3-5 minutes
5. Bot now knows about new post!
```

---

### **Scenario 3: You Update Docs**

```
1. Update docs.auto.finance
2. Click "Docs Only" in GUI
3. Wait 3-5 minutes
4. Bot has updated documentation!
```

---

### **Scenario 4: Weekly Deep Refresh**

```
Sunday 3:00 AM (or manual):
  → Click "Full Update"
  → Everything fresh
  → Catches any changes you missed
```

---

## 🎛️ Command Line Usage

### **Quick Reference:**

```bash
# Quick update (website only)
python scrape_selective.py quick

# Full update (everything)
python scrape_selective.py full

# Blog only
python scrape_selective.py blog

# Docs only
python scrape_selective.py docs
```

---

## ⚙️ Configuration

### **Stored in:** `update_config.json`

```json
{
  "schedule": {
    "enabled": true,
    "daily_time": "03:00",
    "daily_type": "quick",
    "weekly_day": "sunday",
    "weekly_time": "03:00",
    "weekly_enabled": true
  },
  "last_updates": {
    "docs": "2025-10-15T11:00:00Z",
    "website": "2025-10-15T11:00:00Z",
    "blog": "2025-10-15T11:00:00Z",
    "full": "2025-10-15T11:00:00Z"
  }
}
```

**Edit manually or use GUI!**

---

## 💰 Time & Cost Savings

### **Old Way (Full Update Every Time):**
```
Daily scrape: 20 mins × 7 days = 140 mins/week
```

### **New Way (Smart Selective):**
```
Daily quick: 7 mins × 7 days = 49 mins/week
Weekly full: 20 mins × 1 day = 20 mins/week
Total: 69 mins/week
```

**Savings: 50% time saved!** ⚡

---

## 🐛 Troubleshooting

### **"Update failed" error**

Check logs in GUI for specific error. Common issues:
- Internet connection
- Website structure changed
- Playwright not installed

### **Scheduler not running**

1. Make sure "Active" (green) shows in GUI
2. Check config time is valid (HH:MM format)
3. Scheduler runs in background - won't see immediate action

### **Bot not using new data**

After update:
1. Stop bot (if running)
2. Start bot again
3. Bot loads fresh collection

---

## 📋 Best Practices

### **Recommended Setup:**

✅ **Daily:** Quick update at 3 AM (automated)  
✅ **Weekly:** Full update on Sunday (manual or automated)  
✅ **On-demand:** Blog/docs when you publish  

### **When to Use Each:**

| Situation | Update Type |
|-----------|-------------|
| **Daily morning** | Quick (auto) |
| **Published blog post** | Blog Only |
| **Updated docs** | Docs Only |
| **Weekly refresh** | Full |
| **After long time** | Full |

---

## 🎯 Summary

**You now have:**

✅ **4 update options** - Quick, Full, Blog, Docs  
✅ **Manual buttons** in GUI  
✅ **Automated scheduler** with time picker  
✅ **Smart merging** - Only scrape what changed  
✅ **Time tracking** - See when last updated  
✅ **Next run display** - Know when next update  

**All integrated in the GUI!** 🎉

---

## 🚀 Quick Start

1. **Open GUI:**
   ```bash
   python bot_gui.py
   ```

2. **Set schedule:**
   - Daily: `03:00`
   - Type: `quick`
   - Click "Enable Scheduler"

3. **Or update manually:**
   - Click "Quick Update" for daily refresh
   - Click "Blog Only" after publishing
   - Click "Full Update" weekly

**That's it!** Bot stays fresh automatically! 🎯

---

## 📞 Need Help?

**Files:**
- `scrape_selective.py` - Selective scraping logic
- `scheduler.py` - Automated scheduling
- `bot_gui.py` - GUI with all controls
- `update_config.json` - Configuration (auto-created)

**Everything is ready to use!** 🚀

