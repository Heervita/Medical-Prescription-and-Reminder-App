# app.py
import streamlit as st
from dotenv import load_dotenv
import os
from pymongo import MongoClient

st.set_page_config(page_title="MedGlow", layout="wide")

load_dotenv()

st.markdown(sidebar_css, unsafe_allow_html=True)
sidebar_css = """
<style>
/* Import font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

:root{
  --bg1: #041a14;
  --glass: rgba(255,255,255,0.04);
  --accent: #1ee38a;
  --accent-2: #7fffd4;
  --muted: rgba(255,255,255,0.7);
}

/* Make app full height and remove Streamlit padding */
.css-18e3th9 { padding-top: 0rem; } /* top padding area */
[data-testid="stAppViewContainer"] { background: radial-gradient(circle at 10% 10%, rgba(6,48,32,0.6), rgba(2,8,6,1)); font-family: 'Inter', sans-serif; }

/* TOPNAV replacement hidden (we will use sidebar styled) */
header[data-testid="stHeader"]{display:none}

/* Sidebar container styling (glass) */
[data-testid="stSidebar"] > div:first-child {
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  border-radius: 14px;
  padding: 18px;
  border: 1px solid rgba(255,255,255,0.04);
  box-shadow: 0 8px 40px rgba(3,35,24,0.6);
}

/* Sidebar title */
[data-testid="stSidebar"] .css-1d391kg { color: var(--accent); font-weight:800; font-size:20px; margin-bottom:6px; }

/* Sidebar buttons - make them look like tabs */
.stSidebarButton, .sidebar-btn {
  display:flex; align-items:center; gap:10px;
  width:100%; text-align:left; padding:10px 14px; border-radius:10px;
  background:transparent; color: #eafff4; border:none; cursor:pointer; margin:6px 0;
  transition: all .18s ease;
}
.sidebar-btn:hover { transform: translateX(6px); background: rgba(255,255,255,0.02); box-shadow: inset 0 1px 0 rgba(255,255,255,0.02); }
.sidebar-btn.active { background: linear-gradient(90deg, rgba(30,200,120,0.12), rgba(30,200,120,0.06)); box-shadow: 0 14px 40px rgba(25,200,120,0.08); color: var(--accent); }

/* Icon style (emoji or SVG) */
.menu-icon { font-size:18px; margin-right:6px; width:22px; text-align:center; }

/* Page container - central area */
.main-content {
  padding: 28px;
  border-radius: 14px;
  margin: 22px;
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(0,0,0,0.02));
  border: 1px solid rgba(255,255,255,0.02);
  box-shadow: 0 20px 60px rgba(2,10,8,0.6);
  overflow: hidden;
}

/* Slide-in animation */
.slide-in-left {
  animation: slideIn 380ms cubic-bezier(.2,.9,.3,1);
}
@keyframes slideIn {
  from { transform: translateX(18px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* small card + buttons */
.card { padding:16px; border-radius:12px; background: rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.03); margin-bottom:12px; }
.btn { padding:10px 14px; border-radius:10px; background: linear-gradient(90deg,var(--accent-2),var(--accent)); border:none; color:#022214; font-weight:700; cursor:pointer; }

/* responsive tweak */
@media (max-width:900px){
  .main-content { margin:10px; padding:16px; }
  .sidebar-btn { padding:8px; }
}
</style>
"""

from passlib.context import CryptContext
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time


MONGO_URI = os.getenv("MONGO_URI")  # e.g. mongodb+srv://user:pass@cluster0.../dbname
DB_NAME = os.getenv("DB_NAME", "medglow_db")

MAIL_HOST = os.getenv("MAIL_HOST", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USER = os.getenv("MAIL_USER")   # your gmail
MAIL_PASS = os.getenv("MAIL_PASS")   # app password
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USER)

# Password hashing
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Connect to MongoDB
@st.cache_resource
def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

db = get_db()
users_col = db["users"]
presc_col = db["prescriptions"]
med_col = db["medicines"]

# Scheduler singleton
def get_scheduler():
    if "scheduler" not in st.session_state:
        sched = BackgroundScheduler()
        sched.start()
        st.session_state["scheduler"] = sched
    return st.session_state["scheduler"]

# Hashing helpers
def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_ctx.verify(password, hashed)

# Email sender (simple, synchronous)
def send_email(to_email: str, subject: str, html_body: str):
    if not (MAIL_USER and MAIL_PASS):
        print("Mail settings not configured. Skipping email.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = MAIL_FROM
        msg["To"] = to_email
        part = MIMEText(html_body, "html")
        msg.attach(part)

        server = smtplib.SMTP(MAIL_HOST, MAIL_PORT)
        server.ehlo()
        server.starttls()
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_FROM, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

# Reminder checker (run every minute)
def check_reminders_and_notify():
    try:
        now = datetime.now()
        time_now = now.strftime("%H:%M")
        today_str = now.strftime("%Y-%m-%d")

        # find medicines active today and having time == current time
        # medicines stored with keys: name, dosage, times (list of "HH:MM"), start_date, end_date, user_email, user_id
        medicines = med_col.find({
            "times": time_now,
            "start_date": {"$lte": today_str},
            "end_date": {"$gte": today_str}
        })

        for med in medicines:
            user_id = med.get("user_id")
            user = users_col.find_one({"_id": user_id})
            if not user:
                continue
            email = user.get("email")
            if not email:
                continue

            subject = f"MedGlow Reminder — {med.get('name')}"
            html = f"""
            <p>Hi {user.get('name')},</p>
            <p>This is a reminder to take your medicine:</p>
            <h3>{med.get('name')}</h3>
            <p><strong>Dosage:</strong> {med.get('dosage')}</p>
            <p><strong>Time:</strong> {time_now}</p>
            <p>Stay well — MedGlow</p>
            """

            sent = send_email(email, subject, html)

            # Log notification in a collection (optional)
            db["notifications"].insert_one({
                "user_id": user_id,
                "email": email,
                "medicine_id": med.get("_id"),
                "time": datetime.utcnow(),
                "sent_email": bool(sent),
                "time_string": time_now
            })

            # Also print server-side
            print(f"Reminder processed for {email} — {med.get('name')} — sent: {sent}")

    except Exception as e:
        print("Reminder check error:", e)

# start scheduler job once
sched = get_scheduler()
# Add job if not already added
if not any(j.id == "reminder_job" for j in sched.get_jobs()):
    sched.add_job(check_reminders_and_notify, "interval", minutes=1, id="reminder_job", next_run_time=datetime.now())

# ------------------ Streamlit UI ------------------


if "user" not in st.session_state:
    st.session_state["user"] = None

def signup_ui():
    st.header("Create account")
    name = st.text_input("Full name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Create account"):
        if not (name and email and password):
            st.warning("Please fill all fields.")
            return
        if users_col.find_one({"email": email}):
            st.error("Email already registered.")
            return
        hashed = hash_password(password)
        user_doc = {"name": name, "email": email, "password": hashed}
        res = users_col.insert_one(user_doc)
        st.success("Account created. Please login.")
        st.rerun()

def login_ui():
    st.header("Sign in")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Sign in"):
        user = users_col.find_one({"email": email})
        if not user:
            st.error("No user found.")
            return
        if verify_password(password, user["password"]):
            st.session_state["user"] = {"_id": user["_id"], "name": user["name"], "email": user["email"]}
            st.success(f"Welcome {user['name']}!")
            time.sleep(0.8)
            st.rerun()
        else:
            st.error("Incorrect password.")

def logout_ui():
    st.session_state["user"] = None
    st.success("Logged out.")
    time.sleep(0.6)
    st.rerun()

# helper to convert time objects to "HH:MM"
def time_to_str(t):
    return t.strftime("%H:%M")

# UI for adding prescription
def add_prescription_ui():
    st.header("Add Prescription")
    title = st.text_input("Title (e.g., General Checkup)")
    doctor = st.text_input("Doctor's name")
    d = st.date_input("Date", value=date.today())
    if st.button("Save Prescription"):
        if not title:
            st.warning("Add a title.")
            return
        doc = {
            "title": title,
            "doctor_name": doctor,
            "date": d.strftime("%Y-%m-%d"),
            "user_id": st.session_state["user"]["_id"],
            "created_at": datetime.utcnow()
        }
        presc_col.insert_one(doc)
        st.success("Saved.")

# UI for adding medicine (with dynamic time pickers based on count)
def add_medicine_ui():
    st.header("Add Medicine")
    prescription_id = st.text_input("Prescription ID (optional)")
    name = st.text_input("Medicine name")
    dosage = st.text_input("Dosage (e.g., 1 tablet)")
    frequency = st.number_input("Times per day", min_value=1, max_value=10, value=1)
    times_count = st.number_input("How many reminder times?", min_value=1, max_value=10, value=frequency)
    st.markdown("Select the times:")
    times = []
    for i in range(times_count):
        t = st.time_input(f"Time #{i+1}", key=f"time_{i}")
        times.append(time_to_str(t))

    start_date = st.date_input("Start date", value=date.today())
    end_date = st.date_input("End date", value=date.today())

    if st.button("Save Medicine"):
        if not name:
            st.warning("Provide medicine name.")
            return
        # Save medicine doc
        med_doc = {
            "prescription_id": prescription_id if prescription_id else None,
            "name": name,
            "dosage": dosage,
            "frequency": frequency,
            "times": times,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "user_id": st.session_state["user"]["_id"],
            "created_at": datetime.utcnow()
        }
        med_col.insert_one(med_doc)
        st.success("Medicine saved.")

# view prescriptions
def view_prescriptions_ui():
    st.header("All Prescriptions")
    rows = list(presc_col.find({"user_id": st.session_state["user"]["_id"]}).sort("created_at", -1))
    if not rows:
        st.info("No prescriptions yet.")
        return
    import pandas as pd
    df = pd.DataFrame([{"Title": r["title"], "Doctor": r.get("doctor_name",""), "Date": r.get("date","-")} for r in rows])
    st.table(df)

# view medicines
def view_medicines_ui():
    st.header("All Medicines")
    rows = list(med_col.find({"user_id": st.session_state["user"]["_id"]}).sort("created_at", -1))
    if not rows:
        st.info("No medicines yet.")
        return
    import pandas as pd
    df = pd.DataFrame([{
        "Name": r["name"],
        "Dosage": r.get("dosage",""),
        "Frequency": r.get("frequency",""),
        "Times": ", ".join(r.get("times",[])),
        "Start": r.get("start_date",""),
        "End": r.get("end_date",""),
        "Prescription": r.get("prescription_id") or ""
    } for r in rows])
    st.dataframe(df, use_container_width=True)

# Dashboard with upcoming reminders (in-app check)
def dashboard_ui():
    st.header(f"Welcome, {st.session_state['user']['name']}")
    st.subheader("Upcoming reminders (next 24 hours)")

    # compute upcoming reminders from medicines
    today = date.today().strftime("%Y-%m-%d")
    # find all medicines for user that are active today or later
    meds = list(med_col.find({"user_id": st.session_state["user"]["_id"]}))
    upcoming = []
    now = datetime.now()
    now_minutes = now.hour * 60 + now.minute

    for m in meds:
        # skip if outside range
        if m.get("end_date") and m.get("start_date"):
            if not (m["start_date"] <= today <= m["end_date"]):
                continue
        for t in m.get("times", []):
            # t is "HH:MM"
            try:
                hh, mm = [int(x) for x in t.split(":")]
                minutes = hh*60 + mm
                delta = minutes - now_minutes
                if -60 <= delta <= 24*60:  # show reminders occurred within last hour or next 24 h
                    upcoming.append({
                        "name": m["name"],
                        "time": t,
                        "dosage": m.get("dosage","")
                    })
            except:
                continue

    if upcoming:
        for u in sorted(upcoming, key=lambda x: x["time"]):
            st.write(f"⏱ **{u['time']}** — {u['name']} — {u['dosage']}")
    else:
        st.info("No reminders for the next 24 hours.")

# main app control flow
def main():
    # ---------------- NAVIGATION ----------------
    st.sidebar.title("MedGlow")

    if st.session_state["user"] is None:
        # Public menu
        if st.sidebar.button("Login"):
            st.session_state["page"] = "login"
        if st.sidebar.button("Signup"):
            st.session_state["page"] = "signup"

    else:
        # Logged-in menu
        if st.sidebar.button("Dashboard"):
            st.session_state["page"] = "dashboard"
        if st.sidebar.button("Add Prescription"):
            st.session_state["page"] = "add_p"
        if st.sidebar.button("Add Medicine"):
            st.session_state["page"] = "add_m"
        if st.sidebar.button("Prescriptions"):
            st.session_state["page"] = "view_p"
        if st.sidebar.button("Medicines"):
            st.session_state["page"] = "view_m"
        if st.sidebar.button("Logout"):
            st.session_state["page"] = "logout"

    page = st.session_state.get("page", "login")

    if page == "login":
        login_ui()
    elif page == "signup":
        signup_ui()
    elif page == "dashboard":
        dashboard_ui()
    elif page == "add_p":
        add_prescription_ui()
    elif page == "add_m":
        add_medicine_ui()
    elif page == "view_p":
        view_prescriptions_ui()
    elif page == "view_m":
        view_medicines_ui()
    elif page == "logout":
        logout_ui()


if __name__ == "__main__":
    main()
