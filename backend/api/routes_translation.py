import logging
import json
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database.db import get_db, Translation, Meeting, Transcript, Summary
from backend.translation.translator import translator

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/languages")
def get_supported_languages():
    """Returns the list of supported translation target languages."""
    return translator.get_supported_languages()

@router.get("/translate/{meeting_id}")
def get_translation(
    meeting_id: int, 
    target_lang: str = Query(..., description="Target language code (e.g. hi, ml, ta)"),
    db: Session = Depends(get_db)
):
    """
    Returns the translation of the transcript and summary for the meeting.
    If it doesn't exist, performs translation synchronously.
    """
    # Verify meeting exists
    meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    source_lang = meeting.language or "en"
    
    # 1. Look up cached translation
    translations = db.query(Translation).filter(
        Translation.meeting_id == meeting_id,
        Translation.target_language == target_lang
    ).all()
    
    res = {
        "meeting_id": meeting_id,
        "source_language": source_lang,
        "target_language": target_lang,
        "translated_transcript": "",
        "translated_summary": ""
    }
    
    has_transcript = False
    has_summary = False
    
    for t in translations:
        if t.content_type == "transcript":
            res["translated_transcript"] = t.translated_text
            has_transcript = True
        elif t.content_type == "summary":
            res["translated_summary"] = t.translated_text
            has_summary = True
            
    # 2. Translate on-the-fly if not cached
    if not has_transcript:
        # Load original transcript text
        db_trans = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
        if db_trans:
            try:
                data = json.loads(db_trans.text)
                orig_text = data.get("text", "")
            except Exception:
                orig_text = db_trans.text or ""
                
            translated_text = translator.translate_text(orig_text, source_lang=source_lang, target_lang=target_lang)
            res["translated_transcript"] = translated_text
            
            # Cache it
            new_trans = Translation(
                meeting_id=meeting_id,
                source_language=source_lang,
                target_language=target_lang,
                content_type="transcript",
                original_text=orig_text,
                translated_text=translated_text
            )
            db.add(new_trans)
            db.commit()
            
    if not has_summary:
        # Load original summary
        db_summ = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
        if db_summ:
            orig_text = db_summ.summary_text or ""
            translated_text = translator.translate_text(orig_text, source_lang=source_lang, target_lang=target_lang)
            res["translated_summary"] = translated_text
            
            # Cache it
            new_summ = Translation(
                meeting_id=meeting_id,
                source_language=source_lang,
                target_language=target_lang,
                content_type="summary",
                original_text=orig_text,
                translated_text=translated_text
            )
            db.add(new_summ)
            db.commit()
            
    return res

def run_async_translation(meeting_id: int, target_lang: str):
    """Background helper to perform translation."""
    db = SessionLocal = None
    from backend.database.db import SessionLocal
    db = SessionLocal()
    try:
        meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        if not meeting:
            return
        source_lang = meeting.language or "en"
        
        # Translate transcript
        db_trans = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
        if db_trans:
            existing = db.query(Translation).filter(
                Translation.meeting_id == meeting_id,
                Translation.target_language == target_lang,
                Translation.content_type == "transcript"
            ).first()
            if not existing:
                try:
                    data = json.loads(db_trans.text)
                    orig_text = data.get("text", "")
                except Exception:
                    orig_text = db_trans.text or ""
                translated_text = translator.translate_text(orig_text, source_lang=source_lang, target_lang=target_lang)
                new_trans = Translation(
                    meeting_id=meeting_id,
                    source_language=source_lang,
                    target_language=target_lang,
                    content_type="transcript",
                    original_text=orig_text,
                    translated_text=translated_text
                )
                db.add(new_trans)
                
        # Translate summary
        db_summ = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
        if db_summ:
            existing = db.query(Translation).filter(
                Translation.meeting_id == meeting_id,
                Translation.target_language == target_lang,
                Translation.content_type == "summary"
            ).first()
            if not existing:
                orig_text = db_summ.summary_text or ""
                translated_text = translator.translate_text(orig_text, source_lang=source_lang, target_lang=target_lang)
                new_summ = Translation(
                    meeting_id=meeting_id,
                    source_language=source_lang,
                    target_language=target_lang,
                    content_type="summary",
                    original_text=orig_text,
                    translated_text=translated_text
                )
                db.add(new_summ)
                
        db.commit()
        logger.info(f"Async translation completed for meeting {meeting_id} to language {target_lang}")
    except Exception as e:
        logger.error(f"Async translation failed: {e}")
        db.rollback()
    finally:
        db.close()

@router.post("/translate/{meeting_id}")
def request_translation(
    meeting_id: int, 
    background_tasks: BackgroundTasks,
    target_lang: str = Query(..., description="Target language code"),
    db: Session = Depends(get_db)
):
    """Triggers asynchronous translation of the meeting contents."""
    meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    background_tasks.add_task(run_async_translation, meeting_id, target_lang)
    return {
        "status": "queued",
        "meeting_id": meeting_id,
        "target_language": target_lang,
        "message": f"Async translation to {target_lang} queued successfully."
    }
