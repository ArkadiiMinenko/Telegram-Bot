import asyncio
import nest_asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder
from loguru import logger
from src.config.settings import TELEGRAM_BOT_TOKEN
from src.bot.handlers import translate_ua, translate_en, help_command, setup_commands, setup_handlers
from src.db.database import init_db, get_db, cleanup_old_messages

# Дозволяємо вкладені event loops
nest_asyncio.apply()

async def scheduled_cleanup(context):
    """Періодичне очищення бази даних"""
    logger.info("Starting scheduled database cleanup")
    cleanup_old_messages()

async def main():
    """Головна функція"""
    try:
        # Ініціалізуємо базу даних
        init_db()
        
        # Створюємо та налаштовуємо бота
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Налаштовуємо всі обробники
        setup_handlers(application)
        
        # Налаштовуємо команди в меню бота
        await setup_commands(application)
        
        # Налаштовуємо періодичне очищення бази даних
        application.job_queue.run_repeating(
            scheduled_cleanup,
            interval=timedelta(days=7),
            first=datetime.now() + timedelta(minutes=1)
        )
        
        # Запускаємо бота
        logger.info("Bot is running. Press Ctrl+C to stop.")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Bot stopped due to error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 