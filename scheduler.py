from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from database import db

scheduler = BackgroundScheduler()

async def check_reminders():
    now = datetime.now().strftime("%H:%M")

    meds_due = await db.medicines.find({"times": now}).to_list(100)

    for med in meds_due:
        print(f"Reminder → Take {med['name']} ({med['dosage']})")

def start_scheduler():
    scheduler.add_job(check_reminders, "interval", minutes=1)
    scheduler.start()
