import asyncio
import nest_asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder
from loguru import logger

from src.config.settings import TELEGRAM_BOT_TOKEN
from src.bot.handlers import setup_commands, setup_handlers
from src.db.database import init_db, cleanup_old_messages, check_db_size

# Enable nested event loops (for environments like notebooks or Uvicorn)
nest_asyncio.apply()

async def scheduled_cleanup(context):
    """Periodic database cleanup"""
    logger.info("Starting scheduled database cleanup")
    cleanup_old_messages()

async def main():
    """Main function to run the bot"""
    try:
        init_db()
        
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        setup_handlers(application)
        await setup_commands(application)

        # Cleanup every 3 days
        application.job_queue.run_repeating(
            scheduled_cleanup,
            interval=timedelta(days=3),
            first=datetime.now() + timedelta(minutes=1)
        )

        # Additional weekly cleanup
        application.job_queue.run_repeating(
            scheduled_cleanup,
            interval=timedelta(days=7),
            first=datetime.now() + timedelta(hours=1)
        )

        # Size check every 6 hours
        application.job_queue.run_repeating(
            lambda context: check_db_size(),
            interval=timedelta(hours=6),
            first=datetime.now() + timedelta(minutes=5)
        )

        logger.info("Bot is running. Press Ctrl+C to stop.")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Bot stopped due to error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
