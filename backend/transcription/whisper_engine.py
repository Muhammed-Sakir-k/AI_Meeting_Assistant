import os
import logging
import numpy as np
import whisper
import librosa
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

# Configuration
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "base")
DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
MODEL_DIR = os.getenv("MODEL_DIR", "models")

# Ensure models directory exists
os.makedirs(MODEL_DIR, exist_ok=True)

class WhisperTranscriber:
    def __init__(self):
        self.model = None
        
    def _load_model(self):
        """Lazy load the Whisper model to save startup time."""
        if self.model is None:
            import time
            start_time = time.time()
            logger.info(f"Loading Whisper model '{WHISPER_MODEL_NAME}' on {DEVICE}...")
            # Set fp16 to False if running on CPU to avoid warnings
            self.model = whisper.load_model(
                WHISPER_MODEL_NAME, 
                device=DEVICE, 
                download_root=MODEL_DIR
            )
            load_time = time.time() - start_time
            logger.info(f"Whisper model loaded successfully in {load_time:.2f} seconds.")
            
    def calculate_confidence(self, avg_logprob, no_speech_prob):
        """Converts average logprob to a confidence score between 0.0 and 1.0."""
        # avg_logprob is negative (0 is perfect, -1.5 is poor)
        # exp(avg_logprob) maps to 0 to 1
        confidence = np.exp(avg_logprob)
        # Penalize if there's high probability of no speech
        if no_speech_prob > 0.5:
            confidence *= (1.0 - no_speech_prob)
        return float(round(confidence, 2))
        
    def transcribe(self, audio_path: str, retry_count=2, backoff=2.0) -> dict:
        """
        Transcribes the given audio file using Whisper.
        Retries on failure with exponential backoff.
        """
        self._load_model()
        
        for attempt in range(retry_count + 1):
            try:
                logger.info(f"Transcribing {audio_path} (Attempt {attempt + 1})...")
                
                # Transcribe with language detection enabled automatically
                fp16 = True if DEVICE == "cuda" else False
                logger.info(f"Loading audio array for {audio_path}...")
                audio_array, _ = librosa.load(audio_path, sr=16000, mono=True)
                
                # Run whisper model
                result = self.model.transcribe(audio_array, fp16=fp16)
                
                segments = []
                total_confidence = 0.0
                detected_lang = result.get("language", "en")
                
                prev_end = 0.0
                current_speaker = "Speaker 1"
                
                for seg in result.get("segments", []):
                    avg_logprob = seg.get("avg_logprob", 0.0)
                    no_speech_prob = seg.get("no_speech_prob", 0.0)
                    
                    confidence = self.calculate_confidence(avg_logprob, no_speech_prob)
                    total_confidence += confidence
                    
                    # Low-confidence threshold specified in prompt: < 0.75
                    is_low = confidence < 0.75
                    
                    start_time = round(seg.get("start", 0.0), 2)
                    end_time = round(seg.get("end", 0.0), 2)
                    
                    # Heuristic: If silent gap is greater than 1.8 seconds, toggle speaker
                    if start_time - prev_end > 1.8:
                        current_speaker = "Speaker 2" if current_speaker == "Speaker 1" else "Speaker 1"
                    prev_end = end_time
                    
                    segments.append({
                        "id": seg.get("id"),
                        "start": start_time,
                        "end": end_time,
                        "text": seg.get("text", "").strip(),
                        "confidence": confidence,
                        "is_low_confidence": is_low,
                        "speaker": current_speaker
                    })
                
                avg_confidence = 0.0
                if segments:
                    avg_confidence = round(total_confidence / len(segments), 2)
                    
                raw_text = result.get("text", "").strip()
                
                logger.info(f"Transcription completed. Language: {detected_lang}, Avg Confidence: {avg_confidence}")
                
                return {
                    "text": raw_text,
                    "language": detected_lang,
                    "confidence_score": str(avg_confidence),
                    "segments": segments
                }
                
            except Exception as e:
                logger.error(f"Error during Whisper transcription on attempt {attempt + 1}: {e}")
                if attempt < retry_count:
                    import time
                    sleep_time = backoff * (2 ** attempt)
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    raise e
                    
transcriber = WhisperTranscriber()
