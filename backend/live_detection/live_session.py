import os
import uuid
import logging
from datetime import datetime

# Database imports
from backend.database.db import SessionLocal
from backend.database.models import Meeting, Transcript

logger = logging.getLogger(__name__)

class LiveSessionManager:
    def __init__(self):
        # Maps session_id -> {
        #   "meeting_id": int,
        #   "transcript_segments": list,
        #   "start_time": datetime,
        #   "audio_data": bytearray
        # }
        self.active_sessions = {}
        
    def start_session(self, title: str = None) -> str:
        """
        Starts a new live meeting session in the DB and returns a session_id.
        """
        db = SessionLocal()
        session_id = str(uuid.uuid4())
        
        try:
            meeting_title = title if title else f"Live Meeting - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            meeting = Meeting(
                title=meeting_title,
                date=datetime.utcnow(),
                processing_status="processing",
                language="en" # default, updated by live transcriber
            )
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
            
            self.active_sessions[session_id] = {
                "meeting_id": meeting.meeting_id,
                "transcript_segments": [],
                "start_time": datetime.utcnow(),
                "audio_data": bytearray()
            }
            logger.info(f"Live session {session_id} started (Meeting ID: {meeting.meeting_id})")
            return session_id
        except Exception as e:
            logger.error(f"Failed to start live session: {e}")
            db.rollback()
            raise e
        finally:
            db.close()

    def get_meeting_id(self, session_id: str) -> int:
        """Returns the meeting_id associated with a session."""
        session = self.active_sessions.get(session_id)
        return session["meeting_id"] if session else None

    def append_audio_chunk(self, session_id: str, chunk: bytes):
        """Accumulates incoming raw PCM audio bytes."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["audio_data"].extend(chunk)

    def add_transcript_segment(self, session_id: str, text: str, confidence: float, start_time: float, end_time: float):
        """Appends a finalized transcript segment to the session memory."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["transcript_segments"].append({
                "text": text,
                "confidence": confidence,
                "start": start_time,
                "end": end_time
            })

    def stop_session(self, session_id: str) -> int:
        """
        Stops live detection, saves accumulated transcript and audio, and releases session memory.
        Returns the meeting_id.
        """
        session = self.active_sessions.pop(session_id, None)
        if not session:
            logger.warning(f"Attempted to stop non-existent live session: {session_id}")
            return None
            
        meeting_id = session["meeting_id"]
        db = SessionLocal()
        try:
            # 1. Update Meeting Status and Duration
            meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
            if meeting:
                end_time = datetime.utcnow()
                duration = int((end_time - session["start_time"]).total_seconds())
                meeting.duration_seconds = duration
                meeting.processing_status = "completed"
                
                # Write audio file of the session to disk
                uploads_dir = os.path.abspath("uploads")
                os.makedirs(uploads_dir, exist_ok=True)
                audio_path = os.path.join(uploads_dir, f"live_{meeting_id}.wav")
                
                # Write raw PCM audio as standard mono WAV (16kHz PCM 16-bit)
                raw_audio = bytes(session["audio_data"])
                if raw_audio:
                    import wave
                    with wave.open(audio_path, 'wb') as wav_file:
                        wav_file.setnchannels(1)
                        wav_file.setsampwidth(2) # 16-bit
                        wav_file.setframerate(16000)
                        wav_file.writeframes(raw_audio)
                    meeting.audio_path = audio_path
                    
                db.add(meeting)
                
            # 2. Save Transcript
            segments = session["transcript_segments"]
            full_text = " ".join([seg["text"] for seg in segments]).strip()
            
            # Simple average confidence
            confs = [seg["confidence"] for seg in segments]
            avg_conf = str(round(sum(confs) / len(confs), 2)) if confs else "1.0"
            
            import json
            transcript_data = {
                "text": full_text,
                "segments": segments
            }
            
            db_transcript = Transcript(
                meeting_id=meeting_id,
                text=json.dumps(transcript_data),
                language="en", # Default, updateable
                confidence_score=avg_conf
            )
            db.add(db_transcript)
            
            db.commit()
            logger.info(f"Live session {session_id} finalized and saved to DB (Meeting ID: {meeting_id})")
            
            # Trigger subsequent intelligence pipeline asynchronously if desired
            # But for live sessions, basic save of transcript is immediate.
            # We can kick off the rest of the extraction stages (NLP, summary, sentiments)
            # using Celery or FastAPI BackgroundTasks right now!
            
            return meeting_id
        except Exception as e:
            logger.error(f"Error stopping live session {session_id}: {e}")
            db.rollback()
            raise e
        finally:
            db.close()

live_session_manager = LiveSessionManager()
