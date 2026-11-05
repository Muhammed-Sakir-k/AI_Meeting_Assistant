import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.db import get_db, Summary

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/summary/{meeting_id}")
def get_summary(meeting_id: int, db: Session = Depends(get_db)):
    """Returns the detailed summary, executive summary, and key decisions."""
    summary = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found for this meeting")
        
    try:
        decisions = json.loads(summary.key_decisions)
    except Exception:
        decisions = [summary.key_decisions] if summary.key_decisions else []
        
    return {
        "summary_id": summary.summary_id,
        "meeting_id": summary.meeting_id,
        "summary_text": summary.summary_text,
        "executive_summary": summary.executive_summary or summary.summary_text[:200],
        "key_decisions": decisions
    }
