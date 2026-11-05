import os
import logging
from transformers import pipeline
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

PRIORITY_MODEL_NAME = os.getenv("PRIORITY_MODEL", "facebook/bart-large-mnli")
MODEL_DIR = os.getenv("MODEL_DIR", "models")

class PriorityDetector:
    def __init__(self):
        self.classifier = None
        self.initialized = False
        
    def _load_model(self):
        """Lazy load the zero-shot classifier model."""
        if self.initialized:
            return
            
        try:
            logger.info(f"Loading zero-shot priority classification model '{PRIORITY_MODEL_NAME}'...")
            import time
            start = time.time()
            self.classifier = pipeline(
                "zero-shot-classification",
                model=PRIORITY_MODEL_NAME,
                device=-1,  # CPU for reliability
                model_kwargs={"cache_dir": MODEL_DIR}
            )
            self.initialized = True
            logger.info(f"Priority classifier loaded successfully in {time.time() - start:.2f}s.")
        except Exception as e:
            logger.error(f"Failed to load priority zero-shot model: {e}. Fallback to keyword-based classification active.")
            self.classifier = None
            self.initialized = True  # Avoid retrying continuously on failures

    def detect_priority(self, text: str) -> str:
        """
        Detects action item priority: high, medium, or low.
        Uses keyword boosting + zero-shot classification.
        """
        self._load_model()
        
        text_lower = text.lower()
        
        # 1. Keyword Boosting to High Priority
        high_priority_keywords = ["asap", "critical", "deadline", "must", "immediately", "urgent", "instantly", "high priority"]
        for kw in high_priority_keywords:
            if kw in text_lower:
                return "high"
                
        # Low priority keywords
        low_priority_keywords = ["sometime", "low priority", "nice to have", "if possible", "backlog", "low-priority"]
        for kw in low_priority_keywords:
            if kw in text_lower:
                return "low"
                
        # 2. Zero-shot Classification fallback if model loaded successfully
        if self.classifier:
            try:
                candidate_labels = ["urgent important", "normal task", "low priority routine"]
                res = self.classifier(text, candidate_labels=candidate_labels)
                top_label = res["labels"][0]
                
                if top_label == "urgent important":
                    return "high"
                elif top_label == "low priority routine":
                    return "low"
                else:
                    return "medium"
            except Exception as e:
                logger.warning(f"Priority zero-shot model classification failed: {e}. Defaulting to medium.")
                
        return "medium"

priority_detector = PriorityDetector()
