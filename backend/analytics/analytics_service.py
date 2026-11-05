import logging
import json
from collections import Counter
from sqlalchemy import func
from datetime import datetime, timedelta

# Database imports
from backend.database.db import SessionLocal
from backend.database.models import (
    Meeting, Transcript, ActionItem, Summary, Sentiment,
    Question, Reminder, EmailLog, AnalyticsEvent
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    def log_event(self, meeting_id: int, event_type: str, event_data: dict = None):
        """Logs an event to the analytics_events table."""
        db = SessionLocal()
        try:
            event = AnalyticsEvent(
                meeting_id=meeting_id,
                event_type=event_type,
                event_data=event_data if event_data else {}
            )
            db.add(event)
            db.commit()
            logger.info(f"Logged analytics event: {event_type} for meeting {meeting_id}")
        except Exception as e:
            logger.error(f"Failed to log analytics event: {e}")
            db.rollback()
        finally:
            db.close()

    def get_meeting_analytics(self, meeting_id: int) -> dict:
        """Compiles analytics for a single meeting."""
        db = SessionLocal()
        try:
            meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
            if not meeting:
                return {}
                
            transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
            actions = db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).all()
            sentiments = db.query(Sentiment).filter(Sentiment.meeting_id == meeting_id).all()
            questions = db.query(Question).filter(Question.meeting_id == meeting_id).all()
            
            # Word Count
            word_count = 0
            raw_text = ""
            if transcript:
                try:
                    data = json.loads(transcript.text)
                    raw_text = data.get("text", "")
                except Exception:
                    raw_text = transcript.text or ""
                word_count = len(raw_text.split())
                
            # Sentiment counts
            pos = sum(1 for s in sentiments if s.label == "Positive")
            neu = sum(1 for s in sentiments if s.label == "Neutral")
            neg = sum(1 for s in sentiments if s.label == "Negative")
            total_sent = len(sentiments)
            
            sentiment_dist = {
                "positive": round((pos / total_sent * 100), 1) if total_sent > 0 else 0,
                "neutral": round((neu / total_sent * 100), 1) if total_sent > 0 else 100,
                "negative": round((neg / total_sent * 100), 1) if total_sent > 0 else 0
            }
            
            # Action items
            total_actions = len(actions)
            completed_actions = sum(1 for a in actions if a.status == "done")
            action_rate = round((completed_actions / total_actions * 100), 1) if total_actions > 0 else 100.0
            
            # Action owners and priorities
            owners = []
            priorities = {"high": 0, "medium": 0, "low": 0}
            for a in actions:
                if a.owner:
                    owners.append(a.owner)
                p = (a.priority or "medium").lower()
                if p in priorities:
                    priorities[p] += 1
                    
            owner_counts = dict(Counter(owners))
            
            # Questions
            total_questions = len(questions)
            answered_questions = sum(1 for q in questions if q.status == "answered")
            unanswered_questions = total_questions - answered_questions
            
            # Simple keyword extraction (TF-IDF mock)
            stop_words = {"the", "a", "an", "and", "or", "but", "if", "then", "we", "they", "he", "she", "it", "i", "you", "to", "of", "in", "on", "at", "for", "with", "about", "that", "this", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "not", "so", "our", "us"}
            words = [w.strip(".,!?\"'").lower() for w in raw_text.split() if w.strip(".,!?\"'").lower() not in stop_words and len(w.strip(".,!?\"'")) > 3]
            top_keywords = dict(Counter(words).most_common(10))
            
            return {
                "meeting_id": meeting_id,
                "title": meeting.title,
                "date": meeting.date.isoformat() if meeting.date else None,
                "duration_seconds": meeting.duration_seconds or 0,
                "word_count": word_count,
                "sentiment_distribution": sentiment_dist,
                "action_items_completion_rate": action_rate,
                "action_items_total": total_actions,
                "action_items_completed": completed_actions,
                "priority_distribution": priorities,
                "most_common_owners": owner_counts,
                "questions_total": total_questions,
                "questions_answered": answered_questions,
                "questions_unanswered": unanswered_questions,
                "top_keywords": top_keywords
            }
        except Exception as e:
            logger.error(f"Error compiling meeting analytics for {meeting_id}: {e}")
            return {}
        finally:
            db.close()

    def get_aggregate_analytics(self) -> dict:
        """Compiles analytics across all meetings in the system."""
        db = SessionLocal()
        try:
            meetings = db.query(Meeting).all()
            if not meetings:
                return {
                    "total_meetings": 0,
                    "average_duration_seconds": 0,
                    "average_action_items": 0,
                    "language_distribution": {},
                    "aggregate_sentiment": {"positive": 0, "neutral": 100, "negative": 0},
                    "meeting_frequency": [],
                    "most_active_participants": {}
                }
                
            total_meetings = len(meetings)
            total_duration = sum(m.duration_seconds or 0 for m in meetings)
            avg_duration = round(total_duration / total_meetings, 1)
            
            # Action items
            actions = db.query(ActionItem).all()
            avg_actions = round(len(actions) / total_meetings, 1)
            
            # Languages
            languages = [m.language for m in meetings if m.language]
            lang_dist = dict(Counter(languages))
            
            # Overall Sentiments
            sentiments = db.query(Sentiment).all()
            total_sent = len(sentiments)
            pos = sum(1 for s in sentiments if s.label == "Positive")
            neu = sum(1 for s in sentiments if s.label == "Neutral")
            neg = sum(1 for s in sentiments if s.label == "Negative")
            
            aggregate_sent = {
                "positive": round((pos / total_sent * 100), 1) if total_sent > 0 else 0,
                "neutral": round((neu / total_sent * 100), 1) if total_sent > 0 else 100,
                "negative": round((neg / total_sent * 100), 1) if total_sent > 0 else 0
            }
            
            # Most active participants
            owners = [a.owner for a in actions if a.owner and a.owner != "Unassigned"]
            top_owners = dict(Counter(owners).most_common(10))
            
            # Meeting frequency over time (last 7 days/meetings grouping)
            # Create a simple list of meeting date vs count
            meeting_dates = []
            for m in meetings:
                if m.date:
                    meeting_dates.append(m.date.strftime("%Y-%m-%d"))
            frequency = dict(Counter(meeting_dates))
            
            # Sort chronologically
            sorted_frequency = [{"date": k, "count": v} for k, v in sorted(frequency.items())]
            
            return {
                "total_meetings": total_meetings,
                "average_duration_seconds": avg_duration,
                "average_action_items": avg_actions,
                "language_distribution": lang_dist,
                "aggregate_sentiment": aggregate_sent,
                "meeting_frequency": sorted_frequency[-10:], # return last 10 dates
                "most_active_participants": top_owners
            }
        except Exception as e:
            logger.error(f"Error compiling aggregate analytics: {e}")
            return {}
        finally:
            db.close()

analytics_service = AnalyticsService()
