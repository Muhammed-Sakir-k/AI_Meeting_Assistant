import os
import logging
from transformers import pipeline
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

SENTIMENT_MODEL_NAME = os.getenv("SENTIMENT_MODEL", "lxyuan/distilbert-base-multilingual-cased-sentiments-student")
MODEL_DIR = os.getenv("MODEL_DIR", "models")

class SentimentAnalyzer:
    def __init__(self):
        self.classifier = None
        self.initialized = False
        
    def _load_model(self):
        """Lazy loads Hugging Face sentiment pipeline."""
        if self.initialized:
            return
            
        try:
            logger.info(f"Loading sentiment analysis model '{SENTIMENT_MODEL_NAME}'...")
            import time
            start = time.time()
            self.classifier = pipeline(
                "sentiment-analysis",
                model=SENTIMENT_MODEL_NAME,
                device=-1,  # CPU for reliability
                model_kwargs={"cache_dir": MODEL_DIR}
            )
            self.initialized = True
            logger.info(f"Sentiment analyzer loaded successfully in {time.time() - start:.2f}s.")
        except Exception as e:
            logger.error(f"Failed to load sentiment model: {e}. Fallback sentiment classification active.")
            self.classifier = None
            self.initialized = True

    def analyze_text(self, text: str) -> dict:
        """
        Analyzes sentiment of text segment.
        Returns: {"label": "Positive"/"Neutral"/"Negative", "score": float}
        """
        self._load_model()
        
        # Heuristic fallback if model not loaded
        if not self.classifier:
            return self._fallback_analyze(text)
            
        try:
            res = self.classifier(text)[0]
            # lxyuan/distilbert-base-multilingual-cased-sentiments-student outputs positive/neutral/negative
            label = res["label"].lower()
            score = float(res["score"])
            
            # Map labels cleanly
            if "positive" in label:
                clean_label = "Positive"
            elif "negative" in label:
                clean_label = "Negative"
            else:
                clean_label = "Neutral"
                
            return {
                "label": clean_label,
                "score": score
            }
        except Exception as e:
            logger.warning(f"Sentiment pipeline failed for: '{text[:30]}...'. Error: {e}. Using fallback.")
            return self._fallback_analyze(text)

    def _fallback_analyze(self, text: str) -> dict:
        """Rule-based lexicon fallback for sentiment analysis."""
        text_lower = text.lower()
        
        # Lexicons
        positive_words = ["good", "great", "excellent", "awesome", "agree", "perfect", "resolved", "solved", "happy", "yes", "achieved", "completed", "success"]
        negative_words = ["bad", "worst", "error", "fail", "failed", "incorrect", "disagree", "delay", "issue", "problem", "difficult", "no", "risk", "critical"]
        
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            return {"label": "Neutral", "score": 0.5}
            
        score = max(pos_count, neg_count) / total
        
        if pos_count > neg_count:
            return {"label": "Positive", "score": float(round(score, 2))}
        elif neg_count > pos_count:
            return {"label": "Negative", "score": float(round(score, 2))}
        else:
            return {"label": "Neutral", "score": 0.5}

    def aggregate_meeting_sentiment(self, segments_sentiment: list) -> dict:
        """
        Computes aggregate meeting-level sentiment statistics.
        segments_sentiment is a list of {"label": str, "score": float}
        """
        if not segments_sentiment:
            return {"overall": "Neutral", "positive_pct": 0, "neutral_pct": 100, "negative_pct": 0}
            
        pos = sum(1 for s in segments_sentiment if s["label"] == "Positive")
        neu = sum(1 for s in segments_sentiment if s["label"] == "Neutral")
        neg = sum(1 for s in segments_sentiment if s["label"] == "Negative")
        
        total = len(segments_sentiment)
        
        pos_pct = round((pos / total) * 100, 1)
        neu_pct = round((neu / total) * 100, 1)
        neg_pct = round((neg / total) * 100, 1)
        
        # Calculate overall tone
        if pos > neg and pos >= neu:
            overall = "Positive"
        elif neg > pos and neg >= neu:
            overall = "Negative"
        else:
            overall = "Neutral"
            
        return {
            "overall": overall,
            "positive_pct": pos_pct,
            "neutral_pct": neu_pct,
            "negative_pct": neg_pct
        }

sentiment_analyzer = SentimentAnalyzer()
