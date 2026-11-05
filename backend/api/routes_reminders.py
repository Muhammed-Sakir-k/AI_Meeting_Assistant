import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.db import get_db, Reminder
from backend.reminders.reminder_service import reminder_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/reminders/{meeting_id}")
def get_reminders(meeting_id: int, db: Session = Depends(get_db)):
    """Returns all reminders associated with a meeting."""
    reminders = db.query(Reminder).filter(Reminder.meeting_id == meeting_id).all()
    return [
        {
            "reminder_id": r.reminder_id,
            "meeting_id": r.meeting_id,
            "action_id": r.action_id,
            "owner_name": r.owner_name,
            "reminder_text": r.reminder_text,
            "scheduled_at": r.scheduled_at.isoformat() if r.scheduled_at else None,
            "status": r.status
        }
        for r in reminders
    ]

@router.post("/reminders/{meeting_id}/dismiss/{reminder_id}")
def dismiss_reminder(meeting_id: int, reminder_id: int, db: Session = Depends(get_db)):
    """Dismisses a reminder."""
    success = reminder_service.dismiss_reminder(reminder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "success", "message": f"Reminder {reminder_id} dismissed."}

@router.post("/reminders/{meeting_id}/resend/{reminder_id}")
def resend_reminder(meeting_id: int, reminder_id: int, db: Session = Depends(get_db)):
    """Manually resends/re-triggers a reminder."""
    success = reminder_service.resend_reminder(reminder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "success", "message": f"Reminder {reminder_id} resent."}
