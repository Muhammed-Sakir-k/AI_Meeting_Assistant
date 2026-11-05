import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.db import get_db, Question

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/questions/{meeting_id}")
def get_questions(meeting_id: int, db: Session = Depends(get_db)):
    """Returns detected questions (answered/unanswered) for a meeting."""
    questions = db.query(Question).filter(Question.meeting_id == meeting_id).all()
    return [
        {
            "question_id": q.question_id,
            "meeting_id": q.meeting_id,
            "question_text": q.question_text,
            "asked_at": q.asked_at,
            "status": q.status
        }
        for q in questions
    ]
