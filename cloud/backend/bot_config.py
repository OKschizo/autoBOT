"""
Bot Configuration Storage
Manages persistent storage of bot configurations using SQLite
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class BotConfigStorage:
    def __init__(self, db_path: str = "bot_configs.db"):
        """Initialize bot configuration storage"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_configs (
                bot_id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                name TEXT NOT NULL,
                token TEXT NOT NULL,
                model TEXT NOT NULL,
                system_prompt TEXT DEFAULT 'default',
                status TEXT DEFAULT 'registered',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                messages_processed INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                uptime_seconds INTEGER DEFAULT 0,
                FOREIGN KEY (bot_id) REFERENCES bot_configs(bot_id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_bot(self, bot_config: Dict[str, Any]) -> bool:
        """Save or update a bot configuration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            # Check if bot exists
            cursor.execute("SELECT bot_id FROM bot_configs WHERE bot_id = ?", (bot_config['bot_id'],))
            exists = cursor.fetchone() is not None
            
            if exists:
                # Update existing bot
                cursor.execute("""
                    UPDATE bot_configs
                    SET platform = ?, name = ?, token = ?, model = ?, 
                        system_prompt = ?, status = ?, updated_at = ?, metadata = ?
                    WHERE bot_id = ?
                """, (
                    bot_config['platform'],
                    bot_config['name'],
                    bot_config['token'],
                    bot_config['model'],
                    bot_config.get('system_prompt', 'default'),
                    bot_config.get('status', 'registered'),
                    now,
                    json.dumps(bot_config.get('metadata', {})),
                    bot_config['bot_id']
                ))
            else:
                # Insert new bot
                cursor.execute("""
                    INSERT INTO bot_configs 
                    (bot_id, platform, name, token, model, system_prompt, status, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bot_config['bot_id'],
                    bot_config['platform'],
                    bot_config['name'],
                    bot_config['token'],
                    bot_config['model'],
                    bot_config.get('system_prompt', 'default'),
                    bot_config.get('status', 'registered'),
                    now,
                    now,
                    json.dumps(bot_config.get('metadata', {}))
                ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error saving bot config: {e}")
            return False
    
    def get_bot(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """Get a bot configuration by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM bot_configs WHERE bot_id = ?", (bot_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                bot = dict(row)
                bot['metadata'] = json.loads(bot['metadata']) if bot['metadata'] else {}
                return bot
            return None
            
        except Exception as e:
            print(f"Error getting bot config: {e}")
            return None
    
    def get_all_bots(self) -> List[Dict[str, Any]]:
        """Get all bot configurations"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM bot_configs ORDER BY created_at DESC")
            rows = cursor.fetchall()
            conn.close()
            
            bots = []
            for row in rows:
                bot = dict(row)
                bot['metadata'] = json.loads(bot['metadata']) if bot['metadata'] else {}
                bots.append(bot)
            
            return bots
            
        except Exception as e:
            print(f"Error getting all bots: {e}")
            return []
    
    def delete_bot(self, bot_id: str) -> bool:
        """Delete a bot configuration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM bot_configs WHERE bot_id = ?", (bot_id,))
            deleted = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            return deleted
            
        except Exception as e:
            print(f"Error deleting bot config: {e}")
            return False
    
    def update_bot_status(self, bot_id: str, status: str) -> bool:
        """Update a bot's status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE bot_configs
                SET status = ?, updated_at = ?
                WHERE bot_id = ?
            """, (status, datetime.now().isoformat(), bot_id))
            
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return updated
            
        except Exception as e:
            print(f"Error updating bot status: {e}")
            return False
    
    def record_bot_stats(self, bot_id: str, messages_processed: int = 0, 
                         errors: int = 0, uptime_seconds: int = 0) -> bool:
        """Record bot statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO bot_stats (bot_id, timestamp, messages_processed, errors, uptime_seconds)
                VALUES (?, ?, ?, ?, ?)
            """, (bot_id, datetime.now().isoformat(), messages_processed, errors, uptime_seconds))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error recording bot stats: {e}")
            return False
    
    def get_bot_stats(self, bot_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get bot statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM bot_stats
                WHERE bot_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (bot_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            print(f"Error getting bot stats: {e}")
            return []
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics for all bots"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total bots
            cursor.execute("SELECT COUNT(*) FROM bot_configs")
            total_bots = cursor.fetchone()[0]
            
            # Running bots
            cursor.execute("SELECT COUNT(*) FROM bot_configs WHERE status = 'running'")
            running_bots = cursor.fetchone()[0]
            
            # Total messages processed (last 24 hours)
            cursor.execute("""
                SELECT SUM(messages_processed) FROM bot_stats
                WHERE timestamp > datetime('now', '-1 day')
            """)
            messages_24h = cursor.fetchone()[0] or 0
            
            # Total errors (last 24 hours)
            cursor.execute("""
                SELECT SUM(errors) FROM bot_stats
                WHERE timestamp > datetime('now', '-1 day')
            """)
            errors_24h = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_bots': total_bots,
                'running_bots': running_bots,
                'messages_24h': messages_24h,
                'errors_24h': errors_24h
            }
            
        except Exception as e:
            print(f"Error getting aggregate stats: {e}")
            return {
                'total_bots': 0,
                'running_bots': 0,
                'messages_24h': 0,
                'errors_24h': 0
            }

# Global instance
bot_config_storage = BotConfigStorage()


