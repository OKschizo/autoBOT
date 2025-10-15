"""
Telegram Bot for Auto Finance Documentation
Answers questions using Claude RAG agent
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from rag_agent_complete import CompleteRAGAgent
from conversation_manager import ConversationManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class AutoFinanceBot:
    """Telegram bot for Auto Finance documentation"""
    
    def __init__(self):
        # Load config from .env (support both old and new format)
        self.bot_token = (
            os.getenv('TELEGRAM_BOT_TOKEN') or 
            os.getenv('TELEGRAM_BOT_TOKEN_MAIN') or
            os.getenv('TELEGRAM_BOT_TOKEN_main')
        )
        self.model = os.getenv('BOT_MODEL', 'claude-sonnet-4-20250514')
        self.max_tokens = int(os.getenv('BOT_MAX_TOKENS', '2000'))
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file! Add TELEGRAM_BOT_TOKEN_MAIN=your-token")
        
        # Initialize RAG agent (uses complete dataset)
        logger.info("Initializing RAG agent with complete dataset...")
        self.agent = CompleteRAGAgent()
        
        # Check if index is built
        if self.agent.collection is None or self.agent.collection.count() == 0:
            logger.info("Building vector index...")
            self.agent.build_index()
            logger.info("Index built successfully!")
        
        logger.info(f"Bot ready with {self.agent.collection.count()} chunks indexed")
        
        # Stats
        self.questions_answered = 0
        
        # Conversation tracking
        self.conversation_manager = ConversationManager(
            max_messages=10,  # Summarize after 10 messages
            timeout_minutes=30  # Clear after 30 mins inactivity
        )
        
        # Get bot username for mention detection
        self.bot_username = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 *Auto Finance Documentation Bot*

I can answer questions about Auto Finance using the official documentation!

*How to use:*
• Just send me a question about Autopools, TOKE staking, or anything Auto Finance related
• I'll search the documentation and provide an accurate answer with sources

*Examples:*
• "What are Autopools?"
• "How does TOKE staking work?"
• "What are the security audits?"

*Commands:*
/help - Show this message
/stats - Show bot statistics
/clear - Clear conversation history

*In group chats:*
Mention me with @YourBotName to get my attention!

Let's get started! Ask me anything about Auto Finance! 🚀
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        conv_stats = self.conversation_manager.get_stats()
        
        stats_message = f"""
📊 *Bot Statistics*

Questions answered: {self.questions_answered}
Documents indexed: {self.agent.collection.count()}
Active conversations: {conv_stats['active_conversations']}
Model: {self.model}

Bot is running smoothly! 🎯
        """
        await update.message.reply_text(stats_message, parse_mode='Markdown')
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command - clears conversation history"""
        user = update.effective_user
        self.conversation_manager.clear_conversation(user.id)
        
        await update.message.reply_text(
            "✅ Conversation cleared! Starting fresh.",
            parse_mode='Markdown'
        )
    
    async def handle_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user questions - only when mentioned"""
        message_text = update.message.text
        user = update.effective_user
        chat = update.message.chat
        
        # Get bot username if we don't have it
        if not self.bot_username:
            bot_info = await context.bot.get_me()
            self.bot_username = bot_info.username
        
        # Check if bot is mentioned
        bot_mentioned = False
        
        # Check for @username mention
        if f"@{self.bot_username}" in message_text:
            bot_mentioned = True
            # Remove the mention from the question
            question = message_text.replace(f"@{self.bot_username}", "").strip()
        
        # Also check for direct messages (private chat)
        elif chat.type == "private":
            bot_mentioned = True
            question = message_text
        
        # Ignore if not mentioned (in group chats)
        if not bot_mentioned:
            return
        
        logger.info(f"Question from {user.username or user.id}: {question}")
        
        # Send "typing" indicator
        await update.message.chat.send_action("typing")
        
        try:
            # Get conversation context
            conv_context = self.conversation_manager.get_context(user.id)
            
            # Build enhanced question with context
            if conv_context:
                enhanced_question = f"{conv_context}\n\nCurrent question: {question}"
            else:
                enhanced_question = question
            
            # Get answer from RAG agent (use more chunks for better context)
            response = self.agent.ask(
                enhanced_question,
                model=self.model,
                max_tokens=self.max_tokens,
                n_results=10  # Retrieve 10 chunks instead of default 8
            )
            
            # Format answer - just the answer, casual
            answer = response['answer']
            
            # Check if user explicitly asked for sources
            wants_sources = any(word in question.lower() for word in ['source', 'link', 'where', 'reference', 'doc'])
            
            if wants_sources:
                sources = response['sources'][:3]
                answer += "\n\n📚 *Sources:*\n"
                for source in sources:
                    answer += f"• [{source['title']}]({source['url']})\n"
            
            # Try to send, fallback to plain text if Markdown fails
            try:
                await update.message.reply_text(answer, parse_mode='Markdown')
            except:
                # Markdown formatting failed, send as plain text
                await update.message.reply_text(answer)
            
            # Save to conversation history
            self.conversation_manager.add_message(user.id, 'user', question)
            self.conversation_manager.add_message(user.id, 'assistant', answer)
            
            self.questions_answered += 1
            logger.info(f"Successfully answered question from {user.username or user.id}")
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            error_message = (
                "Sorry, I encountered an error processing your question. "
                "Please try rephrasing it or contact support if the issue persists."
            )
            await update.message.reply_text(error_message)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Auto Finance Telegram Bot...")
        
        # Create application
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("clear", self.clear_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_question))
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        # Start bot
        logger.info("Bot is running! Press Ctrl+C to stop.")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def stop(self):
        """Stop the bot gracefully"""
        if hasattr(self, 'application') and self.application:
            logger.info("Stopping bot...")
            self.application.stop_running()
            logger.info("Bot stopped")


def main():
    """Main entry point with scrape option"""
    import sys
    
    # Check if we should scrape first
    if '--no-scrape' not in sys.argv:
        print("\n" + "="*70)
        print(" AUTO FINANCE TELEGRAM BOT")
        print("="*70)
        print("\nDo you want to scrape fresh data before starting the bot?")
        print("  (Recommended for daily use to get latest APYs, blog posts, etc.)")
        print("\nThis will:")
        print("  • Scrape docs.auto.finance (documentation)")
        print("  • Scrape app.auto.finance (live data, pool info)")
        print("  • Scrape blog.tokemak.xyz (blog posts)")
        print("  • Rebuild complete index")
        print("\nTime: ~10-20 minutes")
        
        choice = input("\nScrape fresh data? (y/n): ").strip().lower()
        
        if choice == 'y':
            print("\nStarting scraper...")
            try:
                from scrape_all_data import run_all_scrapers
                success = run_all_scrapers()
                
                if not success:
                    print("\n! Scraping failed. Bot will use existing data.")
                    response = input("Continue with bot startup? (y/n): ").strip().lower()
                    if response != 'y':
                        print("Cancelled.")
                        return
            except Exception as e:
                print(f"\n! Scraping error: {e}")
                print("Bot will use existing data.")
        else:
            print("\nSkipping scrape, using existing data...")
    
    # Start bot
    try:
        print("\n" + "="*70)
        print(" STARTING BOT")
        print("="*70 + "\n")
        
        bot = AutoFinanceBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()

