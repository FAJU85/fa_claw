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

# Groq chat-completion model. Override with OPENCLAW_GROQ_MODEL.
DEFAULT_GROQ_MODEL = 'llama-3.3-70b-versatile'

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
    telegram_token = os.environ.get('OPENCLAW_TELEGRAM_BOT_TOKEN', 'Not set')
    groq_key = get_groq_token()
    hf_key = get_hf_token()

    # Mirror the provider-selection logic used by handle_message.
    if groq_key:
        active_provider = "Groq"
    elif hf_key:
        active_provider = "Hugging Face"
    else:
        active_provider = "None (set a provider key)"

    status_msg = (
        "🔧 Open Claw Status\n\n"
        f"✅ Telegram Bot: {'Connected' if telegram_token else 'Disconnected'}\n"
        f"{'✅' if groq_key else '⚙️'} Groq: {'Connected' if groq_key else 'Not configured'}\n"
        f"{'✅' if hf_key else '⚙️'} Hugging Face: {'Connected' if hf_key else 'Not configured'}\n"
        f"⚙️ OpenRouter: {'Connected' if os.environ.get('OPENCLAW_OPENROUTER_API_KEY') else 'Not configured'}\n\n"
        f"🧠 Active AI provider: {active_provider}\n"
        "Storage: /data (persistent)"
    )
    await update.message.reply_text(status_msg)

def get_groq_token():
    """Return the configured Groq API key, if any."""
    return os.environ.get('OPENCLAW_GROQ_API_KEY') or os.environ.get('GROQ_API_KEY')


def get_hf_token():
    """Return the configured Hugging Face token, if any."""
    return os.environ.get('OPENCLAW_HUGGINGFACE_API_KEY') or os.environ.get('OPENCLAW_HF_TOKEN')


async def _groq_reply(user_message):
    """Generate a reply with the Groq chat-completions API."""
    from groq import Groq  # imported lazily so HF-only deploys don't need it

    model = os.environ.get('OPENCLAW_GROQ_MODEL') or DEFAULT_GROQ_MODEL
    client = Groq(api_key=get_groq_token())

    logger.info(f"Sending request to Groq model '{model}'...")
    # The Groq SDK call is blocking; run it off the asyncio event loop.
    completion = await asyncio.to_thread(
        client.chat.completions.create,
        messages=[{"role": "user", "content": user_message}],
        model=model,
        max_tokens=512,
    )
    return completion.choices[0].message.content


async def _hf_reply(user_message):
    """Generate a reply with the Hugging Face Inference Providers router."""
    model = os.environ.get('OPENCLAW_HF_MODEL') or DEFAULT_HF_MODEL
    # The InferenceClient handles provider selection and routing automatically.
    client = InferenceClient(token=get_hf_token())

    logger.info(f"Sending request to Hugging Face model '{model}'...")
    # chat_completion is a blocking network call; run it in a worker thread.
    completion = await asyncio.to_thread(
        client.chat_completion,
        messages=[{"role": "user", "content": user_message}],
        model=model,
        max_tokens=512,
    )
    return completion.choices[0].message.content


async def handle_message(update, context):
    """Handle incoming text messages."""
    user_message = update.message.text
    logger.info(f"Received message from user {update.message.chat.id}: {user_message}")

    # Pick a provider: Groq is preferred when configured (fast, generous free
    # tier), otherwise fall back to Hugging Face Inference Providers.
    if get_groq_token():
        provider, generate = "Groq", _groq_reply
    elif get_hf_token():
        provider, generate = "Hugging Face", _hf_reply
    else:
        logger.warning("No AI provider configured - using placeholder response")
        await update.message.reply_text(
            f"🤖 Open Claw received your message:\n\n"
            f"\"{user_message}\"\n\n"
            f"No AI provider is configured yet. Set OPENCLAW_GROQ_API_KEY or "
            f"OPENCLAW_HUGGINGFACE_API_KEY to enable AI responses."
        )
        return

    try:
        ai_response = await generate(user_message)
        if not ai_response:
            ai_response = "No response generated"
        logger.info(f"{provider} response received")
        await update.message.reply_text(f"🤖 Open Claw AI Response:\n\n{ai_response}")
    except Exception as e:
        # Log full detail server-side, but don't leak internals to users.
        logger.error(f"Error calling {provider} API: {e}")
        await update.message.reply_text(
            "⚠️ Sorry, I couldn't process your message right now. "
            "Your message was received — please try again shortly."
        )

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
