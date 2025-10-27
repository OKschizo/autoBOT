"""
Cloud Bot Manager
Manages Telegram and Discord bot instances running in the cloud
"""

import asyncio
import threading
import logging
from typing import Dict, Optional, List
from datetime import datetime
from collections import deque
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from telegram_bot import AutoFinanceBot as TelegramBot
from discord_bot import AutoFinanceDiscordBot as DiscordBot

# Import bot_config_storage
try:
    from bot_config import bot_config_storage
except ImportError:
    # Create a simple in-memory fallback if bot_config module not available
    bot_config_storage = None

logger = logging.getLogger(__name__)


class BotInstance:
    """Represents a single bot instance"""
    
    def __init__(self, bot_id: str, platform: str, token: str, name: str, 
                 model: str, system_prompt: str):
        self.bot_id = bot_id
        self.platform = platform  # 'telegram' or 'discord'
        self.token = token
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.status = "stopped"  # stopped, starting, running, error
        self.thread: Optional[threading.Thread] = None
        self.bot_instance: Optional[any] = None
        self.start_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.activity_log: deque = deque(maxlen=100)  # Keep last 100 log entries
        self.stop_event = threading.Event()
        
    def log(self, message: str, level: str = "INFO"):
        """Add a log entry"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self.activity_log.append(entry)
        logger.log(getattr(logging, level), f"[{self.bot_id}] {message}")
        
    def get_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent log entries"""
        return list(self.activity_log)[-limit:]
        
    def get_status(self) -> Dict:
        """Get bot status"""
        uptime = None
        if self.start_time and self.status == "running":
            uptime = (datetime.now() - self.start_time).total_seconds()
            
        return {
            "bot_id": self.bot_id,
            "platform": self.platform,
            "name": self.name,
            "status": self.status,
            "model": self.model,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": uptime,
            "error_message": self.error_message,
            "log_count": len(self.activity_log)
        }


class CloudBotManager:
    """Manages multiple bot instances in the cloud"""
    
    def __init__(self):
        self.bots: Dict[str, BotInstance] = {}
        self.lock = threading.Lock()
        logger.info("CloudBotManager initialized")
        
        # Restore bots from storage on startup
        self._restore_bots_from_storage()
        
    def register_bot(self, bot_id: str, platform: str, token: str, name: str,
                    model: str = "gpt-4o", system_prompt: str = "default", 
                    auto_start: bool = False) -> Dict:
        """Register a new bot"""
        with self.lock:
            if bot_id in self.bots:
                return {"success": False, "error": "Bot ID already exists"}
                
            bot = BotInstance(bot_id, platform, token, name, model, system_prompt)
            self.bots[bot_id] = bot
            bot.log(f"Bot registered: {name} ({platform})")
            
            # Save to persistent storage
            if bot_config_storage:
                bot_config_storage.save_bot({
                    'bot_id': bot_id,
                    'platform': platform,
                    'token': token,
                    'name': name,
                    'model': model,
                    'system_prompt': system_prompt,
                    'status': 'registered'
                })
            
            # Auto-start if requested
            if auto_start:
                self.start_bot(bot_id)
            
            return {"success": True, "bot": bot.get_status()}
            
    def unregister_bot(self, bot_id: str) -> Dict:
        """Unregister a bot"""
        with self.lock:
            if bot_id not in self.bots:
                return {"success": False, "error": "Bot not found"}
                
            bot = self.bots[bot_id]
            if bot.status == "running":
                self.stop_bot(bot_id)
                
            del self.bots[bot_id]
            logger.info(f"Bot unregistered: {bot_id}")
            
            return {"success": True}
            
    def start_bot(self, bot_id: str) -> Dict:
        """Start a bot"""
        with self.lock:
            if bot_id not in self.bots:
                return {"success": False, "error": "Bot not found"}
                
            bot = self.bots[bot_id]
            
            if bot.status == "running":
                return {"success": False, "error": "Bot is already running"}
                
            bot.status = "starting"
            bot.error_message = None
            bot.log(f"Starting {bot.platform} bot...")
            
        # Start bot in background thread
        def run_bot():
            try:
                if bot.platform == "telegram":
                    bot.log("Initializing Telegram bot...")
                    
                    # Set environment variables for the bot
                    os.environ['TELEGRAM_BOT_TOKEN'] = bot.token
                    os.environ['BOT_MODEL'] = bot.model
                    
                    # Create bot instance (reads from env vars)
                    bot.bot_instance = TelegramBot()
                    bot.status = "running"
                    bot.start_time = datetime.now()
                    bot.log(f"✅ Telegram bot '{bot.name}' started successfully")
                    
                    # Save status to storage
                    self._save_bot_status(bot_id)
                    
                    # Run the bot
                    bot.bot_instance.run()
                    
                elif bot.platform == "discord":
                    bot.log("Initializing Discord bot...")
                    
                    # Set environment variables for the bot
                    os.environ['DISCORD_BOT_TOKEN'] = bot.token
                    os.environ['BOT_MODEL'] = bot.model
                    
                    # Create bot instance (reads from env vars)
                    bot.bot_instance = DiscordBot()
                    bot.status = "running"
                    bot.start_time = datetime.now()
                    bot.log(f"✅ Discord bot '{bot.name}' started successfully")
                    
                    # Save status to storage
                    self._save_bot_status(bot_id)
                    
                    # Run the bot
                    asyncio.run(bot.bot_instance.start(bot.token))
                    
            except Exception as e:
                bot.status = "error"
                bot.error_message = str(e)
                bot.log(f"❌ Error starting bot: {e}", "ERROR")
                logger.error(f"Bot {bot_id} error: {e}", exc_info=True)
                
        bot.thread = threading.Thread(target=run_bot, daemon=True)
        bot.thread.start()
        
        return {"success": True, "bot": bot.get_status()}
        
    def stop_bot(self, bot_id: str) -> Dict:
        """Stop a bot"""
        with self.lock:
            if bot_id not in self.bots:
                return {"success": False, "error": "Bot not found"}
                
            bot = self.bots[bot_id]
            
            if bot.status != "running":
                return {"success": False, "error": "Bot is not running"}
                
            bot.log("Stopping bot...")
            
            try:
                if bot.bot_instance:
                    if bot.platform == "telegram":
                        # Stop Telegram bot
                        if hasattr(bot.bot_instance, 'application'):
                            asyncio.run(bot.bot_instance.application.stop())
                    elif bot.platform == "discord":
                        # Stop Discord bot
                        if hasattr(bot.bot_instance, 'close'):
                            asyncio.run(bot.bot_instance.close())
                            
                bot.status = "stopped"
                bot.start_time = None
                bot.log("✅ Bot stopped successfully")
                
                # Save status to storage
                self._save_bot_status(bot_id)
                
            except Exception as e:
                bot.log(f"Error stopping bot: {e}", "ERROR")
                logger.error(f"Error stopping bot {bot_id}: {e}", exc_info=True)
                
            return {"success": True, "bot": bot.get_status()}
            
    def restart_bot(self, bot_id: str) -> Dict:
        """Restart a bot"""
        stop_result = self.stop_bot(bot_id)
        if not stop_result["success"]:
            return stop_result
            
        # Wait a moment for clean shutdown
        import time
        time.sleep(2)
        
        return self.start_bot(bot_id)
        
    def get_bot_status(self, bot_id: str) -> Optional[Dict]:
        """Get status of a specific bot"""
        with self.lock:
            if bot_id not in self.bots:
                return None
            return self.bots[bot_id].get_status()
            
    def get_all_bots_status(self) -> List[Dict]:
        """Get status of all bots"""
        with self.lock:
            return [bot.get_status() for bot in self.bots.values()]
            
    def get_bot_logs(self, bot_id: str, limit: int = 50) -> Optional[List[Dict]]:
        """Get logs for a specific bot"""
        with self.lock:
            if bot_id not in self.bots:
                return None
            return self.bots[bot_id].get_logs(limit)
            
    def update_bot_config(self, bot_id: str, model: Optional[str] = None,
                         system_prompt: Optional[str] = None) -> Dict:
        """Update bot configuration"""
        with self.lock:
            if bot_id not in self.bots:
                return {"success": False, "error": "Bot not found"}
                
            bot = self.bots[bot_id]
            
            if bot.status == "running":
                return {
                    "success": False, 
                    "error": "Cannot update config while bot is running. Stop bot first."
                }
                
            if model:
                bot.model = model
                bot.log(f"Model updated to: {model}")
                
            if system_prompt:
                bot.system_prompt = system_prompt
                bot.log(f"System prompt updated")
            
            # Save updated config to storage
            if bot_config_storage:
                bot_config_storage.save_bot({
                    'bot_id': bot_id,
                    'platform': bot.platform,
                    'token': bot.token,
                    'name': bot.name,
                    'model': bot.model,
                    'system_prompt': bot.system_prompt,
                    'status': bot.status
                })
                
            return {"success": True, "bot": bot.get_status()}
    
    def _restore_bots_from_storage(self):
        """Restore bots from persistent storage on startup"""
        if not bot_config_storage:
            logger.info("No bot config storage available, skipping restore")
            return
            
        try:
            saved_bots = bot_config_storage.get_all_bots()
            logger.info(f"Found {len(saved_bots)} saved bot(s) in storage")
            
            for bot_config in saved_bots:
                bot_id = bot_config['bot_id']
                
                # Create bot instance
                bot = BotInstance(
                    bot_id=bot_id,
                    platform=bot_config['platform'],
                    token=bot_config['token'],
                    name=bot_config['name'],
                    model=bot_config['model'],
                    system_prompt=bot_config.get('system_prompt', 'default')
                )
                
                self.bots[bot_id] = bot
                bot.log(f"Restored from storage: {bot_config['name']}")
                
                # Auto-start if it was running before
                if bot_config.get('status') == 'running':
                    logger.info(f"Auto-starting bot {bot_id} (was running before shutdown)")
                    # Start in background thread to avoid blocking startup
                    threading.Thread(
                        target=lambda b=bot_id: self.start_bot(b),
                        daemon=True
                    ).start()
                    
            logger.info(f"✅ Restored {len(saved_bots)} bot(s) from storage")
            
        except Exception as e:
            logger.error(f"Error restoring bots from storage: {e}", exc_info=True)
    
    def _save_bot_status(self, bot_id: str):
        """Save bot status to persistent storage"""
        if not bot_config_storage:
            return
            
        try:
            bot = self.bots.get(bot_id)
            if bot:
                bot_config_storage.update_bot_status(bot_id, bot.status)
        except Exception as e:
            logger.error(f"Error saving bot status: {e}")
    
    def restart_all_running_bots(self):
        """Restart all currently running bots (for data updates)"""
        logger.info("Restarting all running bots after data update...")
        
        running_bots = [bot_id for bot_id, bot in self.bots.items() if bot.status == "running"]
        
        if not running_bots:
            logger.info("No running bots to restart")
            return
        
        logger.info(f"Restarting {len(running_bots)} bot(s)...")
        
        for bot_id in running_bots:
            try:
                logger.info(f"Restarting bot {bot_id}...")
                self.restart_bot(bot_id)
            except Exception as e:
                logger.error(f"Error restarting bot {bot_id}: {e}")


# Global bot manager instance
bot_manager = CloudBotManager()

