import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Database imports
from backend.database.db import SessionLocal
from backend.database.models import EmailLog, Meeting, Transcript, Summary, ActionItem

logger = logging.getLogger(__name__)
load_dotenv()

# SMTP Config
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")

# SendGrid Config
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")

# OpenAI Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

class EmailService:
    def generate_draft(self, meeting_id: int, email_type="mom") -> dict:
        """
        Generates email draft based on templates.
        Upgrades to LLM composition if OPENAI_API_KEY is present.
        """
        db = SessionLocal()
        try:
            meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
            if not meeting:
                raise ValueError("Meeting not found")
                
            summary = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
            action_items = db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).all()
            
            meeting_title = meeting.title or "Meeting"
            meeting_date = meeting.date.strftime("%Y-%m-%d") if meeting.date else ""
            summary_text = summary.summary_text if summary else "No summary available."
            decisions_text = summary.key_decisions if summary else "[]"
            
            import json
            try:
                decisions = json.loads(decisions_text)
            except Exception:
                decisions = [decisions_text] if decisions_text else []
                
            # Default Template Drafts
            recipients = []
            for item in action_items:
                if item.owner and "@" in item.owner: # Check if owner is an email
                    recipients.append(item.owner)
            
            subject = f"Minutes of Meeting: {meeting_title} ({meeting_date})"
            body = ""
            
            if email_type == "mom":
                subject = f"Minutes of Meeting: {meeting_title} ({meeting_date})"
                body = f"Hello Team,\n\nHere are the Minutes of Meeting (MOM) for '{meeting_title}' held on {meeting_date}.\n\n"
                body += f"--- Executive Summary ---\n{summary_text}\n\n"
                
                if decisions:
                    body += "--- Key Decisions ---\n"
                    for dec in decisions:
                        body += f"- {dec}\n"
                    body += "\n"
                    
                if action_items:
                    body += "--- Action Items ---\n"
                    for item in action_items:
                        body += f"- {item.owner}: {item.task} (Deadline: {item.deadline}, Priority: {item.priority})\n"
                    body += "\n"
                    
                body += "Best regards,\nAI Meeting Assistant"
                
            elif email_type == "action_assignment":
                subject = f"Action Item Assignments: {meeting_title}"
                body = f"Hello Team,\n\nPlease find the action items assigned during our meeting '{meeting_title}' below:\n\n"
                if action_items:
                    for idx, item in enumerate(action_items):
                        body += f"Task {idx+1}:\n"
                        body += f"  - Assigned to: {item.owner}\n"
                        body += f"  - Description: {item.task}\n"
                        body += f"  - Deadline: {item.deadline}\n"
                        body += f"  - Priority: {item.priority.upper()}\n\n"
                else:
                    body += "No action items were assigned during this session.\n\n"
                body += "Please follow up on your respective tasks.\n\nBest regards,\nAI Meeting Assistant"
                
            elif email_type == "followup":
                subject = f"Follow-up: {meeting_title} Tasks"
                body = f"Hello Team,\n\nThis is a quick follow-up to check on the progress of action items assigned in our last meeting '{meeting_title}':\n\n"
                if action_items:
                    for item in action_items:
                        body += f"- {item.owner}: {item.task} (Status: {item.status.upper()})\n"
                body += "\nLet's catch up soon to resolve any blockers.\n\nBest regards,\nAI Meeting Assistant"
                
            # If OpenAI Key is present, upgrade composition with LLM
            if OPENAI_API_KEY:
                try:
                    logger.info("Upgrading email draft generation via OpenAI LLM...")
                    import openai
                    client = openai.OpenAI(api_key=OPENAI_API_KEY)
                    
                    prompt = f"""
                    Write a highly professional {email_type.upper().replace('_', ' ')} email for the following meeting details:
                    Title: {meeting_title}
                    Date: {meeting_date}
                    Summary: {summary_text}
                    Decisions: {json.dumps(decisions)}
                    Action Items: {[{'owner': i.owner, 'task': i.task, 'deadline': i.deadline} for i in action_items]}
                    
                    Keep the tone clear, warm, and structured. Return ONLY the body text of the email.
                    """
                    
                    response = client.chat.completions.create(
                        model=LLM_MODEL,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    body = response.choices[0].message.content.strip()
                    logger.info("Email draft generated successfully by OpenAI.")
                except Exception as llm_err:
                    logger.warning(f"Failed to generate email via LLM: {llm_err}. Using template fallback.")
                    
            return {
                "meeting_id": meeting_id,
                "recipients": recipients,
                "subject": subject,
                "body": body,
                "email_type": email_type
            }
        finally:
            db.close()

    def send_email(self, meeting_id: int, recipient: str, subject: str, body: str, email_type="mom") -> bool:
        """
        Sends the email using SendGrid or SMTP fallback,
        and logs the outcome in email_log.
        """
        db = SessionLocal()
        sent_status = "sent"
        
        # Save to DB log as draft/sending
        db_log = EmailLog(
            meeting_id=meeting_id,
            recipient=recipient,
            subject=subject,
            body=body,
            email_type=email_type,
            sent_at=datetime.utcnow(),
            status="failed" # default until success
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        
        try:
            # 1. Option 1: SendGrid
            if SENDGRID_API_KEY:
                logger.info(f"Sending email to {recipient} via SendGrid SDK...")
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail
                
                message = Mail(
                    from_email=EMAIL_FROM or SMTP_USER,
                    to_emails=recipient,
                    subject=subject,
                    plain_text_content=body
                )
                sg = SendGridAPIClient(SENDGRID_API_KEY)
                sg.send(message)
                logger.info("Email sent successfully via SendGrid.")
                
            # 2. Option 2: SMTP
            elif SMTP_USER and SMTP_PASSWORD:
                logger.info(f"Sending email to {recipient} via SMTP server {SMTP_HOST}:{SMTP_PORT}...")
                msg = MIMEMultipart()
                msg['From'] = EMAIL_FROM or SMTP_USER
                msg['To'] = recipient
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))
                
                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
                server.quit()
                logger.info("Email sent successfully via SMTP.")
                
            else:
                logger.warning("No SMTP or SendGrid configured in .env. Mocking successful send...")
                # We mock it for development convenience so it doesn't fail if configs are blank
                
            db_log.status = "sent"
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            db_log.status = "failed"
            db.commit()
            return False
        finally:
            db.close()

email_service = EmailService()
