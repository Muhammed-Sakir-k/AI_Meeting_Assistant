import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database.db import get_db, Meeting, Transcript

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/search")
def search_meetings(
    q: str = Query("", description="Search string for meeting titles and transcripts"),
    db: Session = Depends(get_db)
):
    """
    Searches across meeting titles and transcript contents.
    If the query is empty, returns all meetings.
    """
    try:
        if not q or not q.strip():
            # Return all meetings if search query is empty
            results = db.query(Meeting).all()
        else:
            query_str = f"%{q}%"
            # Join with transcripts and filter by title or transcript text matching query
            results = db.query(Meeting).outerjoin(Transcript).filter(
                (Meeting.title.like(query_str)) | (Transcript.text.like(query_str))
            ).all()

        return [
            {
                "meeting_id": m.meeting_id,
                "title": m.title,
                "date": m.date.isoformat() if m.date else None,
                "language": m.language,
                "audio_path": m.audio_path
            }
            for m in results
        ]
    except Exception as e:
        logger.error(f"Search endpoint query error: {e}")
        return []

@router.get("/meetings")
def list_meetings(db: Session = Depends(get_db)):
    """Returns the list of all meetings."""
    try:
        results = db.query(Meeting).all()
        return [
            {
                "meeting_id": m.meeting_id,
                "title": m.title,
                "date": m.date.isoformat() if m.date else None,
                "language": m.language,
                "audio_path": m.audio_path
            }
            for m in results
        ]
    except Exception as e:
        logger.error(f"List meetings endpoint error: {e}")
        return []

@router.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """Returns the metadata of a single meeting."""
    meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {
        "meeting_id": meeting.meeting_id,
        "title": meeting.title,
        "date": meeting.date.isoformat() if meeting.date else None,
        "language": meeting.language,
        "duration_seconds": meeting.duration_seconds,
        "processing_status": meeting.processing_status,
        "audio_path": meeting.audio_path
    }
