import os
import logging
import hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database.db import get_db, Meeting
from backend.tasks.pipeline_tasks import run_meeting_pipeline, process_meeting_pipeline_task

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Accepts meeting audio files, validates format, checks for duplicates,
    initiates database entries, and queues background processing via Celery or BackgroundTasks.
    """
    # 1. Validate File Format
    allowed_extensions = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: WAV, MP3, M4A, FLAC, OGG, WEBM"
        )
        
    # Ensure upload directory exists
    upload_dir = os.path.abspath("uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # 2. Compute File Hash to Detect Duplicates
    try:
        hasher = hashlib.sha256()
        chunk_size = 8192
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
            
        file_hash = hasher.hexdigest()
        await file.seek(0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read/hash audio file: {str(e)}")
        
    target_path = os.path.join(upload_dir, f"{file_hash}{file_ext}")
    
    # Check if duplicate meeting exists
    existing_meeting = db.query(Meeting).filter(Meeting.audio_hash == file_hash).first()
    if existing_meeting:
        return JSONResponse(
            status_code=409,
            content={
                "status": "duplicate",
                "duplicate": True,
                "message": "Duplicate meeting upload detected. Reprocessing skipped.",
                "meeting_id": existing_meeting.meeting_id
            }
        )
        
    # 3. Write uploaded file to disk
    try:
        with open(target_path, "wb") as f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        logger.error(f"Failed to save upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save upload on server: {str(e)}")
        
    # 4. Create Meeting DB Entry
    meeting_title = title if title else os.path.splitext(file.filename)[0]
    db_meeting = Meeting(
        title=meeting_title,
        date=datetime.utcnow(),
        audio_path=target_path,
        audio_hash=file_hash,
        language="en",
        processing_status="queued"
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    
    meeting_id = db_meeting.meeting_id
    
    # 5. Queue Background Task
    try:
        # Check if Redis is reachable to avoid blocking on celery when offline
        import redis
        from celery_worker import celery_app
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url, socket_timeout=1.0)
        r.ping()
        
        # Check if Celery workers are active
        inspector = celery_app.control.inspect(timeout=1.0)
        active_workers = inspector.active()
        if not active_workers:
            raise Exception("No active Celery workers listening.")
            
        # Try Celery dispatch
        process_meeting_pipeline_task.delay(meeting_id, target_path, meeting_title)
        logger.info(f"Enqueued meeting pipeline task via Celery for meeting {meeting_id}")
    except Exception as celery_err:
        logger.warning(f"Celery dispatch skipped/failed: {celery_err}. Falling back to FastAPI BackgroundTasks thread.")
        background_tasks.add_task(run_meeting_pipeline, meeting_id, target_path, meeting_title)
        
    return {
        "status": "queued",
        "meeting_id": meeting_id,
        "message": "Meeting successfully uploaded and queued."
    }

@router.get("/status/{meeting_id}")
def get_status(meeting_id: int, db: Session = Depends(get_db)):
    """Returns the current pipeline processing status."""
    meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {
        "meeting_id": meeting_id,
        "status": meeting.processing_status,
        "message": f"Pipeline is currently at state: {meeting.processing_status}"
    }
