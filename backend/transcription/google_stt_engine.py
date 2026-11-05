import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

GOOGLE_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./google_credentials.json")
DEFAULT_LANGUAGE = os.getenv("GOOGLE_STT_LANGUAGE", "en-US")

class GoogleSTTEngine:
    def __init__(self):
        self.client = None
        self.initialized = False
        
    def _initialize(self):
        """Initializes the Google Cloud STT client, handling missing credentials or packages gracefully."""
        if self.initialized:
            return
            
        if not os.path.exists(GOOGLE_CREDENTIALS) and "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
            logger.warning(f"Google credentials file '{GOOGLE_CREDENTIALS}' not found. Google STT will not be available.")
            raise FileNotFoundError("Google credentials file not found. Fallback to Whisper will be active.")
            
        try:
            from google.cloud import speech
            # If path exists, set environment variable explicitly so client picks it up
            if os.path.exists(GOOGLE_CREDENTIALS):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(GOOGLE_CREDENTIALS)
            self.client = speech.SpeechClient()
            self.initialized = True
            logger.info("Google Speech-to-Text client initialized successfully.")
        except ImportError:
            logger.error("google-cloud-speech library is not installed.")
            raise ImportError("google-cloud-speech library is missing. Fallback to Whisper will be active.")
        except Exception as e:
            logger.error(f"Failed to initialize Google STT client: {e}")
            raise e

    def transcribe_stream(self, audio_generator, sample_rate=16000, language_code=DEFAULT_LANGUAGE):
        """
        Transcribes a stream of audio chunks.
        audio_generator should yield raw 16-bit PCM mono bytes.
        """
        self._initialize()
        
        from google.cloud import speech
        
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
            enable_automatic_punctuation=True,
        )
        
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True
        )
        
        # Helper generator to format chunks into streaming requests
        def request_generator():
            for chunk in audio_generator:
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
                
        try:
            responses = self.client.streaming_recognize(
                config=streaming_config,
                requests=request_generator()
            )
            return responses
        except Exception as e:
            logger.error(f"Google STT streaming error: {e}")
            raise e

google_stt_engine = GoogleSTTEngine()
