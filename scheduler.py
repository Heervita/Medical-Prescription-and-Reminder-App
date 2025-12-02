from apscheduler.schedulers.background import BackgroundScheduler
from utils.database import medicine_collection, user_collection
from datetime import datetime
from utils.email_config import fm, MessageSchema

scheduler = BackgroundScheduler()

async def send_email(email, subject, body):
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype="html"
    )
    await fm.send_message(message)

async def check_reminders():
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%Y-%m-%d")

    medicines = medicine_collection.find({})

    for med in medicines:
        start = med["start_date"]
        end = med["end_date"]

        # Only valid dates
        if not (start <= current_date <= end):
            continue

        # Check times like ["08:00", "14:00"]
        for t in med["times"]:
            if t == current_time:
                user = user_collection.find_one({"_id": med["user_id"]})

                if user:
                    subject = f"Medicine Reminder: {med['name']}"
                    body = f"""
                    <h3>Hello {user['name']},</h3>
                    <p>This is a reminder to take your medicine:</p>
                    <h2>{med['name']}</h2>
                    <p>Dosage: {med['dosage']}</p>
                    <p>Frequency: {med['frequency']} times/day</p>
                    <br>
                    <p>Stay healthy ❤️</p>
                    """

                    await send_email(user["email"], subject, body)
                    print(f"Email sent to {user['email']} for {med['name']}")

scheduler.add_job(check_reminders, "interval", minutes=1)
scheduler.start()
