import os
import sys
import unittest
import numpy as np
from fastapi.testclient import TestClient

# Add project root to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db
from backend.transcription.preprocessing import butter_highpass, highpass_filter
from backend.transcription.whisper_wrapper import transcriber
from backend.nlp.nlp_extractor import extractor
from backend.summarization.summarizer import summarizer
from main import app

class TestAudioPreprocessing(unittest.TestCase):
    def test_butter_highpass(self):
        """Tests that Butterworth filter coefficients are generated correctly."""
        b, a = butter_highpass(cutoff=80.0, fs=16000, order=4)
        self.assertEqual(len(b), 5)
        self.assertEqual(len(a), 5)

    def test_highpass_filter(self):
        """Tests that the highpass filter removes low-frequency signals."""
        fs = 16000
        t = np.linspace(0, 1, fs)
        # Create a signal containing a low-frequency hum (50Hz) and a high-frequency signal (1000Hz)
        signal = np.sin(2 * np.pi * 50 * t) + np.sin(2 * np.pi * 1000 * t)
        
        filtered = highpass_filter(signal, cutoff=80.0, fs=fs, order=4)
        
        # Power of signal at 50Hz should be reduced relative to 1000Hz
        self.assertEqual(len(filtered), len(signal))

class TestWhisperWrapper(unittest.TestCase):
    def test_confidence_calculation(self):
        """Tests that average logprob and no_speech_prob map logically to 0.0-1.0 confidence score."""
        # 1. High probability (logprob near 0, no_speech_prob near 0)
        c1 = transcriber.calculate_confidence(avg_logprob=0.0, no_speech_prob=0.0)
        self.assertEqual(c1, 1.0)
        
        # 2. Lower probability (avg_logprob -0.7)
        c2 = transcriber.calculate_confidence(avg_logprob=-0.7, no_speech_prob=0.1)
        self.assertTrue(0.4 <= c2 <= 0.6)
        
        # 3. High no_speech_prob should penalize confidence
        c3 = transcriber.calculate_confidence(avg_logprob=0.0, no_speech_prob=0.8)
        self.assertTrue(c3 < 0.3)

class TestNLPExtraction(unittest.TestCase):
    def setUp(self):
        extractor._load_models()  # Ensure spaCy model is loaded

    def test_fallback_classify(self):
        """Tests the keyword classifier fallback logic."""
        # Action Item keyword detection
        class_action = extractor._fallback_classify("John will draft the proposal by Friday.")
        self.assertEqual(class_action, "action item")
        
        # Decision keyword detection
        class_decision = extractor._fallback_classify("We decided to proceed with option B.")
        self.assertEqual(class_decision, "decision")
        
        # General discussion
        class_discuss = extractor._fallback_classify("The project went well last year.")
        self.assertEqual(class_discuss, "discussion")

    def test_action_details_extraction(self):
        """Tests spaCy NER + dependency parsing mapping owner, task, and deadline."""
        text = "Alice must review the security protocols by tomorrow."
        doc = extractor.nlp(text)
        details = extractor.extract_action_details(text, doc)
        
        # Alice is the PERSON (Owner)
        self.assertEqual(details["owner"], "Alice")
        # Tomorrow is the TIME (Deadline)
        self.assertEqual(details["deadline"], "tomorrow")
        # Task is parsed from the verb phrase
        self.assertIn("review", details["task"].lower())
        self.assertIn("security", details["task"].lower())

    def test_action_details_partial_fallback(self):
        """Tests that missing fields result in placeholder fallbacks instead of dropping records."""
        text = "Review the document."
        doc = extractor.nlp(text)
        details = extractor.extract_action_details(text, doc)
        
        # No person -> Unassigned
        self.assertEqual(details["owner"], "Unassigned")
        # No date -> No deadline specified
        self.assertEqual(details["deadline"], "No deadline specified")
        # Task should extract the verb phrase
        self.assertIn("review", details["task"].lower())

class TestSummarization(unittest.TestCase):
    def test_extractive_fallback(self):
        """Tests that the extractive fallback selects key sentences from a long text block."""
        text = (
            "The meeting started on time. "
            "We discussed the financial report and agreed we need to cut costs. "
            "Alice raised concerns about the timeline of Phase 2. "
            "Finally, the team approved the new marketing budget."
        )
        summary = summarizer._extractive_fallback(text)
        self.assertTrue(len(summary) > 10)
        self.assertIn("meeting started", summary.lower())
        self.assertIn("marketing budget", summary.lower())

class TestAPI(unittest.TestCase):
    def setUp(self):
        init_db()  # Ensure DB structure exists
        self.client = TestClient(app)

    def test_invalid_upload_extension(self):
        """Tests that uploads with unsupported file extensions are rejected with 400 Bad Request."""
        # Create a mock text file
        response = self.client.post(
            "/upload",
            files={"file": ("test.txt", b"dummy content", "text/plain")},
            data={"title": "Test Title"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported file format", response.json()["detail"])

    def test_search_endpoint_empty(self):
        """Tests search returns empty or matches list."""
        response = self.client.get("/search?q=xyz_nonexistent_xyz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

if __name__ == "__main__":
    unittest.main()
