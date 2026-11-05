import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.database.db import get_db, ActionItem

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/actions/{meeting_id}")
def get_actions(meeting_id: int, db: Session = Depends(get_db)):
    """Returns all action items for a meeting."""
    actions = db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).all()
    return [
        {
            "action_id": item.action_id,
            "meeting_id": item.meeting_id,
            "owner": item.owner,
            "task": item.task,
            "deadline": item.deadline,
            "priority": item.priority,
            "status": item.status
        }
        for item in actions
    ]

@router.patch("/actions/{meeting_id}/{action_id}")
def update_action_status(
    meeting_id: int, 
    action_id: int, 
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Updates the status of a specific action item (e.g. pending/done)."""
    status = payload.get("status")
    if not status or status not in ["pending", "in_progress", "done"]:
        raise HTTPException(status_code=400, detail="Invalid status value. Allowed: pending, in_progress, done")
        
    action = db.query(ActionItem).filter(
        ActionItem.meeting_id == meeting_id,
        ActionItem.action_id == action_id
    ).first()
    
    if not action:
        raise HTTPException(status_code=404, detail="Action item not found")
        
    action.status = status
    db.commit()
    db.refresh(action)
    
    return {
        "status": "success",
        "action_id": action.action_id,
        "new_status": action.status
    }
