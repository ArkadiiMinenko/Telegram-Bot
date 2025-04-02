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

async def handle_translation(update: Update, context: ContextTypes.DEFAULT_TYPE, translation_func, translation_type: str):
    """Загальний обробник для обох типів перекладу"""
    try:
        if not update.effective_message:
            logger.error("No effective message found")
            return

        # Перевіряємо тип чату
        chat_type = update.effective_message.chat.type
        logger.info(f"Processing translation in chat type: {chat_type}")

        if not update.effective_message.reply_to_message:
            help_text = (
                "Будь ласка, використовуйте команду як відповідь на повідомлення, яке потрібно перекласти.\n\n"
                "В приватному чаті:\n"
                "1. Відправте текст\n"
                "2. Відповідьте на нього командою\n\n"
                "В груповому чаті:\n"
                "1. Відправте текст\n"
                "2. Відповідьте на нього командою з моїм іменем\n"
                "Наприклад: /translateua@BotUsername"
            )
            await update.effective_message.reply_text(help_text)
            return

        reply_to_message = update.effective_message.reply_to_message
        logger.info(f"Reply to message: {reply_to_message.text[:50]}...")
        
        db = next(get_db())
        
        # Отримуємо повідомлення з БД
        original_message = await get_message_by_id(reply_to_message.message_id, reply_to_message.chat_id, db)
        
        if not original_message:
            # Якщо повідомлення немає в БД, спробуємо зберегти його
            original_message = await save_message(reply_to_message, db)
            
        if not original_message:
            await update.effective_message.reply_text(
                "Не вдалося знайти текст для перекладу. Переконайтеся, що відповідаєте на текстове повідомлення."
            )
            return

        # Перекладаємо текст
        translated_text = translation_func(original_message.original_text)
        logger.info(f"Translated text: {original_message.original_text} -> {translated_text}")
        
        # Оновлюємо запис в БД
        original_message.translated_text = translated_text
        original_message.translation_type = translation_type
        db.commit()
        
        # Формуємо відповідь в залежності від типу чату
        if chat_type == Chat.PRIVATE:
            reply_text = translated_text
        else:
            # В групових чатах додаємо оригінальний текст
            reply_text = f"Оригінал: {original_message.original_text}\nПереклад: {translated_text}"
        
        await update.effective_message.reply_text(reply_text)
        logger.info(f"Successfully sent translation in {chat_type} chat: {original_message.original_text} -> {translated_text}")
            
    except Exception as e:
        logger.error(f"Error in translation handler: {e}")
        if update.effective_message:
            await update.effective_message.reply_text("Виникла помилка при перекладі. Спробуйте ще раз.")

async def translate_ua(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /translateUA - перекладає текст з англійської розкладки в українську"""
    await handle_translation(update, context, transliterate_to_ua, 'UA')

async def translate_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /translateEN - перекладає текст з української розкладки в англійську"""
    await handle_translation(update, context, transliterate_to_en, 'EN')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /help - показує список доступних команд"""
    logger.info("Received help command")
    chat_type = update.effective_message.chat.type
    
    if chat_type == Chat.PRIVATE:
        help_text = (
            "🤖 Привіт! Я бот для транслітерації тексту.\n\n"
            "Доступні команди:\n"
            "/translateua - перекласти текст з англійської розкладки в українську\n"
            "/translateen - перекласти текст з української розкладки в англійську\n"
            "/help - показати це повідомлення\n\n"
            "Як використовувати:\n"
            "1. Відправте текст, який потрібно перекласти\n"
            "2. Відповідьте на це повідомлення командою /translateua або /translateen\n"
            "3. Отримайте переклад\n\n"
            "Приклади:\n"
            "• ghbdtn -> привіт (використовуйте /translateua)\n"
            "• привіт -> ghbdtn (використовуйте /translateen)"
        )
    else:
        help_text = (
            "🤖 Привіт! Я бот для транслітерації тексту.\n\n"
            "Доступні команди:\n"
            "/translateua@BotUsername - перекласти текст з англійської розкладки в українську\n"
            "/translateen@BotUsername - перекласти текст з української розкладки в англійську\n"
            "/help@BotUsername - показати це повідомлення\n\n"
            "Як використовувати в груповому чаті:\n"
            "1. Відправте текст, який потрібно перекласти\n"
            "2. Відповідьте на це повідомлення командою з моїм іменем\n"
            "3. Отримайте переклад з оригінальним текстом\n\n"
            "Приклади:\n"
            "• ghbdtn -> привіт (використовуйте /translateua@BotUsername)\n"
            "• привіт -> ghbdtn (використовуйте /translateen@BotUsername)"
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
    """Налаштування команд для відображення в меню бота"""
    logger.info("Setting up bot commands")
    commands = [
        BotCommand("translateua", "Переклад з англійської розкладки"),
        BotCommand("translateen", "Переклад з української розкладки"),
        BotCommand("help", "Показати довідку")
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands set up successfully")

def setup_handlers(application):
    """Налаштування обробників команд та повідомлень"""
    # Додаємо обробник для всіх текстових повідомлень
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Додаємо обробники команд
    application.add_handler(CommandHandler("translateua", translate_ua))
    application.add_handler(CommandHandler("translateen", translate_en))
    application.add_handler(CommandHandler("help", help_command))
    logger.info("Handlers set up successfully") 