from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from database import db
import asyncio

scheduler = BackgroundScheduler()

# Get or create event loop once
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def async_check_reminders():
    now = datetime.now().strftime("%H:%M")

    meds_due = await db.medicines.find({"times": now}).to_list(100)

    for med in meds_due:
        print(f"Reminder → Take {med['name']} ({med['dosage']})")

def check_reminders():
    # Run async task inside persistent loop
    asyncio.ensure_future(async_check_reminders(), loop=loop)

def start_scheduler():
    scheduler.add_job(check_reminders, "interval", minutes=1)
    scheduler.start()
    # Start the loop in background
    loop.run_forever()
