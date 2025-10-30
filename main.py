#!/usr/bin/env python3
import os
import sys
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from bot.handlers import (
    start_command,
    help_command,
    about_command,
    handle_message,
    button_callback,
    error_handler
)
from config.settings import TELEGRAM_BOT_TOKEN, LOG_LEVEL, DOWNLOAD_DIR

logger_configured = False

def setup_logging():
    """Configure logging to prevent duplicates"""
    global logger_configured
    if logger_configured:
        return logging.getLogger(__name__)
    
    logger_configured = True
    
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log')
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

def validate_environment():
    """Validate all required environment variables"""
    missing_vars = []
    
    if not TELEGRAM_BOT_TOKEN:
        missing_vars.append("TELEGRAM_BOT_TOKEN")
    
    if missing_vars:
        logger.error("=" * 50)
        logger.error("MISSING REQUIRED ENVIRONMENT VARIABLES")
        logger.error("=" * 50)
        for var in missing_vars:
            logger.error(f"  ❌ {var} is not set")
        logger.error("=" * 50)
        logger.error("Please set the required environment variables in .env file")
        logger.error("You can copy .env.example to .env and fill in your values")
        logger.error("=" * 50)
        return False
    
    logger.info("✅ All required environment variables are set")
    return True

def main():
    """Start the bot"""
    
    logger.info("=" * 50)
    logger.info("DiskWala Video Downloader Bot")
    logger.info("Version: 1.0.0")
    logger.info("=" * 50)
    
    if not validate_environment():
        sys.exit(1)
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    logger.info(f"Download directory: {os.path.abspath(DOWNLOAD_DIR)}")
    
    logger.info("Starting DiskWala Downloader Bot...")
    
    try:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        
        application.add_handler(CallbackQueryHandler(button_callback))
        
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        application.add_error_handler(error_handler)
        
        logger.info("✅ Bot started successfully!")
        logger.info("Polling for updates...")
        logger.info("Press Ctrl+C to stop the bot")
        logger.info("=" * 50)
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 50)
        logger.info("Bot stopped by user")
        logger.info("=" * 50)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
