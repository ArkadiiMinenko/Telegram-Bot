import sys
from loguru import logger
import os

# Створюємо директорію для логів, якщо вона не існує
os.makedirs("logs", exist_ok=True)

# Налаштовуємо логування
logger.remove()  # Видаляємо стандартний обробник
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {module}:{function}:{line} - {message}",
    level="INFO",
    colorize=True
)

# Add file logging for errors
logger.add(
    "logs/errors.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {module}:{function}:{line} - {message}",
    level="ERROR",
    rotation="1 week",
    compression="zip"
)

logger.add(
    "logs/bot.log",
    rotation="1 day",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
) 