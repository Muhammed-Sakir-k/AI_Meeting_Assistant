from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Meeting(Base):
    __tablename__ = 'meetings'
    
    meeting_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    audio_path = Column(Text, nullable=True)
    language = Column(String(50), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    processing_status = Column(String(50), default="queued") # queued/preprocessing/transcribing/nlp_extraction/summarizing/completed/failed
    audio_hash = Column(String(64), nullable=True)
    
    # Relationships
    transcripts = relationship("Transcript", back_populates="meeting", cascade="all, delete-orphan")
    translations = relationship("Translation", back_populates="meeting", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="meeting", cascade="all, delete-orphan")
    sentiments = relationship("Sentiment", back_populates="meeting", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="meeting", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="meeting", cascade="all, delete-orphan")
    emails = relationship("EmailLog", back_populates="meeting", cascade="all, delete-orphan")
    analytics_events = relationship("AnalyticsEvent", back_populates="meeting", cascade="all, delete-orphan")

class Transcript(Base):
    __tablename__ = 'transcripts'
    
    transcript_id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey('meetings.meeting_id'), nullable=False)
    text = Column(Text, nullable=True)
    language = Column(String(50), nullable=True)
    confidence_score = Column(String(20), nullable=True)
    segment_index = Column(Integer, nullable=True)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    
    meeting = relationship("Meeting", back_populates="transcripts")

class Translation(Base):
    __tablename__ = 'translations'
    
    translation_id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey('meetings.meeting_id'), nullable=False)
    source_language = Column(String(50), nullable=True)
    target_language = Column(String(50), nullable=True)
    content_type = Column(String(50), nullable=True) # 'transcript' or 'summary'
    original_text = Column(Text, nullable=True)
    translated_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    meeting = relationship("Meeting", back_populates="translations")

class ActionItem(Base):
    __tablename__ = 'action_items'
    
    action_id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey('meetings.meeting_id'), nullable=False)
    owner = Column(String(255), nullable=True)
    task = Column(Text, nullable=True)
    deadline = Column(String(100), nullable=True)
    priority = Column(String(20), default='medium') # high/medium/low
    status = Column(String(50), default='pending') # pending/in_progress/done
    
    meeting = relationship("Meeting", back_populates="action_items")
    reminders = relationship("Reminder", back_populates="action_item", cascade="all, delete-orphan")

class Summary(Base):
    __tablename__ = 'summaries'
    
    summary_id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey('meetings.meeting_id'), nullable=False)
    summary_text = Column(Text, nullable=True)
    key_decisions = Column(Text, nullable=True)
    executive_summary = Column(Text, nullable=True)
    
    meeting = relationship("Meeting", back_populates="summaries")

class Sentiment(Base):
    __tablename__ = 'sentiments'
    
    sentiment_id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey('meetings.meeting_id'), nullable=False)
    segment_index = Column(Integer, nullable=True)
    label = Column(String(20), nullable=True) # Positive/Neutral/Negative
    score = Column(Float, nullable=True)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    
    meeting = relationship("Meeting", back_populates="sentiments")

class Question(Base):
    __tablename__ = 'questions'
    
    question_id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey('meetings.meeting_id'), nullable=False)
    question_text = Column(Text, nullable=True)
    asked_at = Column(Float, nullable=True) # timestamp in seconds
    status = Column(String(20), default='unanswered') # answered/unanswered
    
    meeting = relationship("Meeting", back_populates="questions")

class Reminder(Base):
    __tablename__ = 'reminders'
    
    reminder_id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey('meetings.meeting_id'), nullable=False)
    action_id = Column(Integer, ForeignKey('action_items.action_id'), nullable=False)
    owner_name = Column(String(255), nullable=True)
    reminder_text = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    status = Column(String(20), default='pending') # pending/sent/dismissed
    
    meeting = relationship("Meeting", back_populates="reminders")
    action_item = relationship("ActionItem", back_populates="reminders")

class EmailLog(Base):
    __tablename__ = 'email_log'
    
    email_id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey('meetings.meeting_id'), nullable=False)
    recipient = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=True)
    email_type = Column(String(50), nullable=True) # 'mom'/'action_assignment'/'followup'
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(20), default='draft') # draft/sent/failed
    
    meeting = relationship("Meeting", back_populates="emails")

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    role = Column(String(100), nullable=True)
    notification_prefs = Column(JSON, nullable=True) # {"email":true,"inapp":true}

class AnalyticsEvent(Base):
    __tablename__ = 'analytics_events'
    
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey('meetings.meeting_id'), nullable=False)
    event_type = Column(String(100), nullable=True) # e.g. 'export_pdf','send_email','voice_cmd'
    event_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    meeting = relationship("Meeting", back_populates="analytics_events")
