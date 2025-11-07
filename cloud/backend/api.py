"""
FastAPI Backend for Auto Finance Bot
Provides REST API for web-based Q&A interface
"""

import os
import sys
from typing import Optional, Dict, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Header, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
import logging

# Add parent directory to path to import existing modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from conversation_manager import ConversationManager
from conversation_storage import ConversationStorage
from rag_agent_complete import CompleteRAGAgent
from rag_agent_openai import OpenAIRAGAgent
from dotenv import load_dotenv

# Load .env file only if it exists (for local development)
# In Cloud Run, environment variables are set directly, so this won't override them
load_dotenv(override=False)

# Setup logging FIRST before any other imports that might use it
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import bot_manager from current directory
try:
    from bot_manager import bot_manager
except ImportError:
    # Fallback for different import contexts
    import bot_manager as bm
    bot_manager = bm.bot_manager

# Import data scraper service
try:
    from data_scraper_service import scraper_service
except ImportError as e:
    scraper_service = None
    logger.warning(f"Data scraper service not available: {e}")

# Import GCS storage
try:
    from gcs_storage import gcs_storage
except ImportError as e:
    gcs_storage = None
    logger.warning(f"GCS storage not available: {e}")

# Initialize FastAPI
app = FastAPI(
    title="Auto Finance Bot API",
    description="AI-powered Q&A for Auto Finance",
    version="1.0.0"
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Start background services on app startup"""
    logger.info("Starting background services...")
    
    # Restore persistent data from GCS if available
    if gcs_storage and gcs_storage.use_gcs:
        logger.info("Restoring data from GCS...")
        gcs_storage.load_sqlite_db('conversations.db', 'conversations.db')
        gcs_storage.load_sqlite_db('bot_configs.db', 'bot_configs.db')
        logger.info("✅ Data restored from GCS")
    
    # ChromaDB is pre-built and baked into the Docker image
    logger.info("✅ ChromaDB pre-loaded in Docker image")
    
    # Start scraper service
    if scraper_service:
        # Register callback to restart bots when data is updated
        def on_data_update():
            logger.info("📊 Data updated! Restarting user bots...")
            bot_manager.restart_all_running_bots()
        
        scraper_service.register_update_callback(on_data_update)
        scraper_service.start()
        logger.info("✅ Data scraper service started")
    else:
        logger.warning("⚠️ Data scraper service not available")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background services on app shutdown"""
    logger.info("Stopping background services...")
    
    # Stop scraper
    if scraper_service:
        scraper_service.stop()
        logger.info("✅ Data scraper service stopped")
    
    # Backup persistent data to GCS
    if gcs_storage and gcs_storage.use_gcs:
        logger.info("Backing up data to GCS...")
        gcs_storage.save_sqlite_db('conversations.db', 'conversations.db')
        gcs_storage.save_sqlite_db('bot_configs.db', 'bot_configs.db')
        
        # Backup ChromaDB (the main knowledge base)
        chroma_path = "/app/chroma_db" if os.path.exists("/app") else "./chroma_db"
        gcs_storage.backup_directory(chroma_path, 'chroma_db')
        
        logger.info("✅ Data backed up to GCS")

# CORS - Allow your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://your-app.web.app",  # Replace with your Firebase domain
        "*"  # For development - remove in production!
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
conversation_manager = ConversationManager(max_messages=10, timeout_minutes=30)
storage = ConversationStorage()

# Initialize RAG agent based on model
model = os.getenv('BOT_MODEL', 'claude-sonnet-4-20250514')
if model.startswith('gpt'):
    agent = OpenAIRAGAgent()
    logger.info(f"Using OpenAI model: {model}")
else:
    agent = CompleteRAGAgent()
    logger.info(f"Using Claude model: {model}")

# Google OAuth client ID - try multiple ways to get it
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or os.getenv('GOOGLE_CLIENT_ID', '')
# Log for debugging (remove in production if sensitive)
if GOOGLE_CLIENT_ID:
    logger.info(f"GOOGLE_CLIENT_ID loaded: {GOOGLE_CLIENT_ID[:20]}... (length: {len(GOOGLE_CLIENT_ID)})")
else:
    logger.error("GOOGLE_CLIENT_ID is empty or not set!")
    logger.error(f"Available env vars with 'GOOGLE': {[k for k in os.environ.keys() if 'GOOGLE' in k.upper()]}")

# Serve static frontend files FIRST (before API routes)
# Try multiple possible frontend locations
frontend_path = None
possible_paths = [
    os.path.join(os.path.dirname(__file__), "../frontend"),  # Relative to backend/api.py
    "/app/frontend",  # Docker absolute path
    os.path.join(os.getcwd(), "frontend"),  # Relative to working directory
]

for path in possible_paths:
    abs_path = os.path.abspath(path)
    logger.info(f"Checking frontend path: {abs_path}")
    if os.path.exists(abs_path):
        frontend_path = abs_path
        logger.info(f"✓ Found frontend at: {frontend_path}")
        logger.info(f"Frontend files: {os.listdir(frontend_path)}")
        break
    else:
        logger.warning(f"✗ Not found: {abs_path}")

if not frontend_path:
    logger.error("Frontend directory not found in any expected location!")
    frontend_path = "/app/frontend"  # Fallback for error messages

# Always define these routes (they'll 404 if files don't exist, but won't break the app)
@app.get("/styles.css")
async def serve_css():
    css_path = os.path.join(frontend_path, "styles.css")
    if os.path.exists(css_path):
        return FileResponse(css_path)
    raise HTTPException(status_code=404, detail="CSS not found")

@app.get("/app.js")
async def serve_js():
    js_path = os.path.join(frontend_path, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path)
    raise HTTPException(status_code=404, detail="JS not found")

@app.get("/favicon.ico")
async def serve_favicon():
    favicon_path = os.path.join(frontend_path, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    # Return empty 204 No Content if favicon doesn't exist
    return Response(status_code=204)

@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html"""
    index_path = os.path.join(frontend_path, "index.html")
    logger.info(f"Attempting to serve index.html from: {index_path}")
    logger.info(f"Index.html exists: {os.path.exists(index_path)}")
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # Fallback if frontend not found
    logger.warning(f"Frontend not found at {frontend_path}")
    return {
        "status": "running",
        "service": "Auto Finance Bot API",
        "model": model,
        "version": "1.0.0",
        "note": "Frontend not found. API only.",
        "frontend_path": frontend_path,
        "exists": os.path.exists(frontend_path)
    }

# Pydantic models
class AskRequest(BaseModel):
    question: str
    user_id: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    thread_id: Optional[str] = None  # Conversation thread ID
    system_prompt: Optional[str] = None  # Custom system prompt (Option A)

class AskResponse(BaseModel):
    answer: str
    timestamp: str
    model: str
    thread_id: Optional[str] = None  # Return thread_id so frontend can track it

class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: str

class ClearConversationRequest(BaseModel):
    user_id: str

class GoogleAuthRequest(BaseModel):
    id_token: str

class UserInfo(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None


# Auth helper
async def verify_google_token(token: str) -> Dict:
    """Verify Google ID token and return user info"""
    try:
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        return {
            'user_id': idinfo['sub'],
            'email': idinfo['email'],
            'name': idinfo.get('name', 'User'),
            'picture': idinfo.get('picture')
        }
    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")


# Routes
@app.get("/api/health")
async def health_check():
    """Health check"""
    return {
        "status": "running",
        "service": "Auto Finance Bot API",
        "model": model,
        "version": "1.0.0"
    }

@app.get("/api/config")
async def get_config():
    """Get public configuration (safe to expose)"""
    # Re-read env vars at request time to ensure we have latest values
    current_client_id = os.environ.get('GOOGLE_CLIENT_ID') or os.getenv('GOOGLE_CLIENT_ID', '') or GOOGLE_CLIENT_ID
    current_model = os.environ.get('BOT_MODEL') or os.getenv('BOT_MODEL', '') or model
    
    logger.info(f"Config requested - client_id length: {len(current_client_id)}, model: {current_model}")
    
    return {
        "google_client_id": current_client_id,
        "model": current_model
    }

@app.post("/api/auth/google")
async def google_auth(request: GoogleAuthRequest):
    """Verify Google Sign-In token"""
    user_info = await verify_google_token(request.id_token)
    return UserInfo(**user_info)

@app.post("/api/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Ask a question and get an AI response
    Maintains conversation context per user
    """
    try:
        logger.info(f"Question from {request.user_name or request.user_id}: {request.question}")
        
        # Get conversation context for the user (use thread_id if provided)
        user_id_int = int(request.user_id.replace('google_', '').encode().hex(), 16) % (10**10)
        
        # Use thread_id hash as chat_id for proper context isolation
        chat_id_for_context = 0
        if request.thread_id:
            chat_id_for_context = hash(request.thread_id) % (10**10)
        
        conv_context = conversation_manager.get_context(
            user_id=user_id_int,
            chat_id=chat_id_for_context
        )
        
        # Use the question directly (conversation context is maintained separately)
        # The RAG agent will retrieve relevant context from the knowledge base
        try:
            result = agent.ask(
                question=request.question,
                model=model,
                max_tokens=2000,
                n_results=10,  # Retrieve more chunks for better context
                system_prompt=request.system_prompt  # Pass custom prompt (Option A)
            )
            answer = result.get('answer', 'Sorry, I encountered an error processing your question.')
        except Exception as rag_error:
            logger.error(f"RAG agent error: {rag_error}", exc_info=True)
            # Provide more specific error messages
            error_str = str(rag_error)
            if "401" in error_str or "authentication" in error_str.lower() or "invalid x-api-key" in error_str.lower():
                answer = "⚠️ API authentication error. Please check that the Anthropic API key is configured correctly in Cloud Run environment variables."
            elif "collection" in error_str.lower() or "index not built" in error_str.lower() or "No collection found" in error_str.lower():
                answer = "⚠️ I'm having trouble accessing my knowledge base. The data might not be scraped yet. Please run a scrape from the Data Status page to populate the knowledge base."
            else:
                answer = f"⚠️ Error processing your question: {error_str[:200]}"
            result = {'usage': {'total_tokens': 0}}
        
        # Create or use thread
        thread_id = request.thread_id
        if not thread_id:
            # Create new thread for this conversation
            thread_id = storage.create_thread(request.user_id)
        
        # Add to conversation manager (use thread_id hash as chat_id for context)
        user_id_int = int(request.user_id.replace('google_', '').encode().hex(), 16) % (10**10)
        chat_id_int = hash(thread_id) % (10**10) if thread_id else 0  # Convert thread_id to int for manager
        conversation_manager.add_message(user_id_int, 'user', request.question, chat_id_int)
        conversation_manager.add_message(user_id_int, 'assistant', answer, chat_id_int)
        
        # Save to persistent storage with thread
        storage.save_conversation(
            user_id=request.user_id,
            username=request.user_name or 'User',
            platform='web',
            chat_id='web_chat',
            question=request.question,
            answer=answer,
            model=model,
            tokens_used=result.get('usage', {}).get('total_tokens', 0),
            thread_id=thread_id,
            system_prompt=request.system_prompt
        )
        
        logger.info(f"Successfully answered question from {request.user_name or request.user_id}")
        
        return AskResponse(
            answer=answer,
            timestamp=datetime.now().isoformat(),
            model=model,
            thread_id=thread_id
        )
        
    except Exception as e:
        logger.error(f"Error answering question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/api/conversation/{user_id}", response_model=List[ConversationMessage])
async def get_conversation(user_id: str):
    """Get conversation history for a user"""
    try:
        user_id_int = int(user_id.replace('google_', '').encode().hex(), 16) % (10**10)
        messages = conversation_manager.get_messages_for_llm(user_id_int, 0)
        
        return [
            ConversationMessage(
                role=msg['role'],
                content=msg['content'],
                timestamp=datetime.now().isoformat()
            )
            for msg in messages
        ]
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversation/clear")
async def clear_conversation(request: ClearConversationRequest):
    """Clear conversation history for a user"""
    try:
        user_id_int = int(request.user_id.replace('google_', '').encode().hex(), 16) % (10**10)
        conversation_manager.clear_conversation(user_id_int, 0)
        return {"status": "success", "message": "Conversation cleared"}
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CONVERSATION THREAD MANAGEMENT
# ============================================================================

class CreateThreadRequest(BaseModel):
    user_id: str
    title: Optional[str] = None

class UpdateThreadTitleRequest(BaseModel):
    user_id: str
    title: str

@app.post("/api/threads/create")
async def create_thread(request: CreateThreadRequest):
    """Create a new conversation thread"""
    try:
        thread_id = storage.create_thread(request.user_id, request.title)
        return {"success": True, "thread_id": thread_id}
    except Exception as e:
        logger.error(f"Error creating thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/threads/{user_id}")
async def get_user_threads(user_id: str):
    """Get all conversation threads for a user"""
    try:
        threads = storage.get_user_threads(user_id)
        return {"threads": threads}
    except Exception as e:
        logger.error(f"Error getting threads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str):
    """Get all messages in a conversation thread"""
    try:
        messages = storage.get_thread_messages(thread_id)
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error getting thread messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/threads/{thread_id}")
async def delete_thread(thread_id: str, user_id: str = Query(..., description="User ID")):
    """Delete a conversation thread"""
    try:
        success = storage.delete_thread(thread_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Thread not found or access denied")
        return {"success": True, "message": "Thread deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/threads/{thread_id}/title")
async def update_thread_title(thread_id: str, request: UpdateThreadTitleRequest):
    """Update a thread's title"""
    try:
        success = storage.update_thread_title(thread_id, request.user_id, request.title)
        if not success:
            raise HTTPException(status_code=404, detail="Thread not found or access denied")
        return {"success": True, "message": "Title updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating thread title: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

@app.get("/api/prompts/templates")
async def get_prompt_templates():
    """Get available prompt templates"""
    try:
        import json
        from pathlib import Path
        
        prompt_file = Path("system_prompts.json")
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                prompts = json.load(f)
                return {
                    "templates": [
                        {"name": "default", "description": "Standard Auto Finance assistant"},
                        {"name": "technical", "description": "Technical expert mode"},
                        {"name": "beginner_friendly", "description": "Beginner-friendly explanations"},
                        {"name": "marketing", "description": "Marketing-focused responses"},
                        {"name": "seo_specialist", "description": "SEO specialist mode (auto-detected)"}
                    ],
                    "prompts": prompts
                }
        else:
            return {"templates": [], "prompts": {}}
    except Exception as e:
        logger.error(f"Error getting prompt templates: {e}")
        return {"templates": [], "prompts": {}}

@app.get("/api/stats")
async def get_stats():
    """Get bot statistics"""
    try:
        analytics = storage.get_analytics()
        return {
            "total_conversations": analytics.get("total_conversations", 0),
            "unique_users": analytics.get("unique_users", 0),
            "total_tokens": analytics.get("total_tokens", 0),
            "platforms": analytics.get("platform_breakdown", {})
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BOT MANAGEMENT API ENDPOINTS
# ============================================================================

class RegisterBotRequest(BaseModel):
    bot_id: str
    platform: str  # 'telegram' or 'discord'
    token: str
    name: str
    model: Optional[str] = "gpt-4o"
    system_prompt: Optional[str] = "default"

class UpdateBotConfigRequest(BaseModel):
    model: Optional[str] = None
    system_prompt: Optional[str] = None

@app.post("/api/bots/register")
async def register_bot(request: RegisterBotRequest):
    """Register a new bot"""
    try:
        result = bot_manager.register_bot(
            bot_id=request.bot_id,
            platform=request.platform,
            token=request.token,
            name=request.name,
            model=request.model,
            system_prompt=request.system_prompt
        )
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Error registering bot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/bots/{bot_id}")
async def unregister_bot(bot_id: str):
    """Unregister a bot"""
    try:
        result = bot_manager.unregister_bot(bot_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Error unregistering bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bots/{bot_id}/start")
async def start_bot(bot_id: str):
    """Start a bot"""
    try:
        result = bot_manager.start_bot(bot_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bots/{bot_id}/stop")
async def stop_bot(bot_id: str):
    """Stop a bot"""
    try:
        result = bot_manager.stop_bot(bot_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bots/{bot_id}/restart")
async def restart_bot(bot_id: str):
    """Restart a bot"""
    try:
        result = bot_manager.restart_bot(bot_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Error restarting bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bots")
async def list_bots():
    """List all bots"""
    try:
        bots = bot_manager.get_all_bots_status()
        return {"bots": bots}
    except Exception as e:
        logger.error(f"Error listing bots: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bots/{bot_id}")
async def get_bot_status(bot_id: str):
    """Get bot status"""
    try:
        status = bot_manager.get_bot_status(bot_id)
        if not status:
            raise HTTPException(status_code=404, detail="Bot not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bots/{bot_id}/logs")
async def get_bot_logs(bot_id: str, limit: int = 50):
    """Get bot logs"""
    try:
        logs = bot_manager.get_bot_logs(bot_id, limit)
        if logs is None:
            raise HTTPException(status_code=404, detail="Bot not found")
        return {"logs": logs}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/bots/{bot_id}/config")
async def update_bot_config(bot_id: str, request: UpdateBotConfigRequest):
    """Update bot configuration"""
    try:
        result = bot_manager.update_bot_config(
            bot_id=bot_id,
            model=request.model,
            system_prompt=request.system_prompt
        )
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bot config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DATA SCRAPER ENDPOINTS
# ============================================================================

@app.get("/api/scraper/status")
async def get_scraper_status():
    """Get data scraper status"""
    if not scraper_service:
        raise HTTPException(status_code=503, detail="Scraper service not available")
    return scraper_service.get_status()

@app.post("/api/scraper/trigger")
async def trigger_manual_scrape(scrape_type: str = Query("full", description="Type of scrape: full, gitbook, website, or blog")):
    """Manually trigger a data scrape"""
    if not scraper_service:
        logger.error("Scraper service not available")
        raise HTTPException(status_code=503, detail="Scraper service not available")
    
    if scrape_type not in ("full", "gitbook", "website", "blog"):
        raise HTTPException(status_code=400, detail=f"Invalid scrape_type: {scrape_type}. Must be one of: full, gitbook, website, blog")
    
    full_scrape = (scrape_type == "full")
    result = scraper_service.trigger_manual_scrape(full_scrape=full_scrape, scrape_type=scrape_type)
    if not result['success']:
        logger.warning(f"Failed to trigger scrape: {result.get('error', 'Unknown error')}")
        raise HTTPException(status_code=400, detail=result.get('error', 'Unknown error'))
    
    logger.info(f"Manual {scrape_type} scrape triggered successfully: {result.get('message', '')}")
    return result

@app.get("/api/test/playwright")
async def test_playwright():
    """Test if Playwright works in the container"""
    import subprocess
    try:
        result = subprocess.run(
            ['python', '/app/test_playwright.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Test timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/emergency/build-index")
async def emergency_build_index():
    """Emergency endpoint to build index from existing data"""
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, '/app/run_build_now.py'],
            capture_output=True,
            text=True,
            timeout=120
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Build timed out after 2 minutes"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

