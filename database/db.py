# Compatibility wrapper to forward database imports to backend/database/db.py and models.py
from backend.database.db import get_db, init_db, SessionLocal, engine
from backend.database.models import (
    Base,
    Meeting,
    Transcript,
    Translation,
    ActionItem,
    Summary,
    Sentiment,
    Question,
    Reminder,
    EmailLog,
    User,
    AnalyticsEvent
)
