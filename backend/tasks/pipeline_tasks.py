import os
import json
import logging
from celery_worker import celery_app
from dotenv import load_dotenv

# Database imports
from backend.database.db import SessionLocal
from backend.database.models import (
    Meeting, Transcript, ActionItem, Summary, Sentiment, Question
)

# Pipeline engines imports
from backend.preprocessing.audio_processor import preprocess_audio, split_audio_into_chunks
from backend.transcription.whisper_engine import transcriber
from backend.nlp.action_extractor import action_extractor
from backend.nlp.question_detector import question_detector
from backend.sentiment.sentiment_analyzer import sentiment_analyzer
from backend.summarization.summarizer import summarizer
from backend.reminders.reminder_service import reminder_service

logger = logging.getLogger(__name__)
load_dotenv()

def resolve_speaker_names(segments, nlp_model):
    import re
    # Group segments by speaker
    speaker_texts = {}
    for seg in segments:
        spk = seg.get("speaker")
        if spk not in speaker_texts:
            speaker_texts[spk] = []
        speaker_texts[spk].append(seg.get("text", ""))
        
    # Find names for each speaker
    speaker_name_map = {}
    patterns = [
        r"\bmy name is ([A-Z][a-z]+)\b",
        r"\bi am ([A-Z][a-z]+)\b",
        r"\bi'm ([A-Z][a-z]+)\b",
        r"\bthis is ([A-Z][a-z]+)\b",
        r"\b([A-Z][a-z]+) here\b"
    ]
    lower_patterns = [
        r"\bmy name is ([a-z]+)\b",
        r"\bi am ([a-z]+)\b",
        r"\bi'm ([a-z]+)\b",
        r"\bthis is ([a-z]+)\b",
        r"\b([a-z]+) here\b"
    ]
    
    for spk, texts in speaker_texts.items():
        detected_name = None
        for text in texts:
            text_clean = text.strip()
            # Check capitalized patterns
            for pattern in patterns:
                matches = re.findall(pattern, text_clean)
                if matches:
                    detected_name = matches[0]
                    break
            if detected_name:
                break
                
            # Check lower-case patterns
            for pattern in lower_patterns:
                matches = re.findall(pattern, text_clean, re.IGNORECASE)
                if matches:
                    detected_name = matches[0].capitalize()
                    break
            if detected_name:
                break
                
            # Check spaCy PERSON entity
            if nlp_model:
                doc = nlp_model(text)
                for ent in doc.ents:
                    if ent.label_ == "PERSON" and len(ent.text.split()) <= 2:
                        detected_name = ent.text
                        break
            if detected_name:
                break
                
        if detected_name:
            speaker_name_map[spk] = detected_name
            logger.info(f"Resolved speaker '{spk}' to real name: '{detected_name}'")
            
    # Update the speaker label in all segments
    for seg in segments:
        spk = seg.get("speaker")
        if spk in speaker_name_map:
            seg["speaker"] = speaker_name_map[spk]

# Utility to update status in DB
def update_meeting_status(db, meeting_id: int, status: str):
    try:
        meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        if meeting:
            meeting.processing_status = status
            db.add(meeting)
            db.commit()
            logger.info(f"Updated meeting {meeting_id} status in DB to: {status}")
    except Exception as e:
        logger.error(f"Failed to update meeting status: {e}")
        db.rollback()

def run_meeting_pipeline(meeting_id: int, file_path: str, title: str):
    """
    Main processing pipeline logic.
    Can be run synchronously in Celery task, or on thread via FastAPI BackgroundTasks.
    """
    db = SessionLocal()
    try:
        # 1. Preprocessing Stage
        update_meeting_status(db, meeting_id, "preprocessing")
        logger.info(f"Preprocessing audio: {file_path}")
        uploads_dir = os.path.dirname(file_path)
        preprocessed_path = preprocess_audio(file_path, uploads_dir)
        
        # Calculate meeting duration based on preprocessed audio
        import librosa
        duration_seconds = int(librosa.get_duration(path=preprocessed_path))
        
        # Update meeting metadata
        meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        if meeting:
            meeting.duration_seconds = duration_seconds
            db.add(meeting)
            db.commit()
            
        # 2. Transcription Stage
        update_meeting_status(db, meeting_id, "transcribing")
        logger.info(f"Transcribing audio: {preprocessed_path}")
        
        # Audio chunking for Whisper (ordered reassembly) if long file
        chunks = split_audio_into_chunks(preprocessed_path)
        
        segments = []
        full_text_list = []
        detected_lang = "en"
        confidence_scores = []
        
        seg_idx = 0
        for chunk_idx, chunk_path in enumerate(chunks):
            trans_res = transcriber.transcribe(chunk_path)
            detected_lang = trans_res.get("language", "en")
            confidence_scores.append(float(trans_res.get("confidence_score", "1.0")))
            full_text_list.append(trans_res.get("text", ""))
            
            # Offset segment timestamps based on chunk index
            time_offset = (chunk_idx * 600000) / 1000  # 10 minutes in seconds
            for seg in trans_res.get("segments", []):
                segments.append({
                    "id": seg.get("id"),
                    "start": seg.get("start", 0.0) + time_offset,
                    "end": seg.get("end", 0.0) + time_offset,
                    "text": seg.get("text", ""),
                    "confidence": seg.get("confidence", 1.0),
                    "is_low_confidence": seg.get("is_low_confidence", False),
                    "speaker": seg.get("speaker", "Speaker 1")
                })
                
            # Clean up intermediate chunk file
            if len(chunks) > 1 and os.path.exists(chunk_path):
                os.remove(chunk_path)
                
        raw_text = " ".join(full_text_list).strip()
        avg_confidence = str(round(sum(confidence_scores) / len(confidence_scores), 2)) if confidence_scores else "1.0"
        
        # Resolve speaker names to real names if mentioned in text
        try:
            action_extractor._load_models()
            resolve_speaker_names(segments, action_extractor.nlp)
        except Exception as spk_err:
            logger.warning(f"Failed to resolve speaker names: {spk_err}")
        
        # Update meeting metadata language
        meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        if meeting:
            meeting.language = detected_lang
            db.add(meeting)
            db.commit()
            
        # Save transcript
        transcript_data = {
            "text": raw_text,
            "segments": segments
        }
        db_transcript = Transcript(
            meeting_id=meeting_id,
            text=json.dumps(transcript_data),
            language=detected_lang,
            confidence_score=avg_confidence
        )
        db.add(db_transcript)
        db.commit()
        
        # 3. Sentiment Analysis Stage
        # Run per-segment sentiment analysis
        for idx, seg in enumerate(segments):
            seg_text = seg.get("text", "")
            if len(seg_text.split()) > 2:
                analysis = sentiment_analyzer.analyze_text(seg_text)
                db_sentiment = Sentiment(
                    meeting_id=meeting_id,
                    segment_index=idx,
                    label=analysis["label"],
                    score=analysis["score"],
                    start_time=seg.get("start", 0.0),
                    end_time=seg.get("end", 0.0)
                )
                db.add(db_sentiment)
        db.commit()
        
        # 4. Question Detection Stage
        detected_qs = question_detector.detect_questions(segments)
        for q in detected_qs:
            db_q = Question(
                meeting_id=meeting_id,
                question_text=q["question_text"],
                asked_at=q["asked_at"],
                status=q["status"]
            )
            db.add(db_q)
        db.commit()
        
        # 5. NLP Extraction Stage (Action items, decisions, priorities)
        update_meeting_status(db, meeting_id, "nlp_extraction")
        action_items, decisions = action_extractor.process_transcript(raw_text)
        
        for item in action_items:
            db_action = ActionItem(
                meeting_id=meeting_id,
                owner=item["owner"],
                task=item["task"],
                deadline=item["deadline"],
                priority=item["priority"],
                status="pending"
            )
            db.add(db_action)
        db.commit()
        
        # 6. Summarization Stage (Detailed, Executive summaries)
        update_meeting_status(db, meeting_id, "summarizing")
        detailed_summary = summarizer.summarize(raw_text)
        executive_summary = summarizer.generate_executive_summary(detailed_summary)
        
        db_summary = Summary(
            meeting_id=meeting_id,
            summary_text=detailed_summary,
            key_decisions=json.dumps(decisions),
            executive_summary=executive_summary
        )
        db.add(db_summary)
        db.commit()
        
        # 7. Generate Action Reminders
        reminder_service.create_reminders_for_meeting(meeting_id)
        
        # Complete
        update_meeting_status(db, meeting_id, "completed")
        logger.info(f"Meeting pipeline completed successfully for meeting {meeting_id}")
        
        # Clean up preprocessed file
        if os.path.exists(preprocessed_path) and preprocessed_path != file_path:
            os.remove(preprocessed_path)
            
    except Exception as e:
        logger.error(f"Error executing meeting pipeline for meeting {meeting_id}: {e}", exc_info=True)
        update_meeting_status(db, meeting_id, "failed")
        db.rollback()
    finally:
        db.close()

# Celery Task Wrapper
@celery_app.task(name="process_meeting_pipeline_task")
def process_meeting_pipeline_task(meeting_id: int, file_path: str, title: str):
    logger.info(f"Celery task triggered for meeting {meeting_id}")
    run_meeting_pipeline(meeting_id, file_path, title)
