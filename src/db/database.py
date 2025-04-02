from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
import os
from pathlib import Path
from datetime import datetime, timedelta
from src.config.settings import DATABASE_URL, MAX_DB_SIZE_MB
from src.db.models import Base, Message

# Check if database URL is set
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")

# Create database directory if it doesn't exist
db_path = DATABASE_URL.replace('sqlite:///', '')
if db_path:
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database and create tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error initializing database: {e}")
        raise

def get_db():
    """Return database session"""
    db = SessionLocal()
    try:
        # Check connection
        db.execute(text("SELECT 1"))
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        db.close()

def check_db_size():
    """Check database size and clean old records if needed"""
    try:
        db_path = DATABASE_URL.replace('sqlite:///', '')
        
        if os.path.exists(db_path):
            # Get file size in bytes
            db_size_bytes = os.path.getsize(db_path)
            
            # Convert to megabytes
            db_size_mb = db_size_bytes / (1024 * 1024)
            
            if db_size_mb > MAX_DB_SIZE_MB:
                logger.warning(f"Database size ({db_size_mb:.2f}MB) exceeds limit ({MAX_DB_SIZE_MB}MB). Cleaning old records...")
                cleanup_old_messages()
                logger.info("Old records cleaned successfully")
    except (SQLAlchemyError, OSError) as e:
        logger.error(f"Error checking database size: {e}")

async def scheduled_cleanup(context):
    """Scheduled cleanup of old messages"""
    logger.info("Starting scheduled database cleanup")
    cleanup_old_messages()

def cleanup_old_messages():
    """Clean up old messages (older than 24 hours)"""
    try:
        db = next(get_db())
        # Define cutoff time (24 hours ago)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Delete old messages but keep messages newer than 24 hours
        deleted_count = db.query(Message).filter(
            Message.created_at < cutoff_time
        ).delete(synchronize_session=False)
        
        db.commit()
        logger.info(f"Cleaned up {deleted_count} messages older than {cutoff_time}")
        
    except Exception as e:
        logger.error(f"Error during message cleanup: {e}")
    finally:
        db.close()

# Initialize database when module is imported
init_db() 