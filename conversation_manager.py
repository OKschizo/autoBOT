"""
Conversation Manager with Summarization
Tracks conversations per user and summarizes when hitting context limits
"""

import time
from typing import Dict, List, Optional
from anthropic import Anthropic
import os


class ConversationManager:
    """Manages conversation context per user with automatic summarization"""
    
    def __init__(self, max_messages: int = 10, timeout_minutes: int = 30):
        """
        Args:
            max_messages: Max messages before summarization
            timeout_minutes: Clear conversation after this many minutes of inactivity
        """
        self.max_messages = max_messages
        self.timeout_seconds = timeout_minutes * 60
        self.conversations: Dict[tuple, Dict] = {}  # (user_id, chat_id) -> conversation data
        
        # For summarization
        self.anthropic_client = None
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            self.anthropic_client = Anthropic(api_key=api_key)
    
    def add_message(self, user_id: int, role: str, content: str, chat_id: int = None):
        """Add a message to the conversation"""
        now = time.time()
        
        # Use (user_id, chat_id) as key for separate conversations per chat
        conv_key = (user_id, chat_id) if chat_id else (user_id, user_id)  # DM uses user_id for both
        
        # Initialize or check timeout
        if conv_key not in self.conversations:
            self.conversations[conv_key] = {
                'messages': [],
                'summary': None,
                'last_activity': now
            }
        else:
            # Check timeout
            if now - self.conversations[conv_key]['last_activity'] > self.timeout_seconds:
                # Conversation timed out, start fresh
                self.conversations[conv_key] = {
                    'messages': [],
                    'summary': None,
                    'last_activity': now
                }
        
        # Add message
        self.conversations[conv_key]['messages'].append({
            'role': role,
            'content': content,
            'timestamp': now
        })
        self.conversations[conv_key]['last_activity'] = now
        
        # Check if we need to summarize
        if len(self.conversations[conv_key]['messages']) > self.max_messages:
            self._summarize_conversation(conv_key)
    
    def get_context(self, user_id: int, chat_id: int = None, include_last_n: int = 5) -> str:
        """
        Get conversation context for RAG query
        
        Returns formatted context with summary + recent messages
        """
        conv_key = (user_id, chat_id) if chat_id else (user_id, user_id)
        
        if conv_key not in self.conversations:
            return ""
        
        conv = self.conversations[conv_key]
        context_parts = []
        
        # Add summary if exists
        if conv['summary']:
            context_parts.append(f"Previous conversation summary: {conv['summary']}")
        
        # Add recent messages
        recent_messages = conv['messages'][-include_last_n:]
        if recent_messages:
            context_parts.append("\nRecent conversation:")
            for msg in recent_messages:
                role_label = "User" if msg['role'] == 'user' else "Assistant"
                context_parts.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def get_messages_for_llm(self, user_id: int, chat_id: int = None) -> List[Dict]:
        """
        Get conversation messages formatted for Claude API
        
        Returns list of message dicts with role and content
        """
        conv_key = (user_id, chat_id) if chat_id else (user_id, user_id)
        
        if conv_key not in self.conversations:
            return []
        
        conv = self.conversations[conv_key]
        
        # If we have a summary, start with it as context
        messages = []
        if conv['summary']:
            messages.append({
                'role': 'user',
                'content': f'[Previous conversation context: {conv["summary"]}]'
            })
            messages.append({
                'role': 'assistant',
                'content': 'Got it, I remember our previous discussion.'
            })
        
        # Add recent actual messages (keep last 6-8 for context)
        recent_messages = conv['messages'][-8:]
        messages.extend([
            {'role': msg['role'], 'content': msg['content']}
            for msg in recent_messages
        ])
        
        return messages
    
    def _summarize_conversation(self, conv_key: tuple):
        """Summarize the conversation and keep only recent messages"""
        if not self.anthropic_client:
            # No API key, just truncate
            self.conversations[conv_key]['messages'] = \
                self.conversations[conv_key]['messages'][-5:]
            return
        
        conv = self.conversations[conv_key]
        
        # Get messages to summarize (all but last 3)
        messages_to_summarize = conv['messages'][:-3]
        if not messages_to_summarize:
            return
        
        # Build text to summarize
        conversation_text = []
        for msg in messages_to_summarize:
            role_label = "User" if msg['role'] == 'user' else "Assistant"
            conversation_text.append(f"{role_label}: {msg['content']}")
        
        # Summarize using Claude
        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{
                    'role': 'user',
                    'content': f"""Summarize this conversation concisely, focusing on key topics discussed and important context:

{chr(10).join(conversation_text)}

Keep it brief and conversational. Focus on what the user was asking about and key points established."""
                }]
            )
            
            summary = response.content[0].text
            
            # Update conversation
            if conv['summary']:
                # Append to existing summary
                conv['summary'] = f"{conv['summary']} {summary}"
            else:
                conv['summary'] = summary
            
            # Keep only last 3 messages
            conv['messages'] = conv['messages'][-3:]
            
        except Exception as e:
            print(f"Summarization failed: {e}, truncating instead")
            # Fallback: just truncate
            conv['messages'] = conv['messages'][-5:]
    
    def clear_conversation(self, user_id: int, chat_id: int = None):
        """Manually clear a user's conversation"""
        conv_key = (user_id, chat_id) if chat_id else (user_id, user_id)
        if conv_key in self.conversations:
            del self.conversations[conv_key]
    
    def get_stats(self) -> Dict:
        """Get statistics about active conversations"""
        now = time.time()
        active = sum(
            1 for conv in self.conversations.values()
            if now - conv['last_activity'] < self.timeout_seconds
        )
        
        return {
            'total_users': len(self.conversations),
            'active_conversations': active,
            'timeout_minutes': self.timeout_seconds / 60
        }

