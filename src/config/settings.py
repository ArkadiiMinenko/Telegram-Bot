import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Base settings
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Telegram settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables")

# Database settings
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/data/bot.db')
MAX_DB_SIZE_MB = float(os.getenv('MAX_DB_SIZE_MB', 400))  # Maximum size in MB

# Інші налаштування
MAX_DB_SIZE_GB = float(os.getenv('MAX_DB_SIZE_GB', 1)) 