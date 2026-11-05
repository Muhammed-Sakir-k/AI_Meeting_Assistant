import os
import logging
import queue
import threading
import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.database.db import get_db, Meeting, Transcript
from backend.live_detection.live_session import live_session_manager
from backend.transcription.google_stt_engine import google_stt_engine
from backend.tasks.pipeline_tasks import process_meeting_pipeline_task, run_meeting_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()

# Active WebSocket connections list to help with cleanup
# session_id -> WebSocket
active_sockets: Dict[str, WebSocket] = {}

class AudioStreamIterator:
    def __init__(self):
        self.q = queue.Queue()
        self.closed = False

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                chunk = self.q.get(timeout=0.2)
                if chunk is None:
                    raise StopIteration
                return chunk
            except queue.Empty:
                if self.closed:
                    raise StopIteration
                continue

    def put(self, chunk):
        if not self.closed:
            self.q.put(chunk)

    def close(self):
        self.closed = True
        self.q.put(None)

@router.post("/live/start")
def start_live_meeting(
    title: str = Form(None),
    db: Session = Depends(get_db)
):
    """Starts a new live meeting session."""
    try:
        session_id = live_session_manager.start_session(title=title)
        meeting_id = live_session_manager.get_meeting_id(session_id)
        return {
            "status": "started",
            "session_id": session_id,
            "meeting_id": meeting_id,
            "message": "Live meeting session successfully started."
        }
    except Exception as e:
        logger.error(f"Error starting live meeting: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start live session: {str(e)}")

@router.post("/live/stop/{session_id}")
def stop_live_meeting(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Stops the live meeting session and triggers NLP analysis."""
    meeting_id = live_session_manager.get_meeting_id(session_id)
    if not meeting_id:
        raise HTTPException(status_code=404, detail="Active live session not found")

    try:
        # Finalize and write local file to disk
        meeting_id = live_session_manager.stop_session(session_id)
        
        # Clean up any residual active socket entries
        active_sockets.pop(session_id, None)

        meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Associated meeting record not found")

        # Trigger full pipeline analysis (transcription is already saved, but NLP, Summary, Reminders, Sentiments are needed)
        meeting.processing_status = "nlp_extraction"
        db.add(meeting)
        db.commit()

        # Dispatch pipeline downstream tasks via Celery or BackgroundTasks
        try:
            import redis
            from celery_worker import celery_app
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            r = redis.from_url(redis_url, socket_timeout=1.0)
            r.ping()
            
            # Check if Celery workers are active
            inspector = celery_app.control.inspect(timeout=1.0)
            active_workers = inspector.active()
            if not active_workers:
                raise Exception("No active Celery workers listening.")
                
            process_meeting_pipeline_task.delay(meeting_id, meeting.audio_path, meeting.title)
            logger.info(f"Dispatched downstream meeting pipeline via Celery for live meeting {meeting_id}")
        except Exception as celery_err:
            logger.warning(f"Celery dispatch failed/skipped: {celery_err}. Running in background thread.")
            # Run in a background thread
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, run_meeting_pipeline, meeting_id, meeting.audio_path, meeting.title)

        return {
            "status": "completed",
            "meeting_id": meeting_id,
            "message": "Live session stopped successfully. Analytics processing initiated."
        }
    except Exception as e:
        logger.error(f"Error stopping live meeting: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to finalize live session: {str(e)}")

@router.websocket("/ws/live/{session_id}")
async def websocket_live_stream(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time live streaming of meeting audio."""
    meeting_id = live_session_manager.get_meeting_id(session_id)
    if not meeting_id:
        await websocket.close(code=1008, reason="Invalid session ID")
        return

    await websocket.accept()
    active_sockets[session_id] = websocket
    logger.info(f"WebSocket client connected for live session {session_id}")

    # Check Google STT initialization
    stt_available = True
    try:
        google_stt_engine._initialize()
    except Exception as err:
        logger.warning(f"Google Speech-to-Text client failed to load: {err}. Fallback to Whisper active.")
        stt_available = False
        await websocket.send_json({
            "type": "info",
            "message": "Google STT offline. Local Whisper model fallback will transcribe upon meeting completion."
        })

    loop = asyncio.get_event_loop()
    audio_iterator = AudioStreamIterator()

    def run_stt_streaming():
        """Consumes audio iterator and sends transcripts back over WebSocket."""
        if not stt_available:
            return
            
        try:
            responses = google_stt_engine.transcribe_stream(
                audio_iterator, 
                sample_rate=16000, 
                language_code="en-US"
            )
            
            for response in responses:
                if not response.results:
                    continue
                result = response.results[0]
                if not result.alternatives:
                    continue
                alternative = result.alternatives[0]
                
                transcript = alternative.transcript
                confidence = alternative.confidence
                is_final = result.is_final
                
                # Send text segment to client
                msg = {
                    "type": "transcript",
                    "text": transcript,
                    "confidence": float(round(confidence, 2)),
                    "is_final": is_final
                }
                
                # Async-safe send message to client via event loop
                asyncio.run_coroutine_threadsafe(
                    websocket.send_json(msg),
                    loop
                )
                
                # If finalized, add segment to session database memory
                if is_final:
                    live_session_manager.add_transcript_segment(
                        session_id=session_id,
                        text=transcript,
                        confidence=confidence,
                        start_time=0.0,
                        end_time=0.0
                    )
        except Exception as e:
            logger.error(f"Google STT streaming thread encountered an error: {e}")
            asyncio.run_coroutine_threadsafe(
                websocket.send_json({
                    "type": "error",
                    "message": f"Google STT streaming error: {str(e)}. Fallback to Whisper on final save."
                }),
                loop
            )

    stt_thread = None
    if stt_available:
        stt_thread = threading.Thread(target=run_stt_streaming, daemon=True)
        stt_thread.start()

    try:
        while True:
            # Receive binary or text message
            data = await websocket.receive()
            if "bytes" in data:
                raw_bytes = data["bytes"]
                # Append audio to the session manager for final WAV generation
                live_session_manager.append_audio_chunk(session_id, raw_bytes)
                
                # If Google STT is running, pipe audio chunk to it
                if stt_available:
                    audio_iterator.put(raw_bytes)
            elif "text" in data:
                # Text frame for status or heartbeats
                payload = data["text"]
                if payload == "ping":
                    await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for live session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket processing error on session {session_id}: {e}")
    finally:
        # Clean up stream iterator and connections
        audio_iterator.close()
        active_sockets.pop(session_id, None)
        if stt_thread and stt_thread.is_alive():
            stt_thread.join(timeout=1.0)
