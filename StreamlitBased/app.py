import streamlit as st
st.set_page_config(page_title="MedGlow", layout="wide", initial_sidebar_state="expanded")

from pymongo import MongoClient
from passlib.context import CryptContext
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date
from dotenv import load_dotenv
import os, time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from bson import ObjectId

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "").strip()
DB_NAME = os.getenv("DB_NAME", "medglow_db")
MAIL_HOST = os.getenv("MAIL_HOST", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USER = os.getenv("MAIL_USER", "")
MAIL_PASS = os.getenv("MAIL_PASS", "")
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USER)

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        return pwd_ctx.verify(password, hashed)
    except:
        return False

@st.cache_resource
def get_db():
    if not MONGO_URI:
        raise ValueError("MONGO_URI not set in .env (must begin with mongodb:// or mongodb+srv://)")
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

try:
    db = get_db()
    users_col = db["users"]
    presc_col = db["prescriptions"]
    med_col = db["medicines"]
    notes_col = db["notifications"]
except Exception as e:
    db = None
    users_col = presc_col = med_col = notes_col = None

def send_email(to_email: str, subject: str, html_body: str) -> bool:
    if not (MAIL_USER and MAIL_PASS):
        print("Mail credentials missing; skipping email send.")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = MAIL_FROM
        msg["To"] = to_email
        part = MIMEText(html_body, "html")
        msg.attach(part)

        server = smtplib.SMTP(MAIL_HOST, MAIL_PORT, timeout=15)
        server.ehlo()
        server.starttls()
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_FROM, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Email send error:", e)
        return False

def get_scheduler():
    if "scheduler" not in st.session_state:
        sched = BackgroundScheduler()
        sched.start()
        st.session_state["scheduler"] = sched
    return st.session_state["scheduler"]

def check_reminders_and_notify():
    if med_col is None or users_col is None:
        print("DB not initialized - skipping reminder check.")
        return
    now = datetime.now()
    time_now = now.strftime("%H:%M")
    today_str = now.strftime("%Y-%m-%d")
    try:
        query = {
            "times": time_now,
            "start_date": {"$lte": today_str},
            "end_date": {"$gte": today_str}
        }
        meds = med_col.find(query)
        for m in meds:
            user_id = m.get("user_id")
            if not user_id:
                continue
            user = users_col.find_one({"_id": user_id})
            if not user:
                continue
            email = user.get("email")
            if not email:
                continue
            subject = f"MedGlow Reminder — {m.get('name')}"
            html = (
                f"<p>Hi {user.get('name')},</p>"
                f"<p>This is a reminder to take your medicine:</p>"
                f"<h3>{m.get('name')}</h3>"
                f"<p><strong>Dosage:</strong> {m.get('dosage')}</p>"
                f"<p><strong>Time:</strong> {time_now}</p>"
                f"<p>— MedGlow</p>"
            )
            sent = send_email(email, subject, html)
            if notes_col is not None:
                notes_col.insert_one({
                    "user_id": user_id,
                    "email": email,
                    "medicine_id": m.get("_id"),
                    "time_utc": datetime.utcnow(),
                    "time_local": time_now,
                    "sent_email": bool(sent)
                })
            print(f"Reminder sent to {email} for {m.get('name')} (sent={sent})")
    except Exception as e:
        print("Reminder job error:", e)

if db is not None:
    sched = get_scheduler()
    if not any(j.id == "reminder_job" for j in sched.get_jobs()):
        sched.add_job(check_reminders_and_notify, "interval", minutes=1, id="reminder_job", next_run_time=datetime.now())

SIDEBAR_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
:root{
  --accent: #1ee38a;
  --accent-2: #7fffd4;
  --glass: rgba(255,255,255,0.03);
}
.css-18e3th9 { padding-top: 0rem; }
[data-testid="stAppViewContainer"] { 
  background: radial-gradient(circle at 10% 10%, rgba(6,48,32,0.6), rgba(2,8,6,1)); 
  font-family: 'Inter', sans-serif; 
}
header[data-testid="stHeader"], footer { display: none; }
[data-testid="stSidebar"] > div:first-child {
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  border-radius: 14px;
  padding: 18px;
  border: 1px solid rgba(255,255,255,0.04);
  box-shadow: 0 8px 40px rgba(3,35,24,0.6);
}
[data-testid="stSidebar"] .css-1d391kg { 
  color: var(--accent); 
  font-weight:800; 
  font-size:20px; 
  margin-bottom:6px; 
}
.sidebar-btn {
  display:flex; 
  align-items:center; 
  gap:10px;
  width:100%; 
  text-align:left; 
  padding:10px 14px; 
  border-radius:10px;
  background:transparent; 
  color: #eafff4; 
  border:none; 
  cursor:pointer; 
  margin:6px 0;
  transition: all .18s ease;
}
.sidebar-btn:hover { 
  transform: translateX(6px); 
  background: rgba(255,255,255,0.02); 
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.02); 
}
.sidebar-btn.active { 
  background: linear-gradient(90deg, rgba(30,200,120,0.12), rgba(30,200,120,0.06)); 
  box-shadow: 0 14px 40px rgba(25,200,120,0.08); 
  color: var(--accent); 
}
.menu-icon { font-size:18px; margin-right:6px; width:22px; text-align:center; }
.main-content {
  padding: 28px; 
  border-radius: 14px; 
  margin: 22px;
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(0,0,0,0.02));
  border: 1px solid rgba(255,255,255,0.02); 
  box-shadow: 0 20px 60px rgba(2,10,8,0.6);
  overflow: hidden;
}
.slide-in-left { animation: slideIn 420ms cubic-bezier(.2,.9,.3,1); }
@keyframes slideIn { 
  from { transform: translateX(18px); opacity: 0; } 
  to { transform: translateX(0); opacity: 1; } 
}
.card { 
  padding:16px; 
  border-radius:12px; 
  background: rgba(255,255,255,0.02); 
  border:1px solid rgba(255,255,255,0.03); 
  margin-bottom:12px; 
}
.btn { 
  padding:10px 14px; 
  border-radius:10px; 
  background: linear-gradient(90deg,var(--accent-2),var(--accent)); 
  border:none; color:#022214; 
  font-weight:700; 
  cursor:pointer; 
}
.login-card { max-width:520px; margin:auto; padding:28px; border-radius:14px; }
@media (max-width:900px){
  .main-content { margin:10px; padding:16px; }
  .sidebar-btn { padding:8px; }
}
</style>
"""
st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)
def time_to_str(t):
    return t.strftime("%H:%M")

if "page" not in st.session_state:
    st.session_state["page"] = "login"
if "user" not in st.session_state:
    st.session_state["user"] = None

def signup_ui():
    st.markdown("<div class='main-content slide-in-left'>", unsafe_allow_html=True)
    st.header("Create account")
    name = st.text_input("Full name", key="su_name")
    email = st.text_input("Email", key="su_email")
    password = st.text_input("Password", type="password", key="su_pass")
    if st.button("Create account", key="su_btn"):
        if not (name and email and password):
            st.warning("Please fill all fields.")
        elif users_col is not None and users_col.find_one({"email": email}):
            st.error("Email already registered.")
        else:
            hashed = hash_password(password)
            doc = {"name": name, "email": email, "password": hashed}
            if users_col is not None:
                res = users_col.insert_one(doc)
                st.success("Account created. Redirecting to login...")
                st.session_state["page"] = "login"
                time.sleep(0.6)
                st.rerun()
            else:
                st.error("Database not configured. Check MONGO_URI in .env.")
    st.markdown("</div>", unsafe_allow_html=True)

def login_ui():
    st.markdown("<div class='main-content slide-in-left'>", unsafe_allow_html=True)
    st.header("Sign in")
    email = st.text_input("Email", key="li_email")
    password = st.text_input("Password", type="password", key="li_pass")
    if st.button("Sign in", key="li_btn"):
        if not email or not password:
            st.warning("Enter both email and password.")
        elif users_col is None:
            st.error("Database not configured. Check MONGO_URI in .env.")
        else:
            user = users_col.find_one({"email": email})
            if not user:
                st.error("No user found with that email.")
            elif verify_password(password, user["password"]):
                st.session_state["user"] = {"_id": user["_id"], "name": user["name"], "email": user["email"]}
                st.success(f"Welcome {user['name']}! Redirecting to dashboard...")
                st.session_state["page"] = "dashboard"
                time.sleep(0.4)
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.markdown("</div>", unsafe_allow_html=True)

def logout_ui():
    st.session_state["user"] = None
    st.session_state["page"] = "login"
    st.success("Logged out.")
    time.sleep(0.5)
    st.rerun()

def dashboard_ui():
    st.markdown("<div class='main-content slide-in-left'>", unsafe_allow_html=True)
    st.header(f"Welcome, {st.session_state['user']['name']}")
    st.subheader("Upcoming reminders (next 24 hours)")
    today = date.today().strftime("%Y-%m-%d")
    meds = []
    if med_col is not None:
        meds = list(med_col.find({"user_id": st.session_state["user"]["_id"]}))
    now = datetime.now()
    now_minutes = now.hour * 60 + now.minute
    upcoming = []
    for m in meds:
        if m.get("start_date") and m.get("end_date"):
            if not (m["start_date"] <= today <= m["end_date"]):
                continue
        for t in m.get("times", []):
            try:
                hh, mm = [int(x) for x in t.split(":")]
                minutes = hh * 60 + mm
                delta = minutes - now_minutes
                if -60 <= delta <= 24*60:
                    upcoming.append({"name": m["name"], "time": t, "dosage": m.get("dosage","")})
            except:
                continue
    if upcoming:
        for u in sorted(upcoming, key=lambda x: x["time"]):
            st.info(f"⏱ {u['time']} — {u['name']} — {u['dosage']}")
    else:
        st.success("No reminders for the next 24 hours.")
    st.markdown("</div>", unsafe_allow_html=True)

def add_prescription_ui():
    st.markdown("<div class='main-content slide-in-left'>", unsafe_allow_html=True)
    st.header("Add Prescription")
    title = st.text_input("Title", key="p_title")
    doctor = st.text_input("Doctor's name", key="p_doc")
    d = st.date_input("Date", value=date.today(), key="p_date")
    if st.button("Save Prescription", key="p_save"):
        if not title:
            st.warning("Add a title.")
        else:
            doc = {
                "title": title,
                "doctor_name": doctor,
                "date": d.strftime("%Y-%m-%d"),
                "user_id": st.session_state["user"]["_id"],
                "created_at": datetime.utcnow()
            }
            if presc_col is not None:
                presc_col.insert_one(doc)
                st.success("Saved.")
            else:
                st.error("DB not configured.")
    st.markdown("</div>", unsafe_allow_html=True)

def add_medicine_ui():
    st.markdown("<div class='main-content slide-in-left'>", unsafe_allow_html=True)
    st.header("Add Medicine")
    presc = st.text_input("Prescription ID (optional)", key="m_pid")
    name = st.text_input("Medicine name", key="m_name")
    dosage = st.text_input("Dosage (e.g., 1 tablet)", key="m_dosage")
    frequency = st.number_input("Times per day", min_value=1, max_value=10, value=1, key="m_freq")
    times_count = st.number_input("How many reminder times?", min_value=1, max_value=10, value=frequency, key="m_tcount")
    st.markdown("Select the times:")
    times = []
    for i in range(times_count):
        t = st.time_input(f"Time #{i+1}", key=f"time_{i}")
        times.append(time_to_str(t))
    start_date = st.date_input("Start date", value=date.today(), key="m_start")
    end_date = st.date_input("End date", value=date.today(), key="m_end")
    if st.button("Save Medicine", key="m_save"):
        if not name:
            st.warning("Provide medicine name.")
        else:
            med_doc = {
                "prescription_id": presc if presc else None,
                "name": name,
                "dosage": dosage,
                "frequency": frequency,
                "times": times,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "user_id": st.session_state["user"]["_id"],
                "created_at": datetime.utcnow()
            }
            if med_col is not None:
                med_col.insert_one(med_doc)
                st.success("Medicine saved.")
            else:
                st.error("DB not configured.")
    st.markdown("</div>", unsafe_allow_html=True)

def view_prescriptions_ui():
    st.markdown("<div class='main-content slide-in-left'>", unsafe_allow_html=True)
    st.header("All Prescriptions")
    if presc_col is None:
        st.error("DB not configured.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    rows = list(presc_col.find({"user_id": st.session_state["user"]["_id"]}).sort("created_at", -1))
    if not rows:
        st.info("No prescriptions yet.")
    else:
        df = pd.DataFrame([
            {"Title": r["title"], "Doctor": r.get("doctor_name",""), "Date": r.get("date","-")}
        for r in rows])
        st.table(df)
    st.markdown("</div>", unsafe_allow_html=True)

def view_medicines_ui():
    st.markdown("<div class='main-content slide-in-left'>", unsafe_allow_html=True)
    st.header("All Medicines")
    if med_col is None:
        st.error("DB not configured.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    rows = list(med_col.find({"user_id": st.session_state["user"]["_id"]}).sort("created_at", -1))
    if not rows:
        st.info("No medicines yet.")
    else:
        df = pd.DataFrame([{
            "Name": r["name"],
            "Dosage": r.get("dosage",""),
            "Frequency": r.get("frequency",""),
            "Times": ", ".join(r.get("times",[])),
            "Start": r.get("start_date",""),
            "End": r.get("end_date",""),
            "Prescription": str(r.get("prescription_id") or "")
        } for r in rows])
        st.dataframe(df, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<div style='font-weight:800;color:#11ff88;font-size:20px;margin-bottom:12px'>MedGlow</div>", unsafe_allow_html=True)

    if st.session_state["user"] is None:
        if st.button("🔐 Login", key="b_login"): st.session_state["page"]="login"
        if st.button("✍️ Signup", key="b_signup"): st.session_state["page"]="signup"
    else:
        st.markdown(f"<div style='margin-bottom:12px;color:#eafff4'>Signed in: <b>{st.session_state['user']['name']}</b></div>", unsafe_allow_html=True)
        if st.button("🏠 Dashboard", key="b_dash"): st.session_state["page"]="dashboard"
        if st.button("➕ Add Prescription", key="b_addp"): st.session_state["page"]="add_p"
        if st.button("💊 Add Medicine", key="b_addm"): st.session_state["page"]="add_m"
        if st.button("📄 Prescriptions", key="b_viewp"): st.session_state["page"]="view_p"
        if st.button("🧾 Medicines", key="b_viewm"): st.session_state["page"]="view_m"
        if st.button("🚪 Logout", key="b_logout"): logout_ui()

page = st.session_state.get("page", "login")

if page == "login":
    login_ui()
elif page == "signup":
    signup_ui()
else:
    if st.session_state["user"] is None:
        st.warning("Please login first.")
        st.session_state["page"] = "login"
        st.rerun()
    else:
        if page == "dashboard":
            dashboard_ui()
        elif page == "add_p":
            add_prescription_ui()
        elif page == "add_m":
            add_medicine_ui()
        elif page == "view_p":
            view_prescriptions_ui()
        elif page == "view_m":
            view_medicines_ui()
        else:
            st.info("Page not found. Resetting.")
            st.session_state["page"] = "dashboard"
            st.rerun()
def notification_settings_ui():
    st.markdown("<div class='main-content slide-in-left'>", unsafe_allow_html=True)
    st.header("Notification Settings")

    user = st.session_state["user"]
    current_pref = user.get("notification_pref", "email")

    new_pref = st.radio(
        "Choose how you want reminders:",
        ["email", "popup", "both"],
        index=["email", "popup", "both"].index(current_pref)
    )

    if st.button("Save Settings"):
        if users_col is not None:
            users_col.update_one(
                {"_id": user["_id"]},
                {"$set": {"notification_pref": new_pref}}
            )
            st.session_state["user"]["notification_pref"] = new_pref
            st.success("Updated!")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
