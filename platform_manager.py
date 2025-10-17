"""
Multi-Platform Bot Manager
Supports Telegram, Discord, and other platforms
"""

import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class PlatformConfig:
    """Configuration for different bot platforms"""
    
    PLATFORMS = {
        'telegram': {
            'name': 'Telegram',
            'token_prefix': 'TELEGRAM_BOT_TOKEN_',
            'module': 'telegram_bot',
            'class': 'AutoFinanceBot',
            'color': '#0088cc'
        },
        'discord': {
            'name': 'Discord',
            'token_prefix': 'DISCORD_BOT_TOKEN_',
            'module': 'discord_bot',
            'class': 'AutoFinanceDiscordBot',
            'color': '#5865F2',
            'status': 'active'
        },
        'slack': {
            'name': 'Slack',
            'token_prefix': 'SLACK_BOT_TOKEN_',
            'module': 'slack_bot',
            'class': 'AutoFinanceSlackBot',
            'color': '#4A154B',
            'status': 'active'
        }
    }
    
    @classmethod
    def get_available_bots(cls) -> List[Dict]:
        """Get all configured bots from environment"""
        bots = []
        
        for platform_key, platform_info in cls.PLATFORMS.items():
            # Find all tokens for this platform
            prefix = platform_info['token_prefix']
            
            for env_key, env_value in os.environ.items():
                if env_key.startswith(prefix) and env_value and env_value != f'your-{platform_key}-bot-token':
                    # Extract bot name (everything after prefix)
                    bot_name = env_key.replace(prefix, '').lower()
                    
                    bots.append({
                        'id': f"{platform_key}:{bot_name}",
                        'platform': platform_key,
                        'platform_name': platform_info['name'],
                        'bot_name': bot_name,
                        'display_name': f"{platform_info['name']} - {bot_name.capitalize()}",
                        'token_env_key': env_key,
                        'token': env_value,
                        'module': platform_info.get('module'),
                        'class_name': platform_info.get('class'),
                        'color': platform_info.get('color'),
                        'status': platform_info.get('status', 'active')
                    })
        
        return bots
    
    @classmethod
    def get_bot_by_id(cls, bot_id: str) -> Optional[Dict]:
        """Get specific bot configuration by ID"""
        bots = cls.get_available_bots()
        for bot in bots:
            if bot['id'] == bot_id:
                return bot
        return None
    
    @classmethod
    def get_platform_info(cls, platform: str) -> Optional[Dict]:
        """Get platform information"""
        return cls.PLATFORMS.get(platform)


class BotLauncher:
    """Launches bots for different platforms"""
    
    @staticmethod
    def launch_telegram_bot(config: Dict):
        """Launch Telegram bot"""
        # Set the token for this specific bot
        os.environ['TELEGRAM_BOT_TOKEN'] = config['token']
        
        from telegram_bot import AutoFinanceBot
        bot = AutoFinanceBot()
        return bot
    
    @staticmethod
    def launch_discord_bot(config: Dict):
        """Launch Discord bot"""
        # Set the token for this specific bot
        os.environ['DISCORD_BOT_TOKEN'] = config['token']
        
        from discord_bot import AutoFinanceDiscordBot
        bot = AutoFinanceDiscordBot()
        return bot
    
    @staticmethod
    def launch_slack_bot(config: Dict):
        """Launch Slack bot"""
        os.environ['SLACK_BOT_TOKEN'] = config['token']
        
        from slack_bot import AutoFinanceSlackBot
        bot = AutoFinanceSlackBot()
        return bot
    
    @staticmethod
    def launch_bot(bot_config: Dict):
        """Launch bot based on platform"""
        platform = bot_config['platform']
        
        if platform == 'telegram':
            return BotLauncher.launch_telegram_bot(bot_config)
        elif platform == 'discord':
            return BotLauncher.launch_discord_bot(bot_config)
        elif platform == 'slack':
            return BotLauncher.launch_slack_bot(bot_config)
        else:
            raise ValueError(f"Unsupported platform: {platform}")


def main():
    """Demo - list available bots"""
    print("Available Bots:")
    print("="*50)
    
    bots = PlatformConfig.get_available_bots()
    
    if not bots:
        print("No bots configured in .env file")
        print("\nAdd bot tokens like:")
        print("  TELEGRAM_BOT_TOKEN_MAIN=your-token")
        print("  DISCORD_BOT_TOKEN_MAIN=your-token")
        return
    
    for bot in bots:
        status = bot.get('status', 'active')
        status_icon = '[OK]' if status == 'active' else '[ ]'
        print(f"{status_icon} {bot['display_name']}")
        print(f"   ID: {bot['id']}")
        print(f"   Status: {status}")
        print()
    
    print(f"Total: {len(bots)} bot(s) configured")


if __name__ == "__main__":
    main()

