import logging
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database.db import get_db, Meeting, Transcript, Summary, ActionItem
from backend.api.report_utils import generate_pdf_report, generate_docx_report
from backend.analytics.analytics_service import analytics_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/report/{meeting_id}")
def get_report(
    meeting_id: int, 
    format: str = Query("pdf", description="Format type: pdf or docx"), 
    db: Session = Depends(get_db)
):
    """Generates and streams a downloadable PDF or DOCX report."""
    meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    summary = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
    actions = db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).all()
    
    clean_title = (meeting.title or "meeting_report").replace(" ", "_").lower()
    format_lower = format.lower()
    
    if format_lower == "pdf":
        buffer = generate_pdf_report(meeting, transcript, summary, actions)
        filename = f"{clean_title}_report.pdf"
        media_type = "application/pdf"
    elif format_lower == "docx":
        buffer = generate_docx_report(meeting, transcript, summary, actions)
        filename = f"{clean_title}_report.docx"
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        raise HTTPException(status_code=400, detail="Invalid report format. Allowed formats: pdf, docx")
        
    # Log the export event to analytics
    analytics_service.log_event(
        meeting_id=meeting_id,
        event_type=f"export_{format_lower}",
        event_data={"format": format_lower}
    )
        
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
