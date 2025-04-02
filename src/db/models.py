from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import BigInteger
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Message(Base):
    """
    Message model for storing telegram messages
    
    Attributes:
        id (int): Primary key
        message_id (int): Telegram message ID
        chat_id (int): Telegram chat ID
        user_id (int): Telegram user ID
        original_text (str): Original message text
        translated_text (str): Translated message text
        translation_type (str): Type of translation (ua->en or en->ua)
        created_at (datetime): Message creation timestamp
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer)
    chat_id = Column(BigInteger)
    user_id = Column(BigInteger)
    original_text = Column(String)
    translated_text = Column(String)
    translation_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow) 