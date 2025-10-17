"""
Slack Bot for Auto Finance Documentation
Same features as Telegram and Discord bots
"""

import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
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


class AutoFinanceSlackBot:
    """Slack bot for Auto Finance documentation"""
    
    def __init__(self):
        # Reload .env
        load_dotenv(override=True)
        
        # Load config
        self.bot_token = (
            os.getenv('SLACK_BOT_TOKEN') or
            os.getenv('SLACK_BOT_TOKEN_MAIN') or
            os.getenv('SLACK_BOT_TOKEN_main')
        )
        self.app_token = os.getenv('SLACK_APP_TOKEN')  # For Socket Mode
        
        self.model = os.getenv('BOT_MODEL', 'claude-sonnet-4-20250514')
        self.max_tokens = int(os.getenv('BOT_MAX_TOKENS', '2000'))
        
        if not self.bot_token:
            raise ValueError("SLACK_BOT_TOKEN not found in .env file! Add SLACK_BOT_TOKEN_MAIN=your-token")
        
        # Initialize RAG agent
        logger.info("Initializing RAG agent with complete dataset...")
        
        if self.model.startswith('gpt'):
            from rag_agent_openai import OpenAIRAGAgent
            self.agent = OpenAIRAGAgent()
            logger.info(f"Using OpenAI model: {self.model}")
        else:
            self.agent = CompleteRAGAgent()
            logger.info(f"Using Claude model: {self.model}")
        
        if self.agent.collection is None or self.agent.collection.count() == 0:
            logger.error("No data indexed!")
            raise ValueError("No indexed data found")
        
        logger.info(f"Bot ready with {self.agent.collection.count()} chunks indexed")
        
        # Stats
        self.questions_answered = 0
        
        # Conversation tracking
        self.conversation_manager = ConversationManager(
            max_messages=10,
            timeout_minutes=30
        )
        
        # Setup Slack app
        self.app = App(token=self.bot_token)
        self.bot_user_id = None
        
        # Register handlers
        self.register_handlers()
    
    def register_handlers(self):
        """Register Slack event handlers"""
        
        @self.app.event("app_mention")
        def handle_mention(event, say, client):
            """Handle @mentions"""
            self.handle_message(event, say, client)
        
        @self.app.event("message")
        def handle_message_event(event, say, client):
            """Handle messages"""
            # Ignore bot's own messages
            if event.get('bot_id'):
                return
            
            # Get bot user ID if we don't have it
            if not self.bot_user_id:
                auth_response = client.auth_test()
                self.bot_user_id = auth_response['user_id']
            
            # Check if bot should respond
            should_respond = False
            
            # DM - always respond
            if event.get('channel_type') == 'im':
                should_respond = True
            
            # Mentioned
            elif f'<@{self.bot_user_id}>' in event.get('text', ''):
                should_respond = True
            
            # Thread reply to bot
            elif event.get('thread_ts'):
                # Check if replying in a thread where bot participated
                try:
                    thread_messages = client.conversations_replies(
                        channel=event['channel'],
                        ts=event['thread_ts'],
                        limit=1
                    )
                    if thread_messages['messages'] and thread_messages['messages'][0].get('user') == self.bot_user_id:
                        should_respond = True
                except:
                    pass
            
            if should_respond:
                self.handle_message(event, say, client)
        
        @self.app.command("/ask")
        def handle_ask_command(ack, command, say, client):
            """Handle /ask slash command"""
            ack()  # Acknowledge command
            
            question = command['text']
            user_id = command['user_id']
            channel_id = command['channel_id']
            
            logger.info(f"Slash command from {user_id}: {question}")
            
            try:
                answer = self.get_answer(question, user_id, channel_id)
                say(answer)
                self.questions_answered += 1
            except Exception as e:
                logger.error(f"Error in /ask command: {e}")
                say("Sorry, I encountered an error processing your question.")
        
        @self.app.command("/clear")
        def handle_clear_command(ack, command, say):
            """Handle /clear command"""
            ack()
            
            user_id = command['user_id']
            channel_id = command['channel_id']
            
            self.conversation_manager.clear_conversation(int(user_id), int(channel_id, 36))
            say("✅ Conversation cleared! Starting fresh.")
        
        @self.app.command("/stats")
        def handle_stats_command(ack, command, say):
            """Handle /stats command"""
            ack()
            
            conv_stats = self.conversation_manager.get_stats()
            
            stats_text = f"""
📊 *Bot Statistics*

• Questions Answered: {self.questions_answered}
• Documents Indexed: {self.agent.collection.count()}
• Active Conversations: {conv_stats['active_conversations']}
• Model: {self.model}

Bot is running smoothly! 🎯
            """
            say(stats_text)
    
    def handle_message(self, event, say, client):
        """Handle incoming message"""
        text = event.get('text', '')
        user_id = event.get('user')
        channel_id = event.get('channel')
        
        # Remove bot mention from text
        if self.bot_user_id:
            text = text.replace(f'<@{self.bot_user_id}>', '').strip()
        
        logger.info(f"Question from {user_id}: {text}")
        
        try:
            answer = self.get_answer(text, user_id, channel_id, thread_ts=event.get('ts'))
            
            # Send in thread if original message was in thread
            if event.get('thread_ts'):
                say(text=answer, thread_ts=event['thread_ts'])
            else:
                say(text=answer, thread_ts=event['ts'])  # Create thread
            
            self.questions_answered += 1
            logger.info(f"Successfully answered question from {user_id}")
            
        except Exception as e:
            logger.error(f"Error answering: {e}")
            say("Sorry, I encountered an error processing your question.")
    
    def get_answer(self, question: str, user_id: str, channel_id: str, thread_ts=None):
        """Get answer from RAG system"""
        # Convert IDs to integers for conversation manager
        user_id_int = int(user_id.lstrip('U'), 36) if user_id.startswith('U') else hash(user_id)
        channel_id_int = int(channel_id.lstrip('C'), 36) if channel_id.startswith('C') else hash(channel_id)
        
        # Get conversation context
        conv_context = self.conversation_manager.get_context(user_id_int, channel_id_int)
        
        # Build enhanced question
        if conv_context:
            enhanced_question = f"{conv_context}\n\nCurrent question: {question}"
        else:
            enhanced_question = question
        
        # Get answer from RAG
        response = self.agent.ask(
            enhanced_question,
            model=self.model,
            max_tokens=self.max_tokens,
            n_results=10
        )
        
        answer = response['answer']
        
        # Check if user wants sources
        wants_sources = any(word in question.lower() for word in ['source', 'link', 'where', 'reference', 'doc'])
        
        if wants_sources:
            sources = response['sources'][:3]
            answer += "\n\n*Sources:*\n"
            for source in sources:
                answer += f"• <{source['url']}|{source['title']}>\n"
        
        # Save to conversation
        self.conversation_manager.add_message(user_id_int, 'user', question, channel_id_int)
        self.conversation_manager.add_message(user_id_int, 'assistant', answer, channel_id_int)
        
        return answer
    
    def run(self):
        """Start the Slack bot"""
        logger.info("Starting Auto Finance Slack Bot...")
        
        if self.app_token:
            # Socket Mode (recommended for development)
            handler = SocketModeHandler(self.app, self.app_token)
            handler.start()
        else:
            # HTTP Mode (requires public URL)
            logger.warning("No SLACK_APP_TOKEN found. Starting in HTTP mode...")
            logger.warning("You'll need to configure a public URL for webhooks.")
            from slack_bolt.adapter.flask import SlackRequestHandler
            from flask import Flask, request
            
            flask_app = Flask(__name__)
            handler = SlackRequestHandler(self.app)
            
            @flask_app.route("/slack/events", methods=["POST"])
            def slack_events():
                return handler.handle(request)
            
            flask_app.run(port=3000)
    
    def stop(self):
        """Stop the bot"""
        logger.info("Stopping Slack bot...")
        # Slack Bolt doesn't have a clean stop method for Socket Mode
        # Just exit gracefully
        logger.info("Slack bot stopped")


def main():
    """Main entry point"""
    try:
        bot = AutoFinanceSlackBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()


