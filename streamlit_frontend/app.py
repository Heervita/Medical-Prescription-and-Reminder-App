# streamlit_frontend/app.py
import streamlit as st
import requests
from datetime import date, time

# ==========================
# CONFIG
# ==========================
st.set_page_config(
    page_title="MedGlow",
    page_icon="💊",
    layout="wide"
)

# 👉 YAHAN APNA BACKEND URL DALO
BACKEND_URL = "http://127.0.0.1:8000"   # FastAPI default

# ==========================
# CUSTOM CSS FOR BEAUTIFUL UI
# ==========================
CUSTOM_CSS = """
<style>
.stApp {
    background: radial-gradient(circle at top left, #e0f7f5, #f8fffe);
    font-family: "Poppins", sans-serif;
}
.main-title {
    font-size: 34px;
    font-weight: 700;
    color: #00695c;
}
.sub-title {
    font-size: 16px;
    color: #5f6c76;
}
.glass-card {
    background: rgba(255, 255, 255, 0.85);
    border-radius: 18px;
    padding: 20px 24px;
    box-shadow: 0 20px 45px rgba(0,0,0,0.08);
    border: 1px solid rgba(255,255,255,0.8);
}
.metric-card {
    background: rgba(255,255,255,0.92);
    border-radius: 16px;
    padding: 16px 18px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    border-left: 4px solid #00bfa5;
}
.stButton>button {
    border-radius: 999px;
    padding: 0.4rem 1.3rem;
    font-weight: 600;
    border: none;
    background: linear-gradient(135deg,#00c9a7,#00897b);
    color: white;
    box-shadow: 0 10px 20px rgba(0, 137, 123, 0.3);
}
.stButton>button:hover {
    transform: translateY(-1px);
}
.chip {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    background: #e0f2f1;
    color: #004d40;
    font-size: 12px;
    margin-right: 6px;
}
.dataframe tbody tr:hover {
    background-color: #e0f7fa !important;
}
.pill-icon {
    width: 32px;
    height: 32px;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg,#ff9a9e,#fad0c4);
    margin-right: 8px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==========================
# SESSION STATE INIT
# ==========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None

# ==========================
# API HELPERS
# ==========================
def api_post(path: str, payload: dict, auth: bool = False):
    url = f"{BACKEND_URL}{path}"
    headers = {}
    if auth and st.session_state.auth_token:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        return resp
    except Exception as e:
        st.error(f"Backend se connect nahi ho paaya: {e}")
        return None

def api_get(path: str, params: dict = None, auth: bool = False):
    url = f"{BACKEND_URL}{path}"
    headers = {}
    if auth and st.session_state.auth_token:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        return resp
    except Exception as e:
        st.error(f"Backend se connect nahi ho paaya: {e}")
        return None

# ==========================
# AUTH SCREENS
# ==========================
def show_login_page():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h2 class='main-title'>Welcome to MedGlow 💊</h2>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Sign in to manage your prescriptions & reminders.</p>", unsafe_allow_html=True)

    col1, col2 = st.columns([2,1])
    with col1:
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter password")

        if st.button("Sign In"):
            if not email or not password:
                st.warning("Email & password daalo 🙂")
            else:
                # 👉 yahan tumhare backend ka login route aayega
                resp = api_post("/auth/login", {"email": email, "password": password}, auth=False)
                if resp is None:
                    return
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.logged_in = True
                    st.session_state.auth_token = data.get("access_token") or data.get("token")
                    st.session_state.user_name = data.get("name") or "User"
                    st.success("Logged in successfully ✅")
                    st.experimental_rerun()
                else:
                    st.error(f"Login failed ❌ ({resp.status_code}) - {resp.text}")

        st.info("New here? Neeche signup form hai.")

    with col2:
        st.markdown("### ⏱ Next dose preview")
        st.markdown("**09:00 AM** · Paracetamol 500mg")
        st.markdown("**02:00 PM** · Vitamin C")
        st.markdown("**09:30 PM** · Antibiotic")

    st.markdown("</div>", unsafe_allow_html=True)
    st.write("")
    show_signup_section()

def show_signup_section():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### Create a new account 🩺")
    name = st.text_input("Full Name", key="signup_name")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")

    if st.button("Create Account"):
        if not name or not email or not password:
            st.warning("Saare fields bhar do 🙂")
        else:
            resp = api_post("/auth/signup", {"name": name, "email": email, "password": password}, auth=False)
            if resp is None:
                return
            if resp.status_code in (200, 201):
                st.success("Account created ✅, ab upar se login karo.")
            else:
                st.error(f"Signup failed ❌ ({resp.status_code}) - {resp.text}")
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================
# LOGGED-IN PAGES
# ==========================
def show_dashboard():
    st.markdown(
        f"<h2 class='main-title'>Hello, {st.session_state.user_name or 'User'} 👋</h2>",
        unsafe_allow_html=True
    )
    st.markdown("<p class='sub-title'>Your health overview at a glance.</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("**Today's Doses**")
        st.markdown("Taken: **3 / 6**")
        st.markdown("<span class='chip'>On track ✅</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("**Active Prescriptions**")
        st.markdown("**4** prescriptions running")
        st.markdown("<span class='chip'>Review weekly</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markmarkdown("**Upcoming Reminder**")
        st.markdown("In **45 mins** · Vitamin D 💊")
        st.markdown("<span class='chip'>Evening dose</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### Today's Schedule ⏰")
    schedule_data = [
        {"time": "09:00 AM", "name": "Paracetamol 500mg", "note": "After breakfast"},
        {"time": "02:00 PM", "name": "Vitamin C", "note": "With water"},
        {"time": "09:30 PM", "name": "Antibiotic", "note": "Before sleep"},
    ]
    for row in schedule_data:
        col_a, col_b, col_c = st.columns([1, 3, 2])
        with col_a:
            st.write(f"**{row['time']}**")
        with col_b:
            st.write(f"💊 {row['name']}")
        with col_c:
            st.write(row["note"])
    st.markdown("</div>", unsafe_allow_html=True)

def show_add_prescription():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("## Add Prescription 🧾")
    title = st.text_input("Prescription Title", placeholder="e.g. General Checkup")
    doctor_name = st.text_input("Doctor's Name", placeholder="e.g. Dr. Sharma")
    presc_date = st.date_input("Prescription Date", value=date.today())
    notes = st.text_area("Notes (optional)", placeholder="Doctor's notes, diagnosis, etc.")

    if st.button("Save Prescription"):
        payload = {
            "title": title,
            "doctor_name": doctor_name,
            "date": str(presc_date),
            "notes": notes
        }
        resp = api_post("/prescriptions", payload, auth=True)
        if resp is None:
            return
        if resp.status_code in (200, 201):
            st.success("Prescription saved ✅")
        else:
            st.error(f"Error saving prescription ❌ ({resp.status_code}) - {resp.text}")
    st.markdown("</div>", unsafe_allow_html=True)

def show_add_medicine():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("## Add Medicine 💊")
    col1, col2 = st.columns(2)
    with col1:
        prescription_id = st.text_input("Prescription ID (optional)")
        name = st.text_input("Medicine Name", placeholder="e.g. Paracetamol")
        dosage = st.text_input("Dosage", placeholder="e.g. 1 tablet")
        frequency = st.number_input("Times per day", min_value=1, max_value=10, step=1, value=3)
    with col2:
        med_type = st.selectbox("Medicine Type", ["Tablet", "Capsule", "Syrup", "Injection", "Other"])
        start_date = st.date_input("Start Date", value=date.today())
        end_date = st.date_input("End Date", value=date.today())

    st.markdown("### Reminder Times ⏰")
    times = []
    for i in range(frequency):
        t = st.time_input(f"Dose {i+1} time", value=time(hour=9 + i*4), key=f"time_{i}")
        times.append(str(t))

    if st.button("Save Medicine"):
        payload = {
            "prescription_id": prescription_id or None,
            "name": name,
            "dosage": dosage,
            "frequency": int(frequency),
            "times": times,
            "type": med_type,
            "start_date": str(start_date),
            "end_date": str(end_date),
        }
        resp = api_post("/medicines", payload, auth=True)
        if resp is None:
            return
        if resp.status_code in (200, 201):
            st.success("Medicine saved ✅")
        else:
            st.error(f"Error saving medicine ❌ ({resp.status_code}) - {resp.text}")
    st.markdown("</div>", unsafe_allow_html=True)

def show_view_prescriptions():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("## All Prescriptions 📋")
    resp = api_get("/prescriptions", auth=True)
    if resp is None:
        st.markdown("</div>", unsafe_allow_html=True)
        return
    if resp.status_code == 200:
        data = resp.json()
        if not data:
            st.info("Abhi koi prescription add nahi hai.")
        else:
            for p in data:
                with st.expander(f"{p.get('title', 'Untitled')} · {p.get('doctor_name', 'Unknown doctor')}"):
                    st.write(f"**Date:** {p.get('date', '-')}")
                    st.write(f"**Notes:** {p.get('notes', '-')}")
                    meds = p.get("medicines", [])
                    if meds:
                        st.write("### Medicines:")
                        for m in meds:
                            st.write(f"- {m.get('name')} — {m.get('dosage')} × {m.get('frequency')} / day")
    else:
        st.error(f"Failed to load prescriptions ({resp.status_code}) - {resp.text}")
    st.markdown("</div>", unsafe_allow_html=True)

def show_view_medicines():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("## All Medicines 💚")
    view_type = st.radio("View as", ["Cards", "Table"], horizontal=True)

    resp = api_get("/medicines", auth=True)
    if resp is None:
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if resp.status_code == 200:
        meds = resp.json()
        if not meds:
            st.info("Abhi koi medicine add nahi hai.")
        else:
            if view_type == "Cards":
                for m in meds:
                    col_icon, col_content = st.columns([1, 5])
                    with col_icon:
                        st.markdown("<div class='pill-icon'>💊</div>", unsafe_allow_html=True)
                    with col_content:
                        st.write(f"**{m.get('name')}** ({m.get('dosage')})")
                        st.write(f"Frequency: **{m.get('frequency')} / day**")
                        st.write(f"Times: {', '.join(m.get('times', []))}")
                        st.caption(
                            f"Start: {m.get('start_date','-')} · End: {m.get('end_date','-')} · "
                            f"Prescription: {m.get('prescription_id','N/A')}"
                        )
                        st.write("---")
            else:
                import pandas as pd
                df = pd.DataFrame(meds)
                st.dataframe(df, use_container_width=True)
    else:
        st.error(f"Failed to load medicines ({resp.status_code}) - {resp.text}")
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================
# MAIN
# ==========================
def main():
    if not st.session_state.logged_in:
        show_login_page()
        return

    with st.sidebar:
        st.markdown("## MedGlow 💊")
        st.write(f"Logged in as: **{st.session_state.user_name}**")
        page = st.radio(
            "Navigate",
            ["Dashboard", "Add Prescription", "Add Medicine", "View Prescriptions", "View Medicines"],
            label_visibility="collapsed"
        )
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.auth_token = None
            st.session_state.user_name = None
            st.experimental_rerun()

    if page == "Dashboard":
        show_dashboard()
    elif page == "Add Prescription":
        show_add_prescription()
    elif page == "Add Medicine":
        show_add_medicine()
    elif page == "View Prescriptions":
        show_view_prescriptions()
    elif page == "View Medicines":
        show_view_medicines()

if __name__ == "__main__":
    main()
