# ⚡ Quick Start Guide

Get your Auto Finance web bot running in 5 minutes!

---

## 🎯 Step-by-Step

### **1. Get Google OAuth Client ID**

1. Visit [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create project (or select existing)
3. Click **"Create Credentials"** → **"OAuth 2.0 Client ID"**
4. Choose **"Web application"**
5. Add authorized origin: `http://localhost:3000`
6. Copy the **Client ID** (looks like `xxx.apps.googleusercontent.com`)

### **2. Configure Environment**

```bash
cd cloud/
cp env.template .env
```

Edit `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
BOT_MODEL=claude-sonnet-4-20250514
```

Edit `frontend/app.js` (line 2):
```javascript
const GOOGLE_CLIENT_ID = 'your-id.apps.googleusercontent.com';  // Same as .env
```

### **3. Run It!**

**Option A: Python (Easiest)**
```bash
python run_local.py
```

**Option B: Docker**
```bash
docker-compose up
```

**Option C: Manual**
```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
uvicorn api:app --reload

# Terminal 2: Frontend
cd frontend
python -m http.server 3000
```

### **4. Open Browser**

Visit: **http://localhost:3000**

Sign in with any Gmail account and start chatting! 🎉

---

## 🐛 Common Issues

**"Authentication failed"**
- Make sure `GOOGLE_CLIENT_ID` matches in both `.env` AND `app.js`

**"Connection refused"**
- Backend must be running on port 8000
- Check `API_URL` in `app.js`

**"No index found"**
- Run `scrape_all_data.py` from parent directory first
- This builds the knowledge base

---

## 🚀 Deploy to Production

See full [README.md](README.md) for deployment to:
- Google Cloud Run
- Railway
- Render
- Vercel + Supabase

---

**Need help?** Check the main [README.md](README.md) or parent directory's docs.

