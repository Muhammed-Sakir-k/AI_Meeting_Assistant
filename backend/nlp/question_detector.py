import os
import logging
import re
from transformers import pipeline
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

# We can use a zero-shot model or a smaller BERT text classifier for questions
QUESTION_MODEL_NAME = os.getenv("QUESTION_MODEL", "typeform/distilbert-base-uncased-mnli")
MODEL_DIR = os.getenv("MODEL_DIR", "models")

class QuestionDetector:
    def __init__(self):
        self.classifier = None
        self.initialized = False
        
    def _load_model(self):
        """Lazy loads BERT model for sentence classification."""
        if self.initialized:
            return
            
        try:
            logger.info(f"Loading question detection model '{QUESTION_MODEL_NAME}'...")
            import time
            start = time.time()
            self.classifier = pipeline(
                "zero-shot-classification",
                model=QUESTION_MODEL_NAME,
                device=-1,
                model_kwargs={"cache_dir": MODEL_DIR}
            )
            self.initialized = True
            logger.info(f"Question classifier model loaded in {time.time() - start:.2f}s.")
        except Exception as e:
            logger.error(f"Failed to load question classification model: {e}. Rule-based question detection active.")
            self.classifier = None
            self.initialized = True

    def is_question(self, text: str) -> bool:
        """
        Determines if a sentence is a question.
        Uses robust rule-based checks (question marks and Wh- starters).
        """
        text_stripped = text.strip()
        if not text_stripped:
            return False
            
        # 1. Rule 1: Ends with or contains a question mark (highly reliable in transcribed speech)
        if "?" in text_stripped:
            return True
            
        # 2. Rule 2: Wh- interrogative starters (who, what, where, when, why, how, etc.)
        wh_starters = {"who", "what", "where", "when", "why", "how", "which", "whose", "whom"}
        words = re.findall(r'\b\w+\b', text_stripped.lower())
        if words and words[0] in wh_starters:
            # Guard against long statements that start with how/what (e.g. "How we proceed is up to us")
            if len(words) < 15:
                return True
            
        return False

    def detect_questions(self, segments: list) -> list:
        """
        Processes a list of transcribed meeting segments.
        Extracts questions and applies the answered heuristic.
        
        Heuristic: If a question segment is followed by a non-question statement
        within the next 3 segments, mark as 'answered'.
        
        segments is a list of dicts: {"text": str, "start": float, "end": float}
        """
        detected = []
        n = len(segments)
        
        for idx, seg in enumerate(segments):
            text = seg.get("text", "")
            if self.is_question(text):
                # Apply heuristic to check if answered
                status = "unanswered"
                
                # Look at the next 3 segments
                for check_idx in range(idx + 1, min(idx + 4, n)):
                    next_text = segments[check_idx].get("text", "")
                    if not self.is_question(next_text) and len(next_text.split()) > 3:
                        status = "answered"
                        break
                        
                detected.append({
                    "question_text": text,
                    "asked_at": seg.get("start", 0.0),
                    "status": status
                })
                
        return detected

question_detector = QuestionDetector()
