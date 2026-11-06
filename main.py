import os
import sys
import logging
import asyncio

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from database.db import SessionLocal, init_db
from backend.api.routes import router as api_router
from backend.database.models import Meeting
from backend.tasks.pipeline_tasks import run_meeting_pipeline

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("main")

# Load configuration
load_dotenv()
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MODEL_DIR = os.getenv("MODEL_DIR", "models")

# Ensure critical directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# Initialize database schema
logger.info("Initializing database...")
init_db()

# Create FastAPI instance
app = FastAPI(
    title="AI Meeting Assistant API",
    description="Automated transcription, summarization, and action item extraction system",
    version="1.0.0"
)

# Set up CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development convenience
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router)

@app.get("/health")
def health_check():
    from sqlalchemy import text
    from database.db import SessionLocal
    import redis
    
    health = {
        "status": "healthy",
        "database": "connected",
        "redis": "optional",
        "models": {}
    }
    
    # Check Database
    db = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
    except Exception as e:
        health["status"] = "unhealthy"
        health["database"] = f"failed: {str(e)}"
    finally:
        if db is not None:
            db.close()
        
    # Check Redis
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url, socket_timeout=1.0)
        r.ping()
        health["redis"] = "connected"
    except Exception as e:
        health["redis"] = f"unavailable (optional; using background tasks): {e}"
        
    # Check Models status
    try:
        from backend.transcription.whisper_engine import transcriber
        from backend.nlp.action_extractor import action_extractor
        from backend.nlp.question_detector import question_detector
        from backend.sentiment.sentiment_analyzer import sentiment_analyzer
        from backend.summarization.summarizer import summarizer
        
        health["models"] = {
            "whisper": "loaded" if transcriber.model is not None else "lazy_loaded",
            "action_extractor": "loaded" if action_extractor.initialized else "lazy_loaded",
            "question_detector": "loaded" if question_detector.initialized else "lazy_loaded",
            "sentiment_analyzer": "loaded" if sentiment_analyzer.initialized else "lazy_loaded",
            "summarizer": "loaded" if summarizer.initialized else "lazy_loaded",
        }
    except Exception as e:
        health["models_error"] = str(e)
        
    return health


@app.on_event("startup")
async def resume_interrupted_meetings():
    db = SessionLocal()
    try:
        interrupted = db.query(Meeting).filter(
            Meeting.processing_status.in_(
                ["queued", "preprocessing", "transcribing", "nlp_extraction", "summarizing"]
            ),
            Meeting.audio_path.isnot(None),
            Meeting.audio_path != "",
        ).all()
        pending = [
            (meeting.meeting_id, meeting.audio_path, meeting.title or "Meeting")
            for meeting in interrupted
        ]
        for meeting in interrupted:
            meeting.processing_status = "queued"
        db.commit()
    finally:
        db.close()

    if not pending:
        return

    try:
        import redis
        from celery_worker import celery_app

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis.from_url(redis_url, socket_timeout=1.0).ping()
        active_workers = celery_app.control.inspect(timeout=1.0).active()
    except Exception as e:
        logger.info(f"Celery unavailable during recovery; resuming interrupted meetings locally: {e}")
        active_workers = None

    if active_workers:
        logger.info("Celery workers are active; leaving interrupted meeting jobs to Celery.")
        return

    tasks = BackgroundTasks()
    for meeting_id, file_path, title in pending:
        tasks.add_task(run_meeting_pipeline, meeting_id, file_path, title)
    asyncio.get_running_loop().create_task(tasks())
    logger.info(f"Resuming {len(pending)} interrupted meeting pipeline(s) locally.")

# Restore pre-compiled dist folder if it was disabled
dist_disabled_dir = os.path.abspath("frontend/dist_disabled")
dist_dir = os.path.abspath("frontend/dist")
if os.path.exists(dist_disabled_dir) and not os.path.exists(dist_dir):
    try:
        os.rename(dist_disabled_dir, dist_dir)
        logger.info("Successfully restored pre-compiled 'frontend/dist' folder.")
    except Exception as e:
        logger.error(f"Failed to restore frontend/dist folder: {e}")

# Mount Frontend static files
# Make sure frontend folder exists
frontend_dir = os.path.abspath("frontend/dist")
if not os.path.exists(os.path.join(frontend_dir, "index.html")):
    frontend_dir = os.path.abspath("frontend")
    logger.info(f"Vite React build not detected. Serving static files from root '{frontend_dir}' fallback.")
else:
    logger.info(f"Serving compiled Vite React build from '{frontend_dir}'.")

os.makedirs(frontend_dir, exist_ok=True)

try:
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info(f"Frontend static files mounted from {frontend_dir}")
    

except Exception as e:
    logger.warning(f"Could not mount frontend static directory: {e}. Serve API only.")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server at http://{HOST}:{PORT}")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
