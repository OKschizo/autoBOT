# 🚀 Auto Finance Bot - Cloud Deployment

Web-based Q&A interface for Auto Finance. Users sign in with Google, ask questions, and get AI-powered responses with conversation memory.

---

## ✨ Features

- 🔐 **Google Sign-In** - Secure authentication
- 💬 **Chat Interface** - Beautiful, modern UI
- 🧠 **Conversation Memory** - Per-user context tracking
- 🤖 **Dual AI Models** - Claude Sonnet 4 or GPT-4o
- 📊 **Analytics** - Track questions and usage
- 🎨 **Responsive Design** - Works on all devices
- 🐳 **Docker Ready** - One-command deployment

---

## 🎯 Quick Start

### **Option 1: Docker (Recommended)**

```bash
# 1. Clone and navigate
cd cloud/

# 2. Configure environment
cp env.template .env
nano .env  # Add your API keys

# 3. Run with Docker
docker-compose up -d

# 4. Open browser
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

### **Option 2: Manual Setup**

```bash
# 1. Install backend dependencies
cd backend/
pip install -r requirements.txt

# 2. Run API server
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# 3. Serve frontend (in new terminal)
cd ../frontend/
python -m http.server 3000

# 4. Open http://localhost:3000
```

---

## ⚙️ Configuration

### **1. Get Google OAuth Credentials**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google+ API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Authorized JavaScript origins:
   - `http://localhost:3000` (development)
   - `https://your-domain.com` (production)
7. Copy **Client ID** to:
   - `.env` → `GOOGLE_CLIENT_ID`
   - `frontend/app.js` → `GOOGLE_CLIENT_ID`

### **2. Configure API Keys**

Edit `.env`:

```env
# AI Model (pick one or both)
ANTHROPIC_API_KEY=sk-ant-your-key
OPENAI_API_KEY=sk-proj-your-key
BOT_MODEL=claude-sonnet-4-20250514  # or gpt-4o

# Google OAuth
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
```

### **3. Update Frontend API URL**

Edit `frontend/app.js`:

```javascript
const API_URL = 'http://localhost:8000';  // Development
// const API_URL = 'https://your-api.com';  // Production
```

---

## 🌐 Deployment Options

### **Option A: Google Cloud Run (Recommended)**

**Backend:**

```bash
# Build and deploy API
gcloud builds submit --tag gcr.io/YOUR_PROJECT/autofinance-api
gcloud run deploy autofinance-api \
  --image gcr.io/YOUR_PROJECT/autofinance-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY,GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID
```

**Frontend:**

```bash
# Deploy to Firebase Hosting
cd frontend/
firebase init hosting
firebase deploy
```

### **Option B: Railway**

1. Connect GitHub repo
2. Select `cloud/` directory
3. Add environment variables
4. Deploy automatically

### **Option C: Render**

1. Create new **Web Service**
2. Connect repository
3. Set:
   - **Build Command:** `cd cloud && pip install -r backend/requirements.txt`
   - **Start Command:** `cd cloud && uvicorn backend.api:app --host 0.0.0.0 --port $PORT`
4. Add environment variables

### **Option D: Vercel + Supabase**

- **Frontend:** Deploy to Vercel
- **Backend:** Deploy as Vercel Serverless Functions
- **Database:** Use Supabase PostgreSQL

---

## 📁 Project Structure

```
cloud/
├── backend/
│   ├── api.py              # FastAPI server
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main page
│   ├── styles.css          # Modern styling
│   └── app.js              # Frontend logic
├── Dockerfile              # Container build
├── docker-compose.yml      # Multi-service setup
├── env.template            # Environment template
└── README.md               # This file
```

---

## 🔧 API Endpoints

### **Authentication**
- `POST /api/auth/google` - Verify Google token

### **Chat**
- `POST /api/ask` - Ask a question
- `GET /api/conversation/{user_id}` - Get conversation history
- `POST /api/conversation/clear` - Clear conversation

### **Stats**
- `GET /api/stats` - Bot statistics
- `GET /api/health` - Health check

---

## 🎨 Customization

### **Change Colors**

Edit `frontend/styles.css`:

```css
:root {
    --primary: #2563eb;      /* Main color */
    --secondary: #10b981;    /* Bot message */
    --bg-main: #0f172a;      /* Background */
}
```

### **Change Model**

Edit `.env`:

```env
BOT_MODEL=gpt-4o  # or claude-sonnet-4-20250514
```

### **Customize System Prompt**

The bot uses prompts from `system_prompts.json` in the parent directory.

---

## 🔒 Security Notes

1. **Never commit `.env`** - Already in `.gitignore`
2. **Enable CORS only for your domain** in `backend/api.py`
3. **Restrict Google OAuth** to your domain
4. **Use environment variables** for all secrets
5. **Enable HTTPS** in production

---

## 🐛 Troubleshooting

### **"Authentication failed"**
- Check `GOOGLE_CLIENT_ID` matches in `.env` and `app.js`
- Verify authorized origins in Google Cloud Console

### **"CORS error"**
- Add your frontend URL to `allow_origins` in `backend/api.py`

### **"Connection refused"**
- Ensure backend is running on port 8000
- Check `API_URL` in `frontend/app.js`

### **"No data/wrong answers"**
- Run `scrape_all_data.py` to build index
- Ensure `scraped_data/` is copied to Docker container

---

## 📊 Monitoring

### **View Logs (Docker)**
```bash
docker-compose logs -f api
```

### **View Stats**
```bash
curl http://localhost:8000/api/stats
```

### **Database**
Conversations are stored in `data/bot_conversations.db` (SQLite)

---

## 🚀 Going to Production

### **Pre-launch Checklist**

- [ ] Set up custom domain
- [ ] Configure Google OAuth for production domain
- [ ] Update `API_URL` in `frontend/app.js`
- [ ] Remove `"*"` from CORS `allow_origins`
- [ ] Enable HTTPS (Let's Encrypt / Cloud provider)
- [ ] Set up monitoring (Sentry, LogRocket)
- [ ] Configure backups for SQLite database
- [ ] Test on mobile devices
- [ ] Set up CDN for frontend (Cloudflare)

### **Environment Variables for Production**

```env
ANTHROPIC_API_KEY=sk-ant-prod-key
OPENAI_API_KEY=sk-proj-prod-key
BOT_MODEL=claude-sonnet-4-20250514
GOOGLE_CLIENT_ID=your-prod-id.apps.googleusercontent.com
DATABASE_PATH=/app/data/bot_conversations.db
```

---

## 💡 Usage Tips

**For Users:**
- Sign in with Google (any Gmail account)
- Ask questions naturally
- Conversations are saved per user
- Use "Clear" button to reset history

**For Admins:**
- Monitor at `/api/stats`
- Access database at `data/bot_conversations.db`
- Change model without redeploying (just restart)
- View logs with `docker-compose logs`

---

## 📞 Support

For issues or questions:
- Check the main README in parent directory
- Review API logs
- Test with `curl` commands

---

## 🎉 You're All Set!

Your Auto Finance bot is now running as a beautiful web application! 🚀

Users can access it at your domain, sign in with Google, and start asking questions.

