import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

TRANSLATION_ENGINE = os.getenv("TRANSLATION_ENGINE", "google").lower()
LIBRETRANSLATE_URL = os.getenv("LIBRETRANSLATE_URL", "http://localhost:5000")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")

# Supported languages map
SUPPORTED_LANGUAGES = {
    "en": "English",
    "ml": "Malayalam",
    "hi": "Hindi",
    "ta": "Tamil",
    "kn": "Kannada",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi"
}

class TranslatorWrapper:
    def __init__(self):
        self.engine_name = TRANSLATION_ENGINE
        
    def _get_translator(self, source="auto", target="en"):
        """Returns the appropriate deep-translator instance based on configuration."""
        # Normalize deep-translator expected codes
        # deep-translator maps ISO codes. E.g. 'ml' for malayalam, etc.
        try:
            if self.engine_name == "libretranslate":
                from deep_translator import LibreTranslator
                return LibreTranslator(
                    url=LIBRETRANSLATE_URL, 
                    source=source if source != "auto" else "en", 
                    target=target
                )
            elif self.engine_name == "deepl" and DEEPL_API_KEY:
                from deep_translator import DeeplTranslator
                return DeeplTranslator(
                    api_key=DEEPL_API_KEY, 
                    source=source if source != "auto" else "en", 
                    target=target,
                    use_free_api=True
                )
            else:
                # Default: Google Translate
                from deep_translator import GoogleTranslator
                return GoogleTranslator(source=source, target=target)
        except Exception as e:
            logger.error(f"Error initializing deep-translator: {e}. Falling back to Google Translator.")
            from deep_translator import GoogleTranslator
            return GoogleTranslator(source="auto", target=target)

    def translate_text(self, text: str, source_lang="auto", target_lang="en") -> str:
        """
        Translates a block of text from source_lang to target_lang.
        If source_lang is 'auto', it auto-detects.
        If translation fails, logs warning and returns original text.
        """
        if not text or not text.strip():
            return ""
            
        # If source and target are same, return text
        if source_lang == target_lang:
            return text
            
        try:
            # deep-translator handles segment boundaries under the hood,
            # but for very large text blocks (e.g. >5000 characters) it's safer to translate in paragraphs
            translator = self._get_translator(source=source_lang, target=target_lang)
            
            # Paragraph split batching
            paragraphs = text.split("\n\n")
            translated_paragraphs = []
            
            for para in paragraphs:
                if not para.strip():
                    translated_paragraphs.append("")
                    continue
                # Translate paragraph
                val = translator.translate(para)
                translated_paragraphs.append(val)
                
            return "\n\n".join(translated_paragraphs)
        except Exception as e:
            logger.error(f"Translation API error: {e}. Returning original text.")
            return text

    def get_supported_languages(self) -> dict:
        """Returns target languages supported by system."""
        return SUPPORTED_LANGUAGES

translator = TranslatorWrapper()
