"""
Open Claw Headless Daemon - Main Entry Point

This is the main entry point for the Open Claw headless engine.
It integrates with Telegram and Hugging Face APIs.
Groq and OpenRouter integrations are optional and can be added later.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from huggingface_hub import InferenceClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate required environment variables (only Telegram is mandatory for now)
REQUIRED_ENV_VARS = [
    'OPENCLAW_TELEGRAM_BOT_TOKEN'
]

OPTIONAL_ENV_VARS = [
    'OPENCLAW_HUGGINGFACE_API_KEY',
    'OPENCLAW_GROQ_API_KEY',
    'OPENCLAW_OPENROUTER_API_KEY',
    'OPENCLAW_HF_TOKEN'
]

# Hugging Face chat-completion model served through the Inference Providers
# router (https://router.huggingface.co). Override with OPENCLAW_HF_MODEL.
DEFAULT_HF_MODEL = 'Qwen/Qwen2.5-7B-Instruct'

def validate_environment():
    """Validate that all required environment variables are set."""
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    
    # Log which optional variables are set
    for var in OPTIONAL_ENV_VARS:
        if os.environ.get(var):
            logger.info(f"Optional environment variable {var} is set")
        else:
            logger.info(f"Optional environment variable {var} is not set (will not be available)")
    
    logger.info("All required environment variables are set")
    return True

def initialize_storage():
    """Initialize persistent storage at /data."""
    data_path = Path('/data')
    try:
        data_path.mkdir(parents=True, exist_ok=True)
        # Test write access
        test_file = data_path / '.write_test'
        test_file.write_text('test')
        test_file.unlink()
        logger.info(f"Persistent storage initialized at {data_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize storage at {data_path}: {e}")
        return False

async def start_command(update, context):
    """Handle the /start command."""
    await update.message.reply_text(
        "👋 Welcome to Open Claw!\n\n"
        "I'm your AI assistant powered by Hugging Face models.\n"
        "Send me a message and I'll process it for you.\n\n"
        "Available commands:\n"
        "/start - Show this welcome message\n"
        "/help - Show help information\n"
        "/status - Show system status"
    )

async def help_command(update, context):
    """Handle the /help command."""
    await update.message.reply_text(
        "📖 Open Claw Help\n\n"
        "Just send me any text message and I'll process it using AI.\n"
        "You can also use the following commands:\n\n"
        "/start - Welcome message\n"
        "/help - This help message\n"
        "/status - Check system status"
    )

async def status_command(update, context):
    """Handle the /status command."""
    hf_key = os.environ.get('OPENCLAW_HUGGINGFACE_API_KEY')
    telegram_token = os.environ.get('OPENCLAW_TELEGRAM_BOT_TOKEN', 'Not set')
    
    status_msg = (
        "🔧 Open Claw Status\n\n"
        f"✅ Telegram Bot: {'Connected' if telegram_token else 'Disconnected'}\n"
        f"{'✅' if hf_key else '❌'} Hugging Face: {'Connected' if hf_key else 'Not configured (optional)'}\n"
        f"⚙️ Groq: {'Connected' if os.environ.get('OPENCLAW_GROQ_API_KEY') else 'Not configured'}\n"
        f"⚙️ OpenRouter: {'Connected' if os.environ.get('OPENCLAW_OPENROUTER_API_KEY') else 'Not configured'}\n\n"
        "Storage: /data (persistent)"
    )
    await update.message.reply_text(status_msg)

async def handle_message(update, context):
    """Handle incoming text messages."""
    user_message = update.message.text
    logger.info(f"Received message from user {update.message.chat.id}: {user_message}")
    
    # Check if Hugging Face is configured
    hf_key_1 = os.environ.get('OPENCLAW_HUGGINGFACE_API_KEY')
    hf_key_2 = os.environ.get('OPENCLAW_HF_TOKEN')
    hf_token = hf_key_1 or hf_key_2
    
    logger.info(f"Hugging Face key check - OPENCLAW_HUGGINGFACE_API_KEY: {'SET' if hf_key_1 else 'NOT SET'}")
    logger.info(f"Hugging Face key check - OPENCLAW_HF_TOKEN: {'SET' if hf_key_2 else 'NOT SET'}")
    logger.info(f"Hugging Face token available: {'YES' if hf_token else 'NO'}")
    
    if hf_token:
        model = os.environ.get('OPENCLAW_HF_MODEL') or DEFAULT_HF_MODEL
        try:
            # Call the Hugging Face Inference Providers router via the
            # OpenAI-compatible chat-completions API. The InferenceClient
            # handles provider selection and routing automatically.
            client = InferenceClient(token=hf_token)

            logger.info(f"Sending request to Hugging Face model '{model}'...")
            # chat_completion is a blocking network call; run it in a worker
            # thread so it does not block the bot's asyncio event loop.
            completion = await asyncio.to_thread(
                client.chat_completion,
                messages=[{"role": "user", "content": user_message}],
                model=model,
                max_tokens=512,
            )

            ai_response = completion.choices[0].message.content
            if not ai_response:
                ai_response = "No response generated"

            logger.info("Hugging Face response received")
            await update.message.reply_text(f"🤖 Open Claw AI Response:\n\n{ai_response}")
        except Exception as e:
            # Log full detail server-side, but don't leak internals to users.
            logger.error(f"Error calling Hugging Face API: {e}")
            await update.message.reply_text(
                "⚠️ Sorry, I couldn't process your message right now. "
                "Your message was received — please try again shortly."
            )
    else:
        # Placeholder response when HF is not configured
        logger.warning("Hugging Face not configured - using placeholder response")
        response = (
            f"🤖 Open Claw received your message:\n\n"
            f"\"{user_message}\"\n\n"
            f"AI processing will be implemented soon with Hugging Face integration."
        )
        await update.message.reply_text(response)

async def error_handler(update, context):
    """Handle errors."""
    logger.error(f"Update {update} caused error: {context.error}")

def setup_telegram_bot():
    """Set up and start the Telegram bot."""
    
    token = os.environ.get('OPENCLAW_TELEGRAM_BOT_TOKEN')
    
    # Build the application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    logger.info("Telegram bot handlers configured")
    
    return application

def main():
    """Main entry point for the Open Claw daemon."""
    logger.info("Starting Open Claw Headless Daemon...")
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Initialize storage
    if not initialize_storage():
        sys.exit(1)
    
    # Set up Telegram bot
    try:
        application = setup_telegram_bot()
        logger.info("Telegram bot initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Telegram bot: {e}")
        sys.exit(1)
    
    # Log successful initialization
    logger.info("Open Claw Headless Daemon initialized successfully")
    logger.info("Required integrations: Telegram Bot")
    logger.info("Optional integrations: Hugging Face, Groq, OpenRouter")
    logger.info("Starting Telegram bot polling...")
    
    # Start the bot
    try:
        # Run the bot until Ctrl-C is pressed
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("Shutting down Open Claw Daemon...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
