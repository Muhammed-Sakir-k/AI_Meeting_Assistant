import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Mapping from English language names to code
LANGUAGE_MAP = {
    "english": "en",
    "malayalam": "ml",
    "hindi": "hi",
    "tamil": "ta",
    "kannada": "kn",
    "telugu": "te",
    "bengali": "bn",
    "marathi": "mr",
    "gujarati": "gu",
    "punjabi": "pa"
}

class CommandRouter:
    def route_command(self, command_str: str) -> Dict[str, Any]:
        """
        Routes the recognized voice command text to a system action.
        Returns a dictionary representing the action details.
        """
        cmd_lower = command_str.strip().lower()
        logger.info(f"Voice Command received: '{command_str}'")
        
        # 1. Start recording
        if "start recording" in cmd_lower or "start meeting" in cmd_lower:
            return {
                "action": "start_recording",
                "message": "✓ Starting recording...",
                "payload": {}
            }
            
        # 2. Stop recording
        if "stop recording" in cmd_lower or "stop meeting" in cmd_lower:
            return {
                "action": "stop_recording",
                "message": "✓ Finalizing meeting transcript...",
                "payload": {}
            }
            
        # 3. Generate summary
        if "generate summary" in cmd_lower or "summarize" in cmd_lower:
            return {
                "action": "generate_summary",
                "message": "✓ Generating summary...",
                "payload": {}
            }
            
        # 4. Export report
        if "export report" in cmd_lower or "download report" in cmd_lower or "export pdf" in cmd_lower:
            return {
                "action": "export_report",
                "message": "✓ Exporting PDF report...",
                "payload": {"format": "pdf"}
            }
            
        # 5. Send email
        if "send email" in cmd_lower or "compose email" in cmd_lower:
            return {
                "action": "compose_email",
                "message": "✓ Opening email composer...",
                "payload": {"type": "mom"}
            }
            
        # 6. Set reminder
        if "set reminder" in cmd_lower or "create reminder" in cmd_lower:
            return {
                "action": "set_reminder",
                "message": "✓ Setting reminder for the action item...",
                "payload": {}
            }
            
        # 7. Show questions
        if "show questions" in cmd_lower or "view questions" in cmd_lower or "questions log" in cmd_lower:
            return {
                "action": "show_questions",
                "message": "✓ Scrolling to Questions panel...",
                "payload": {}
            }
            
        # 8. Translate to [language]
        translate_match = re.search(r"translate to\s+(\w+)", cmd_lower)
        if translate_match:
            lang_name = translate_match.group(1)
            lang_code = LANGUAGE_MAP.get(lang_name)
            
            if lang_code:
                return {
                    "action": "translate_dashboard",
                    "message": f"✓ Translating dashboard to {lang_name.capitalize()}...",
                    "payload": {"language": lang_code}
                }
            else:
                return {
                    "action": "unsupported_language",
                    "message": f"✗ Language '{lang_name}' not supported.",
                    "payload": {"language": lang_name}
                }
                
        # Command not understood
        return {
            "action": "not_recognized",
            "message": "✗ Command not understood.",
            "payload": {"raw_input": command_str}
        }

command_router = CommandRouter()
