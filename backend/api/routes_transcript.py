import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.db import get_db, Transcript

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/transcript/{meeting_id}")
def get_transcript(meeting_id: int, db: Session = Depends(get_db)):
    """Returns the transcript segment list and metadata of a meeting."""
    transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found for this meeting")
        
    try:
        data = json.loads(transcript.text)
        return {
            "transcript_id": transcript.transcript_id,
            "meeting_id": transcript.meeting_id,
            "text": data.get("text", ""),
            "language": transcript.language,
            "confidence_score": transcript.confidence_score,
            "segments": data.get("segments", [])
        }
    except Exception:
        # Fallback if raw text was saved instead of JSON string
        return {
            "transcript_id": transcript.transcript_id,
            "meeting_id": transcript.meeting_id,
            "text": transcript.text,
            "language": transcript.language,
            "confidence_score": transcript.confidence_score,
            "segments": []
        }
