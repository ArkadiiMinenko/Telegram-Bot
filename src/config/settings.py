import os
from dotenv import load_dotenv
from pathlib import Path

# Завантажуємо змінні оточення
load_dotenv()

# Базові налаштування
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Налаштування Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables")

# Налаштування бази даних
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/data/bot.db')

# Інші налаштування
MAX_DB_SIZE_GB = float(os.getenv('MAX_DB_SIZE_GB', 1)) 