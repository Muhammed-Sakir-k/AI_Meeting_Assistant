import os
import logging
from transformers import pipeline
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

SUMMARIZATION_MODEL_NAME = os.getenv("SUMMARIZATION_MODEL", "sshleifer/distilbart-cnn-12-6")
MODEL_DIR = os.getenv("MODEL_DIR", "models")

class TranscriptSummarizer:
    def __init__(self):
        self.summarizer = None
        self.initialized = False
        
    def _load_model(self):
        """Lazy loads the Hugging Face summarization pipeline."""
        if self.initialized:
            return
            
        try:
            logger.info(f"Loading summarization model '{SUMMARIZATION_MODEL_NAME}'...")
            import time
            start = time.time()
            self.summarizer = pipeline(
                "summarization",
                model=SUMMARIZATION_MODEL_NAME,
                device=-1,  # CPU for reliability
                model_kwargs={"cache_dir": MODEL_DIR}
            )
            self.initialized = True
            logger.info(f"Summarization model loaded successfully in {time.time() - start:.2f}s.")
        except Exception as e:
            logger.error(f"Failed to load summarization model: {e}. Fallback extractive summarization active.")
            self.summarizer = None
            self.initialized = True

    def _extractive_fallback(self, text: str, max_sentences=4) -> str:
        """Fallback extractive summary which extracts key sentences."""
        sentences = [s.strip() for s in text.replace("\n", ". ").split(".") if len(s.strip()) > 15]
        if not sentences:
            return text
            
        num_sentences = len(sentences)
        selected = []
        if num_sentences <= max_sentences:
            selected = sentences
        else:
            selected.append(sentences[0])
            selected.append(sentences[1])
            # Add middle sentence
            selected.append(sentences[num_sentences // 2])
            # Add final sentence
            selected.append(sentences[-1])
            
        return ". ".join(selected) + "."

    def summarize(self, text: str) -> str:
        """
        Summarizes long transcripts by chunking them to fit model token limits.
        Produces a detailed summary (main paragraph version).
        """
        if not text or not text.strip():
            return "No content available to summarize."
            
        self._load_model()
        
        if not self.summarizer:
            logger.warning("Summarizer model not loaded. Using extractive fallback.")
            return self._extractive_fallback(text, max_sentences=6)
            
        try:
            words = text.split()
            chunk_size = 600
            chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
            
            logger.info(f"Splitting transcript into {len(chunks)} chunk(s) for detailed summarization...")
            summaries = []
            
            for idx, chunk in enumerate(chunks):
                chunk_word_count = len(chunk.split())
                if chunk_word_count < 30:
                    continue
                    
                max_len = min(150, int(chunk_word_count * 0.6))
                min_len = min(30, int(chunk_word_count * 0.2))
                
                if max_len <= min_len:
                    max_len = min_len + 10
                    
                logger.info(f"Summarizing chunk {idx + 1}/{len(chunks)} ({chunk_word_count} words)...")
                
                res = self.summarizer(
                    chunk, 
                    max_length=max_len, 
                    min_length=min_len, 
                    do_sample=False
                )
                summary_text = res[0]["summary_text"].strip()
                summaries.append(summary_text)
                
            if not summaries:
                return self._extractive_fallback(text, max_sentences=6)
                
            final_summary = "\n\n".join(summaries)
            logger.info("Detailed summary generation completed.")
            return final_summary
            
        except Exception as e:
            logger.error(f"Error in summarization pipeline: {e}. Falling back to extractive summary.")
            return self._extractive_fallback(text, max_sentences=6)

    def generate_executive_summary(self, detailed_text: str) -> str:
        """
        Generates a concise 3-5 sentence executive summary based on the detailed summary.
        """
        if not detailed_text or not detailed_text.strip():
            return "No meeting details to summarize."
            
        self._load_model()
        if not self.summarizer:
            return self._extractive_fallback(detailed_text, max_sentences=3)
            
        try:
            words = detailed_text.split()
            word_count = len(words)
            if word_count < 50:
                return detailed_text
                
            # Summarize the summary to make it highly concise
            max_len = min(80, int(word_count * 0.5))
            min_len = min(25, int(word_count * 0.15))
            if max_len <= min_len:
                max_len = min_len + 10
                
            res = self.summarizer(
                detailed_text,
                max_length=max_len,
                min_length=min_len,
                do_sample=False
            )
            exec_summary = res[0]["summary_text"].strip()
            
            # Formatting check: make sure it has at least a few sentences
            sentences = exec_summary.split(".")
            if len(sentences) < 3:
                # Append one sentence fallback if too short
                return exec_summary + " " + self._extractive_fallback(detailed_text, max_sentences=1)
                
            return exec_summary
        except Exception as e:
            logger.warning(f"Failed to generate executive summary: {e}. Using extractive fallback.")
            return self._extractive_fallback(detailed_text, max_sentences=3)

summarizer = TranscriptSummarizer()
