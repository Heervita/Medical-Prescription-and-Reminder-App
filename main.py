from fastapi import FastAPI
from routes import auth, prescription, reminder
# import threading
# from scheduler import start_scheduler

# # Run scheduler in background thread
# threading.Thread(target=start_scheduler, daemon=True).start()


app = FastAPI()

app.include_router(auth.router)
app.include_router(prescription.router)
app.include_router(reminder.router)

@app.get("/")
def home():
    return {"message": "Medical App Backend Running"}
