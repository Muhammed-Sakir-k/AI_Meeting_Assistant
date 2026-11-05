import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.database.db import get_db
from backend.voice_commands.command_router import command_router
from backend.analytics.analytics_service import analytics_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/voice-command")
def process_voice_command(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Receives voice command text from frontend, routes it to the command router,
    logs the event to analytics, and returns the action details.
    """
    command_str = payload.get("command")
    meeting_id = payload.get("meeting_id")
    
    if not command_str:
        raise HTTPException(status_code=400, detail="Missing required field 'command'")
        
    try:
        # Route command
        action_res = command_router.route_command(command_str)
        
        # Log to analytics if meeting_id is provided
        if meeting_id:
            analytics_service.log_event(
                meeting_id=meeting_id,
                event_type="voice_cmd",
                event_data={"command": command_str, "action_routed": action_res.get("action")}
            )
            
        return action_res
    except Exception as e:
        logger.error(f"Error routing voice command '{command_str}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to route voice command: {str(e)}")
