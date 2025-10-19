"""
FastAPI Backend for Auto Finance Bot
Provides REST API for web-based Q&A interface
"""

import os
import sys
from typing import Optional, Dict, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
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

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Auto Finance Bot API",
    description="AI-powered Q&A for Auto Finance",
    version="1.0.0"
)

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

# Google OAuth client ID
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')

# Pydantic models
class AskRequest(BaseModel):
    question: str
    user_id: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None

class AskResponse(BaseModel):
    answer: str
    timestamp: str
    model: str

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
@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "running",
        "service": "Auto Finance Bot API",
        "model": model,
        "version": "1.0.0"
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
        
        # Get conversation context
        conv_context = conversation_manager.get_context(
            user_id=int(request.user_id.replace('google_', '').encode().hex(), 16) % (10**10),
            chat_id=0  # Single chat per user in web interface
        )
        
        # Get messages for LLM
        messages = conversation_manager.get_messages_for_llm(
            user_id=int(request.user_id.replace('google_', '').encode().hex(), 16) % (10**10),
            chat_id=0
        )
        
        # Ask the agent
        result = agent.ask(
            question=request.question,
            model=model,
            conversation_history=messages
        )
        
        answer = result.get('answer', 'Sorry, I encountered an error processing your question.')
        
        # Add to conversation manager
        user_id_int = int(request.user_id.replace('google_', '').encode().hex(), 16) % (10**10)
        conversation_manager.add_message(user_id_int, 'user', request.question, 0)
        conversation_manager.add_message(user_id_int, 'assistant', answer, 0)
        
        # Save to persistent storage
        storage.save_conversation(
            user_id=request.user_id,
            username=request.user_name or 'User',
            platform='web',
            chat_id='web_chat',
            question=request.question,
            answer=answer,
            model=model,
            tokens_used=result.get('usage', {}).get('total_tokens', 0)
        )
        
        logger.info(f"Successfully answered question from {request.user_name or request.user_id}")
        
        return AskResponse(
            answer=answer,
            timestamp=datetime.now().isoformat(),
            model=model
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

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "model": model,
        "rag_agent": "openai" if model.startswith('gpt') else "claude",
        "conversation_manager": "active",
        "storage": "active"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

