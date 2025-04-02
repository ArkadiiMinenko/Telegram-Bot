import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

from src.config.settings import DATABASE_URL, MAX_DB_SIZE_MB
from src.config.log_config import logger
from src.db.models import Message

Base = declarative_base()

# Detect DB type
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# SQLAlchemy engine and session setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database (create tables if needed)."""
    try:
        if IS_SQLITE:
            db_path = DATABASE_URL.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logger.info(f"Created database directory: {db_dir}")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except SQLAlchemyError as e:
        logger.error(f"Database initialization failed: {e}")


def get_db():
    """Provide a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def cleanup_old_messages(hours: int = 24):
    """Delete messages older than the specified number of hours."""
    try:
        db = next(get_db())
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        deleted = db.query(Message).filter(Message.created_at < cutoff_time).delete()
        db.commit()
        logger.info(f"Cleaned up {deleted} old messages older than {hours}h")
    except SQLAlchemyError as e:
        logger.error(f"Cleanup failed: {e}")


def check_db_size():
    """Check database size and clean up if it exceeds MAX_DB_SIZE_MB (only for SQLite)."""
    if not IS_SQLITE:
        logger.debug("Skipping DB size check (not SQLite)")
        return

    try:
        db_path = DATABASE_URL.replace("sqlite:///", "")
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        logger.debug(f"Current DB size: {size_mb:.2f} MB")

        if size_mb > MAX_DB_SIZE_MB:
            logger.warning(f"DB size {size_mb:.2f} MB exceeds {MAX_DB_SIZE_MB} MB, running cleanup...")
            cleanup_old_messages()
    except (OSError, ValueError) as e:
        logger.error(f"DB size check failed: {e}")
