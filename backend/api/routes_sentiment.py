import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.db import get_db, Sentiment

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/sentiment/{meeting_id}")
def get_sentiment(meeting_id: int, db: Session = Depends(get_db)):
    """Returns per-segment sentiment scores and labels for a meeting."""
    sentiments = db.query(Sentiment).filter(Sentiment.meeting_id == meeting_id).order_by(Sentiment.segment_index).all()
    if not sentiments:
        return []
        
    return [
        {
            "sentiment_id": s.sentiment_id,
            "meeting_id": s.meeting_id,
            "segment_index": s.segment_index,
            "label": s.label,
            "score": s.score,
            "start_time": s.start_time,
            "end_time": s.end_time
        }
        for s in sentiments
    ]
