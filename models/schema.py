from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Language(Base):
    __tablename__ = 'languages'

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)

class Card(Base):
    __tablename__ = 'cards'

    id = Column(Integer, primary_key=True)
    word = Column(String(500), nullable=False)
    translation = Column(String(500), nullable=False)
    source_lang = Column(String(10), ForeignKey('languages.code'), nullable=False)
    target_lang = Column(String(10), ForeignKey('languages.code'), nullable=False)
    context = Column(String(1000))
    created_at = Column(DateTime, default=datetime.utcnow)

    progress = relationship("Progress", back_populates="card", uselist=False)

class Progress(Base):
    __tablename__ = 'progress'

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey('cards.id'), unique=True, nullable=False)
    correct_count = Column(Integer, default=0)
    incorrect_count = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)
    avg_response_time_ms = Column(Float)
    std_dev_response_time_ms = Column(Float)
    last_reviewed_at = Column(DateTime)
    next_review_at = Column(DateTime)

    card = relationship("Card", back_populates="progress")

class UserSettings(Base):
    __tablename__ = 'user_settings'

    id = Column(Integer, primary_key=True)
    native_lang = Column(String(10), ForeignKey('languages.code'))
    learning_lang = Column(String(10), ForeignKey('languages.code'))

engine = create_engine('sqlite:///evolving_cards.db')
Base.metadata.create_all(engine)
