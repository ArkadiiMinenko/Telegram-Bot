from telegram import Update, BotCommand, Message as TelegramMessage, Chat
from telegram.ext import ContextTypes, MessageHandler, filters, CommandHandler
from loguru import logger
from sqlalchemy.orm import Session
from src.db.models import Message
from src.db.database import get_db
from src.bot.logic import transliterate_to_ua, transliterate_to_en

def extract_command_text(text: str, entity) -> str:
    """Витягує текст після команди, враховуючи @BotUsername"""
    command_end = entity.offset + entity.length
    return text[command_end:].strip()

async def save_message(message: TelegramMessage, db: Session):
    """Зберігає повідомлення в базу даних"""
    try:
        if not message.text:
            logger.info("Пропускаємо порожнє повідомлення")
            return None
            
        # Не зберігаємо повідомлення від ботів
        if message.from_user.is_bot:
            logger.info(f"Пропускаємо повідомлення від бота: {message.from_user.username}")
            return None
            
        logger.info(f"Зберігаємо повідомлення в БД - ID: {message.message_id}, Chat: {message.chat_id}, Text: {message.text}")
        db_message = Message(
            message_id=message.message_id,
            chat_id=message.chat_id,
            user_id=message.from_user.id,
            original_text=message.text,
            translated_text="",  # Буде заповнено при перекладі
            translation_type=""  # Буде заповнено при перекладі
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        logger.info(f"✅ Повідомлення успішно збережено в БД - ID: {db_message.message_id}")
        return db_message
    except Exception as e:
        logger.error(f"❌ Помилка збереження в БД: {e}")
        return None

async def get_message_by_id(message_id: int, chat_id: int, db: Session) -> Message:
    """Отримує повідомлення з бази даних за message_id та chat_id"""
    try:
        logger.info(f"Шукаємо повідомлення в БД - ID: {message_id}, Chat: {chat_id}")
        message = db.query(Message).filter(
            Message.message_id == message_id,
            Message.chat_id == chat_id
        ).first()
        if message:
            logger.info(f"✅ Знайдено повідомлення в БД - Text: {message.original_text}")
        else:
            logger.info(f"❌ Повідомлення не знайдено в БД - ID: {message_id}, Chat: {chat_id}")
        return message
    except Exception as e:
        logger.error(f"❌ Помилка пошуку в БД: {e}")
        return None

async def handle_translation(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                           translate_func, translation_type: str):
    """
    Generic handler for translation commands
    
    Args:
        update (Update): Telegram update object
        context (ContextTypes.DEFAULT_TYPE): Telegram context
        translate_func (callable): Translation function to use
        translation_type (str): Type of translation being performed
    """
    if not update.message:
        return

    chat_type = update.message.chat.type
    reply = update.message.reply_to_message
    
    try:
        db = next(get_db())
        
        if reply:
            # Handle reply to message
            message = await get_message_by_id(reply.message_id, reply.chat_id, db)
            if message and message.original_text:
                translated = translate_func(message.original_text)
                await update.message.reply_text(translated)
                return
        
        # Handle direct command with text
        command_text = update.message.text
        if ' ' in command_text:
            text = command_text.split(' ', 1)[1]
            translated = translate_func(text)
            await update.message.reply_text(translated)
            return
            
        # No text provided
        await help_command(update, context)
        
    except Exception as e:
        logger.error(f"Error in translation handler: {e}")
        await update.message.reply_text("Sorry, an error occurred during translation.")

async def translate_ua(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /translateua command
    Translates text from English layout to Ukrainian
    """
    await handle_translation(update, context, transliterate_to_ua, "en->ua")

async def translate_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /translateen command
    Translates text from Ukrainian layout to English
    """
    await handle_translation(update, context, transliterate_to_en, "ua->en")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message with command usage instructions"""
    chat_type = update.message.chat.type if update.message else "unknown"
    
    if chat_type == Chat.PRIVATE:
        help_text = (
            "To translate text, use one of these methods:\n\n"
            "1. Send text and reply with command:\n"
            "   - Reply with /translateua for EN->UA\n"
            "   - Reply with /translateen for UA->EN\n\n"
            "2. Send command with text:\n"
            "   - /translateua your_text\n"
            "   - /translateen your_text"
        )
    else:
        help_text = (
            "To translate text in group chat:\n\n"
            "1. Reply to message with command:\n"
            "   - /translateua@BotUsername\n"
            "   - /translateen@BotUsername\n\n"
            "2. Send command with text:\n"
            "   - /translateua@BotUsername text\n"
            "   - /translateen@BotUsername text"
        )
    
    await update.message.reply_text(help_text)
    logger.info(f"Help message sent in {chat_type} chat")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник для всіх текстових повідомлень"""
    if not update.message or not update.message.text:
        return

    try:
        db = next(get_db())
        await save_message(update.message, db)
    except Exception as e:
        logger.error(f"❌ Помилка в обробнику повідомлень: {e}")

async def setup_commands(application):
    """Setup bot commands for display in menu"""
    logger.info("Setting up bot commands")
    commands = [
        BotCommand("translateua", "Translate from English layout"),
        BotCommand("translateen", "Translate from Ukrainian layout"),
        BotCommand("help", "Show help")
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands set up successfully")

def setup_handlers(application):
    """Setup message and command handlers"""
    # Add handler for all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Add command handlers
    application.add_handler(CommandHandler("translateua", translate_ua))
    application.add_handler(CommandHandler("translateen", translate_en))
    application.add_handler(CommandHandler("help", help_command))
    logger.info("Handlers set up successfully") 