from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
import os
from pathlib import Path
from src.config.settings import DATABASE_URL, MAX_DB_SIZE_GB
from src.db.models import Base, Message
from datetime import datetime, timedelta

# Перевіряємо чи вказано шлях до бази даних
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")

# Створюємо директорію для бази даних, якщо вона не існує
db_path = DATABASE_URL.replace('sqlite:///', '')
if db_path:
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Ініціалізує базу даних та створює таблиці"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error initializing database: {e}")
        raise

def get_db():
    """Повертає сесію бази даних"""
    db = SessionLocal()
    try:
        # Перевіряємо підключення
        db.execute(text("SELECT 1"))
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        db.close()

def check_db_size():
    """Перевіряє розмір бази даних та очищає старі записи якщо потрібно"""
    try:
        # Отримуємо шлях до файлу бази даних з URL
        db_path = DATABASE_URL.replace('sqlite:///', '')
        
        if os.path.exists(db_path):
            # Отримуємо розмір файлу в байтах
            db_size_bytes = os.path.getsize(db_path)
            
            # Конвертуємо в гігабайти
            db_size_gb = db_size_bytes / (1024 * 1024 * 1024)
            
            if db_size_gb > MAX_DB_SIZE_GB:
                logger.warning(f"Database size ({db_size_gb:.2f}GB) exceeds limit ({MAX_DB_SIZE_GB}GB). Cleaning old records...")
                
                # Видаляємо старі записи
                with engine.connect() as connection:
                    connection.execute(text("""
                        DELETE FROM messages 
                        WHERE created_at < datetime('now', '-30 days')
                    """))
                    connection.commit()
                
                logger.info("Old records cleaned successfully")
    except (SQLAlchemyError, OSError) as e:
        logger.error(f"Error checking/cleaning database: {e}")

def cleanup_old_messages():
    """Очищення старих повідомлень (старіших за 24 години)"""
    try:
        db = next(get_db())
        # Визначаємо час, старіше якого видаляємо повідомлення (24 години тому)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Видаляємо старі повідомлення
        deleted_count = db.query(Message).filter(
            Message.created_at < cutoff_time
        ).delete(synchronize_session=False)
        
        db.commit()
        logger.info(f"Cleaned up {deleted_count} messages older than {cutoff_time}")
        
    except Exception as e:
        logger.error(f"Error during message cleanup: {e}")
    finally:
        db.close()

# Ініціалізуємо базу даних при імпорті модуля
init_db() 