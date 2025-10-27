# Google OAuth Setup Guide

## Your OAuth Client ID
```
421060950723-eivjljukiav2gu0l898lrnj0tkktbg5p.apps.googleusercontent.com
```

## Setup Steps

### 1. Go to Google Cloud Console
**Direct Link:**
```
https://console.cloud.google.com/apis/credentials?project=autobot-475622
```

### 2. Find Your OAuth 2.0 Client ID
Look for the client ID ending in `...tkktbg5p.apps.googleusercontent.com`

### 3. Click the Edit Icon (Pencil)

### 4. Add Authorized JavaScript Origins
⚠️ **IMPORTANT**: Add these EXACT URLs (no trailing slashes):
```
http://localhost:8000
https://autofinance-bot-421060950723.us-central1.run.app
```

**How to add:**
1. Find the section "Authorized JavaScript origins"
2. Click "+ ADD URI"
3. Paste `http://localhost:8000` (exactly as shown)
4. Click "+ ADD URI" again
5. Paste the Cloud Run URL
6. Click "SAVE"

### 5. Add Authorized Redirect URIs
⚠️ **IMPORTANT**: Add these EXACT URLs (no trailing slashes):
```
http://localhost:8000
https://autofinance-bot-421060950723.us-central1.run.app
```

**How to add:**
1. Find the section "Authorized redirect URIs"
2. Click "+ ADD URI"
3. Paste `http://localhost:8000` (exactly as shown)
4. Click "+ ADD URI" again
5. Paste the Cloud Run URL
6. Click "SAVE"

### 6. Click "Save"

Wait 1-2 minutes for changes to propagate.

---

## Test It

### Local Testing:
1. Go to `http://localhost:8000`
2. Click "Sign in with Google"
3. Should work!

### Cloud Testing:
1. Go to `https://autofinance-bot-421060950723.us-central1.run.app`
2. Click "Sign in with Google"
3. Should work!

---

## Current Status

✅ **Frontend:** Working perfectly (HTML, CSS, JS all loading)  
✅ **Backend API:** Running and responding  
✅ **Local Server:** Running on port 8000  
✅ **Cloud Deployment:** Live at the URL above  
❌ **Google Sign-In:** Needs OAuth configuration (follow steps above)

---

## What Works Right Now

Even without OAuth configured, you can see:
- Beautiful dark-themed chat interface
- Google Sign-In button (just can't click it yet)
- Fully functional UI

Once OAuth is configured, users can:
- Sign in with Google
- Ask questions about Auto Finance
- Get AI-powered answers with context from docs/website/blog
- Have persistent conversation history

