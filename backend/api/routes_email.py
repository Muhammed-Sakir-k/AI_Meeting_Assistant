import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.database.db import get_db, EmailLog
from backend.email_gen.email_service import email_service
from backend.analytics.analytics_service import analytics_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/email/draft/{meeting_id}")
def get_email_draft(
    meeting_id: int, 
    type: str = Query("mom", description="Draft type: mom, action_assignment, followup"),
    db: Session = Depends(get_db)
):
    """Generates an email draft for the meeting summary or action assignments."""
    if type not in ["mom", "action_assignment", "followup"]:
        raise HTTPException(status_code=400, detail="Invalid email type. Allowed: mom, action_assignment, followup")
        
    try:
        draft = email_service.generate_draft(meeting_id, email_type=type)
        return draft
    except Exception as e:
        logger.error(f"Error generating email draft: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate email draft: {str(e)}")

@router.post("/email/send/{meeting_id}")
def send_email(
    meeting_id: int, 
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Sends the composed email to the recipient list and logs the status."""
    recipient = payload.get("recipient")
    subject = payload.get("subject")
    body = payload.get("body")
    email_type = payload.get("email_type", "mom")
    
    if not recipient or not subject or not body:
        raise HTTPException(status_code=400, detail="Missing required email fields (recipient, subject, body)")
        
    # Log analytics event
    analytics_service.log_event(meeting_id, "send_email", {"recipient": recipient, "type": email_type})
    
    success = email_service.send_email(meeting_id, recipient, subject, body, email_type=email_type)
    if not success:
        raise HTTPException(status_code=500, detail="Email delivery failed. Saved in logs as failed.")
        
    return {"status": "success", "message": "Email sent successfully."}
