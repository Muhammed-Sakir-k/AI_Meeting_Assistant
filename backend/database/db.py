import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import Base and models from backend.database.models
from backend.database.models import Base, Meeting, Transcript, Translation, ActionItem, Summary, Sentiment, Question, Reminder, EmailLog, User, AnalyticsEvent

logger = logging.getLogger(__name__)
load_dotenv()

DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "ai_meeting_assistant")

engine = None
SessionLocal = None

def init_engine():
    global engine, SessionLocal
    if DB_TYPE == "mysql":
        connection_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        try:
            logger.info("Attempting to connect to MySQL database...")
            engine = create_engine(connection_str, pool_pre_ping=True)
            with engine.connect() as conn:
                pass
            logger.info("Successfully connected to MySQL database.")
        except Exception as e:
            logger.warning(f"Failed to connect to MySQL database: {e}. Falling back to SQLite...")
            sqlite_path = os.path.abspath("ai_meeting_assistant.db")
            engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
            logger.info(f"Using SQLite database at: {sqlite_path}")
    else:
        sqlite_path = os.path.abspath("ai_meeting_assistant.db")
        engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
        logger.info(f"Using SQLite database at: {sqlite_path}")
        
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize on import
init_engine()

def init_db():
    """Initializes tables in database."""
    try:
        if DB_TYPE != "mysql":
            sqlite_path = os.path.abspath("ai_meeting_assistant.db")
            # We don't necessarily want to delete the database file if it already contains entries,
            # but for Phase 1 table generation, if columns mismatch, the user can reset it.
            # Let's keep it if we can, or create it if not.
            logger.info("Verifying SQLite tables...")
        init_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")

def get_db():
    """Dependency injection session generator."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
