"""
Conversation Storage & Analytics System
Stores, indexes, and analyzes all bot conversations
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import re


class ConversationStorage:
    """Persistent storage for all bot conversations"""
    
    def __init__(self, db_path="bot_conversations.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT,
                chat_id TEXT NOT NULL,
                chat_type TEXT,
                platform TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                model TEXT,
                tokens_used INTEGER,
                context_length INTEGER
            )
        ''')
        
        # User index
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                platform TEXT,
                first_seen DATETIME,
                last_seen DATETIME,
                total_questions INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0
            )
        ''')
        
        # Create indexes for faster searching
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON conversations(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_platform ON conversations(platform)')
        
        conn.commit()
        conn.close()
    
    def save_conversation(self, user_id: str, username: str, chat_id: str, 
                         question: str, answer: str, platform: str = 'telegram',
                         chat_type: str = 'private', model: str = None,
                         tokens_used: int = None):
        """Save a conversation exchange"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Save conversation
        cursor.execute('''
            INSERT INTO conversations 
            (user_id, username, chat_id, chat_type, platform, question, answer, model, tokens_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, chat_id, chat_type, platform, question, answer, model, tokens_used))
        
        # Update user index
        cursor.execute('''
            INSERT INTO users (user_id, username, platform, first_seen, last_seen, total_questions, total_tokens)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                last_seen = CURRENT_TIMESTAMP,
                total_questions = total_questions + 1,
                total_tokens = total_tokens + COALESCE(excluded.total_tokens, 0)
        ''', (user_id, username, platform, tokens_used or 0))
        
        conn.commit()
        conn.close()
    
    def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get all conversations for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, chat_type, question, answer, model, tokens_used
            FROM conversations
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'timestamp': row[0],
                'chat_type': row[1],
                'question': row[2],
                'answer': row[3],
                'model': row[4],
                'tokens_used': row[5]
            })
        
        conn.close()
        return results
    
    def get_all_users(self) -> List[Dict]:
        """Get all users with stats"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, platform, first_seen, last_seen, total_questions, total_tokens
            FROM users
            ORDER BY total_questions DESC
        ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'user_id': row[0],
                'username': row[1] or 'Unknown',
                'platform': row[2],
                'first_seen': row[3],
                'last_seen': row[4],
                'total_questions': row[5],
                'total_tokens': row[6]
            })
        
        conn.close()
        return results
    
    def search_conversations(self, keyword: str, limit: int = 100) -> List[Dict]:
        """Search conversations by keyword"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, timestamp, question, answer, platform
            FROM conversations
            WHERE question LIKE ? OR answer LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'user_id': row[0],
                'username': row[1] or 'Unknown',
                'timestamp': row[2],
                'question': row[3],
                'answer': row[4],
                'platform': row[5]
            })
        
        conn.close()
        return results
    
    def get_top_questions(self, limit: int = 20) -> List[Dict]:
        """Get most common questions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT question, COUNT(*) as count, platform
            FROM conversations
            GROUP BY LOWER(question)
            ORDER BY count DESC
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'question': row[0],
                'count': row[1],
                'platform': row[2]
            })
        
        conn.close()
        return results
    
    def get_analytics(self) -> Dict:
        """Get overall analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total conversations
        cursor.execute('SELECT COUNT(*) FROM conversations')
        total_convos = cursor.fetchone()[0]
        
        # Unique users
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM users')
        unique_users = cursor.fetchone()[0]
        
        # By platform
        cursor.execute('''
            SELECT platform, COUNT(*) 
            FROM conversations 
            GROUP BY platform
        ''')
        by_platform = dict(cursor.fetchall())
        
        # Most active user
        cursor.execute('''
            SELECT username, total_questions 
            FROM users 
            ORDER BY total_questions DESC 
            LIMIT 1
        ''')
        most_active = cursor.fetchone()
        
        # Total tokens used
        cursor.execute('SELECT SUM(total_tokens) FROM users')
        total_tokens = cursor.fetchone()[0] or 0
        
        # Recent activity (last 24h)
        cursor.execute('''
            SELECT COUNT(*) 
            FROM conversations 
            WHERE datetime(timestamp) > datetime('now', '-1 day')
        ''')
        recent_24h = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_conversations': total_convos,
            'unique_users': unique_users,
            'by_platform': by_platform,
            'most_active_user': most_active[0] if most_active else None,
            'most_active_count': most_active[1] if most_active else 0,
            'total_tokens_used': total_tokens,
            'conversations_24h': recent_24h
        }
    
    def export_to_json(self, output_file: str = "conversations_export.json"):
        """Export all conversations to JSON"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, chat_id, chat_type, platform, 
                   timestamp, question, answer, model, tokens_used
            FROM conversations
            ORDER BY timestamp
        ''')
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'user_id': row[0],
                'username': row[1],
                'chat_id': row[2],
                'chat_type': row[3],
                'platform': row[4],
                'timestamp': row[5],
                'question': row[6],
                'answer': row[7],
                'model': row[8],
                'tokens_used': row[9]
            })
        
        conn.close()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(conversations, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def export_for_finetuning(self, output_file: str = "finetuning_data.jsonl"):
        """Export in OpenAI fine-tuning format"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT question, answer
            FROM conversations
            ORDER BY timestamp
        ''')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for row in cursor.fetchall():
                entry = {
                    "messages": [
                        {"role": "user", "content": row[0]},
                        {"role": "assistant", "content": row[1]}
                    ]
                }
                f.write(json.dumps(entry) + '\n')
        
        conn.close()
        return output_file
    
    def clear_user_data(self, user_id: str):
        """Delete all data for a user (GDPR compliance)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM conversations WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()


if __name__ == "__main__":
    # Test/demo
    storage = ConversationStorage()
    
    # Get analytics
    analytics = storage.get_analytics()
    print("Analytics:")
    print(json.dumps(analytics, indent=2))
    
    # Get users
    users = storage.get_all_users()
    print(f"\nTotal users: {len(users)}")
    for user in users[:5]:
        print(f"  - {user['username']}: {user['total_questions']} questions")

