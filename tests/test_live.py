import os
import sys
import json
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from backend.database.db import init_db, SessionLocal
from backend.database.models import Meeting, Transcript, Summary, ActionItem, Sentiment, Question, Reminder, EmailLog

def run_integration_test():
    print("=" * 60)
    print("STARTING LIVE INTEGRATION TEST FOR AI MEETING ASSISTANT")
    print("=" * 60)

    # 1. Initialize clean DB
    print("\n[1/7] Initializing clean test database...")
    init_db()

    client = TestClient(app)
    audio_file_path = "test_dummy.wav"

    if not os.path.exists(audio_file_path):
        print(f"Error: test audio file '{audio_file_path}' not found in project root.")
        return

    # 2. Upload Meeting Audio
    print(f"\n[2/7] Uploading '{audio_file_path}' to '/upload' endpoint...")
    with open(audio_file_path, "rb") as f:
        response = client.post(
            "/upload",
            files={"file": (audio_file_path, f, "audio/wav")},
            data={"title": "Test Integration Sync Meeting"}
        )
    
    if response.status_code != 200 and response.status_code != 409:
        print(f"Failed to upload: {response.status_code} - {response.text}")
        return

    res_json = response.json()
    meeting_id = res_json.get("meeting_id")
    print(f"Successfully uploaded! Assigned Meeting ID: {meeting_id}")

    # 3. Wait for BackgroundTasks Pipeline to execute
    # Note: TestClient runs FastAPI BackgroundTasks synchronously, so by the time
    # response is returned, the background pipeline task has already finished executing!
    print("\n[3/7] Checking pipeline status...")
    status_resp = client.get(f"/status/{meeting_id}")
    status_json = status_resp.json()
    print(f"Current Pipeline Status: {status_json}")

    db = SessionLocal()
    meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
    print(f"Meeting status in Database: '{meeting.processing_status}' (Duration: {meeting.duration_seconds}s)")

    # 4. Fetch Transcript and Speaker turns
    print("\n[4/7] Fetching transcript data...")
    tr_resp = client.get(f"/transcript/{meeting_id}")
    if tr_resp.status_code == 200:
        tr_json = tr_resp.json()
        print(f"Transcription Language: {tr_json.get('language')}")
        print(f"Confidence Score: {tr_json.get('confidence_score')}")
        print("\n--- Transcript Segment Log ---")
        for seg in tr_json.get("segments", [])[:5]:
            speaker = seg.get("speaker", "Speaker 1")
            print(f"[{seg.get('start'):.2f}s] {speaker}: {seg.get('text')}")
        if len(tr_json.get("segments", [])) > 5:
            print("... [truncated]")
    else:
        print(f"Failed to fetch transcript: {tr_resp.text}")

    # 5. Fetch Summary and Key Decisions
    print("\n[5/7] Fetching summarization data...")
    sm_resp = client.get(f"/summary/{meeting_id}")
    if sm_resp.status_code == 200:
        sm_json = sm_resp.json()
        print("\n--- Executive Summary ---")
        print(sm_json.get("executive_summary"))
        print("\n--- Key Decisions ---")
        for dec in sm_json.get("key_decisions", []):
            print(f"- {dec}")
    else:
        print(f"Failed to fetch summary: {sm_resp.text}")

    # 6. Fetch Action Items & Priorities
    print("\n[6/7] Fetching action items...")
    ac_resp = client.get(f"/actions/{meeting_id}")
    if ac_resp.status_code == 200:
        ac_json = ac_resp.json()
        print("\n--- Action Items Table ---")
        print(f"{'Owner':<12} | {'Task Description':<40} | {'Deadline':<15} | {'Priority':<8}")
        print("-" * 80)
        for item in ac_json:
            print(f"{item.get('owner', 'Unassigned'):<12} | {item.get('task', '')[:38]:<40} | {item.get('deadline', 'N/A'):<15} | {item.get('priority', 'medium'):<8}")
    else:
        print(f"Failed to fetch action items: {ac_resp.text}")

    # 7. Fetch Reminders and Email MOM Drafts
    print("\n[7/7] Fetching reminders and composed MOM email drafts...")
    reminders_resp = client.get(f"/reminders/{meeting_id}")
    if reminders_resp.status_code == 200:
        rem_json = reminders_resp.json()
        print(f"Total Reminders Generated: {len(rem_json)}")
        for rem in rem_json[:2]:
            print(f"- {rem.get('reminder_text')}")
            
    email_resp = client.get(f"/email/draft/{meeting_id}?type=mom")
    if email_resp.status_code == 200:
        em_json = email_resp.json()
        print("\n--- Pre-Composed MOM Email ---")
        print(f"Subject: {em_json.get('subject')}")
        print("\n" + em_json.get("body")[:300] + "\n...")
    
    db.close()
    print("=" * 60)
    print("LIVE INTEGRATION TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_integration_test()
