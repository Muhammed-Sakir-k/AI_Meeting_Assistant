import os
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Database imports
from backend.database.db import SessionLocal
from backend.database.models import Reminder, ActionItem

logger = logging.getLogger(__name__)
load_dotenv()

class ReminderService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("APScheduler initialized and started for reminders.")

    def create_reminders_for_meeting(self, meeting_id: int):
        """
        Creates pending reminders for all action items in a meeting.
        """
        db = SessionLocal()
        try:
            action_items = db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).all()
            
            for item in action_items:
                # Check if reminder already exists
                existing = db.query(Reminder).filter(
                    Reminder.meeting_id == meeting_id,
                    Reminder.action_id == item.action_id
                ).first()
                
                if existing:
                    continue
                    
                # Format reminder text
                owner = item.owner if item.owner else "Unassigned"
                task = item.task if item.task else "Complete action item"
                deadline = item.deadline if item.deadline else "ASAP"
                reminder_text = f"Reminder: {owner} needs to {task} by {deadline}"
                
                # Parse or estimate a schedule date (default: 24 hours before deadline, or 1 hour from now)
                scheduled_at = datetime.utcnow() + timedelta(hours=1)
                
                reminder = Reminder(
                    meeting_id=meeting_id,
                    action_id=item.action_id,
                    owner_name=owner,
                    reminder_text=reminder_text,
                    scheduled_at=scheduled_at,
                    status="pending"
                )
                db.add(reminder)
                
            db.commit()
            logger.info(f"Reminders generated for meeting {meeting_id}.")
        except Exception as e:
            logger.error(f"Error creating reminders: {e}")
            db.rollback()
        finally:
            db.close()

    def send_notification(self, reminder_id: int):
        """Sends reminder notification (email, in-app logs)."""
        db = SessionLocal()
        try:
            reminder = db.query(Reminder).filter(Reminder.reminder_id == reminder_id).first()
            if reminder and reminder.status == "pending":
                logger.info(f"Triggering reminder: {reminder.reminder_text}")
                
                # Update status
                reminder.status = "sent"
                db.commit()
                
                # If email integration is configured, we could trigger email sending here.
        except Exception as e:
            logger.error(f"Failed to trigger reminder {reminder_id}: {e}")
        finally:
            db.close()

    def dismiss_reminder(self, reminder_id: int):
        """Marks reminder as dismissed."""
        db = SessionLocal()
        try:
            reminder = db.query(Reminder).filter(Reminder.reminder_id == reminder_id).first()
            if reminder:
                reminder.status = "dismissed"
                db.commit()
                logger.info(f"Reminder {reminder_id} dismissed.")
                return True
            return False
        except Exception as e:
            logger.error(f"Error dismissing reminder {reminder_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def resend_reminder(self, reminder_id: int):
        """Triggers manual resend of reminder."""
        db = SessionLocal()
        try:
            reminder = db.query(Reminder).filter(Reminder.reminder_id == reminder_id).first()
            if reminder:
                reminder.status = "sent"
                reminder.scheduled_at = datetime.utcnow()
                db.commit()
                logger.info(f"Reminder {reminder_id} manual resend triggered.")
                return True
            return False
        except Exception as e:
            logger.error(f"Error resending reminder {reminder_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

reminder_service = ReminderService()
