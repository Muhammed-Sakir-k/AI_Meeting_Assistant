import logging
from fastapi import APIRouter

# Import all individual routers
from backend.api.routes_upload import router as upload_router
from backend.api.routes_transcript import router as transcript_router
from backend.api.routes_summary import router as summary_router
from backend.api.routes_actions import router as actions_router
from backend.api.routes_translation import router as translation_router
from backend.api.routes_sentiment import router as sentiment_router
from backend.api.routes_questions import router as questions_router
from backend.api.routes_reminders import router as reminders_router
from backend.api.routes_email import router as email_router
from backend.api.routes_live import router as live_router
from backend.api.routes_analytics import router as analytics_router
from backend.api.routes_voice import router as voice_router
from backend.api.routes_report import router as report_router
from backend.api.routes_search import router as search_router
from backend.api.routes_auth import router as auth_router

logger = logging.getLogger(__name__)
router = APIRouter()

# Include all the sub-routers
router.include_router(auth_router)
router.include_router(upload_router)
router.include_router(transcript_router)
router.include_router(summary_router)
router.include_router(actions_router)
router.include_router(translation_router)
router.include_router(sentiment_router)
router.include_router(questions_router)
router.include_router(reminders_router)
router.include_router(email_router)
router.include_router(live_router)
router.include_router(analytics_router)
router.include_router(voice_router)
router.include_router(report_router)
router.include_router(search_router)

logger.info("Successfully mounted all modular API sub-routers in parent APIRouter.")
