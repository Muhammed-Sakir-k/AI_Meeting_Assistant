import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.analytics.analytics_service import analytics_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/analytics/aggregate")
def get_aggregate_analytics():
    """Returns aggregated analytics across all meetings in the system."""
    try:
        data = analytics_service.get_aggregate_analytics()
        return data
    except Exception as e:
        logger.error(f"Error fetching aggregate analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compile aggregate analytics: {str(e)}")

@router.get("/analytics/{meeting_id}")
def get_meeting_analytics(meeting_id: int):
    """Returns analytics details for a single meeting."""
    try:
        data = analytics_service.get_meeting_analytics(meeting_id)
        if not data:
            raise HTTPException(status_code=404, detail="Analytics data not found or meeting doesn't exist.")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching meeting analytics for meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compile meeting analytics: {str(e)}")
