"""
Discord Bot for Auto Finance Documentation
Same features as Telegram bot: conversation memory, RAG answers, etc.
"""

import os
import logging
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from rag_agent_complete import CompleteRAGAgent
from conversation_manager import ConversationManager

# Load environment
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class AutoFinanceDiscordBot:
    """Discord bot for Auto Finance documentation"""
    
    def __init__(self):
        # Reload .env to get latest changes
        load_dotenv(override=True)
        
        # Load config
        self.bot_token = (
            os.getenv('DISCORD_BOT_TOKEN') or
            os.getenv('DISCORD_BOT_TOKEN_MAIN') or
            os.getenv('DISCORD_BOT_TOKEN_main')
        )
        self.model = os.getenv('BOT_MODEL', 'claude-sonnet-4-20250514')
        self.max_tokens = int(os.getenv('BOT_MAX_TOKENS', '2000'))
        
        if not self.bot_token:
            raise ValueError("DISCORD_BOT_TOKEN not found in .env file! Add DISCORD_BOT_TOKEN_MAIN=your-token")
        
        # Initialize RAG agent
        logger.info("Initializing RAG agent with complete dataset...")
        
        if self.model.startswith('gpt'):
            from rag_agent_openai import OpenAIRAGAgent
            self.agent = OpenAIRAGAgent()
            logger.info(f"Using OpenAI model: {self.model}")
        else:
            self.agent = CompleteRAGAgent()
            logger.info(f"Using Claude model: {self.model}")
        
        # Check index
        if self.agent.collection is None:
            logger.error("No data indexed! Run scrape_all_data.py first.")
            raise ValueError("No indexed data found")
        
        logger.info(f"Bot ready with {self.agent.collection.count()} chunks indexed")
        
        # Stats
        self.questions_answered = 0
        
        # Conversation tracking
        self.conversation_manager = ConversationManager(
            max_messages=10,
            timeout_minutes=30
        )
        
        # Setup Discord bot
        intents = discord.Intents.default()
        intents.message_content = True  # Required to read messages
        intents.members = True
        
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        # Use the bot's built-in tree, don't create a new one
        self.tree = self.bot.tree
        
        # Register events and commands
        self.register_events()
        self.register_commands()
    
    def register_events(self):
        """Register Discord events"""
        
        @self.bot.event
        async def on_ready():
            logger.info(f'Discord bot logged in as {self.bot.user}')
            logger.info(f'Bot is in {len(self.bot.guilds)} server(s)')
            
            # Sync slash commands
            try:
                synced = await self.tree.sync()
                logger.info(f'Synced {len(synced)} slash command(s)')
            except Exception as e:
                logger.error(f'Failed to sync commands: {e}')
        
        @self.bot.event
        async def on_message(message):
            # Ignore own messages
            if message.author == self.bot.user:
                return
            
            # Check if bot should respond
            should_respond = False
            question = message.content
            
            # DM - always respond
            if isinstance(message.channel, discord.DMChannel):
                should_respond = True
            
            # Mentioned
            elif self.bot.user in message.mentions:
                should_respond = True
                # Remove mention from question
                question = question.replace(f'<@{self.bot.user.id}>', '').strip()
            
            # Reply to bot's message
            elif message.reference and message.reference.resolved:
                if message.reference.resolved.author == self.bot.user:
                    should_respond = True
                    logger.info("User replying to bot message")
            
            if not should_respond:
                return
            
            logger.info(f'Question from {message.author.name}: {question}')
            
            # Typing indicator
            async with message.channel.typing():
                try:
                    # Get conversation context (per user, per channel)
                    conv_context = self.conversation_manager.get_context(
                        message.author.id,
                        message.channel.id
                    )
                    
                    # Build enhanced question
                    if conv_context:
                        enhanced_question = f"{conv_context}\n\nCurrent question: {question}"
                    else:
                        enhanced_question = question
                    
                    # Get answer
                    response = self.agent.ask(
                        enhanced_question,
                        model=self.model,
                        max_tokens=self.max_tokens,
                        n_results=10
                    )
                    
                    answer = response['answer']
                    
                    # Check if user wants sources
                    wants_sources = any(word in question.lower() for word in ['source', 'link', 'where', 'reference', 'doc'])
                    
                    # Build response
                    if wants_sources:
                        sources = response['sources'][:3]
                        answer += "\n\n**Sources:**\n"
                        for source in sources:
                            answer += f"• [{source['title']}]({source['url']})\n"
                    
                    # Send response (split if too long)
                    if len(answer) > 2000:
                        # Discord has 2000 char limit
                        chunks = [answer[i:i+1900] for i in range(0, len(answer), 1900)]
                        for chunk in chunks:
                            await message.reply(chunk)
                    else:
                        await message.reply(answer)
                    
                    # Save to conversation
                    self.conversation_manager.add_message(
                        message.author.id, 'user', question, message.channel.id
                    )
                    self.conversation_manager.add_message(
                        message.author.id, 'assistant', answer, message.channel.id
                    )
                    
                    self.questions_answered += 1
                    logger.info(f'Successfully answered question from {message.author.name}')
                    
                except Exception as e:
                    logger.error(f'Error answering question: {e}')
                    await message.reply(
                        "Sorry, I encountered an error processing your question. "
                        "Please try rephrasing or contact support."
                    )
    
    def register_commands(self):
        """Register slash commands"""
        
        @self.tree.command(name="ask", description="Ask a question about Auto Finance")
        @app_commands.describe(question="Your question about Auto Finance")
        async def ask_command(interaction: discord.Interaction, question: str):
            """Slash command to ask questions"""
            await interaction.response.defer(thinking=True)
            
            try:
                # Get conversation context
                conv_context = self.conversation_manager.get_context(
                    interaction.user.id,
                    interaction.channel_id
                )
                
                enhanced_question = f"{conv_context}\n\nCurrent question: {question}" if conv_context else question
                
                # Get answer
                response = self.agent.ask(
                    enhanced_question,
                    model=self.model,
                    max_tokens=self.max_tokens,
                    n_results=10
                )
                
                answer = response['answer']
                
                # Save conversation
                self.conversation_manager.add_message(
                    interaction.user.id, 'user', question, interaction.channel_id
                )
                self.conversation_manager.add_message(
                    interaction.user.id, 'assistant', answer, interaction.channel_id
                )
                
                self.questions_answered += 1
                
                # Send response
                if len(answer) > 2000:
                    await interaction.followup.send(answer[:1900] + "...")
                    if len(answer) > 2000:
                        await interaction.channel.send(answer[1900:3800])
                else:
                    await interaction.followup.send(answer)
                    
            except Exception as e:
                logger.error(f'Error in ask command: {e}')
                await interaction.followup.send("Error processing your question.")
        
        @self.tree.command(name="clear", description="Clear your conversation history")
        async def clear_command(interaction: discord.Interaction):
            """Clear conversation history"""
            self.conversation_manager.clear_conversation(
                interaction.user.id,
                interaction.channel_id
            )
            await interaction.response.send_message(
                "✅ Conversation cleared! Starting fresh.",
                ephemeral=True
            )
        
        @self.tree.command(name="stats", description="Show bot statistics")
        async def stats_command(interaction: discord.Interaction):
            """Show bot stats"""
            conv_stats = self.conversation_manager.get_stats()
            
            embed = discord.Embed(
                title="📊 Bot Statistics",
                color=discord.Color.blue()
            )
            embed.add_field(name="Questions Answered", value=str(self.questions_answered))
            embed.add_field(name="Documents Indexed", value=str(self.agent.collection.count()))
            embed.add_field(name="Active Conversations", value=str(conv_stats['active_conversations']))
            embed.add_field(name="Model", value=self.model)
            
            await interaction.response.send_message(embed=embed)
        
        @self.tree.command(name="help", description="Show help information")
        async def help_command(interaction: discord.Interaction):
            """Show help"""
            help_text = """
**Auto Finance Bot Help**

I can answer questions about Auto Finance, Autopools, TOKE staking, and DeFi in general!

**How to use:**
• Mention me: `@AutoFinanceBot your question`
• Reply to my messages (no mention needed!)
• Use `/ask` command
• DM me directly

**Commands:**
• `/ask <question>` - Ask a question
• `/clear` - Clear your conversation history
• `/stats` - Show bot statistics
• `/help` - Show this message

**Examples:**
• "What are Autopools?"
• "What's the current APY on plasmaUSD?"
• "How many autopools are there?"

Let me know if you have any questions!
            """
            await interaction.response.send_message(help_text, ephemeral=True)
    
    def run(self):
        """Start the Discord bot"""
        logger.info("Starting Auto Finance Discord Bot...")
        self.bot.run(self.bot_token)
    
    def stop(self):
        """Stop the bot gracefully"""
        if self.bot:
            logger.info("Stopping Discord bot...")
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.bot.close())
            loop.close()
            logger.info("Discord bot stopped")


def main():
    """Main entry point"""
    try:
        bot = AutoFinanceDiscordBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()

