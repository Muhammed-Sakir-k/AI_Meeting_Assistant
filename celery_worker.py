import os
import logging
from celery import Celery
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery app
celery_app = Celery(
    "ai_meeting_assistant",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.tasks.pipeline_tasks"]
)

# Configuration overrides
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True
)

logger.info(f"Celery client loaded targeting broker {REDIS_URL}")
